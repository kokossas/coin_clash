from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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


def test_read_match():
    create_resp = client.post(
        "/api/v1/matches/",
        json={
            "entry_fee": 1.0,
            "kill_award_rate": 0.5,
            "start_method": "cap",
            "start_threshold": 10
        }
    )
    match_id = create_resp.json()["id"]
    response = client.get(f"/api/v1/matches/{match_id}")
    assert response.status_code == 200
    assert response.json()["id"] == match_id


def test_read_match_not_found():
    response = client.get("/api/v1/matches/999999")
    assert response.status_code == 404
