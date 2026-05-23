from fastapi import status


class TestGetMe:
    def test_get_me_unauthenticated(self, client):
        """Request without token must return 403."""
        response = client.get("/auth/me")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_get_me_invalid_token(self, client):
        """Request with a malformed token must return 401."""
        headers = {"Authorization": "Bearer not.a.valid.token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_register_endpoint_removed(self, client):
        """Legacy /auth/register/ endpoint must no longer exist."""
        response = client.post("/auth/register/", json={})
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_login_endpoint_removed(self, client):
        """Legacy /auth/login endpoint must no longer exist."""
        response = client.post("/auth/login", data={})
        assert response.status_code == status.HTTP_404_NOT_FOUND
