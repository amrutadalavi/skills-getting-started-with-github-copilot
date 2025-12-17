import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_get_activities():
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Check structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_for_activity():
    """Test signing up for an activity"""
    # First, get initial participants count
    response = client.get("/activities")
    initial_data = response.json()
    initial_count = len(initial_data["Chess Club"]["participants"])

    # Sign up a new participant
    response = client.post("/activities/Chess Club/signup?email=test@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@example.com" in data["message"]
    assert "Chess Club" in data["message"]

    # Verify the participant was added
    response = client.get("/activities")
    updated_data = response.json()
    updated_count = len(updated_data["Chess Club"]["participants"])
    assert updated_count == initial_count + 1
    assert "test@example.com" in updated_data["Chess Club"]["participants"]


def test_signup_activity_not_found():
    """Test signing up for non-existent activity"""
    response = client.post("/activities/NonExistent/signup?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_signup_activity_full():
    """Test signing up for a full activity"""
    # Get an activity with low max_participants
    response = client.get("/activities")
    data = response.json()
    # Find an activity to fill up
    activity_name = None
    for name, details in data.items():
        if len(details["participants"]) < details["max_participants"]:
            activity_name = name
            break

    if activity_name:
        # Fill up the activity
        activity = data[activity_name]
        spots_left = activity["max_participants"] - len(activity["participants"])
        for i in range(spots_left):
            response = client.post(f"/activities/{activity_name}/signup?email=fill{i}@example.com")
            assert response.status_code == 200

        # Try to add one more
        response = client.post(f"/activities/{activity_name}/signup?email=overflow@example.com")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "Activity is full" in data["detail"]


def test_root_redirect():
    """Test root endpoint redirects to static index"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


def test_unregister_from_activity():
    """Test unregistering from an activity"""
    # First, sign up a participant
    client.post("/activities/TestActivity/signup?email=unregister@example.com")
    
    # Get initial count
    response = client.get("/activities")
    initial_data = response.json()
    initial_count = len(initial_data["TestActivity"]["participants"])
    
    # Unregister the participant
    response = client.delete("/activities/TestActivity/unregister?participant=unregister@example.com")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "unregister@example.com" in data["message"]
    assert "TestActivity" in data["message"]
    
    # Verify the participant was removed
    response = client.get("/activities")
    updated_data = response.json()
    updated_count = len(updated_data["TestActivity"]["participants"])
    assert updated_count == initial_count - 1
    assert "unregister@example.com" not in updated_data["TestActivity"]["participants"]


def test_unregister_activity_not_found():
    """Test unregistering from non-existent activity"""
    response = client.delete("/activities/NonExistent/unregister?participant=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_unregister_participant_not_found():
    """Test unregistering a participant not in the activity"""
    response = client.delete("/activities/Chess Club/unregister?participant=notfound@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Participant not found in activity" in data["detail"]