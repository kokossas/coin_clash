import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base_class import Base
from app.models.models import (
    Character, Match, MatchEvent, MatchJoinRequest, OwnedCharacter, Player,
)
from app.services.match_lobby import MatchLobbyService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = Session()
    try:
        yield db
    finally:
        db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def mock_payment():
    provider = AsyncMock()
    provider.process_deposit.return_value = {
        "success": True,
        "transaction_id": "mock-tx-1",
        "status": "completed",
        "amount": 1.0,
        "currency": "USDC",
    }
    return provider


MOCK_CONFIG = {
    "listing_fee": 0.1,
    "character_base_price": 1.0,
    "character_revival_fee": 0.5,
}


@pytest.fixture
def service(mock_payment):
    with patch(
        "app.services.match_lobby.BlockchainServiceFactory.get_payment_provider",
        return_value=mock_payment,
    ), patch(
        "app.services.match_lobby.load_config",
        return_value=MOCK_CONFIG,
    ):
        svc = MatchLobbyService()
    return svc


@pytest.fixture
def player(db_session):
    p = Player(wallet_address="0xabc123", username="tester", balance=100.0)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


@pytest.fixture
def player2(db_session):
    p = Player(wallet_address="0xdef456", username="tester2", balance=100.0)
    db_session.add(p)
    db_session.commit()
    db_session.refresh(p)
    return p


def _make_owned_char(db_session, player, name="Warrior", is_alive=True):
    oc = OwnedCharacter(
        player_id=player.id,
        character_name=name,
        is_alive=is_alive,
        revival_count=0,
    )
    db_session.add(oc)
    db_session.commit()
    db_session.refresh(oc)
    return oc


def _make_filling_match(db_session, **overrides):
    defaults = dict(
        entry_fee=1.0,
        kill_award_rate=0.1,
        start_method="cap",
        start_threshold=60,
        status="filling",
        min_players=3,
        max_characters=20,
        max_characters_per_player=3,
        protocol_fee_percentage=Decimal("10.0"),
        creator_wallet_address="0xcreator",
    )
    defaults.update(overrides)
    m = Match(**defaults)
    db_session.add(m)
    db_session.commit()
    db_session.refresh(m)
    return m


class TestCreateMatchLobby:

    @pytest.mark.asyncio
    async def test_creates_match_with_filling_status(self, service, db_session):
        match = await service.create_match_lobby(
            db_session,
            creator_wallet_address="0xcreator",
            entry_fee=1.0,
            kill_award_rate=0.1,
            start_method="cap",
            start_threshold=60,
            min_players=3,
            max_characters=20,
            max_characters_per_player=3,
        )
        assert match.status == "filling"
        assert match.creator_wallet_address == "0xcreator"
        assert match.min_players == 3
        assert match.max_characters == 20
        assert match.max_characters_per_player == 3

    @pytest.mark.asyncio
    async def test_rejects_min_players_out_of_range(self, service, db_session):
        with pytest.raises(ValueError, match="min_players"):
            await service.create_match_lobby(
                db_session,
                creator_wallet_address="0xcreator",
                entry_fee=1.0,
                kill_award_rate=0.1,
                start_method="cap",
                start_threshold=60,
                min_players=2,
            )

    @pytest.mark.asyncio
    async def test_rejects_max_characters_below_min_players(self, service, db_session):
        with pytest.raises(ValueError, match="max_characters"):
            await service.create_match_lobby(
                db_session,
                creator_wallet_address="0xcreator",
                entry_fee=1.0,
                kill_award_rate=0.1,
                start_method="cap",
                start_threshold=60,
                min_players=5,
                max_characters=4,
            )

    @pytest.mark.asyncio
    async def test_deducts_listing_fee(self, service, mock_payment, db_session):
        await service.create_match_lobby(
            db_session,
            creator_wallet_address="0xcreator",
            entry_fee=1.0,
            kill_award_rate=0.1,
            start_method="cap",
            start_threshold=60,
        )
        mock_payment.process_deposit.assert_called_once_with(
            wallet_address="0xcreator",
            amount=0.1,
            currency="USDC",
        )


