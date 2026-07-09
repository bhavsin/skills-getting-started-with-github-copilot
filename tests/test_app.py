import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Reset in-memory activities after each test for isolation."""
    baseline = copy.deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(baseline))


def test_get_activities_returns_activity_map():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")
    payload = response.json()

    # Assert
    assert response.status_code == 200
    assert isinstance(payload, dict)
    assert expected_activity in payload
    assert isinstance(payload[expected_activity]["participants"], list)


def test_signup_adds_new_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    activity_path = quote(activity_name, safe="")
    before_count = len(app_module.activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert len(app_module.activities[activity_name]["participants"]) == before_count + 1
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Chess Club"
    existing_email = "michael@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_existing_participant():
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    activity_path = quote(activity_name, safe="")
    assert email in app_module.activities[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_missing_participant():
    # Arrange
    activity_name = "Chess Club"
    missing_email = "not.enrolled@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": missing_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"
    activity_path = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{activity_path}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
