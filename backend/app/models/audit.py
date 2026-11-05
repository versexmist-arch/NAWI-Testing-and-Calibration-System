import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(50), primary_key=True, default=lambda: f"AUD-{uuid.uuid4().hex[:8].upper()}")
    test_session_id = Column(String(50), ForeignKey("test_sessions.id"), nullable=True, index=True)
    instrument_id = Column(String(50), ForeignKey("instruments.id"), nullable=True, index=True)
    actor = Column(String(100), nullable=False, default="System Operator")
    action = Column(String(100), nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    test_session = relationship("TestSession", back_populates="audit_logs")
    instrument = relationship("Instrument")

