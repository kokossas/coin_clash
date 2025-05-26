import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from ..app.main import app
from ..app.models.models import Match

client = TestClient(app)

@pytest.fixture
def random_string():
    import random
    import string
    return ''.join(random.choices(string.ascii_lowercase, k=10))

# Add the fixture to pytest namespace for use in tests
pytest.random_string = lambda: ''.join(__import__('random').choices(__import__('string').ascii_lowercase, k=10))

def test_read_matches():
    response = client.get("/api/v1/matches/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_create_match():
    response = client.post(
        "/api/v1/matches/",
        json={
            "entry_fee": 1.5,
            "kill_award_rate": 0.6,
            "start_method": "timeout",
            "start_threshold": 60
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["entry_fee"] == 1.5
    assert data["kill_award_rate"] == 0.6
    assert data["start_method"] == "timeout"
    assert data["start_threshold"] == 60
    assert data["status"] == "pending"
    assert "id" in data

def test_read_match(db_session: Session, test_match: Match):
    response = client.get(f"/api/v1/matches/{test_match.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_match.id
    assert data["entry_fee"] == test_match.entry_fee
    assert data["kill_award_rate"] == test_match.kill_award_rate

def test_update_match(db_session: Session, test_match: Match):
    new_entry_fee = 2.0
    response = client.put(
        f"/api/v1/matches/{test_match.id}",
        json={"entry_fee": new_entry_fee}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_match.id
    assert data["entry_fee"] == new_entry_fee

def test_read_match_not_found():
    response = client.get("/api/v1/matches/999999")
    assert response.status_code == 404
