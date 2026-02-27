import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_read_players():
    response = client.get("/api/v1/players/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_player():
    wallet = f"0x{pytest.random_string(40)}"
    username = f"test_create_{pytest.random_string()}"
    response = client.post(
        "/api/v1/players/",
        json={"wallet_address": wallet, "username": username}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["wallet_address"] == wallet
    assert "id" in data


def test_create_player_duplicate_wallet():
    wallet = f"0x{pytest.random_string(40)}"
    client.post("/api/v1/players/", json={"wallet_address": wallet})
    response = client.post("/api/v1/players/", json={"wallet_address": wallet})
    assert response.status_code == 400


def test_read_player():
    wallet = f"0x{pytest.random_string(40)}"
    username = f"test_read_{pytest.random_string()}"
    create_resp = client.post(
        "/api/v1/players/",
        json={"wallet_address": wallet, "username": username}
    )
    player_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/players/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["id"] == player_id
