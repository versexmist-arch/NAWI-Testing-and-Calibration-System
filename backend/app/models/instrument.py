import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id = Column(String(50), primary_key=True, default=lambda: f"INST-{uuid.uuid4().hex[:8].upper()}")
    serial_number = Column(String(100), unique=True, nullable=False, index=True)
    manufacturer = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    instrument_type = Column(String(100), nullable=False, default="Bench Scale")
    accuracy_class = Column(String(50), nullable=False, default="Class III")
    max_capacity = Column(Float, nullable=False)
    min_capacity = Column(Float, nullable=True)
    verification_scale_interval = Column(Float, nullable=False)  # e
    actual_scale_interval = Column(Float, nullable=True)         # d
    unit = Column(String(20), nullable=False, default="g")
    scale_intervals_count = Column(Integer, nullable=True)       # n = Max / e
    location = Column(String(150), nullable=True, default="Metrology Laboratory")
    registration_date = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text, nullable=True)
    is_demo = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    test_sessions = relationship("TestSession", back_populates="instrument", cascade="all, delete-orphan")

