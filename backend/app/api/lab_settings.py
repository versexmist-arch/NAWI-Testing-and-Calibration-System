from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.lab_settings import LaboratorySettings
from ..schemas.lab_settings import LaboratorySettingsUpdate, LaboratorySettingsResponse
from ..services.audit_service import record_audit_event

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
def update_lab_settings(payload: LaboratorySettingsUpdate, db: Session = Depends(get_db)):
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
        actor="Laboratory Manager",
        details={"updated_fields": list(update_dict.keys())}
    )
    return settings_obj

