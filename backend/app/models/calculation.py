import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class CalculationResult(Base):
    __tablename__ = "calculation_results"

    id = Column(String(50), primary_key=True, default=lambda: f"CALC-{uuid.uuid4().hex[:8].upper()}")
    test_session_id = Column(String(50), ForeignKey("test_sessions.id"), unique=True, nullable=False, index=True)
    calculation_version = Column(String(50), nullable=False)
    method = Column(String(200), nullable=False)
    summary_data = Column(JSON, nullable=False)
    full_data = Column(JSON, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_session = relationship("TestSession", back_populates="calculation_result")


class RuleEvaluation(Base):
    __tablename__ = "rule_evaluations"

    id = Column(String(50), primary_key=True, default=lambda: f"EVAL-{uuid.uuid4().hex[:8].upper()}")
    test_session_id = Column(String(50), ForeignKey("test_sessions.id"), unique=True, nullable=False, index=True)
    rule_version = Column(String(50), nullable=False)
    overall_outcome = Column(String(50), nullable=False)  # PASS, FAIL, INCOMPLETE, etc.
    summary_text = Column(String(300), nullable=True)
    evaluations_data = Column(JSON, nullable=False)
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    test_session = relationship("TestSession", back_populates="rule_evaluation")

