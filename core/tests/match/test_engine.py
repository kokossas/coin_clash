"""Tests for MatchEngine — focused on logic that can actually break."""

from typing import Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

from core.match.engine import MatchEngine


# ---------------------------------------------------------------------------
# Minimal stubs — satisfy the engine's interface without a database
# ---------------------------------------------------------------------------

class StubMatch:
    def __init__(self, match_id=1, entry_fee=1.0, kill_award_rate=0.1, protocol_fee_percentage=10.0):
        self.id = match_id
        self.entry_fee = entry_fee
        self.kill_award_rate = kill_award_rate
        self.status = "pending"
        self.winner_character_id = None
        self.protocol_fee_percentage = protocol_fee_percentage


class StubPlayer:
    def __init__(self, player_id, username="player"):
        self.id = player_id
        self.username = username
        self.wins = 0
        self.kills = 0
        self.total_earnings = 0.0
        self.balance = 0.0


class StubCharacter:
    def __init__(self, char_id, player_id, name="Char", owned_character_id=None):
        self.id = char_id
        self.player_id = player_id
        self.name = name
        self.is_alive = True
        self.owned_character_id = owned_character_id
        self.match_id = None
        self._player = StubPlayer(player_id, f"Player_{player_id}")

    @property
    def player_owner(self):
        return self._player

    @property
    def display_name(self):
        return f"{self.name} ({self._player.username})"


class StubOwnedCharacter:
    def __init__(self, oc_id, is_alive=True, last_match_id=None):
        self.id = oc_id
        self.is_alive = is_alive
        self.last_match_id = last_match_id


class StubMatchRepo:
    def __init__(self, match: StubMatch):
        self._match = match

    def get_match_by_id(self, match_id):
        return self._match if self._match.id == match_id else None

    def update_match_status(self, match_id, status):
        self._match.status = status
        return self._match

    def set_match_start_time(self, match_id):
        return self._match

    def set_match_end_time(self, match_id):
        return self._match

    def set_match_winner(self, match_id, winner_character_id):
        self._match.winner_character_id = winner_character_id
        return self._match


class StubPlayerRepo:
    def __init__(self, players: Dict[int, StubPlayer]):
        self._players = players

    def get_player_by_id(self, player_id):
        return self._players.get(player_id)

    def add_kill(self, player_id):
        p = self._players.get(player_id)
        if p:
            p.kills += 1
        return p

    def add_win(self, player_id):
        p = self._players.get(player_id)
        if p:
            p.wins += 1
        return p

    def add_earnings(self, player_id, amount):
        p = self._players.get(player_id)
        if p:
            p.total_earnings += amount
        return p

    def update_player_balance(self, player_id, amount):
        p = self._players.get(player_id)
        if p:
            p.balance += amount
        return p


class StubCharacterRepo:
    def __init__(self, chars: Optional[List] = None):
        self.status_updates: Dict[int, bool] = {}
        self._chars = {c.id: c for c in chars} if chars else {}
        self.db = MagicMock()

    def update_character_status(self, character_id, is_alive):
        self.status_updates[character_id] = is_alive
        # Mirror what SqlCharacterRepo does: mutate the in-memory object
        if character_id in self._chars:
            self._chars[character_id].is_alive = is_alive


class StubEventRepo:
    def __init__(self):
        self.events: list = []

    def create_match_event(self, **kwargs):
        self.events.append(kwargs)


class StubItemRepo:
    pass


# ---------------------------------------------------------------------------
# Shared config and scenarios
# ---------------------------------------------------------------------------

MINIMAL_CONFIG = {
    "primary_event_weights": {
        "direct_kill": 50,
        "self": 15,
        "environmental": 20,
        "group": 5,
        "story": 10,
    },
    "extra_events": {
        "non_lethal_story_chance": 0.0,
        "extra_lethal_base_chance": 0.0,
        "comeback_base_chance": 0.0,
    },
    "lethal_modifiers": {"cap_8_plus": 0.10, "cap_12_plus": 0.20},
    "round_delay_enabled": False,
    "round_delay_min": 0.01,
    "round_delay_max": 0.02,
}

MINIMAL_SCENARIOS = {
    "direct_kill": [{"text": "[Character A] eliminates [Character B].", "id": "dk_000"}],
    "self": [{"text": "[Character A] trips and falls.", "id": "self_000"}],
    "environmental": [{"text": "[Character A] struck by lightning.", "id": "env_000"}],
    "group": [{"text": "[Character A] and [Character B] both fall.", "id": "grp_000"}],
    "story": [{"text": "[Character A] finds a coin.", "id": "story_000"}],
    "comeback": [],
}


