from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserResponse
from ..auth import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication & Roles"])


class LoginRequest(BaseModel):
    username_or_id: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CurrentUserContext(BaseModel):
    user: UserResponse
    can_amend: bool
    can_manage_settings: bool
    can_delete_instruments: bool
    can_manage_users: bool


@router.get("/me", response_model=CurrentUserContext)
def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Retrieve currently authenticated user profile and capability flags."""
    role = (current_user.role or "").lower()
    is_admin = "admin" in role
    is_manager = "manager" in role
    is_reviewer = "reviewer" in role

    can_amend = is_admin or is_manager or is_reviewer
    can_manage = is_admin or is_manager

    return {
        "user": current_user,
        "can_amend": can_amend,
        "can_manage_settings": can_manage,
        "can_delete_instruments": is_admin or is_manager,
        "can_manage_users": is_admin,
    }


@router.post("/login", response_model=AuthTokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate by username or user ID (demonstration token generation)."""
    user = db.query(User).filter(
        (User.username == payload.username_or_id.strip()) |
        (User.id == payload.username_or_id.strip())
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"User '{payload.username_or_id}' not found in laboratory records."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account '{user.username}' is marked inactive."
        )

    return {
        "access_token": user.id,
        "token_type": "bearer",
        "user": user,
    }


@router.get("/available-roles", response_model=List[UserResponse])
def list_available_demo_users(db: Session = Depends(get_db)):
    """List all registered operators and roles available for quick switching in the UI."""
    return db.query(User).filter(User.is_active == True).order_by(User.created_at.asc()).all()

