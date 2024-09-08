import pytest
from fastapi.testclient import TestClient
from main import app
from config.config import config
import uuid

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

@pytest.fixture(scope="module")
def api_key_headers():
    return {"Authorization": f"Bearer {config.BACKEND_API_KEY}"}

@pytest.fixture(scope="function")
def test_user(client, api_key_headers):
    # Create a unique user with a unique phone number
    user_data = {
        "id": str(uuid.uuid4()),
        "phone_number": f"+1314320{uuid.uuid4().hex[:4]}",  # Generate a unique phone number
    }
    response = client.post("/users", json=user_data, headers=api_key_headers)
    
    # Check if creation was successful
    assert response.status_code == 200, f"Failed to create user: {response.json()}"

    created_user = response.json()
    
    # Yield the created user to the test
    yield created_user
    
    # Cleanup: delete the user after the test
    delete_response = client.delete(f"/users/{created_user['id']}", headers=api_key_headers)
    
    # Ensure the user deletion was successful
    assert delete_response.status_code == 200, f"Failed to delete user: {delete_response.json()}"


def test_create_user(client, api_key_headers):
    user_data = {
        "id": str(uuid.uuid4()),
        "phone_number": "+13143209683",
    }
    response = client.post("/users", json=user_data, headers=api_key_headers)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["phone_number"] == user_data["phone_number"]

    # Clean up: delete the created user
    client.delete(f"/users/{response.json()['id']}", headers=api_key_headers)

def test_get_user(client, api_key_headers, test_user):
    response = client.get(f"/users/{test_user['id']}", headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["id"] == test_user['id']

def test_get_user_rooms(client, api_key_headers, test_user):
    response = client.get(f"/users/{test_user['id']}/rooms", headers=api_key_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_update_user(client, api_key_headers, test_user):
    update_data = {"is_subscribed": "false"}
    response = client.patch(f"/users/{test_user['id']}", json=update_data, headers=api_key_headers)
    assert response.status_code == 200
    assert response.json()["is_subscribed"] == False

def test_delete_user(client, api_key_headers):
    # Create a user to delete
    user_data = {
        "id": str(uuid.uuid4()),
        "phone_number": "+13143209684",
    }
    create_response = client.post("/users", json=user_data, headers=api_key_headers)
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Delete the user
    delete_response = client.delete(f"/users/{user_id}", headers=api_key_headers)
    assert delete_response.status_code == 200
    assert delete_response.json() == "Successfully deleted user"

    # Verify the user is deleted
    get_response = client.get(f"/users/{user_id}", headers=api_key_headers)
    assert get_response.status_code == 404

def test_get_nonexistent_user(client, api_key_headers):
    nonexistent_id = str(uuid.uuid4())
    response = client.get(f"/users/{nonexistent_id}", headers=api_key_headers)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_create_user_duplicate_phone(client, api_key_headers, test_user):
    user_data = {
        "id": str(uuid.uuid4()),
        "phone_number": test_user["phone_number"],  # Use the same phone number as test_user
    }
    response = client.post("/users", json=user_data, headers=api_key_headers)
    assert response.status_code == 409
    assert "User with this phone number already exists" in response.json()["detail"]

def test_api_key_required(client):
    response = client.get("/users/123")
    assert response.status_code == 403
    assert "Not authenticated" in response.json()["detail"]

def test_invalid_api_key(client):
    invalid_headers = {"Authorization": "Bearer invalid_key"}
    response = client.get("/users/123", headers=invalid_headers)
    assert response.status_code == 403
    assert "Could not validate credentials" in response.json()["detail"]