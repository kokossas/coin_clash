#!/usr/bin/env python3
"""
Simulate a match end-to-end without a database.

Usage:
    python scripts/simulate_match.py
    python scripts/simulate_match.py --players 8 --chars-per-player 2 --entry-fee 2.0 --kill-award-rate 0.15 --seed 99
    python scripts/simulate_match.py --char-distribution 3,1,2,1 --entry-fee 1.0 --seed 7
"""

import argparse
import sys
import os
from typing import Dict, List, Optional
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config.config_loader import load_config
from core.match.scenario_loader import load_scenarios
from core.match.engine import MatchEngine
from backend.app.services.payout_calculator import (
    CharacterInfo,
    KillEvent,
    calculate_payouts,
)


# ---------------------------------------------------------------------------
# Stubs — lightweight in-memory replacements for DB-backed repos
# ---------------------------------------------------------------------------

class SimMatch:
    def __init__(self, match_id: int, entry_fee: float, kill_award_rate: float):
        self.id = match_id
        self.entry_fee = entry_fee
        self.kill_award_rate = kill_award_rate
        self.status = "filling"
        self.winner_character_id: Optional[int] = None


class SimPlayer:
    def __init__(self, player_id: int, username: str):
        self.id = player_id
        self.username = username
        self.kills = 0
        self.wins = 0


class SimCharacter:
    def __init__(self, char_id: int, player_id: int, name: str):
        self.id = char_id
        self.player_id = player_id
        self.name = name
        self.is_alive = True
        self.owned_character_id = None
        self.match_id = 1

    @property
    def player_owner(self):
        return self.name

    @property
    def display_name(self):
        return self.name


class SimMatchRepo:
    def __init__(self, match: SimMatch):
        self._match = match

    def get_match_by_id(self, match_id: int):
        return self._match

    def update_match_status(self, match_id: int, status: str):
        self._match.status = status

    def set_match_start_time(self, match_id: int):
        pass

    def set_match_end_time(self, match_id: int):
        pass

    def set_match_winner(self, match_id: int, winner_character_id: int):
        self._match.winner_character_id = winner_character_id


class SimPlayerRepo:
    def __init__(self, players: Dict[int, SimPlayer]):
        self._players = players

    def get_player_by_id(self, player_id: int):
        return self._players.get(player_id)

    def add_kill(self, player_id: int):
        p = self._players.get(player_id)
        if p:
            p.kills += 1

    def add_win(self, player_id: int):
        p = self._players.get(player_id)
        if p:
            p.wins += 1

    def add_earnings(self, player_id: int, amount: float):
        pass

    def update_player_balance(self, player_id: int, amount: float):
        pass


class SimCharacterRepo:
    def __init__(self, chars: List[SimCharacter]):
        self.status_updates: Dict[int, bool] = {}
        self._chars = {c.id: c for c in chars}
        # Engine's post-match sync accesses self.character_repo.db.query(...)
        self.db = MagicMock()

    def update_character_status(self, character_id: int, is_alive: bool):
        self.status_updates[character_id] = is_alive
        if character_id in self._chars:
            self._chars[character_id].is_alive = is_alive


class SimEventRepo:
    def __init__(self):
        self.events: list = []

    def create_match_event(self, **kwargs):
        self.events.append(kwargs)


class SimItemRepo:
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def build_participants(
    chars_per_player_list: List[int],
) -> tuple[Dict[int, SimPlayer], List[SimCharacter]]:
    players: Dict[int, SimPlayer] = {}
    chars: List[SimCharacter] = []
    char_id = 1
    for pid, num_chars in enumerate(chars_per_player_list, start=1):
        players[pid] = SimPlayer(pid, f"Player_{pid}")
        for c in range(num_chars):
            chars.append(SimCharacter(char_id, pid, f"P{pid}_Char{c + 1}"))
            char_id += 1
    return players, chars


