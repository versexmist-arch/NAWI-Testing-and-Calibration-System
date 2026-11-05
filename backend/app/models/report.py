import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class GeneratedReport(Base):
    __tablename__ = "generated_reports"

    id = Column(String(50), primary_key=True, default=lambda: f"REP-{uuid.uuid4().hex[:8].upper()}")
    test_session_id = Column(String(50), ForeignKey("test_sessions.id"), nullable=False, index=True)
    instrument_id = Column(String(50), ForeignKey("instruments.id"), nullable=False, index=True)
    file_path = Column(String(300), nullable=False)
    file_name = Column(String(150), nullable=False)
    generated_by = Column(String(100), default="Lead Metrologist")
    report_type = Column(String(100), default="Metrological Testing & Calibration Report")
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_session = relationship("TestSession", back_populates="reports")
    instrument = relationship("Instrument")

