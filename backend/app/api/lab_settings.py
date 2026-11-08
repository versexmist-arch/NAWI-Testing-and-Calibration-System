from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab_settings import LaboratorySettings
from ..schemas.lab_settings import LaboratorySettingsUpdate, LaboratorySettingsResponse
from ..services.audit_service import record_audit_event
from ..auth import get_current_user, normalize_role, MANAGEMENT_PERMITTED_ROLES
from ..models.user import User

router = APIRouter(prefix="/lab-settings", tags=["Laboratory Settings"])


@router.get("", response_model=LaboratorySettingsResponse)
def get_lab_settings(db: Session = Depends(get_db)):
    settings_obj = db.query(LaboratorySettings).first()
    if not settings_obj:
        settings_obj = LaboratorySettings(id=1)
        db.add(settings_obj)
        db.commit()
        db.refresh(settings_obj)
    return settings_obj


@router.put("", response_model=LaboratorySettingsResponse)
def update_lab_settings(
    payload: LaboratorySettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify RBAC permissions: only Admin / Lab Manager can modify laboratory settings
    user_role_canonical = normalize_role(current_user.role)
    allowed_canonical = {normalize_role(r) for r in MANAGEMENT_PERMITTED_ROLES}
    if user_role_canonical not in allowed_canonical:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Permission Denied: User '{current_user.full_name}' with role '{current_user.role}' "
                f"is not authorized to alter accredited laboratory profile settings."
            )
        )

    settings_obj = db.query(LaboratorySettings).first()
    if not settings_obj:
        settings_obj = LaboratorySettings(id=1)
        db.add(settings_obj)

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(settings_obj, k, v)

    db.commit()
    db.refresh(settings_obj)

    record_audit_event(
        db=db,
        action="LAB_SETTINGS_UPDATED",
        actor=current_user.full_name,
        details={"updated_fields": list(update_dict.keys()), "authorized_by": current_user.full_name, "role": current_user.role}
    )
    return settings_obj

