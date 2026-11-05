from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Instrument, TestSession, GeneratedReport, RuleEvaluation

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def get_dashboard_statistics(db: Session = Depends(get_db)):
    total_instruments = db.query(Instrument).filter(Instrument.is_archived == False).count()
    total_tests = db.query(TestSession).count()
    completed_tests = db.query(TestSession).filter(TestSession.status == "Completed").count()
    pending_tests = db.query(TestSession).filter(TestSession.status.in_(["Draft", "In Progress", "Calculated"])).count()

    # Rule outcomes breakdown
    pass_count = db.query(RuleEvaluation).filter(RuleEvaluation.overall_outcome == "PASS").count()
    fail_count = db.query(RuleEvaluation).filter(RuleEvaluation.overall_outcome == "FAIL").count()
    pending_eval_count = db.query(RuleEvaluation).filter(
        RuleEvaluation.overall_outcome.in_(["PENDING_VERIFICATION", "INCOMPLETE"])
    ).count()

    # Test category distribution
    ecc_count = db.query(TestSession).filter(TestSession.test_category == "eccentricity").count()
    lin_count = db.query(TestSession).filter(TestSession.test_category == "linearity").count()
    rep_count = db.query(TestSession).filter(TestSession.test_category == "repeatability").count()

    # Recent tests
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

    # Recent reports
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

    return {
        "metrics": {
            "total_instruments": total_instruments,
            "total_tests": total_tests,
            "completed_tests": completed_tests,
            "pending_tests": pending_tests,
            "pass_count": pass_count,
            "fail_count": fail_count,
            "pending_eval_count": pending_eval_count,
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
        "recent_tests": recent_tests_data,
        "recent_reports": recent_reports_data,
    }

