from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Instrument, TestSession
from ..schemas.instrument import InstrumentCreate, InstrumentUpdate, InstrumentResponse
from ..services.audit_service import record_audit_event
from calculation_engine.common.units import calculate_scale_intervals

router = APIRouter(prefix="/instruments", tags=["Instruments"])


@router.get("", response_model=List[InstrumentResponse])
def list_instruments(
    search: Optional[str] = None,
    accuracy_class: Optional[str] = None,
    include_archived: bool = False,
    is_demo: Optional[bool] = None,
    sort_by: Optional[str] = "created_at",
    sort_order: Optional[str] = "desc",
    db: Session = Depends(get_db),
):
    query = db.query(Instrument)
    if not include_archived:
        query = query.filter(Instrument.is_archived == False)
    if accuracy_class:
        query = query.filter(Instrument.accuracy_class == accuracy_class)
    if is_demo is not None:
        query = query.filter(Instrument.is_demo == is_demo)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter(
            (Instrument.serial_number.ilike(s)) |
            (Instrument.model.ilike(s)) |
            (Instrument.manufacturer.ilike(s)) |
            (Instrument.location.ilike(s))
        )

    # Sorting
    sort_col = getattr(Instrument, sort_by, Instrument.created_at)
    if sort_order.lower() == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    return query.all()


@router.post("", response_model=InstrumentResponse, status_code=201)
def create_instrument(payload: InstrumentCreate, db: Session = Depends(get_db)):
    # Check for existing serial number
    existing = db.query(Instrument).filter(Instrument.serial_number == payload.serial_number.strip()).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"An instrument with serial number '{payload.serial_number}' is already registered."
        )

    # Compute verification scale intervals count n = Max / e
    n_intervals = None
    try:
        n_intervals = calculate_scale_intervals(payload.max_capacity, payload.verification_scale_interval)
    except Exception:
        pass

    instrument = Instrument(
        serial_number=payload.serial_number.strip(),
        manufacturer=payload.manufacturer.strip(),
        model=payload.model.strip(),
        instrument_type=payload.instrument_type,
        accuracy_class=payload.accuracy_class,
        max_capacity=payload.max_capacity,
        min_capacity=payload.min_capacity,
        verification_scale_interval=payload.verification_scale_interval,
        actual_scale_interval=payload.actual_scale_interval,
        unit=payload.unit.strip().lower(),
        scale_intervals_count=n_intervals,
        location=payload.location,
        notes=payload.notes,
        is_demo=False,
    )
    db.add(instrument)
    db.commit()
    db.refresh(instrument)

    record_audit_event(
        db=db,
        action="INSTRUMENT_REGISTERED",
        actor="Operator",
        instrument_id=instrument.id,
        details={
            "serial_number": instrument.serial_number,
            "model": instrument.model,
            "max_capacity": instrument.max_capacity,
            "unit": instrument.unit,
        }
    )

    return instrument


@router.get("/{instrument_id}")
def get_instrument_details(instrument_id: str, db: Session = Depends(get_db)):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found.")

    test_history = db.query(TestSession).filter(TestSession.instrument_id == instrument_id).order_by(TestSession.created_at.desc()).all()

    return {
        "instrument": InstrumentResponse.model_validate(instrument),
        "test_sessions_count": len(test_history),
        "test_sessions": [
            {
                "id": t.id,
                "test_category": t.test_category,
                "test_date": t.test_date,
                "status": t.status,
                "operator_name": t.operator_name,
                "overall_outcome": t.rule_evaluation.overall_outcome if t.rule_evaluation else None,
            }
            for t in test_history
        ]
    }


@router.put("/{instrument_id}", response_model=InstrumentResponse)
def update_instrument(instrument_id: str, payload: InstrumentUpdate, db: Session = Depends(get_db)):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found.")

    update_dict = payload.model_dump(exclude_unset=True)
    if "serial_number" in update_dict and update_dict["serial_number"] != instrument.serial_number:
        # Check duplicate
        exists = db.query(Instrument).filter(
            Instrument.serial_number == update_dict["serial_number"],
            Instrument.id != instrument_id
        ).first()
        if exists:
            raise HTTPException(status_code=409, detail="Serial number already taken by another instrument.")

    for k, v in update_dict.items():
        setattr(instrument, k, v)

    # Re-calculate scale intervals count if max_capacity or e changed
    try:
        instrument.scale_intervals_count = calculate_scale_intervals(
            instrument.max_capacity,
            instrument.verification_scale_interval
        )
    except Exception:
        pass

    db.commit()
    db.refresh(instrument)

    record_audit_event(
        db=db,
        action="INSTRUMENT_UPDATED",
        actor="Operator",
        instrument_id=instrument.id,
        details=update_dict
    )

    return instrument


@router.delete("/{instrument_id}")
def archive_instrument(instrument_id: str, db: Session = Depends(get_db)):
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Instrument not found.")

    instrument.is_archived = True
    db.commit()

    record_audit_event(
        db=db,
        action="INSTRUMENT_ARCHIVED",
        actor="Operator",
        instrument_id=instrument.id,
        details={"status": "archived"}
    )

    return {"status": "success", "message": f"Instrument {instrument.serial_number} archived."}

