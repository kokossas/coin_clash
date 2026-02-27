import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _create_player():
    wallet = f"0x{pytest.random_string(40)}"
    resp = client.post("/api/v1/players/", json={"wallet_address": wallet})
    assert resp.status_code == 200
    return resp.json()


def test_read_transactions():
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_transaction():
    player = _create_player()
    response = client.post(
        "/api/v1/transactions/",
        json={
            "player_id": player["id"],
            "amount": 25.0,
            "currency": "SUI",
            "tx_type": "deposit",
            "status": "pending",
            "provider": "mock"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == player["id"]
    assert data["amount"] == 25.0
    assert data["currency"] == "SUI"


def test_read_transaction_not_found():
    response = client.get("/api/v1/transactions/999999")
    assert response.status_code == 404