def _make_players_and_chars(n: int, with_owned=False):
    players = {}
    chars = []
    for i in range(1, n + 1):
        p = StubPlayer(i, f"Player_{i}")
        players[i] = p
        oc_id = i if with_owned else None
        c = StubCharacter(char_id=i, player_id=i, name=f"Char_{i}", owned_character_id=oc_id)
        chars.append(c)
    return players, chars


def _make_engine(
    players: Dict[int, StubPlayer],
    chars: List[StubCharacter],
    config=None,
    scenarios=None,
    seed=42,
    match=None,
    character_repo=None,
):
    m = match or StubMatch()
    cfg = config or MINIMAL_CONFIG.copy()
    scn = scenarios or MINIMAL_SCENARIOS
    pr = StubPlayerRepo(players)
    cr = character_repo or StubCharacterRepo(chars)
    mr = StubMatchRepo(m)
    er = StubEventRepo()
    ir = StubItemRepo()
    return MatchEngine(
        match_id=m.id,
        config=cfg,
        scenarios=scn,
        player_repo=pr,
        character_repo=cr,
        match_repo=mr,
        event_repo=er,
        item_repo=ir,
        random_seed=seed,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCalculatePayouts:

    def test_basic_split(self):
        players, chars = _make_players_and_chars(4)
        engine = _make_engine(players, chars, match=StubMatch(entry_fee=10.0, kill_award_rate=0.1))
        engine.participants = chars
        engine.entry_fee = 10.0
        engine.kill_award_rate = 0.1

        protocol_cut, kill_awards, winner_payout = engine._calculate_payouts(chars[0])

        total_fees = 4 * 10.0
        assert protocol_cut == pytest.approx(total_fees * 0.10)
        prize_pool = total_fees - protocol_cut
        expected_kills = 3 * (10.0 * 0.1)
        assert kill_awards == pytest.approx(expected_kills)
        assert winner_payout == pytest.approx(prize_pool - expected_kills)
        assert protocol_cut + kill_awards + winner_payout == pytest.approx(total_fees)

    def test_kill_awards_capped_at_prize_pool(self):
        players, chars = _make_players_and_chars(4)
        engine = _make_engine(players, chars, match=StubMatch(entry_fee=10.0, kill_award_rate=5.0))
        engine.participants = chars
        engine.entry_fee = 10.0
        engine.kill_award_rate = 5.0

        protocol_cut, kill_awards, winner_payout = engine._calculate_payouts(chars[0])

        prize_pool = (4 * 10.0) - protocol_cut
        assert kill_awards <= prize_pool
        assert winner_payout >= 0


class TestRunMatchConvergence:

    def test_two_participants_produces_winner(self):
        players, chars = _make_players_and_chars(2)
        engine = _make_engine(players, chars, seed=1)
        winner, log = engine.run_match(chars)

        assert winner is not None
        assert winner.id in [c.id for c in chars]
        assert len(engine.alive_pool) == 1
        assert len(engine.dead_pool) == 1

    def test_ten_participants_produces_winner(self):
        players, chars = _make_players_and_chars(10)
        engine = _make_engine(players, chars, seed=7)
        winner, log = engine.run_match(chars)

        assert winner is not None
        assert len(engine.alive_pool) == 1
        assert len(engine.alive_pool) + len(engine.dead_pool) == 10

    def test_match_status_set_to_completed(self):
        players, chars = _make_players_and_chars(3)
        m = StubMatch()
        engine = _make_engine(players, chars, match=m, seed=99)
        engine.run_match(chars)

        assert m.status == "completed"
        assert m.winner_character_id is not None


class TestPoolManagement:

    def test_elimination_moves_to_dead_pool(self):
        players, chars = _make_players_and_chars(3)
        engine = _make_engine(players, chars)
        engine.alive_pool = {c.id: c for c in chars}
        engine.dead_pool = {}

        engine._apply_elimination(chars[0])

        assert chars[0].id not in engine.alive_pool
        assert chars[0].id in engine.dead_pool

    def test_elimination_of_already_dead_is_noop(self):
        players, chars = _make_players_and_chars(3)
        engine = _make_engine(players, chars)
        engine.alive_pool = {c.id: c for c in chars[1:]}
        engine.dead_pool = {chars[0].id: chars[0]}

        engine._apply_elimination(chars[0])

        assert chars[0].id in engine.dead_pool
        assert chars[0].id not in engine.alive_pool

    def test_revival_moves_to_alive_pool(self):
        players, chars = _make_players_and_chars(3)
        engine = _make_engine(players, chars)
        engine.alive_pool = {c.id: c for c in chars[1:]}
        engine.dead_pool = {chars[0].id: chars[0]}

        engine._apply_revival(chars[0])

        assert chars[0].id in engine.alive_pool
        assert chars[0].id not in engine.dead_pool

    def test_revival_of_alive_is_noop(self):
        players, chars = _make_players_and_chars(3)
        engine = _make_engine(players, chars)
        engine.alive_pool = {c.id: c for c in chars}
        engine.dead_pool = {}

        engine._apply_revival(chars[0])

        assert chars[0].id in engine.alive_pool
        assert chars[0].id not in engine.dead_pool


class TestTwoRemainRule:

    def test_no_group_event_with_two_alive(self):
        players, chars = _make_players_and_chars(2)
        engine = _make_engine(players, chars, seed=1)
        engine.alive_pool = {c.id: c for c in chars}
        engine.dead_pool = {}
        engine.participants = chars

        engine._run_round()

        # Group would kill both → 0 alive. Must not happen.
        assert len(engine.alive_pool) >= 1


class TestRoundDelay:

    @patch("core.match.engine.time.sleep")
    def test_delay_called_when_enabled(self, mock_sleep):
        players, chars = _make_players_and_chars(2)
        cfg = MINIMAL_CONFIG.copy()
        cfg["round_delay_enabled"] = True
        cfg["round_delay_min"] = 0.01
        cfg["round_delay_max"] = 0.02
        engine = _make_engine(players, chars, config=cfg, seed=42)

        engine.run_match(chars)

        assert mock_sleep.call_count >= 1
        for c in mock_sleep.call_args_list:
            delay_val = c[0][0]
            assert 0.01 <= delay_val <= 0.02

    @patch("core.match.engine.time.sleep")
    def test_no_delay_when_disabled(self, mock_sleep):
        players, chars = _make_players_and_chars(2)
        cfg = MINIMAL_CONFIG.copy()
        cfg["round_delay_enabled"] = False
        engine = _make_engine(players, chars, config=cfg, seed=42)

        engine.run_match(chars)

        mock_sleep.assert_not_called()


class TestPostMatchSync:

    def _make_queryable_char_repo(self, owned_map: Dict[int, StubOwnedCharacter], chars: List):
        repo = StubCharacterRepo(chars)

        class FakeFilter:
            def __init__(self, oc_id):
                self._oc_id = oc_id

            def first(self):
                return owned_map.get(self._oc_id)

        class FakeQuery:
            def filter(self, expr):
                # Extract right-hand value from SQLAlchemy BinaryExpression
                try:
                    oc_id = expr.right.effective_value
                except AttributeError:
                    oc_id = expr.right.value
                return FakeFilter(oc_id)

        repo.db = MagicMock()
        repo.db.query.return_value = FakeQuery()
        return repo

    def test_sync_updates_owned_characters(self):
        oc1 = StubOwnedCharacter(1, is_alive=True, last_match_id=None)
        oc2 = StubOwnedCharacter(2, is_alive=True, last_match_id=None)
        owned_map = {1: oc1, 2: oc2}

        players, chars = _make_players_and_chars(2, with_owned=True)
        cr = self._make_queryable_char_repo(owned_map, chars)
        engine = _make_engine(players, chars, character_repo=cr, seed=1)

        winner, _ = engine.run_match(chars)

        winner_oc = owned_map[winner.owned_character_id]
        loser_id = [c.id for c in chars if c.id != winner.id][0]
        loser_oc = owned_map[loser_id]

        assert winner_oc.is_alive is True
        assert loser_oc.is_alive is False
        assert winner_oc.last_match_id == 1
        assert loser_oc.last_match_id == 1

    def test_sync_skips_chars_without_owned_id(self):
        players, chars = _make_players_and_chars(2, with_owned=False)
        cr = StubCharacterRepo(chars)
        engine = _make_engine(players, chars, character_repo=cr, seed=1)

        engine.run_match(chars)

        cr.db.query.assert_not_called()
