import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..app.main import app
from ..app.models.models import Transaction

client = TestClient(app)

def test_read_transactions():
    response = client.get("/api/v1/transactions/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_transaction():
    response = client.post(
        "/api/v1/transactions/",
        json={
            "player_id": 1,
            "amount": 25.0,
            "currency": "SUI",
            "tx_type": "deposit",
            "status": "pending",
            "provider": "mock"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["player_id"] == 1
    assert data["amount"] == 25.0
    assert data["currency"] == "SUI"
    assert data["tx_type"] == "deposit"
    assert data["status"] == "pending"
    assert data["provider"] == "mock"
    assert "id" in data

def test_read_transaction(db_session: Session, test_transaction: Transaction):
    response = client.get(f"/api/v1/transactions/{test_transaction.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_transaction.id
    assert data["player_id"] == test_transaction.player_id
    assert data["amount"] == test_transaction.amount

def test_update_transaction(db_session: Session, test_transaction: Transaction):
    new_status = "failed"
    response = client.put(
        f"/api/v1/transactions/{test_transaction.id}",
        json={"status": new_status}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_transaction.id
    assert data["status"] == new_status

def test_read_transaction_not_found():
    response = client.get("/api/v1/transactions/999999")
    assert response.status_code == 404

def test_read_player_transactions(db_session: Session, test_transaction: Transaction):
    response = client.get(f"/api/v1/transactions/player/{test_transaction.player_id}")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(tx["id"] == test_transaction.id for tx in data)
