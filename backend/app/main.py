import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Add root project folder to sys.path so calculation_engine and rules are discoverable
ROOT_PATH = str(Path(__file__).resolve().parent.parent.parent)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from .config import settings
from .database import engine, Base, SessionLocal
from .models import *  # Ensure all models are registered
from .services.demo_data_service import seed_demo_data

from .api.health import router as health_router
from .api.instruments import router as instruments_router
from .api.tests import router as tests_router
from .api.reports import router as reports_router
from .api.audit import router as audit_router
from .api.rules import router as rules_router
from .api.dashboard import router as dashboard_router
from .api.demo import router as demo_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed demonstration records if database is empty
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()
    yield
    # Shutdown logic if any


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="SIH 2026 NAWI Testing, Calculation & Calibration Management System | Problem ID: SIH26035 | Team: VisionVerity",
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(instruments_router, prefix=settings.API_V1_STR)
app.include_router(tests_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(rules_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)


@app.get("/")
def root_redirect():
    return {
        "project": settings.PROJECT_NAME,
        "team": settings.TEAM_NAME,
        "problem_id": settings.PROBLEM_STATEMENT_ID,
        "api_docs": "/docs",
        "api_status": "/api/health",
    }

