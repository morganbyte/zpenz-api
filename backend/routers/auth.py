from fastapi import APIRouter, Depends
from backend.dependencies import get_current_user
from backend import models, schemas
from backend.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    """Get current user info"""
    return current_user
