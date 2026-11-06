from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Instrument, TestSession, RuleEvaluation, GeneratedReport, AuditLog

router = APIRouter(prefix="/analytics", tags=["Analytics & Insights"])


@router.get("")
def get_comprehensive_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TestSession)
    if start_date:
        try:
            s_dt = datetime.fromisoformat(start_date)
            query = query.filter(TestSession.created_at >= s_dt)
        except Exception:
            pass
    if end_date:
        try:
            e_dt = datetime.fromisoformat(end_date)
            query = query.filter(TestSession.created_at <= e_dt)
        except Exception:
            pass

    sessions = query.all()

    # Category breakdown
    ecc_sessions = [s for s in sessions if s.test_category == "eccentricity"]
    lin_sessions = [s for s in sessions if s.test_category == "linearity"]
    rep_sessions = [s for s in sessions if s.test_category == "repeatability"]

    # Evaluation breakdown
    pass_count = sum(1 for s in sessions if s.rule_evaluation and s.rule_evaluation.overall_outcome == "PASS")
    fail_count = sum(1 for s in sessions if s.rule_evaluation and s.rule_evaluation.overall_outcome == "FAIL")
    pending_count = sum(1 for s in sessions if s.rule_evaluation and s.rule_evaluation.overall_outcome in ("PENDING_VERIFICATION", "INCOMPLETE"))

    # Accuracy class distribution of tested instruments
    class_counts: Dict[str, int] = {"Class I": 0, "Class II": 0, "Class III": 0, "Class IIII": 0}
    for s in sessions:
        if s.instrument and s.instrument.accuracy_class in class_counts:
            class_counts[s.instrument.accuracy_class] += 1
        elif s.instrument:
            class_counts[s.instrument.accuracy_class] = class_counts.get(s.instrument.accuracy_class, 0) + 1

    # Monthly activity (last 6 months trend)
    monthly_data: Dict[str, Dict[str, int]] = {}
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        m_dt = now - timedelta(days=i * 30)
        m_key = m_dt.strftime("%b %Y")
        monthly_data[m_key] = {"month": m_key, "tests": 0, "passed": 0, "failed": 0}

    for s in sessions:
        m_key = s.created_at.strftime("%b %Y")
        if m_key in monthly_data:
            monthly_data[m_key]["tests"] += 1
            if s.rule_evaluation and s.rule_evaluation.overall_outcome == "PASS":
                monthly_data[m_key]["passed"] += 1
            elif s.rule_evaluation and s.rule_evaluation.overall_outcome == "FAIL":
                monthly_data[m_key]["failed"] += 1

    # Total reports generated
    total_reports = db.query(GeneratedReport).count()

    # Operator activity summary
    operator_activity: Dict[str, int] = {}
    for s in sessions:
        op = s.operator_name or "Unknown"
        operator_activity[op] = operator_activity.get(op, 0) + 1

    return {
        "summary": {
            "total_tests": len(sessions),
            "completed_tests": sum(1 for s in sessions if s.status == "Completed"),
            "passed_tests": pass_count,
            "failed_tests": fail_count,
            "pending_tests": pending_count,
            "pass_rate_percentage": round((pass_count / len(sessions) * 100), 1) if sessions else 0,
            "total_reports_generated": total_reports,
        },
        "monthly_trend": list(monthly_data.values()),
        "category_distribution": [
            {"name": "Eccentricity", "value": len(ecc_sessions), "color": "#3b82f6"},
            {"name": "Linearity", "value": len(lin_sessions), "color": "#10b981"},
            {"name": "Repeatability", "value": len(rep_sessions), "color": "#8b5cf6"},
        ],
        "compliance_distribution": [
            {"name": "PASS", "value": pass_count, "color": "#10b981"},
            {"name": "FAIL", "value": fail_count, "color": "#ef4444"},
            {"name": "Pending / Incomplete", "value": pending_count, "color": "#f59e0b"},
        ],
        "accuracy_class_distribution": [
            {"class_name": k, "count": v} for k, v in class_counts.items()
        ],
        "operator_distribution": [
            {"operator": k, "tests_count": v} for k, v in sorted(operator_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
    }

