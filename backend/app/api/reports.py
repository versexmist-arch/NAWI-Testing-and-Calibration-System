import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models import GeneratedReport, TestSession, Instrument
from ..schemas.report import GeneratedReportResponse

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("", response_model=List[GeneratedReportResponse])
def list_reports(
    instrument_id: Optional[str] = None,
    test_session_id: Optional[str] = None,
    include_superseded: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(GeneratedReport)
    if instrument_id:
        query = query.filter(GeneratedReport.instrument_id == instrument_id)
    if test_session_id:
        query = query.filter(GeneratedReport.test_session_id == test_session_id)
    if not include_superseded:
        query = query.filter(GeneratedReport.is_superseded == False)
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

    target_path = report.file_path
    if not os.path.exists(target_path):
        # Cloud/Cross-environment fallback: check if file is located in active REPORTS_DIR
        candidate1 = os.path.join(settings.REPORTS_DIR, report.file_name)
        candidate2 = os.path.join(settings.REPORTS_DIR, os.path.basename(report.file_path))
        if os.path.exists(candidate1):
            target_path = candidate1
        elif os.path.exists(candidate2):
            target_path = candidate2
        else:
            raise HTTPException(
                status_code=404,
                detail="PDF report file does not exist on disk. Generate a new report from the test session."
            )

    return FileResponse(
        path=target_path,
        filename=report.file_name,
        media_type="application/pdf",
    )

