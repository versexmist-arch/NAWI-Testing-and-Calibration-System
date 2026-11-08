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


class TestSessionAmend(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500, description="Documented justification for amending this test")
    operator_name: str = Field(..., min_length=2, max_length=100, description="Operator/Metrologist authorizing the amendment")
    observations: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional revised observations")
    test_configuration: Optional[Dict[str, Any]] = None


class ObservationData(BaseModel):
    observations: List[Dict[str, Any]]


class TestRevisionResponse(BaseModel):
    id: str
    revision_number: int
    amendment_reason: str
    amended_by: str
    status_at_amendment: str
    overall_outcome: Optional[str] = None
    created_at: datetime
    has_observations: bool = False
    has_calculations: bool = False
    has_rule_evaluations: bool = False
    observations: Optional[List[Dict[str, Any]]] = None
    calculation_result: Optional[Dict[str, Any]] = None
    rule_evaluation: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class TestSessionResponse(TestSessionBase):
    id: str
    status: str
    version: int = 1
    is_demo: bool = False
    test_date: datetime
    created_at: datetime
    updated_at: datetime
    instrument: Optional[InstrumentResponse] = None
    has_observations: bool = False
    has_calculations: bool = False
    has_rule_evaluations: bool = False
    overall_outcome: Optional[str] = None
    revisions_count: int = 0

    model_config = ConfigDict(from_attributes=True)
