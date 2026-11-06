import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(50), primary_key=True, default=lambda: f"USR-{uuid.uuid4().hex[:8].upper()}")
    username = Column(String(50), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), nullable=False, default="Metrologist/Operator")  # Administrator, Laboratory Manager, Metrologist/Operator, Reviewer
    qualification = Column(String(200), nullable=True, default="Metrology Specialist, ISO/IEC 17025")
    department = Column(String(100), nullable=True, default="Calibration Standards Laboratory")
    is_active = Column(Boolean, default=True)
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

