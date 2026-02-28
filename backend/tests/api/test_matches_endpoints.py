"""Tests for the new match endpoints: create, open, join, events, status."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import Character, Match, MatchEvent, Player

client = TestClient(app)


def _db():
    """Get a DB session from the overridden dependency."""
    from app.db.session import get_db_dependency

    gen = app.dependency_overrides[get_db_dependency]()
    db = next(gen)
    return db


def _make_player(db, wallet=None):
    wallet = wallet or f"0x{pytest.random_string(40)}"
    p = Player(wallet_address=wallet, username=f"u_{pytest.random_string(6)}", balance=0.0)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def _make_match(db, **overrides):
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
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


def _make_character(db, player_id, match_id, name="Char"):
    c = Character(name=name, player_id=player_id, match_id=match_id, entry_order=1)
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _make_event(db, match_id, round_number=1):
    e = MatchEvent(
        match_id=match_id,
        round_number=round_number,
        event_type="direct_kill",
        scenario_source="test",
        scenario_text="something happened",
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return e


class TestCreateLobby:

    @patch("app.api.api_v1.endpoints.matches.MatchLobbyService")
    def test_create_lobby_returns_match(self, mock_svc_cls):
        mock_svc = MagicMock()
        # Return a mock that looks like a Match ORM object
        mock_match = MagicMock()
        mock_match.id = 1
        mock_match.entry_fee = 2.0
        mock_match.kill_award_rate = 0.1
        mock_match.start_method = "cap"
        mock_match.start_threshold = 60
        mock_match.status = "filling"
        mock_match.creator_wallet_address = "0xcreator"
        mock_match.min_players = 3
        mock_match.max_characters = 20
        mock_match.max_characters_per_player = 3
        mock_match.protocol_fee_percentage = Decimal("10.0")
        mock_match.start_timestamp = None
        mock_match.end_timestamp = None
        mock_match.winner_character_id = None
        mock_match.blockchain_tx_id = None
        mock_match.blockchain_settlement_status = None
        mock_match.start_timer_end = None
        mock_match.countdown_started_at = None
        mock_match.created_at = "2025-01-01T00:00:00"
        mock_match.updated_at = None

        mock_svc.create_match_lobby = AsyncMock(return_value=mock_match)
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/matches/create",
            json={
                "creator_wallet_address": "0xcreator",
                "entry_fee": 2.0,
                "kill_award_rate": 0.1,
                "start_method": "cap",
                "start_threshold": 60,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "filling"
        assert data["entry_fee"] == 2.0

    @patch("app.api.api_v1.endpoints.matches.MatchLobbyService")
    def test_create_lobby_invalid_params_returns_400(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.create_match_lobby = AsyncMock(
            side_effect=ValueError("min_players must be between 3 and 50")
        )
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/matches/create",
            json={
                "creator_wallet_address": "0xcreator",
                "entry_fee": 1.0,
                "kill_award_rate": 0.1,
                "start_method": "cap",
                "start_threshold": 60,
                "min_players": 1,
            },
        )
        assert resp.status_code == 400


class TestGetOpenMatches:

    def test_filters_filling_only(self):
        db = _db()
        _make_match(db, status="filling", entry_fee=1.0)
        _make_match(db, status="completed", entry_fee=2.0)

        resp = client.get("/api/v1/matches/open?has_slots=false")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "filling"

    def test_has_slots_filters_full_matches(self):
        db = _db()
        match = _make_match(db, status="filling", max_characters=1)
        p = _make_player(db)
        _make_character(db, p.id, match.id)

        resp = client.get("/api/v1/matches/open?has_slots=true")
        assert resp.status_code == 200
        data = resp.json()
        # The match is full (1/1), should be excluded
        match_ids = [m["id"] for m in data]
        assert match.id not in match_ids

    def test_fee_range_filter(self):
        db = _db()
        _make_match(db, status="filling", entry_fee=1.0)
        _make_match(db, status="filling", entry_fee=3.0)
        _make_match(db, status="filling", entry_fee=5.0)

        resp = client.get("/api/v1/matches/open?min_fee=2&max_fee=4&has_slots=false")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["entry_fee"] == 3.0


class TestJoinMatch:

    @patch("app.api.api_v1.endpoints.matches.MatchLobbyService")
    def test_join_returns_join_request(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_jr = MagicMock()
        mock_jr.id = 1
        mock_jr.match_id = 10
        mock_jr.player_id = 1
        mock_jr.entry_fee_total = Decimal("2.0")
        mock_jr.payment_status = "confirmed"
        mock_jr.created_at = "2025-01-01T00:00:00"
        mock_jr.confirmed_at = "2025-01-01T00:00:01"

        mock_svc.join_match = AsyncMock(return_value=mock_jr)
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/matches/10/join",
            json={"player_id": 1, "character_ids": [1, 2], "payment_ref": "0xabc"},
        )
        assert resp.status_code == 200
        assert resp.json()["payment_status"] == "confirmed"

    @patch("app.api.api_v1.endpoints.matches.MatchLobbyService")
    def test_join_invalid_returns_400(self, mock_svc_cls):
        mock_svc = MagicMock()
        mock_svc.join_match = AsyncMock(
            side_effect=ValueError("Match is not accepting joins")
        )
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/matches/10/join",
            json={"player_id": 1, "character_ids": [1], "payment_ref": "0xabc"},
        )
        assert resp.status_code == 400


class TestGetEvents:

    def test_returns_events_list(self):
        db = _db()
        match = _make_match(db)
        _make_event(db, match.id, round_number=1)
        _make_event(db, match.id, round_number=2)

        resp = client.get(f"/api/v1/matches/{match.id}/events")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_cursor_filtering(self):
        db = _db()
        match = _make_match(db)
        e1 = _make_event(db, match.id, round_number=1)
        e2 = _make_event(db, match.id, round_number=2)
        e3 = _make_event(db, match.id, round_number=3)

        resp = client.get(f"/api/v1/matches/{match.id}/events?after_event_id={e1.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        ids = [e["id"] for e in data]
        assert e1.id not in ids

    def test_match_not_found_returns_404(self):
        resp = client.get("/api/v1/matches/999999/events")
        assert resp.status_code == 404


class TestGetStatus:

    def test_returns_match_summary(self):
        db = _db()
        match = _make_match(db, status="filling")
        p1 = _make_player(db)
        p2 = _make_player(db)
        _make_character(db, p1.id, match.id, name="C1")
        _make_character(db, p1.id, match.id, name="C2")
        _make_character(db, p2.id, match.id, name="C3")

        resp = client.get(f"/api/v1/matches/{match.id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["match_id"] == match.id
        assert data["status"] == "filling"
        assert data["total_characters"] == 3
        assert data["unique_players"] == 2

    def test_match_not_found_returns_404(self):
        resp = client.get("/api/v1/matches/999999/status")
        assert resp.status_code == 404
