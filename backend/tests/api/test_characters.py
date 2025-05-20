import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..app.main import app
from ..app.models.models import Character

client = TestClient(app)

def test_read_characters():
    response = client.get("/api/v1/characters/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_character():
    response = client.post(
        "/api/v1/characters/",
        json={
            "name": f"Test Character {pytest.random_string()}",
            "owner_username": f"test_owner_{pytest.random_string()}"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "owner_username" in data
    assert "id" in data
    assert data["is_alive"] == True

def test_read_character(db_session: Session, test_character: Character):
    response = client.get(f"/api/v1/characters/{test_character.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_character.id
    assert data["name"] == test_character.name
    assert data["owner_username"] == test_character.owner_username

def test_update_character(db_session: Session, test_character: Character):
    new_name = f"Updated Character {pytest.random_string()}"
    response = client.put(
        f"/api/v1/characters/{test_character.id}",
        json={"name": new_name}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_character.id
    assert data["name"] == new_name

def test_read_character_not_found():
    response = client.get("/api/v1/characters/999999")
    assert response.status_code == 404

def test_assign_character_to_match(db_session: Session, test_character: Character, test_match):
    response = client.post(f"/api/v1/characters/{test_character.id}/assign-to-match/{test_match.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_character.id
    assert data["match_id"] == test_match.id
