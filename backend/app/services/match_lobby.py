import datetime
import logging
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.crud.match import crud_match
from backend.app.crud.match_join_request import crud_match_join_request
from backend.app.crud.owned_character import crud_owned_character
from backend.app.crud.pending_payout import crud_pending_payout
from backend.app.models.models import (
    Character,
    Match,
    MatchEvent,
    MatchJoinRequest,
    OwnedCharacter,
    PendingPayout,
)
from backend.app.schemas.match import MatchCreate
from backend.app.schemas.pending_payout import PendingPayoutCreate
from backend.app.services.blockchain.factory import BlockchainServiceFactory
from backend.app.services.payout_calculator import (
    CharacterInfo,
    KillEvent,
    calculate_payouts,
)
from core.config.config_loader import load_config
from core.scheduler.scheduler import TaskScheduler

logger = logging.getLogger(__name__)


class MatchLobbyService:

    def __init__(self) -> None:
        self._config = load_config()
        self._payment = BlockchainServiceFactory.get_payment_provider()

    async def create_match_lobby(
        self,
        db: Session,
        creator_wallet_address: str,
        entry_fee: float,
        kill_award_rate: float,
        start_method: str,
        start_threshold: int,
        min_players: int = 3,
        max_characters: int = 20,
        max_characters_per_player: int = 3,
    ) -> Match:
        cfg = self._config
        if not (cfg.min_fee <= entry_fee <= cfg.max_fee):
            raise ValueError(
                f"entry_fee must be between {cfg.min_fee} and {cfg.max_fee}"
            )
        if not (cfg.kill_award_rate_min <= kill_award_rate <= cfg.kill_award_rate_max):
            raise ValueError(
                f"kill_award_rate must be between {cfg.kill_award_rate_min} and {cfg.kill_award_rate_max}"
            )
        if not (cfg.num_players_min <= min_players <= cfg.num_players_max):
            raise ValueError(
                f"min_players must be between {cfg.num_players_min} and {cfg.num_players_max}"
            )
        if max_characters < min_players or max_characters > 100:
            raise ValueError("max_characters must be >= min_players and <= 100")
        if not (cfg.chars_per_player_min <= max_characters_per_player <= cfg.chars_per_player_max):
            raise ValueError(
                f"max_characters_per_player must be between {cfg.chars_per_player_min} and {cfg.chars_per_player_max}"
            )

        listing_fee = self._config.listing_fee
        await self._payment.process_deposit(
            wallet_address=creator_wallet_address,
            amount=listing_fee,
            currency="USDC",
        )

        match_in = MatchCreate(
            entry_fee=entry_fee,
            kill_award_rate=kill_award_rate,
            start_method=start_method,
            start_threshold=start_threshold,
            status="filling",
            creator_wallet_address=creator_wallet_address,
            min_players=min_players,
            max_characters=max_characters,
            max_characters_per_player=max_characters_per_player,
        )
        match = crud_match.create(db, obj_in=match_in)
        return match

    async def join_match(
        self,
        db: Session,
        match_id: int,
        player_id: int,
        owned_character_ids: List[int],
        payment_ref: str,
    ) -> MatchJoinRequest:
        try:
            match = crud_match.get(db, match_id)
            if match is None:
                raise ValueError(f"Match {match_id} not found")
            if match.status != "filling":
                raise ValueError(f"Match is not accepting joins (status={match.status})")

            owned_chars = crud_owned_character.get_by_ids_and_player(
                db, ids=owned_character_ids, player_id=player_id,
            )
            if len(owned_chars) != len(owned_character_ids):
                raise ValueError("One or more characters not found or not owned by player")
            for oc in owned_chars:
                if not oc.is_alive:
                    raise ValueError(f"Character {oc.id} is not alive")

            # Check none are in another filling/active match
            in_other_match = (
                db.query(Character.owned_character_id)
                .join(Match, Character.match_id == Match.id)
                .filter(
                    Character.owned_character_id.in_(owned_character_ids),
                    Match.status.in_(["filling", "active"]),
                )
                .all()
            )
            if in_other_match:
                raise ValueError("One or more characters are already in a filling or active match")

            # Per-player character limit
            existing_count = (
                db.query(func.count(Character.id))
                .filter(
                    Character.match_id == match_id,
                    Character.player_id == player_id,
                )
                .scalar()
            ) or 0
            if existing_count + len(owned_character_ids) > match.max_characters_per_player:
                raise ValueError("Exceeds per-player character limit for this match")

            # Total character limit
            total_count = (
                db.query(func.count(Character.id))
                .filter(Character.match_id == match_id)
                .scalar()
            ) or 0
            if total_count + len(owned_character_ids) > match.max_characters:
                raise ValueError("Match is full")

            entry_fee_total = len(owned_character_ids) * match.entry_fee

            # Tiered protocol fee: rate depends on number of characters entered
            fee_tiers = self._config.protocol_fee_tiers
            char_count = len(owned_character_ids)
            tier_key = min(char_count, max(fee_tiers.keys()))
            protocol_rate = fee_tiers[tier_key] / 100.0
            protocol_fee = entry_fee_total * protocol_rate

            await self._payment.process_deposit(
                wallet_address=payment_ref,
                amount=entry_fee_total,
                currency="USDC",
            )

            join_request = crud_match_join_request.create_with_characters(
                db,
                match_id=match_id,
                player_id=player_id,
                entry_fee_total=entry_fee_total,
                protocol_fee=protocol_fee,
                owned_character_ids=owned_character_ids,
            )

            join_request.payment_status = "confirmed"
            join_request.confirmed_at = datetime.datetime.now(datetime.timezone.utc)
            db.flush()

            # Determine next entry_order
            max_order = (
                db.query(func.max(Character.entry_order))
                .filter(Character.match_id == match_id)
                .scalar()
            ) or 0

            for i, oc in enumerate(owned_chars):
                char = Character(
                    name=oc.character_name,
                    player_id=player_id,
                    match_id=match_id,
                    owned_character_id=oc.id,
                    entry_order=max_order + i + 1,
                )
                db.add(char)
            db.flush()

            db.commit()

        except Exception:
            db.rollback()
            raise

        self.check_start_conditions(db, match_id)
        return join_request

    def check_start_conditions(self, db: Session, match_id: int) -> bool:
        match = crud_match.get(db, match_id)
        if match is None or match.status != "filling":
            return False

        characters = (
            db.query(Character)
            .filter(Character.match_id == match_id)
            .all()
        )
        unique_players = len({c.player_id for c in characters})
        total_characters = len(characters)

        if total_characters >= match.max_characters:
            match.status = "active"
            db.commit()
            self._run_match_background(match_id, db)
            return True

        if unique_players >= match.min_players and match.countdown_started_at is None:
            match.countdown_started_at = datetime.datetime.now(datetime.timezone.utc)
            match.start_timer_end = (
                match.countdown_started_at
                + datetime.timedelta(seconds=match.start_threshold)
            )
            db.commit()

            scheduler = TaskScheduler.get_instance()
            scheduler.schedule_match_start(
                match_id=match_id,
                execute_at=match.start_timer_end,
                match_service_factory=lambda: _MatchStarter(db),
            )
            return True

        return False

    def _run_match_background(self, match_id: int, db: Session) -> None:
        from backend.app.services.match_runner import run_match_background
        run_match_background(match_id, db)

    def calculate_and_store_payouts(
        self, db: Session, match_id: int
    ) -> List[PendingPayout]:
        match = crud_match.get(db, match_id)
        if match is None:
            raise ValueError(f"Match {match_id} not found")

        match_characters = (
            db.query(Character)
            .filter(Character.match_id == match_id)
            .all()
        )
        if not match_characters:
            return []

        confirmed_joins = crud_match_join_request.get_confirmed_by_match(db, match_id)
        protocol_fee = sum(float(jr.protocol_fee) for jr in confirmed_joins)

        kill_events_db = (
            db.query(MatchEvent)
            .filter(
                MatchEvent.match_id == match_id,
                MatchEvent.event_type == "direct_kill",
            )
            .all()
        )

        characters = [
            CharacterInfo(character_id=c.id, player_id=c.player_id)
            for c in match_characters
        ]
        kill_events = []
        for event in kill_events_db:
            if not event.affected_character_ids:
                continue
            ids = event.affected_character_ids.split(",")
            kill_events.append(KillEvent(killer_character_id=int(ids[0].strip())))

        result = calculate_payouts(
            characters=characters,
            kill_events=kill_events,
            entry_fee=match.entry_fee,
            kill_award_rate=match.kill_award_rate,
            protocol_fee=protocol_fee,
            winner_character_id=match.winner_character_id,
        )

        payouts: List[PendingPayout] = []

        for player_id, amount in result.kill_awards.items():
            if amount <= 0:
                continue
            payout = crud_pending_payout.create(
                db,
                obj_in=PendingPayoutCreate(
                    match_id=match_id,
                    player_id=player_id,
                    payout_type="kill_award",
                    amount=Decimal(str(round(amount, 2))),
                ),
            )
            payouts.append(payout)

        if result.winner_player_id is not None and result.winner_payout > 0:
            payout = crud_pending_payout.create(
                db,
                obj_in=PendingPayoutCreate(
                    match_id=match_id,
                    player_id=result.winner_player_id,
                    payout_type="winner",
                    amount=Decimal(str(round(result.winner_payout, 2))),
                ),
            )
            payouts.append(payout)

        return payouts


class _MatchStarter:
    """Adapter for TaskScheduler.schedule_match_start callback."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def start_match(self, match_id: int) -> bool:
        from backend.app.services.match_runner import run_match_background

        match = crud_match.get(self._db, match_id)
        if match is None or match.status != "filling":
            return False
        match.status = "active"
        self._db.commit()
        run_match_background(match_id, self._db)
        return True
