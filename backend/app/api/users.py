from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserCreate, UserUpdate, UserResponse
from ..services.audit_service import record_audit_event
from ..auth import get_current_user, normalize_role, MANAGEMENT_PERMITTED_ROLES

router = APIRouter(prefix="/users", tags=["Users & Operators"])


@router.get("", response_model=List[UserResponse])
def list_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if role:
        query = query.filter(User.role == role)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (User.full_name.ilike(s)) |
            (User.username.ilike(s)) |
            (User.email.ilike(s)) |
            (User.department.ilike(s))
        )
    return query.order_by(User.created_at.desc()).all()


@router.post("", response_model=UserResponse, status_code=201)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_role_canonical = normalize_role(current_user.role)
    allowed_canonical = {normalize_role(r) for r in MANAGEMENT_PERMITTED_ROLES}
    if user_role_canonical not in allowed_canonical:
        raise HTTPException(
            status_code=403,
            detail=f"Permission Denied: User '{current_user.full_name}' with role '{current_user.role}' cannot register new laboratory operators."
        )

    # Check duplicate username
    if db.query(User).filter(User.username == payload.username.strip()).first():
        raise HTTPException(status_code=409, detail=f"Username '{payload.username}' is already in use.")
    if db.query(User).filter(User.email == payload.email.strip()).first():
        raise HTTPException(status_code=409, detail=f"Email '{payload.email}' is already registered.")

    user = User(
        username=payload.username.strip(),
        full_name=payload.full_name.strip(),
        email=payload.email.strip(),
        role=payload.role,
        qualification=payload.qualification,
        department=payload.department,
        is_active=payload.is_active,
        is_demo=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    record_audit_event(
        db=db,
        action="USER_CREATED",
        actor=current_user.full_name,
        details={"username": user.username, "role": user.role, "created_by": current_user.full_name}
    )
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_role_canonical = normalize_role(current_user.role)
    allowed_canonical = {normalize_role(r) for r in MANAGEMENT_PERMITTED_ROLES}
    if user_role_canonical not in allowed_canonical:
        raise HTTPException(
            status_code=403,
            detail=f"Permission Denied: User '{current_user.full_name}' with role '{current_user.role}' cannot modify personnel profiles."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)

    record_audit_event(
        db=db,
        action="USER_UPDATED",
        actor=current_user.full_name,
        details={"user_id": user.id, "changes": update_dict}
    )
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_role_canonical = normalize_role(current_user.role)
    allowed_canonical = {normalize_role(r) for r in MANAGEMENT_PERMITTED_ROLES}
    if user_role_canonical not in allowed_canonical:
        raise HTTPException(
            status_code=403,
            detail=f"Permission Denied: User '{current_user.full_name}' with role '{current_user.role}' cannot deactivate personnel profiles."
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    user.is_active = False
    db.commit()

    record_audit_event(
        db=db,
        action="USER_DEACTIVATED",
        actor="Administrator",
        details={"user_id": user.id, "username": user.username}
    )
    return {"status": "success", "message": f"User {user.username} deactivated."}

