from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Instrument, TestSession, GeneratedReport, RuleEvaluation, AuditLog

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_statistics(db: Session = Depends(get_db)):
    # Instruments counts
    all_instruments = db.query(Instrument).all()
    total_instruments = len(all_instruments)
    active_instruments = sum(1 for i in all_instruments if not i.is_archived)
    demo_instruments = sum(1 for i in all_instruments if i.is_demo)
    # Three-way classification: demo | test artifact (SN-TEST-* serial pattern) | genuine user
    test_artifact_count = sum(
        1 for i in all_instruments
        if not i.is_demo and i.serial_number.startswith("SN-TEST-")
    )
    genuine_user_instruments = total_instruments - demo_instruments - test_artifact_count
    user_instruments = total_instruments - demo_instruments

    # Tests counts
    all_tests = db.query(TestSession).all()
    total_tests = len(all_tests)
    completed_tests = sum(1 for t in all_tests if t.status == "Completed")
    pending_tests = sum(1 for t in all_tests if t.status in ("Draft", "In Progress", "Calculated"))
    demo_tests = sum(1 for t in all_tests if t.is_demo)
    # Test artifact tests: those run by "Test Metrologist" operator (from pytest runs)
    test_artifact_tests = sum(1 for t in all_tests if not t.is_demo and t.operator_name == "Test Metrologist")
    genuine_user_tests = total_tests - demo_tests - test_artifact_tests
    user_tests = total_tests - demo_tests

    # Rule outcomes breakdown
    pass_count = sum(1 for t in all_tests if t.rule_evaluation and t.rule_evaluation.overall_outcome == "PASS")
    fail_count = sum(1 for t in all_tests if t.rule_evaluation and t.rule_evaluation.overall_outcome == "FAIL")
    pending_eval_count = sum(
        1 for t in all_tests if t.rule_evaluation and t.rule_evaluation.overall_outcome in ("PENDING_VERIFICATION", "INCOMPLETE")
    )

    # Reports count
    reports_generated = db.query(GeneratedReport).count()

    # Category distribution
    ecc_count = sum(1 for t in all_tests if t.test_category == "eccentricity")
    lin_count = sum(1 for t in all_tests if t.test_category == "linearity")
    rep_count = sum(1 for t in all_tests if t.test_category == "repeatability")

    # Accuracy class distribution
    class_distribution = {"Class I": 0, "Class II": 0, "Class III": 0, "Class IIII": 0}
    for i in all_instruments:
        c = i.accuracy_class
        if c in class_distribution:
            class_distribution[c] += 1
        else:
            class_distribution[c] = class_distribution.get(c, 0) + 1

    # Recently registered instruments (last 5)
    recent_instruments_db = db.query(Instrument).order_by(Instrument.created_at.desc()).limit(5).all()
    recent_instruments_data = [
        {
            "id": inst.id,
            "serial_number": inst.serial_number,
            "manufacturer": inst.manufacturer,
            "model": inst.model,
            "accuracy_class": inst.accuracy_class,
            "max_capacity": inst.max_capacity,
            "unit": inst.unit,
            "is_demo": inst.is_demo,
            "created_at": inst.created_at,
        }
        for inst in recent_instruments_db
    ]

    # Recent tests (last 5)
    recent_sessions = db.query(TestSession).order_by(TestSession.created_at.desc()).limit(6).all()
    recent_tests_data = []
    for s in recent_sessions:
        outcome = s.rule_evaluation.overall_outcome if s.rule_evaluation else None
        recent_tests_data.append({
            "id": s.id,
            "instrument_serial": s.instrument.serial_number if s.instrument else "Unknown",
            "instrument_model": s.instrument.model if s.instrument else "",
            "category": s.test_category,
            "operator": s.operator_name,
            "status": s.status,
            "outcome": outcome,
            "test_date": s.test_date,
            "is_demo": s.is_demo,
        })

    # Recent reports (last 5)
    recent_reports = db.query(GeneratedReport).order_by(GeneratedReport.created_at.desc()).limit(5).all()
    recent_reports_data = [
        {
            "id": r.id,
            "file_name": r.file_name,
            "test_session_id": r.test_session_id,
            "instrument_serial": r.instrument.serial_number if r.instrument else "Unknown",
            "generated_by": r.generated_by,
            "created_at": r.created_at,
        }
        for r in recent_reports
    ]

    # Recent audit events (last 5)
    recent_audit = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(5).all()
    recent_audit_data = [
        {
            "id": a.id,
            "action": a.action,
            "actor": a.actor,
            "test_session_id": a.test_session_id,
            "instrument_id": a.instrument_id,
            "timestamp": a.timestamp,
        }
        for a in recent_audit
    ]

    return {
        "metrics": {
            "total_instruments": total_instruments,
            "active_instruments": active_instruments,
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "pending_tests": pending_tests,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pending_eval_count": pending_eval_count,
            "reports_generated": reports_generated,
            "demo_instruments": demo_instruments,
            "user_instruments": user_instruments,
            "test_artifact_instruments": test_artifact_count,
            "genuine_user_instruments": genuine_user_instruments,
            "demo_tests": demo_tests,
            "user_tests": user_tests,
            "test_artifact_tests": test_artifact_tests,
            "genuine_user_tests": genuine_user_tests,
        },
        "category_distribution": [
            {"name": "Eccentricity", "value": ecc_count, "color": "#3b82f6"},
            {"name": "Linearity", "value": lin_count, "color": "#10b981"},
            {"name": "Repeatability", "value": rep_count, "color": "#8b5cf6"},
        ],
        "compliance_distribution": [
            {"name": "Pass", "value": pass_count, "color": "#10b981"},
            {"name": "Fail", "value": fail_count, "color": "#ef4444"},
            {"name": "Pending / Incomplete", "value": pending_eval_count, "color": "#f59e0b"},
        ],
        "accuracy_class_distribution": [
            {"class_name": k, "count": v} for k, v in class_distribution.items() if v > 0
        ],
        "recent_instruments": recent_instruments_data,
        "recent_tests": recent_tests_data,
        "recent_reports": recent_reports_data,
        "recent_audit_events": recent_audit_data,
    }
