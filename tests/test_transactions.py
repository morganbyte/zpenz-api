import pytest
from fastapi import status

from backend import models


class TestCreateTransaction:
    def test_create_transaction_success(self, client, test_user, test_account, test_category, db):
        """Test successful transaction creation."""
        # Login first
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "Grocery shopping",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["amount"] == 50.0
        assert data["description"] == "Grocery shopping"

    def test_create_transaction_missing_account(self, client, test_user, test_category, db):
        """Test transaction creation fails with invalid account."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "Test",
                "type": "EXPENSE",
                "account_id": 9999,  # Non-existent
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert data["error"] == "NotFoundError"

    def test_create_transaction_negative_amount(self, client, test_user, test_account, test_category):
        """Test transaction creation fails with negative amount."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/transactions",
            json={
                "amount": -50.0,  # Negative
                "description": "Test",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "ValidationError"

    def test_create_transaction_wrong_type(self, client, test_user, test_account, test_category):
        """Test transaction creation fails with wrong category type."""
        # Category is expense type, but we try to create income transaction
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        response = client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "Test",
                "type": "INCOME",  # Mismatch with category type
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data["error"] == "ValidationError"


class TestListTransactions:
    def test_list_transactions(self, client, test_user, test_account, test_category):
        """Test listing user's transactions."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create a transaction first
        client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "Test transaction",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )

        # List transactions
        response = client.get("/transactions", headers=headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1
        assert data[0]["description"] == "Test transaction"

    def test_list_transactions_user_isolation(self, client, test_user, test_account, test_category, db):
        """Test that users only see their own transactions."""
        # Create another user
        other_user = models.User(
            email="other@example.com",
            username="otheruser",
            hashed_password="hashed_password"
        )
        db.add(other_user)
        db.commit()
        db.refresh(other_user)

        # Login as first user and create transaction
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token1 = response.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "User 1 transaction",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers1
        )

        # User 1 should see their transaction
        response = client.get("/transactions", headers=headers1)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) >= 1


class TestUpdateTransaction:
    def test_update_transaction(self, client, test_user, test_account, test_category):
        """Test updating a transaction."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create transaction
        create_response = client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "Original",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        transaction_id = create_response.json()["id"]

        # Update transaction
        response = client.put(
            f"/transactions/{transaction_id}",
            json={
                "amount": 75.0,
                "description": "Updated",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["amount"] == 75.0
        assert data["description"] == "Updated"


class TestDeleteTransaction:
    def test_delete_transaction(self, client, test_user, test_account, test_category):
        """Test deleting a transaction."""
        response = client.post(
            "/auth/login",
            data={"username": "testuser", "password": "testpassword123"}
        )
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create transaction
        create_response = client.post(
            "/transactions",
            json={
                "amount": 50.0,
                "description": "To delete",
                "type": "EXPENSE",
                "account_id": test_account.id,
                "category_id": test_category.id,
                "date": "2025-05-18"
            },
            headers=headers
        )
        transaction_id = create_response.json()["id"]

        # Delete transaction
        response = client.delete(
            f"/transactions/{transaction_id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_200_OK

        # Verify it's gone
        response = client.get(
            f"/transactions/{transaction_id}",
            headers=headers
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND
