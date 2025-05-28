import pytest
from httpx import Client # For TestClient
from sqlalchemy.orm import Session

from backend.models.database_models import User
from backend.core.security import verify_password, create_access_token
from backend.core.config import settings

# Assuming conftest.py provides 'client', 'db_session', 'test_user', 'test_superuser', 'authorized_client', 'superuser_client' fixtures

def test_create_user(client: Client):
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={"username": "newuser", "email": "new@example.com", "password": "newpassword"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "new@example.com"
    assert "hashed_password" not in data # Password should not be returned
    assert data["is_active"] is True
    assert data["is_superuser"] is False

def test_create_existing_user(client: Client):
    # First create a user
    client.post(
        f"{settings.API_V1_STR}/users/",
        json={"username": "existinguser", "email": "existing@example.com", "password": "password"},
    )
    # Try to create again with same username
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json={"username": "existinguser", "email": "another@example.com", "password": "password"},
    )
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]

def test_login_for_access_token(client: Client, test_user: User):
    response = client.post(
        f"{settings.API_V1_STR}/users/token",
        data={"username": test_user.username, "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client: Client):
    response = client.post(
        f"{settings.API_V1_STR}/users/token",
        data={"username": "nonexistent", "password": "wrongpassword"},
    )
    assert response.status_code == 400
    assert "Incorrect username or password" in response.json()["detail"]

def test_read_users_me(authorized_client: Client, test_user: User):
    response = authorized_client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email

def test_read_users_me_unauthenticated(client: Client):
    response = client.get(f"{settings.API_V1_STR}/users/me")
    assert response.status_code == 401
    assert "Not authenticated" in response.json()["detail"]

def test_read_all_users_as_superuser(superuser_client: Client, test_user: User, test_superuser: User):
    response = superuser_client.get(f"{settings.API_V1_STR}/users/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2 # At least test_user and test_superuser
    usernames = [user["username"] for user in data]
    assert test_user.username in usernames
    assert test_superuser.username in usernames

def test_read_all_users_as_regular_user(authorized_client: Client, test_user: User):
    response = authorized_client.get(f"{settings.API_V1_STR}/users/")
    assert response.status_code == 403 # Regular users cannot list all users
    assert "Not enough privileges" in response.json()["detail"]

def test_update_user_as_superuser(superuser_client: Client, test_user: User):
    response = superuser_client.put(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        json={"email": "updated_test@example.com", "is_active": False},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated_test@example.com"
    assert data["is_active"] is False

def test_update_user_as_regular_user_self(authorized_client: Client, test_user: User):
    # Regular user can update their own profile
    response = authorized_client.put(
        f"{settings.API_V1_STR}/users/{test_user.id}",
        json={"full_name": "Updated Name"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"

def test_update_user_as_regular_user_other(authorized_client: Client, test_superuser: User):
    # Regular user cannot update another user's profile
    response = authorized_client.put(
        f"{settings.API_V1_STR}/users/{test_superuser.id}",
        json={"is_active": False},
    )
    assert response.status_code == 403
    assert "Not enough privileges" in response.json()["detail"]

def test_delete_user_as_superuser(superuser_client: Client, test_user: User):
    response = superuser_client.delete(f"{settings.API_V1_STR}/users/{test_user.id}")
    assert response.status_code == 200 # Assuming 200 OK with response body, or 204 No Content
    assert response.json()["username"] == test_user.username # Check if the deleted user is returned

    # Verify user is actually deleted
    response = superuser_client.get(f"{settings.API_V1_STR}/users/{test_user.id}")
    assert response.status_code == 404

def test_delete_user_as_regular_user(authorized_client: Client, test_superuser: User):
    # Regular user cannot delete other users
    response = authorized_client.delete(f"{settings.API_V1_STR}/users/{test_superuser.id}")
    assert response.status_code == 403
    assert "Not enough privileges" in response.json()["detail"]

def test_delete_user_self_as_regular_user(authorized_client: Client, test_user: User):
    # Regular user can delete their own account
    response = authorized_client.delete(f"{settings.API_V1_STR}/users/{test_user.id}")
    assert response.status_code == 200
    assert response.json()["username"] == test_user.username

    # Verify user is actually deleted
    response = authorized_client.get(f"{settings.API_V1_STR}/users/me") # Should fail as user is deleted
    assert response.status_code == 401 # Not authenticated
