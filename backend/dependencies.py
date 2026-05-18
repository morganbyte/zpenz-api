import secrets

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from backend.database import get_db
from backend.auth_utils import verify_supabase_token, get_password_hash
from backend import models
from backend.logging_config import get_logger
from backend.exceptions import AuthenticationError

logger = get_logger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
):
    """Get current user from token"""
    payload = verify_supabase_token(token)
    if payload is None:
        logger.warning("Supabase token rejected")
        raise AuthenticationError("Invalid or expired token")

    email = payload.get("email")
    if not email:
        logger.warning("Token missing email claim")
        raise AuthenticationError("Invalid token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        username = payload.get("user_metadata", {}).get("username")
        if not username:
            username = email.split("@", 1)[0]

        base_username = username
        suffix = 1
        while db.query(models.User).filter(models.User.username == username).first():
            username = f"{base_username}{suffix}"
            suffix += 1

        random_password = secrets.token_urlsafe(32)
        user = models.User(
            email=email,
            username=username,
            hashed_password=get_password_hash(random_password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"New user created from Supabase: {email}")

    return user
