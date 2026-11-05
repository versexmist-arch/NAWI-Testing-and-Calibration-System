from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from .instrument import InstrumentResponse


class GeneratedReportResponse(BaseModel):
    id: str
    test_session_id: str
    instrument_id: str
    file_name: str
    generated_by: str
    report_type: str
    created_at: datetime
    instrument: Optional[InstrumentResponse] = None

    model_config = ConfigDict(from_attributes=True)
