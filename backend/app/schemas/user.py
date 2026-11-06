from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class UserBase(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., max_length=100)
    role: str = Field(default="Metrologist/Operator")
    qualification: Optional[str] = "Metrology Specialist, ISO/IEC 17025"
    department: Optional[str] = "Calibration Standards Laboratory"
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    qualification: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: str
    is_demo: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

