import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import GeneratedReport, TestSession, Instrument
from ..schemas.report import GeneratedReportResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=List[GeneratedReportResponse])
def list_reports(
    instrument_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(GeneratedReport)
    if instrument_id:
        query = query.filter(GeneratedReport.instrument_id == instrument_id)
    return query.order_by(GeneratedReport.created_at.desc()).all()


@router.get("/{report_id}")
def get_report_info(report_id: str, db: Session = Depends(get_db)):
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return GeneratedReportResponse.model_validate(report)


@router.get("/{report_id}/download")
def download_report(report_id: str, db: Session = Depends(get_db)):
    report = db.query(GeneratedReport).filter(GeneratedReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    if not os.path.exists(report.file_path):
        raise HTTPException(status_code=404, detail="PDF report file does not exist on disk.")

    return FileResponse(
        path=report.file_path,
        filename=report.file_name,
        media_type="application/pdf",
    )

