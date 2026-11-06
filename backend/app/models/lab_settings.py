from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from ..database import Base


class LaboratorySettings(Base):
    __tablename__ = "laboratory_settings"

    id = Column(Integer, primary_key=True, default=1)
    lab_name = Column(String(200), nullable=False, default="VisionVerity National Metrology Standards Facility")
    organization = Column(String(200), nullable=False, default="SIH 2026 Advanced Metrology Division")
    accreditation_number = Column(String(100), nullable=False, default="ISO/IEC 17025:2017 Calibration Lab (Accreditation # NABL-CC-26035)")
    address_line1 = Column(String(200), nullable=True, default="Standards Complex, Precision Way")
    address_line2 = Column(String(200), nullable=True, default="Sector 4, Metrology Park")
    city = Column(String(100), nullable=True, default="New Delhi")
    postal_code = Column(String(50), nullable=True, default="110001")
    country = Column(String(100), nullable=True, default="India")
    contact_email = Column(String(100), nullable=True, default="calibration@visionverity-lims.gov.in")
    contact_phone = Column(String(50), nullable=True, default="+91 11 26035000")
    default_temperature = Column(Float, nullable=False, default=20.0)
    default_humidity = Column(Float, nullable=False, default=50.0)
    default_mass_unit = Column(String(20), nullable=False, default="g")
    report_header_title = Column(String(200), nullable=False, default="NAWI CALIBRATION & METROLOGICAL TEST REPORT")
    report_disclaimer = Column(
        Text,
        nullable=False,
        default=(
            "This calibration and metrological evaluation record is issued by VisionVerity under SIH 2026. "
            "Testing is performed in compliance with OIML R-76 recommendations. "
            "This report shall not be reproduced except in full without written approval of the laboratory."
        )
    )
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

