from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from backend.database import get_db
from backend.dependencies import get_current_user
from backend.auth_utils import (
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from backend import models
from backend import schemas
from backend.logging_config import get_logger
from backend.exceptions import ConflictError, AuthenticationError

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post("/register/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register new user"""

    # Check if email already exists
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        logger.warning(f"Registration failed: email already registered: {user.email}")
        raise ConflictError("Email already registered")

    # Check if username already exists
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        logger.warning(f"Registration failed: username already in use: {user.username}")
        raise ConflictError("Username already in use")

    # Create new user
    hashed_password = get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(f"New user registered: {user.email}")
    return new_user

@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """User login"""

    # Find user by username
    user = db.query(models.User).filter(
        models.User.username == form_data.username
    ).first()

    if not user:
        logger.warning(f"Login failed: user not found: {form_data.username}")
        raise AuthenticationError("Invalid credentials")

    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Login failed: invalid password for user: {form_data.username}")
        raise AuthenticationError("Invalid credentials")

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    logger.info(f"User logged in: {form_data.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get current user info"""
    return current_user
