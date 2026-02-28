"""
Pure payout calculation — no DB, no ORM.

Used by MatchLobbyService (with DB-sourced data) and the simulator
(with in-memory data).
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class PayoutResult:
    total_pool: float
    protocol_fee: float
    pool_after_protocol: float
    kill_awards: Dict[int, float]  # player_id → amount
    total_kill_awards: float
    winner_player_id: Optional[int]
    winner_payout: float


@dataclass
class CharacterInfo:
    character_id: int
    player_id: int


@dataclass
class KillEvent:
    """A single direct_kill event. killer_character_id is the first ID in affected_character_ids."""
    killer_character_id: int


def calculate_payouts(
    characters: List[CharacterInfo],
    kill_events: List[KillEvent],
    entry_fee: float,
    kill_award_rate: float,
    protocol_fee: float,
    winner_character_id: Optional[int],
) -> PayoutResult:
    if not characters:
        return PayoutResult(
            total_pool=0,
            protocol_fee=protocol_fee,
            pool_after_protocol=0,
            kill_awards={},
            total_kill_awards=0,
            winner_player_id=None,
            winner_payout=0,
        )

    total_pool = len(characters) * entry_fee
    pool_after_protocol = total_pool - protocol_fee

    char_to_player = {c.character_id: c.player_id for c in characters}

    chars_per_player: Dict[int, int] = {}
    for c in characters:
        chars_per_player[c.player_id] = chars_per_player.get(c.player_id, 0) + 1

    kills_per_player: Dict[int, int] = {}
    for event in kill_events:
        killer_player_id = char_to_player.get(event.killer_character_id)
        if killer_player_id is not None:
            kills_per_player[killer_player_id] = kills_per_player.get(killer_player_id, 0) + 1

    kill_awards: Dict[int, float] = {}
    for player_id, kills in kills_per_player.items():
        raw_award = kills * entry_fee * kill_award_rate
        player_entry_total = chars_per_player.get(player_id, 0) * entry_fee
        kill_awards[player_id] = min(raw_award, player_entry_total)

    total_kill_awards = sum(kill_awards.values())
    # Cap so winner payout doesn't go negative
    if total_kill_awards > pool_after_protocol:
        scale = pool_after_protocol / total_kill_awards if total_kill_awards > 0 else 0
        kill_awards = {pid: amt * scale for pid, amt in kill_awards.items()}
        total_kill_awards = pool_after_protocol

    winner_payout = pool_after_protocol - total_kill_awards

    winner_player_id: Optional[int] = None
    if winner_character_id is not None:
        winner_player_id = char_to_player.get(winner_character_id)

    return PayoutResult(
        total_pool=total_pool,
        protocol_fee=protocol_fee,
        pool_after_protocol=pool_after_protocol,
        kill_awards=kill_awards,
        total_kill_awards=total_kill_awards,
        winner_player_id=winner_player_id,
        winner_payout=winner_payout,
    )