class TestJoinMatch:

    @pytest.mark.asyncio
    async def test_successful_join(self, service, db_session, player):
        match = _make_filling_match(db_session)
        oc = _make_owned_char(db_session, player)

        jr = await service.join_match(
            db_session, match.id, player.id, [oc.id], player.wallet_address,
        )

        assert jr.payment_status == "confirmed"
        assert jr.confirmed_at is not None

        chars = db_session.query(Character).filter(Character.match_id == match.id).all()
        assert len(chars) == 1
        assert chars[0].owned_character_id == oc.id
        assert chars[0].entry_order == 1
        assert chars[0].player_id == player.id

    @pytest.mark.asyncio
    async def test_rejects_non_filling_match(self, service, db_session, player):
        match = _make_filling_match(db_session, status="pending")
        oc = _make_owned_char(db_session, player)

        with pytest.raises(ValueError, match="not accepting joins"):
            await service.join_match(
                db_session, match.id, player.id, [oc.id], player.wallet_address,
            )

    @pytest.mark.asyncio
    async def test_rejects_dead_character(self, service, db_session, player):
        match = _make_filling_match(db_session)
        oc = _make_owned_char(db_session, player, is_alive=False)

        with pytest.raises(ValueError, match="not alive"):
            await service.join_match(
                db_session, match.id, player.id, [oc.id], player.wallet_address,
            )

    @pytest.mark.asyncio
    async def test_rejects_character_in_another_active_match(
        self, service, db_session, player,
    ):
        other_match = _make_filling_match(db_session)
        oc = _make_owned_char(db_session, player)
        # Place character in the other match
        db_session.add(Character(
            name=oc.character_name,
            player_id=player.id,
            match_id=other_match.id,
            owned_character_id=oc.id,
            entry_order=1,
        ))
        db_session.commit()

        new_match = _make_filling_match(db_session)
        with pytest.raises(ValueError, match="already in a filling or active match"):
            await service.join_match(
                db_session, new_match.id, player.id, [oc.id], player.wallet_address,
            )

    @pytest.mark.asyncio
    async def test_rejects_exceeding_per_player_limit(
        self, service, db_session, player,
    ):
        match = _make_filling_match(db_session, max_characters_per_player=1)
        oc1 = _make_owned_char(db_session, player, name="W1")
        oc2 = _make_owned_char(db_session, player, name="W2")

        with pytest.raises(ValueError, match="per-player character limit"):
            await service.join_match(
                db_session, match.id, player.id, [oc1.id, oc2.id],
                player.wallet_address,
            )

    @pytest.mark.asyncio
    async def test_rejects_exceeding_total_limit(
        self, service, db_session, player, player2,
    ):
        match = _make_filling_match(db_session, max_characters=1, min_players=3)
        # Fill the single slot with player2's character
        oc_other = _make_owned_char(db_session, player2, name="Other")
        db_session.add(Character(
            name="Other",
            player_id=player2.id,
            match_id=match.id,
            owned_character_id=oc_other.id,
            entry_order=1,
        ))
        db_session.commit()

        oc = _make_owned_char(db_session, player)
        with pytest.raises(ValueError, match="full"):
            await service.join_match(
                db_session, match.id, player.id, [oc.id], player.wallet_address,
            )

    @pytest.mark.asyncio
    async def test_rollback_on_payment_failure(
        self, service, mock_payment, db_session, player,
    ):
        match = _make_filling_match(db_session)
        oc = _make_owned_char(db_session, player)

        mock_payment.process_deposit.side_effect = RuntimeError("payment failed")

        with pytest.raises(RuntimeError):
            await service.join_match(
                db_session, match.id, player.id, [oc.id], player.wallet_address,
            )

        assert db_session.query(MatchJoinRequest).count() == 0
        assert (
            db_session.query(Character)
            .filter(Character.match_id == match.id)
            .count()
            == 0
        )


