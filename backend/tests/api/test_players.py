import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..app.main import app
from ..app.models.models import Player
from ..app.schemas.player import PlayerCreate

client = TestClient(app)

def test_read_players():
    response = client.get("/api/v1/players/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_player():
    username = f"test_create_api_user_{pytest.random_string()}"
    response = client.post(
        "/api/v1/players/",
        json={"username": username}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert "id" in data

def test_read_player():
    # First create a player
    username = f"test_read_api_user_{pytest.random_string()}"
    create_response = client.post(
        "/api/v1/players/",
        json={"username": username}
    )
    assert create_response.status_code == 200
    player_id = create_response.json()["id"]
    
    # Then read it
    response = client.get(f"/api/v1/players/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == username
    assert data["id"] == player_id

def test_update_player():
    # First create a player
    username = f"test_update_api_user_{pytest.random_string()}"
    create_response = client.post(
        "/api/v1/players/",
        json={"username": username}
    )
    assert create_response.status_code == 200
    player_id = create_response.json()["id"]
    
    # Then update it
    new_username = f"updated_{username}"
    response = client.put(
        f"/api/v1/players/{player_id}",
        json={"username": new_username}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == new_username
    assert data["id"] == player_id

def test_read_player_not_found():
    response = client.get("/api/v1/players/999999")
    assert response.status_code == 404

def test_read_player_by_username(db_session: Session, test_player: Player):
    response = client.get(f"/api/v1/players/by-username/{test_player.username}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_player.username
    assert data["id"] == test_player.id
