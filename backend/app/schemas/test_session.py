from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from .instrument import InstrumentResponse


class TestSessionBase(BaseModel):
    instrument_id: str
    test_category: str = Field(..., description="'eccentricity', 'linearity', or 'repeatability'")
    operator_name: str = Field(default="Senior Metrologist")
    laboratory_location: Optional[str] = "Metrology Laboratory"
    ambient_temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    service_type: str = Field(default="initial", description="'initial' or 'service'")
    test_configuration: Optional[Dict[str, Any]] = None


class TestSessionCreate(TestSessionBase):
    pass


class TestSessionUpdate(BaseModel):
    operator_name: Optional[str] = None
    laboratory_location: Optional[str] = None
    ambient_temperature: Optional[float] = None
    relative_humidity: Optional[float] = None
    service_type: Optional[str] = None
    status: Optional[str] = None
    test_configuration: Optional[Dict[str, Any]] = None


class ObservationData(BaseModel):
    observations: List[Dict[str, Any]]


class TestSessionResponse(TestSessionBase):
    id: str
    status: str
    version: int
    is_demo: bool = False
    test_date: datetime
    created_at: datetime
    updated_at: datetime
    instrument: Optional[InstrumentResponse] = None
    has_observations: bool = False
    has_calculations: bool = False
    has_rule_evaluations: bool = False
    overall_outcome: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