class TestCheckStartConditions:

    def _add_characters_for_players(self, db_session, match, players_and_chars):
        """Add Character rows for each (player, owned_char) pair."""
        order = 1
        for player, oc in players_and_chars:
            db_session.add(Character(
                name=oc.character_name,
                player_id=player.id,
                match_id=match.id,
                owned_character_id=oc.id,
                entry_order=order,
            ))
            order += 1
        db_session.commit()

    @patch("app.services.match_lobby.TaskScheduler")
    def test_starts_countdown_at_min_players(
        self, mock_scheduler_cls, service, db_session,
    ):
        mock_scheduler = MagicMock()
        mock_scheduler_cls.get_instance.return_value = mock_scheduler

        match = _make_filling_match(db_session, min_players=3, max_characters=20)

        players_chars = []
        for i in range(3):
            p = Player(wallet_address=f"0xplayer{i}", balance=0.0)
            db_session.add(p)
            db_session.commit()
            db_session.refresh(p)
            oc = _make_owned_char(db_session, p, name=f"Char{i}")
            players_chars.append((p, oc))

        self._add_characters_for_players(db_session, match, players_chars)

        result = service.check_start_conditions(db_session, match.id)

        assert result is True
        db_session.refresh(match)
        assert match.countdown_started_at is not None
        assert match.start_timer_end is not None
        mock_scheduler.schedule_match_start.assert_called_once()

    @patch.object(MatchLobbyService, "_run_match_background")
    def test_starts_immediately_at_max_characters(
        self, mock_run, service, db_session, player, player2,
    ):
        match = _make_filling_match(
            db_session, min_players=2, max_characters=2,
        )
        # min_players=2 is invalid for create_match_lobby but fine for direct DB setup
        oc1 = _make_owned_char(db_session, player, name="C1")
        oc2 = _make_owned_char(db_session, player2, name="C2")
        self._add_characters_for_players(
            db_session, match, [(player, oc1), (player2, oc2)],
        )

        result = service.check_start_conditions(db_session, match.id)

        assert result is True
        db_session.refresh(match)
        assert match.status == "active"
        mock_run.assert_called_once_with(match.id, db_session)

    @patch("app.services.match_lobby.TaskScheduler")
    def test_noop_if_already_counting_down(
        self, mock_scheduler_cls, service, db_session,
    ):
        import datetime
        match = _make_filling_match(
            db_session,
            min_players=3,
            max_characters=20,
            countdown_started_at=datetime.datetime.now(datetime.timezone.utc),
        )

        players_chars = []
        for i in range(3):
            p = Player(wallet_address=f"0xplayer{i}", balance=0.0)
            db_session.add(p)
            db_session.commit()
            db_session.refresh(p)
            oc = _make_owned_char(db_session, p, name=f"Char{i}")
            players_chars.append((p, oc))

        self._add_characters_for_players(db_session, match, players_chars)

        original_countdown = match.countdown_started_at
        result = service.check_start_conditions(db_session, match.id)

        assert result is False
        db_session.refresh(match)
        assert match.countdown_started_at == original_countdown


