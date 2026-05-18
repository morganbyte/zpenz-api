import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app
from backend import models
from backend.auth_utils import get_password_hash, create_access_token
from datetime import timedelta

# Use SQLite in-memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_engine():
    """Create a test database engine."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    """Create a test database session."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture(scope="function")
def client(db):
    """Create a test client with overridden database."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    test_client = TestClient(app, raise_server_exceptions=False)
    yield test_client

    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db):
    """Create a test user."""
    user = models.User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("testpassword123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@pytest.fixture
def test_account(db, test_user):
    """Create a test account for the test user."""
    account = models.Account(
        name="Test Bank",
        type="banco",
        balance=1000.0,
        user_id=test_user.id
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

@pytest.fixture
def test_category(db, test_user):
    """Create a test category for the test user."""
    category = models.Category(
        name="Groceries",
        type="expense",
        user_id=test_user.id
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category

@pytest.fixture
def test_token(test_user):
    """Create a JWT token for the test user."""
    access_token_expires = timedelta(minutes=30)
    token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=access_token_expires
    )
    return token

@pytest.fixture
def auth_headers(test_token):
    """Create authorization headers with test token."""
    return {"Authorization": f"Bearer {test_token}"}
