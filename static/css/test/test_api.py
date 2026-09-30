import os

# These environment variables must be set
# before importing the FastAPI application.
os.environ["DATABASE_URL"] = (
    "sqlite:///./test_pocketsmart.db"
)

os.environ["AI_MODE"] = "mock"

os.environ["SECRET_KEY"] = (
    "test-secret-key"
)


from fastapi.testclient import TestClient

from app.main import (
    app,
    init_db,
)


init_db()

client = TestClient(app)


def register_and_login():

    email = "tester@example.com"

    response = client.post(
        "/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": "password123",
        },
    )

    assert response.status_code in (
        201,
        409,
    ), response.text


    response = client.post(
        "/login",
        data={
            "username": email,
            "password": "password123",
        },
    )

    assert response.status_code == 200, (
        response.text
    )


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    assert (
        response.json()["status"]
        == "ok"
    )


def test_register_login_session():

    register_and_login()

    response = client.get(
        "/session-info"
    )

    assert response.status_code == 200

    assert (
        response.json()["authenticated"]
        is True
    )


def test_home_planner():

    register_and_login()

    response = client.post(
        "/generate-home",
        json={
            "budget": 50000,
            "rooms": [
                "Living Room"
            ],
            "style": "modern",
            "items": {
                "lights": 2
            },
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    body = response.json()

    assert body["planner"] == "home"

    assert body["ai_used"] is False

    assert body["recommendations"]


def test_party_planner():

    register_and_login()

    response = client.post(
        "/generate-party",
        json={
            "budget": 75000,
            "guests": 30,
            "event_type": "birthday",
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    assert (
        response.json()["planner"]
        == "party"
    )


def test_jewelry_planner_and_history():

    register_and_login()

    response = client.post(
        "/generate-jewelry",
        data={
            "budget": "10000",
            "occasion": "wedding",
            "style": "elegant",
        },
    )

    assert response.status_code == 200, (
        response.text
    )

    assert (
        response.json()["planner"]
        == "jewelry"
    )


    history_response = client.get(
        "/history"
    )

    assert (
        history_response.status_code
        == 200
    )

    assert (
        len(history_response.json())
        >= 1
    )