class TestCalculateAndStorePayouts:

    def _setup_match_with_characters(self, db_session, num_chars_per_player, players,
                                     entry_fee=1.0, kill_award_rate=0.1,
                                     protocol_fee_pct="10.0",
                                     winner_character_id=None):
        match = Match(
            entry_fee=entry_fee,
            kill_award_rate=kill_award_rate,
            start_method="cap",
            start_threshold=60,
            status="completed",
            protocol_fee_percentage=Decimal(protocol_fee_pct),
            winner_character_id=winner_character_id,
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        chars = []
        order = 1
        for player, count in zip(players, num_chars_per_player):
            for j in range(count):
                c = Character(
                    name=f"C{order}",
                    player_id=player.id,
                    match_id=match.id,
                    entry_order=order,
                )
                db_session.add(c)
                db_session.flush()
                chars.append(c)
                order += 1
        db_session.commit()
        return match, chars

    def test_basic_payout_split(self, service, db_session, player, player2):
        p3 = Player(wallet_address="0xp3", balance=0.0)
        p4 = Player(wallet_address="0xp4", balance=0.0)
        db_session.add_all([p3, p4])
        db_session.commit()

        match, chars = self._setup_match_with_characters(
            db_session,
            num_chars_per_player=[1, 1, 1, 1],
            players=[player, player2, p3, p4],
            entry_fee=1.0,
            kill_award_rate=0.1,
            protocol_fee_pct="10.0",
        )
        # Set winner
        match.winner_character_id = chars[0].id
        db_session.commit()

        # 1 kill event: chars[0] kills chars[1]
        db_session.add(MatchEvent(
            match_id=match.id,
            round_number=1,
            event_type="direct_kill",
            scenario_source="test",
            scenario_text="kill",
            affected_character_ids=f"{chars[0].id},{chars[1].id}",
        ))
        db_session.commit()

        payouts = service.calculate_and_store_payouts(db_session, match.id)

        # total_pool = 4 * 1.0 = 4.0
        # protocol_fee = 4.0 * 10% = 0.4
        # pool_after_protocol = 3.6
        # kill_award for player: 1 * 1.0 * 0.1 = 0.1
        # winner_payout = 3.6 - 0.1 = 3.5
        kill_awards = [p for p in payouts if p.payout_type == "kill_award"]
        winner_awards = [p for p in payouts if p.payout_type == "winner"]

        assert len(kill_awards) == 1
        assert float(kill_awards[0].amount) == 0.1
        assert kill_awards[0].player_id == player.id

        assert len(winner_awards) == 1
        assert float(winner_awards[0].amount) == 3.5
        assert winner_awards[0].player_id == player.id

        total_paid = sum(float(p.amount) for p in payouts)
        assert total_paid == pytest.approx(3.6)

    def test_kill_award_capped_at_player_entry_total(
        self, service, db_session, player, player2,
    ):
        match, chars = self._setup_match_with_characters(
            db_session,
            num_chars_per_player=[1, 3],
            players=[player, player2],
            entry_fee=1.0,
            kill_award_rate=0.5,
        )
        match.winner_character_id = chars[0].id
        db_session.commit()

        # player (1 char) gets 3 kills — raw award = 3 * 1.0 * 0.5 = 1.5
        # but cap = 1 char * 1.0 entry_fee = 1.0
        for i in range(3):
            db_session.add(MatchEvent(
                match_id=match.id,
                round_number=i + 1,
                event_type="direct_kill",
                scenario_source="test",
                scenario_text="kill",
                affected_character_ids=f"{chars[0].id},{chars[1 + i].id}",
            ))
        db_session.commit()

        payouts = service.calculate_and_store_payouts(db_session, match.id)
        kill_awards = [p for p in payouts if p.payout_type == "kill_award"]

        assert len(kill_awards) == 1
        assert float(kill_awards[0].amount) == 1.0

    def test_total_kill_awards_capped(self, service, db_session, player, player2):
        # Extreme kill_award_rate so raw total exceeds pool_after_protocol
        match, chars = self._setup_match_with_characters(
            db_session,
            num_chars_per_player=[5, 5],
            players=[player, player2],
            entry_fee=1.0,
            kill_award_rate=0.5,
            protocol_fee_pct="50.0",
        )
        # total_pool=10, protocol_fee=5, pool_after_protocol=5
        # Each player kills 5 of the other's chars → raw award = 5*1.0*0.5 = 2.5 each
        # Per-player cap = 5*1.0 = 5.0 (not hit)
        # Total raw = 5.0, equals pool_after_protocol exactly → no scaling needed
        # But let's push harder: give player 5 kills with rate that exceeds pool
        match.kill_award_rate = 2.0
        db_session.commit()
        # raw per player = 5 * 1.0 * 2.0 = 10.0, capped at 5.0 each → total = 10.0
        # pool_after_protocol = 5.0 → must scale down

        for i in range(5):
            db_session.add(MatchEvent(
                match_id=match.id, round_number=i + 1,
                event_type="direct_kill", scenario_source="test",
                scenario_text="kill",
                affected_character_ids=f"{chars[i].id},{chars[5 + i].id}",
            ))
            db_session.add(MatchEvent(
                match_id=match.id, round_number=i + 1,
                event_type="direct_kill", scenario_source="test",
                scenario_text="kill",
                affected_character_ids=f"{chars[5 + i].id},{chars[i].id}",
            ))
        db_session.commit()

        payouts = service.calculate_and_store_payouts(db_session, match.id)

        total_kill = sum(float(p.amount) for p in payouts if p.payout_type == "kill_award")
        total_winner = sum(float(p.amount) for p in payouts if p.payout_type == "winner")

        assert total_kill <= 5.0 + 0.01  # pool_after_protocol
        assert total_winner >= 0

    def test_no_payouts_for_match_without_characters(self, service, db_session):
        match = Match(
            entry_fee=1.0,
            kill_award_rate=0.1,
            start_method="cap",
            start_threshold=60,
            status="completed",
            protocol_fee_percentage=Decimal("10.0"),
        )
        db_session.add(match)
        db_session.commit()
        db_session.refresh(match)

        payouts = service.calculate_and_store_payouts(db_session, match.id)
        assert payouts == []

    def test_no_winner_payout_if_no_winner_set(self, service, db_session, player, player2):
        match, chars = self._setup_match_with_characters(
            db_session,
            num_chars_per_player=[1, 1],
            players=[player, player2],
            entry_fee=1.0,
            kill_award_rate=0.1,
            winner_character_id=None,
        )

        db_session.add(MatchEvent(
            match_id=match.id,
            round_number=1,
            event_type="direct_kill",
            scenario_source="test",
            scenario_text="kill",
            affected_character_ids=f"{chars[0].id},{chars[1].id}",
        ))
        db_session.commit()

        payouts = service.calculate_and_store_payouts(db_session, match.id)

        assert all(p.payout_type == "kill_award" for p in payouts)
        assert not any(p.payout_type == "winner" for p in payouts)
