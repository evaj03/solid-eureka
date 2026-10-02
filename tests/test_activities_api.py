from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def test_client(monkeypatch):
    activities = deepcopy(app_module.activities)
    monkeypatch.setattr(app_module, "activities", activities)

    with TestClient(app_module.app) as client:
        yield client


def test_get_activities_returns_seeded_activity_data(test_client):
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = test_client.get("/activities")

    # Assert
    assert response.status_code == 200
    activity = response.json()[activity_name]
    assert {"description", "schedule", "max_participants", "participants"} <= activity.keys()
    assert activity["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]


def test_signup_adds_participant_to_activity(test_client):
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    signup_response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    activities_response = test_client.get("/activities")

    # Assert
    assert signup_response.status_code == 200
    assert signup_response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_returns_404_for_unknown_activity(test_client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(test_client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_full_activity(test_client):
    # Arrange
    activity_name = "Chess Club"
    activity = app_module.activities[activity_name]
    activity["participants"] = [
        f"student{number}@mergington.edu"
        for number in range(activity["max_participants"])
    ]

    # Act
    response = test_client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_removes_participant_from_activity(test_client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    unregister_response = test_client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )
    activities_response = test_client.get("/activities")

    # Assert
    assert unregister_response.status_code == 200
    assert unregister_response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities_response.json()[activity_name]["participants"]


def test_unregister_returns_404_for_unknown_activity(test_client):
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = test_client.delete(
        f"/activities/{activity_name}/participants/student@mergington.edu"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_for_unregistered_participant(test_client):
    # Arrange
    activity_name = "Chess Club"
    email = "unregistered@mergington.edu"

    # Act
    response = test_client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"