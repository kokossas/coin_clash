import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_player():
    wallet = f"0x{pytest.random_string(40)}"
    resp = client.post("/api/v1/players/", json={"wallet_address": wallet})
    assert resp.status_code == 200
    return resp.json()


def _create_character(player_id: int, name: str = None):
    name = name or f"Char_{pytest.random_string()}"
    resp = client.post("/api/v1/characters/", json={"name": name, "player_id": player_id})
    assert resp.status_code == 200
    return resp.json()


def test_read_characters():
    response = client.get("/api/v1/characters/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_character():
    player = _create_player()
    data = _create_character(player["id"])
    assert "name" in data
    assert data["player_id"] == player["id"]
    assert "id" in data
    assert data["is_alive"] is True


def test_read_character():
    player = _create_player()
    char = _create_character(player["id"])
    response = client.get(f"/api/v1/characters/{char['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == char["id"]
    assert data["name"] == char["name"]
    assert data["player_id"] == player["id"]


def test_update_character():
    player = _create_player()
    char = _create_character(player["id"])
    new_name = f"Updated_{pytest.random_string()}"
    response = client.put(f"/api/v1/characters/{char['id']}", json={"name": new_name})
    assert response.status_code == 200
    assert response.json()["name"] == new_name


def test_read_character_not_found():
    response = client.get("/api/v1/characters/999999")
    assert response.status_code == 404
