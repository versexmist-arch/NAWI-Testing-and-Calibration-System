from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from ..models.audit import AuditLog


def record_audit_event(
    db: Session,
    action: str,
    actor: str = "System Operator",
    test_session_id: Optional[str] = None,
    instrument_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> AuditLog:
    """Record an immutable audit event to maintain full traceability."""
    log_entry = AuditLog(
        test_session_id=test_session_id,
        instrument_id=instrument_id,
        actor=actor,
        action=action,
        details=details or {},
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry

