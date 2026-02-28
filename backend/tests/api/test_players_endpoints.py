"""Tests for the new player endpoints: profile, match-history."""

import random
import string
from decimal import Decimal
from fastapi.testclient import TestClient

from app.main import app
from app.models.models import Character, Match, PendingPayout, Player

client = TestClient(app)


def _db():
    from app.db.session import get_db_dependency

    gen = app.dependency_overrides[get_db_dependency]()
    db = next(gen)
    return db


def _make_player(db, wallet=None, **overrides):
    wallet = wallet or f"0x{''.join(random.choices(string.hexdigits, k=40))}"
    defaults = dict(
        wallet_address=wallet,
        username=f"u_{''.join(random.choices(string.ascii_lowercase, k=6))}",
        balance=100.0,
        wins=5,
        kills=10,
        total_earnings=50.0,
    )
    defaults.update(overrides)
    p = Player(**defaults)
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
        status="completed",
    )
    defaults.update(overrides)
    m = Match(**defaults)
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


class TestProfileEndpoint:

    def test_returns_player_with_pending_payouts(self, test_player):
        db = _db()
        match = _make_match(db)

        payout = PendingPayout(
            match_id=match.id,
            player_id=test_player.id,
            payout_type="winner",
            amount=Decimal("5.00"),
            currency="USDC",
        )
        db.add(payout)
        db.commit()

        resp = client.get("/api/v1/players/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == test_player.id
        assert data["wallet_address"] == test_player.wallet_address
        assert data["balance"] == 100.0
        assert data["wins"] == 5
        assert len(data["pending_payouts"]) == 1
        assert data["pending_payouts"][0]["payout_type"] == "winner"
        assert float(data["pending_payouts"][0]["amount"]) == 5.0

    def test_profile_unauthenticated_returns_401(self):
        resp = client.get("/api/v1/players/profile")
        assert resp.status_code == 401


class TestMatchHistoryEndpoint:

    def test_returns_entries(self):
        db = _db()
        player = _make_player(db)
        match = _make_match(db)
        c = Character(name="C1", player_id=player.id, match_id=match.id, entry_order=1)
        db.add(c)
        db.commit()

        resp = client.get(f"/api/v1/players/{player.wallet_address}/match-history")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["match_id"] == match.id
        assert data[0]["character_count"] == 1
        assert data[0]["status"] == "completed"

    def test_empty_for_player_with_no_matches(self):
        db = _db()
        player = _make_player(db)

        resp = client.get(f"/api/v1/players/{player.wallet_address}/match-history")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_player_not_found_returns_404(self):
        resp = client.get("/api/v1/players/0xnonexistent/match-history")
        assert resp.status_code == 404

    def test_pagination(self):
        db = _db()
        player = _make_player(db)
        for i in range(3):
            match = _make_match(db)
            c = Character(
                name=f"C{i}", player_id=player.id, match_id=match.id, entry_order=1,
            )
            db.add(c)
        db.commit()

        resp = client.get(
            f"/api/v1/players/{player.wallet_address}/match-history?skip=0&limit=2"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
