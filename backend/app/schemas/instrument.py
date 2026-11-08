from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class InstrumentBase(BaseModel):
    serial_number: str = Field(..., min_length=2, max_length=100)
    manufacturer: str = Field(..., min_length=1, max_length=100)
    model: str = Field(..., min_length=1, max_length=100)
    instrument_type: str = Field(default="Bench Scale")
    accuracy_class: str = Field(default="Class III")
    max_capacity: float = Field(..., gt=0, description="Rated maximum capacity (must be strictly > 0)")
    min_capacity: Optional[float] = Field(default=None, ge=0, description="Minimum capacity (must be >= 0)")
    verification_scale_interval: float = Field(..., gt=0, description="Verification scale interval e (must be strictly > 0)")
    actual_scale_interval: Optional[float] = Field(default=None, gt=0, description="Actual scale interval d (must be strictly > 0)")
    unit: str = Field(default="g")
    location: Optional[str] = Field(default="Metrology Laboratory")
    notes: Optional[str] = None

    @model_validator(mode="after")
    def validate_capacities(self):
        if self.min_capacity is not None and self.max_capacity is not None:
            if self.min_capacity >= self.max_capacity:
                raise ValueError("Minimum capacity must be strictly less than maximum capacity.")
        return self


class InstrumentCreate(InstrumentBase):
    pass


class InstrumentUpdate(BaseModel):
    serial_number: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    instrument_type: Optional[str] = None
    accuracy_class: Optional[str] = None
    max_capacity: Optional[float] = Field(default=None, gt=0, description="Rated maximum capacity (must be strictly > 0)")
    min_capacity: Optional[float] = Field(default=None, ge=0, description="Minimum capacity (must be >= 0)")
    verification_scale_interval: Optional[float] = Field(default=None, gt=0, description="Verification scale interval e (must be strictly > 0)")
    actual_scale_interval: Optional[float] = Field(default=None, gt=0, description="Actual scale interval d (must be strictly > 0)")
    unit: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    is_archived: Optional[bool] = None

    @model_validator(mode="after")
    def validate_capacities(self):
        if self.min_capacity is not None and self.max_capacity is not None:
            if self.min_capacity >= self.max_capacity:
                raise ValueError("Minimum capacity must be strictly less than maximum capacity.")
        return self


class InstrumentResponse(InstrumentBase):
    id: str
    scale_intervals_count: Optional[int] = None
    registration_date: datetime
    is_demo: bool = False
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
