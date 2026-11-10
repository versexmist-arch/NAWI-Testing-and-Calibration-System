from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..config import settings
from ..database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    engine_dialect = "unknown"
    try:
        db.execute(text("SELECT 1"))
        if db.bind:
            engine_dialect = db.bind.dialect.name
    except Exception as e:
        db_status = f"degraded: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "project": settings.PROJECT_NAME,
        "team": settings.TEAM_NAME,
        "problem_id": settings.PROBLEM_STATEMENT_ID,
        "version": settings.VERSION,
        "database": {
            "status": db_status,
            "engine": engine_dialect,
        },
        "system": "NAWI Testing & Calibration Management Platform",
    }
