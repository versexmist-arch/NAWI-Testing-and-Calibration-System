import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from ..database import Base


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(50), primary_key=True, default=lambda: f"OBS-{uuid.uuid4().hex[:8].upper()}")
    test_session_id = Column(String(50), ForeignKey("test_sessions.id"), unique=True, nullable=False, index=True)
    data = Column(JSON, nullable=False)  # Raw structured observation records
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_session = relationship("TestSession", back_populates="observations")

