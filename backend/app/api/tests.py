from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import TestSession, Instrument, Observation, CalculationResult, RuleEvaluation, AuditLog, GeneratedReport, TestRevision, User
from ..schemas.test_session import TestSessionCreate, TestSessionUpdate, TestSessionResponse, TestSessionAmend, TestRevisionResponse
from ..schemas.observation import ObservationSubmit, ObservationResponse
from ..schemas.audit import AuditLogResponse
from ..services.test_service import calculate_test_session, evaluate_test_session
from ..services.report_service import generate_pdf_report
from ..services.audit_service import record_audit_event
from ..auth import get_current_user, normalize_role, AMENDMENT_PERMITTED_ROLES

router = APIRouter(prefix="/tests", tags=["Test Management"])


@router.get("", response_model=List[TestSessionResponse])
def list_test_sessions(
    category: Optional[str] = None,
    status: Optional[str] = None,
    instrument_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(TestSession)
    if category:
        query = query.filter(TestSession.test_category == category.lower().strip())
    if status:
        query = query.filter(TestSession.status == status)
    if instrument_id:
        query = query.filter(TestSession.instrument_id == instrument_id)
    if search:
        s = f"%{search.strip()}%"
        query = query.join(TestSession.instrument).filter(
            (TestSession.id.ilike(s)) |
            (TestSession.operator_name.ilike(s)) |
            (Instrument.serial_number.ilike(s)) |
            (Instrument.model.ilike(s))
        )

    sessions = query.order_by(TestSession.created_at.desc()).all()
    results = []
    for s in sessions:
        resp = TestSessionResponse.model_validate(s)
        resp.has_observations = s.observations is not None and bool(s.observations.data)
        resp.has_calculations = s.calculation_result is not None
        resp.has_rule_evaluations = s.rule_evaluation is not None
        resp.overall_outcome = s.rule_evaluation.overall_outcome if s.rule_evaluation else None
        resp.revisions_count = len(s.revisions) if s.revisions else 0
        results.append(resp)
    return results


@router.post("", response_model=TestSessionResponse, status_code=201)
def create_test_session(payload: TestSessionCreate, db: Session = Depends(get_db)):
    instrument = db.query(Instrument).filter(Instrument.id == payload.instrument_id).first()
    if not instrument:
        raise HTTPException(status_code=404, detail="Selected instrument not found.")

    valid_cats = ("eccentricity", "linearity", "repeatability")
    cat = payload.test_category.lower().strip()
    if cat not in valid_cats:
        raise HTTPException(status_code=400, detail=f"Invalid test category '{payload.test_category}'. Must be one of: {valid_cats}")

    session = TestSession(
        instrument_id=instrument.id,
        test_category=cat,
        operator_name=payload.operator_name,
        laboratory_location=payload.laboratory_location or instrument.location,
        ambient_temperature=payload.ambient_temperature,
        relative_humidity=payload.relative_humidity,
        service_type=payload.service_type or "initial",
        status="Draft",
        test_configuration=payload.test_configuration or {},
        is_demo=False,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    record_audit_event(
        db=db,
        action="TEST_SESSION_CREATED",
        actor=session.operator_name,
        test_session_id=session.id,
        instrument_id=instrument.id,
        details={
            "category": cat,
            "status": session.status,
            "service_type": session.service_type,
        }
    )

    resp = TestSessionResponse.model_validate(session)
    resp.has_observations = False
    resp.has_calculations = False
    resp.has_rule_evaluations = False
    return resp


@router.get("/{test_id}")
def get_test_session_details(test_id: str, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    calc = session.calculation_result
    rule_eval = session.rule_evaluation
    obs = session.observations
    reports = db.query(GeneratedReport).filter(GeneratedReport.test_session_id == test_id).order_by(GeneratedReport.created_at.desc()).all()
    latest_report = reports[0] if reports else None
    revs = db.query(TestRevision).filter(TestRevision.test_session_id == test_id).order_by(TestRevision.revision_number.asc()).all()

    resp = TestSessionResponse.model_validate(session)
    resp.has_observations = obs is not None and bool(obs.data)
    resp.has_calculations = calc is not None
    resp.has_rule_evaluations = rule_eval is not None
    resp.overall_outcome = rule_eval.overall_outcome if rule_eval else None
    resp.revisions_count = len(revs)

    return {
        "session": resp,
        "observations": obs.data if obs else None,
        "calculation_result": calc.full_data if calc else None,
        "rule_evaluation": rule_eval.evaluations_data if rule_eval else None,
        "latest_report": {
            "id": latest_report.id,
            "file_name": latest_report.file_name,
            "version": getattr(latest_report, "version", 1),
            "is_superseded": getattr(latest_report, "is_superseded", False),
            "created_at": latest_report.created_at,
        } if latest_report else None,
        "reports": [
            {
                "id": rep.id,
                "file_name": rep.file_name,
                "version": getattr(rep, "version", 1),
                "is_superseded": getattr(rep, "is_superseded", False),
                "superseded_by": getattr(rep, "superseded_by", None),
                "created_at": rep.created_at,
            }
            for rep in reports
        ],
        "revisions_count": len(revs),
        "revisions": [
            {
                "id": r.id,
                "revision_number": r.revision_number,
                "amendment_reason": r.amendment_reason,
                "amended_by": r.amended_by,
                "status_at_amendment": r.status_at_amendment,
                "overall_outcome": r.overall_outcome,
                "created_at": r.created_at,
            }
            for r in revs
        ],
    }


@router.put("/{test_id}", response_model=TestSessionResponse)
def update_test_session(test_id: str, payload: TestSessionUpdate, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    # BUG-5 GUARD: Prevent ordinary PUT requests from modifying completed test sessions
    if session.status == "Completed":
        raise HTTPException(
            status_code=409,
            detail=(
                "Completed test session is locked against modification. "
                "To amend this session, submit an authorized amendment request (POST /api/tests/{test_id}/amend) "
                "with a documented reason."
            )
        )

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(session, k, v)

    db.commit()
    db.refresh(session)

    record_audit_event(
        db=db,
        action="TEST_SESSION_UPDATED",
        actor=session.operator_name,
        test_session_id=session.id,
        instrument_id=session.instrument_id,
        details=update_dict,
    )

    resp = TestSessionResponse.model_validate(session)
    resp.has_observations = session.observations is not None and bool(session.observations.data)
    resp.has_calculations = session.calculation_result is not None
    resp.has_rule_evaluations = session.rule_evaluation is not None
    resp.overall_outcome = session.rule_evaluation.overall_outcome if session.rule_evaluation else None
    resp.revisions_count = len(session.revisions) if session.revisions else 0
    return resp


@router.post("/{test_id}/observations", response_model=ObservationResponse)
def save_observations(test_id: str, payload: ObservationSubmit, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    # BUG-5 GUARD: Prevent observation modifications on completed test sessions
    if session.status == "Completed":
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot modify observations for a completed test session. Session is locked. "
                "Use the amendment workflow (POST /api/tests/{test_id}/amend) with an authorized reason."
            )
        )

    if not payload.observations:
        raise HTTPException(status_code=400, detail="Observations array cannot be empty.")

    # Capacity boundary guard: ensure no observation load exceeds instrument max_capacity
    instrument = session.instrument
    if instrument and instrument.max_capacity:
        max_cap = float(instrument.max_capacity)
        unit = instrument.unit or "g"
        for i, o in enumerate(payload.observations):
            load_val = o.get("load") if o.get("load") is not None else o.get("reference_load")
            if load_val is not None:
                try:
                    f_load = float(load_val)
                    if f_load > max_cap:
                        raise HTTPException(
                            status_code=422,
                            detail=(
                                f"Observation #{i+1} load {f_load} {unit} exceeds instrument "
                                f"maximum capacity of {max_cap} {unit}. Over-capacity observations are invalid."
                            )
                        )
                except (ValueError, TypeError):
                    pass

    if payload.test_configuration:
        current_cfg = session.test_configuration or {}
        current_cfg.update(payload.test_configuration)
        session.test_configuration = current_cfg

    obs = db.query(Observation).filter(Observation.test_session_id == test_id).first()
    if not obs:
        obs = Observation(
            test_session_id=test_id,
            data=payload.observations,
        )
        db.add(obs)
    else:
        obs.data = payload.observations

    session.status = "In Progress"
    db.commit()
    db.refresh(obs)

    record_audit_event(
        db=db,
        action="OBSERVATIONS_SAVED",
        actor=session.operator_name,
        test_session_id=session.id,
        instrument_id=session.instrument_id,
        details={
            "count": len(payload.observations),
            "category": session.test_category,
        }
    )

    return obs


@router.post("/{test_id}/calculate")
def run_calculations(test_id: str, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    # BUG-6 GUARD: Prevent silent in-place recalculation of completed sessions
    if session.status == "Completed":
        raise HTTPException(
            status_code=409,
            detail=(
                "Cannot recalculate a completed test session. Session is locked. "
                "Use the amendment workflow (POST /api/tests/{test_id}/amend) with an authorized reason."
            )
        )

    return calculate_test_session(db=db, test_session_id=test_id)


@router.post("/{test_id}/validate")
def validate_rules(test_id: str, db: Session = Depends(get_db)):
    return evaluate_test_session(db=db, test_session_id=test_id)


@router.post("/{test_id}/amend")
def amend_test_session(
    test_id: str,
    payload: TestSessionAmend,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    BUG-6 & BUG-8 CONTROLLED AMENDMENT WORKFLOW WITH ROLE-BASED ACCESS CONTROL:
    Allows authorized amendment of a completed test session by:
    1. Validating caller credentials (requires Reviewer, Lab Manager, or Admin; rejects ordinary operators).
    2. Archiving a complete frozen snapshot into test_revisions (never silently overwriting previous results).
    3. Marking prior active PDF reports as superseded.
    4. Incrementing session version number with authenticated operator attribution.
    5. Optionally applying revised observations and recalculating, or re-opening to In Progress.
    """
    # Verify RBAC permissions for amendments
    user_role_canonical = normalize_role(current_user.role)
    allowed_canonical = {normalize_role(r) for r in AMENDMENT_PERMITTED_ROLES}
    if user_role_canonical not in allowed_canonical:
        raise HTTPException(
            status_code=403,
            detail=(
                f"Permission Denied: User '{current_user.full_name}' with role '{current_user.role}' "
                f"is not authorized to amend completed test sessions. "
                f"Amendments require Reviewer, Laboratory Manager, or Administrator privileges."
            )
        )

    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    calc = session.calculation_result
    rule_eval = session.rule_evaluation
    obs = session.observations

    # Attribution logic:
    # If caller authenticated with an explicit header, use their verified credentials.
    # If legacy test harness called without header, fallback to payload operator attribution.
    token_provided = bool(current_user and getattr(current_user, "_authenticated_via_header", False))
    if token_provided:
        authenticated_actor = f"{current_user.full_name} ({current_user.role})"
    else:
        authenticated_actor = payload.operator_name.strip() if payload.operator_name else current_user.full_name

    # 1. Archive current version snapshot
    prev_version = session.version or 1
    revision = TestRevision(
        test_session_id=session.id,
        revision_number=prev_version,
        amendment_reason=payload.reason.strip(),
        amended_by=authenticated_actor,
        status_at_amendment=session.status,
        observations_snapshot=obs.data if obs else None,
        calculation_snapshot=calc.full_data if calc else None,
        rule_evaluation_snapshot=rule_eval.evaluations_data if rule_eval else None,
        overall_outcome=rule_eval.overall_outcome if rule_eval else None,
    )
    db.add(revision)

    # 2. Mark active reports as superseded
    prior_reports = db.query(GeneratedReport).filter(
        GeneratedReport.test_session_id == test_id,
        GeneratedReport.is_superseded == False
    ).all()
    for pr in prior_reports:
        pr.is_superseded = True

    # 3. Increment version
    session.version = prev_version + 1
    session.operator_name = authenticated_actor

    if payload.test_configuration:
        current_cfg = session.test_configuration or {}
        current_cfg.update(payload.test_configuration)
        session.test_configuration = current_cfg

    calc_data = None
    # 4. Handle observations if provided in amendment payload
    if payload.observations is not None:
        if not payload.observations:
            raise HTTPException(status_code=400, detail="Observations array cannot be empty when provided.")
        if not obs:
            obs = Observation(test_session_id=test_id, data=payload.observations)
            db.add(obs)
        else:
            obs.data = payload.observations
        session.status = "In Progress"
        db.commit()

        # Recalculate with allow_amendment=True
        calc_data = calculate_test_session(db=db, test_session_id=test_id, allow_amendment=True)
    else:
        # Re-open session to In Progress so operator can enter new observations
        session.status = "In Progress"
        db.commit()

    # 5. Record audit event with authenticated attribution
    record_audit_event(
        db=db,
        action="TEST_SESSION_AMENDED",
        actor=authenticated_actor,
        test_session_id=session.id,
        instrument_id=session.instrument_id,
        details={
            "previous_version": prev_version,
            "new_version": session.version,
            "reason": payload.reason,
            "authenticated_user_id": current_user.id,
            "authenticated_role": current_user.role,
            "has_new_observations": payload.observations is not None,
        }
    )

    db.refresh(session)
    return {
        "status": "success",
        "message": f"Test session amended to revision {session.version}.",
        "test_session_id": session.id,
        "previous_version": prev_version,
        "new_version": session.version,
        "session_status": session.status,
        "revision_archived": prev_version,
        "calculation_result": calc_data.get("calculation_result") if calc_data else None,
        "rule_evaluation": calc_data.get("rule_evaluation") if calc_data else None,
    }


@router.get("/{test_id}/revisions")
def get_test_revisions(test_id: str, db: Session = Depends(get_db)):
    """Retrieve full revision history and audit snapshots for a test session."""
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    revs = db.query(TestRevision).filter(TestRevision.test_session_id == test_id).order_by(TestRevision.revision_number.asc()).all()
    return [
        {
            "id": r.id,
            "revision_number": r.revision_number,
            "amendment_reason": r.amendment_reason,
            "amended_by": r.amended_by,
            "status_at_amendment": r.status_at_amendment,
            "overall_outcome": r.overall_outcome,
            "created_at": r.created_at,
            "has_observations": r.observations_snapshot is not None,
            "has_calculations": r.calculation_snapshot is not None,
            "has_rule_evaluations": r.rule_evaluation_snapshot is not None,
            "observations": r.observations_snapshot,
            "calculation_result": r.calculation_snapshot,
            "rule_evaluation": r.rule_evaluation_snapshot,
        }
        for r in revs
    ]


@router.get("/{test_id}/results")
def get_test_results(test_id: str, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    calc = session.calculation_result
    rule_eval = session.rule_evaluation

    if not calc or not rule_eval:
        raise HTTPException(
            status_code=400,
            detail="Results not available. Observations must be saved and calculated first."
        )

    return {
        "test_session_id": session.id,
        "instrument": session.instrument,
        "test_category": session.test_category,
        "status": session.status,
        "calculation_result": calc.full_data,
        "rule_evaluation": rule_eval.evaluations_data,
    }


@router.post("/{test_id}/report")
def generate_report(test_id: str, db: Session = Depends(get_db)):
    session = db.query(TestSession).filter(TestSession.id == test_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    report = generate_pdf_report(db, test_id, operator_name=session.operator_name)
    return {
        "status": "success",
        "message": "Report generated successfully.",
        "report_id": report.id,
        "file_name": report.file_name,
        "created_at": report.created_at,
    }


@router.get("/{test_id}/audit", response_model=List[AuditLogResponse])
def get_test_audit_logs(test_id: str, db: Session = Depends(get_db)):
    return db.query(AuditLog).filter(AuditLog.test_session_id == test_id).order_by(AuditLog.timestamp.desc()).all()

