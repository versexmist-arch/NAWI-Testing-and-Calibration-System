import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class TestRevision(Base):
    __tablename__ = "test_revisions"

    id = Column(String(50), primary_key=True, default=lambda: f"REV-{uuid.uuid4().hex[:8].upper()}")
    test_session_id = Column(String(50), ForeignKey("test_sessions.id"), nullable=False, index=True)
    revision_number = Column(Integer, nullable=False)
    amendment_reason = Column(String(500), nullable=False)
    amended_by = Column(String(100), nullable=False)
    status_at_amendment = Column(String(50), nullable=False)
    observations_snapshot = Column(JSON, nullable=True)
    calculation_snapshot = Column(JSON, nullable=True)
    rule_evaluation_snapshot = Column(JSON, nullable=True)
    overall_outcome = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_session = relationship("TestSession", back_populates="revisions")


class TestSession(Base):
    __tablename__ = "test_sessions"

    id = Column(String(50), primary_key=True, default=lambda: f"TEST-{uuid.uuid4().hex[:8].upper()}")
    instrument_id = Column(String(50), ForeignKey("instruments.id"), nullable=False, index=True)
    test_category = Column(String(50), nullable=False)  # eccentricity, linearity, repeatability
    operator_name = Column(String(100), nullable=False, default="Senior Metrologist")
    laboratory_location = Column(String(150), nullable=True)
    test_date = Column(DateTime, default=datetime.utcnow)
    ambient_temperature = Column(Float, nullable=True)
    relative_humidity = Column(Float, nullable=True)
    service_type = Column(String(50), default="initial")  # initial vs service
    status = Column(String(50), default="Draft")  # Draft, In Progress, Calculated, Completed, Incomplete
    version = Column(Integer, default=1)
    test_configuration = Column(JSON, nullable=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    instrument = relationship("Instrument", back_populates="test_sessions")
    observations = relationship("Observation", back_populates="test_session", uselist=False, cascade="all, delete-orphan")
    calculation_result = relationship("CalculationResult", back_populates="test_session", uselist=False, cascade="all, delete-orphan")
    rule_evaluation = relationship("RuleEvaluation", back_populates="test_session", uselist=False, cascade="all, delete-orphan")
    reports = relationship("GeneratedReport", back_populates="test_session", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="test_session", cascade="all, delete-orphan")
    revisions = relationship("TestRevision", back_populates="test_session", order_by="TestRevision.revision_number.desc()", cascade="all, delete-orphan")
