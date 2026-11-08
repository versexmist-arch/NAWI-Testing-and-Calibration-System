from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.demo_data_service import reset_demo_data, seed_demo_data
from ..auth import get_current_user, normalize_role, ADMIN_PERMITTED_ROLES
from ..models.user import User

router = APIRouter(prefix="/demo", tags=["Demonstration Data"])


@router.post("/reset")
def reset_demo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_role_canonical = normalize_role(current_user.role)
    allowed_canonical = {normalize_role(r) for r in ADMIN_PERMITTED_ROLES}
    if user_role_canonical not in allowed_canonical:
        raise HTTPException(
            status_code=403,
            detail=f"Permission Denied: User '{current_user.full_name}' with role '{current_user.role}' cannot reset laboratory demonstration datasets. Administrator authorization required."
        )
    return reset_demo_data(db)


@router.post("/seed")
def seed_demo(db: Session = Depends(get_db)):
    return seed_demo_data(db)

