from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ObservationSubmit(BaseModel):
    observations: List[Dict[str, Any]] = Field(..., description="Array of observed readings")
    test_configuration: Optional[Dict[str, Any]] = None


class ObservationResponse(BaseModel):
    id: str
    test_session_id: str
    data: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
