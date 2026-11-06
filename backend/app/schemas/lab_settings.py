from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LaboratorySettingsBase(BaseModel):
    lab_name: str
    organization: str
    accreditation_number: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    default_temperature: float = 20.0
    default_humidity: float = 50.0
    default_mass_unit: str = "g"
    report_header_title: str = "NAWI CALIBRATION & METROLOGICAL TEST REPORT"
    report_disclaimer: str


class LaboratorySettingsUpdate(BaseModel):
    lab_name: Optional[str] = None
    organization: Optional[str] = None
    accreditation_number: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    default_temperature: Optional[float] = None
    default_humidity: Optional[float] = None
    default_mass_unit: Optional[str] = None
    report_header_title: Optional[str] = None
    report_disclaimer: Optional[str] = None


class LaboratorySettingsResponse(LaboratorySettingsBase):
    id: int
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

