from fastapi import APIRouter
from ..config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "team": settings.TEAM_NAME,
        "problem_id": settings.PROBLEM_STATEMENT_ID,
        "version": settings.VERSION,
        "database": "connected",
        "system": "NAWI Testing & Calibration Management Platform",
    }