def compute_protocol_fee(
    chars_per_player_list: List[int],
    entry_fee: float,
    fee_tiers: Dict[int, float],
) -> float:
    """Per-player tiered protocol fee, summed across all players."""
    max_tier = max(fee_tiers.keys())
    total = 0.0
    for count in chars_per_player_list:
        tier_key = min(count, max_tier)
        rate = fee_tiers[tier_key] / 100.0
        total += count * entry_fee * rate
    return total


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    config = load_config()

    parser = argparse.ArgumentParser(description="Simulate a match")
    parser.add_argument("--players", type=int, default=config.num_players_default)
    parser.add_argument("--chars-per-player", type=int, default=1)
    parser.add_argument(
        "--char-distribution",
        type=str,
        default=None,
        help="Comma-separated chars per player, e.g. '3,1,2,1'. Overrides --players and --chars-per-player.",
    )
    parser.add_argument("--entry-fee", type=float, default=config.default_fee)
    parser.add_argument("--kill-award-rate", type=float, default=config.kill_award_rate_default)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.char_distribution is not None:
        chars_per_player_list = [int(x.strip()) for x in args.char_distribution.split(",")]
        num_players = len(chars_per_player_list)
    else:
        num_players = args.players
        chars_per_player_list = [args.chars_per_player] * num_players

    scenarios = load_scenarios(config.scenario_dir)

    match = SimMatch(match_id=1, entry_fee=args.entry_fee, kill_award_rate=args.kill_award_rate)
    players, chars = build_participants(chars_per_player_list)

    player_repo = SimPlayerRepo(players)
    character_repo = SimCharacterRepo(chars)
    match_repo = SimMatchRepo(match)
    event_repo = SimEventRepo()
    item_repo = SimItemRepo()

    engine = MatchEngine(
        match_id=match.id,
        config=config,
        scenarios=scenarios,
        player_repo=player_repo,
        character_repo=character_repo,
        match_repo=match_repo,
        event_repo=event_repo,
        item_repo=item_repo,
        random_seed=args.seed,
    )

    winner, match_log = engine.run_match(chars)

    # --- Print match log ---
    print("=" * 60)
    print("MATCH LOG")
    print("=" * 60)
    for line in match_log:
        print(line)

    # --- Payout calculation ---
    kill_events = [
        KillEvent(killer_character_id=int(e["affected_character_ids"].split(",")[0].strip()))
        for e in event_repo.events
        if e["event_type"] == "direct_kill" and e.get("affected_character_ids")
    ]

    character_infos = [
        CharacterInfo(character_id=c.id, player_id=c.player_id)
        for c in chars
    ]

    protocol_fee = compute_protocol_fee(
        chars_per_player_list=chars_per_player_list,
        entry_fee=args.entry_fee,
        fee_tiers=config.protocol_fee_tiers,
    )

    result = calculate_payouts(
        characters=character_infos,
        kill_events=kill_events,
        entry_fee=args.entry_fee,
        kill_award_rate=args.kill_award_rate,
        protocol_fee=protocol_fee,
        winner_character_id=match.winner_character_id,
    )

    # --- Print economic summary ---
    print()
    print("=" * 60)
    print("ECONOMIC SUMMARY")
    print("=" * 60)
    print(f"Players:              {num_players}")
    print(f"Char distribution:    {chars_per_player_list}")
    print(f"Total characters:     {len(chars)}")
    print(f"Entry fee:            {args.entry_fee:.2f}")
    print(f"Kill award rate:      {args.kill_award_rate:.2%}")
    print(f"Seed:                 {args.seed}")
    print()
    print(f"Total pool:           {result.total_pool:.2f}")
    print(f"Protocol fee:         {result.protocol_fee:.2f}")
    print(f"Pool after protocol:  {result.pool_after_protocol:.2f}")
    print(f"Total kill awards:    {result.total_kill_awards:.2f}")
    print(f"Winner payout:        {result.winner_payout:.2f}")
    print()

    if result.kill_awards:
        print("Kill awards:")
        for pid, amt in sorted(result.kill_awards.items()):
            pname = players[pid].username
            print(f"  {pname}: {amt:.2f}  (kills: {players[pid].kills})")

    if result.winner_player_id is not None:
        winner_name = players[result.winner_player_id].username
        print(f"\nWinner: {winner_name} (player {result.winner_player_id}) → {result.winner_payout:.2f}")
    else:
        print("\nNo winner determined.")


if __name__ == "__main__":
    main()
