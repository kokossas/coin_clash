"""Tests for the new character endpoints: purchase, inventory, revival-fee, revive."""

from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_owned_character(player_id, char_id=1, name="Warrior"):
    from datetime import datetime, timezone

    m = MagicMock()
    m.id = char_id
    m.player_id = player_id
    m.character_name = name
    m.is_alive = True
    m.revival_count = 0
    m.last_match_id = None
    m.created_at = datetime.now(timezone.utc)
    m.__class__ = type("OwnedCharacter", (), {})
    m.model_dump = lambda: {
        "id": m.id,
        "player_id": m.player_id,
        "character_name": m.character_name,
        "is_alive": m.is_alive,
        "revival_count": m.revival_count,
        "last_match_id": m.last_match_id,
        "created_at": m.created_at.isoformat(),
    }
    return m


class TestPurchaseEndpoint:

    @patch("app.api.api_v1.endpoints.characters.CharacterInventoryService")
    def test_purchase_returns_owned_characters(self, mock_svc_cls, test_player):
        mock_svc = MagicMock()
        mock_svc.purchase_characters = AsyncMock(
            return_value=[_mock_owned_character(test_player.id, char_id=10)]
        )
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/characters/purchase",
            json={"quantity": 1, "payment_ref": "0xabc"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["character_name"] == "Warrior"

    @patch("app.api.api_v1.endpoints.characters.CharacterInventoryService")
    def test_purchase_invalid_quantity_returns_400(self, mock_svc_cls, test_player):
        mock_svc = MagicMock()
        mock_svc.purchase_characters = AsyncMock(
            side_effect=ValueError("quantity must be between 1 and 10")
        )
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/characters/purchase",
            json={"quantity": 0, "payment_ref": "0xabc"},
        )
        assert resp.status_code == 400


class TestInventoryEndpoint:

    @patch("app.api.api_v1.endpoints.characters.CharacterInventoryService")
    def test_inventory_returns_list(self, mock_svc_cls, test_player):
        mock_svc = MagicMock()
        mock_svc.get_player_inventory.return_value = [
            _mock_owned_character(test_player.id, char_id=1),
            _mock_owned_character(test_player.id, char_id=2, name="Mage"),
        ]
        mock_svc_cls.return_value = mock_svc

        resp = client.get("/api/v1/characters/inventory")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2


class TestRevivalFeeEndpoint:

    @patch("app.api.api_v1.endpoints.characters.load_config")
    def test_revival_fee_returns_config_value(self, mock_config):
        mock_config.return_value = MagicMock(character_revival_fee=0.75)

        resp = client.get("/api/v1/characters/42/revival-fee")
        assert resp.status_code == 200
        data = resp.json()
        assert data["character_id"] == 42
        assert data["revival_fee"] == 0.75
        assert data["currency"] == "USDC"


class TestReviveEndpoint:

    @patch("app.api.api_v1.endpoints.characters.CharacterInventoryService")
    def test_revive_returns_owned_character(self, mock_svc_cls, test_player):
        mock_svc = MagicMock()
        oc = _mock_owned_character(test_player.id, char_id=5)
        oc.revival_count = 1
        mock_svc.revive_character = AsyncMock(return_value=oc)
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/characters/5/revive",
            json={"payment_ref": "0xabc"},
        )
        assert resp.status_code == 200
        assert resp.json()["id"] == 5

    @patch("app.api.api_v1.endpoints.characters.CharacterInventoryService")
    def test_revive_wrong_player_returns_400(self, mock_svc_cls, test_player):
        mock_svc = MagicMock()
        mock_svc.revive_character = AsyncMock(
            side_effect=ValueError("Character not owned by this player")
        )
        mock_svc_cls.return_value = mock_svc

        resp = client.post(
            "/api/v1/characters/5/revive",
            json={"payment_ref": "0xabc"},
        )
        assert resp.status_code == 400
