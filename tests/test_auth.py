import pytest
from fastapi import status

from backend import models


class TestRegister:
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/auth/register/",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "securepassword123"
            }
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"

    def test_register_duplicate_email(self, client, test_user):
        """Test registration fails with duplicate email."""
        response = client.post(
            "/auth/register/",
            json={
                "email": "test@example.com",  # Already exists
                "username": "newuser",
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["error"] == "ConflictError"

    def test_register_duplicate_username(self, client, test_user):
        """Test registration fails with duplicate username."""
        response = client.post(
            "/auth/register/",
            json={
                "email": "another@example.com",
                "username": "testuser",  # Already exists
                "password": "password123"
            }
        )
        assert response.status_code == status.HTTP_409_CONFLICT
        data = response.json()
        assert data["error"] == "ConflictError"


class TestLogin:
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_username(self, client):
        """Test login fails with invalid username."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "anypassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"] == "AuthenticationError"

    def test_login_invalid_password(self, client, test_user):
        """Test login fails with invalid password."""
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        data = response.json()
        assert data["error"] == "AuthenticationError"


class TestGetMe:
    def test_get_me_authenticated(self, client, test_user, auth_headers):
        """Test getting current user when authenticated."""
        # We need to modify this to test with the local JWT token
        response = client.post(
            "/auth/login",
            data={
                "username": "testuser",
                "password": "testpassword123"
            }
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/auth/me", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"

    def test_get_me_unauthenticated(self, client):
        """Test getting current user returns 401 without token."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN
