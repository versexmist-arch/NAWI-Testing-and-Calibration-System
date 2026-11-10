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
from .database import engine, Base, SessionLocal, ensure_schema_compatibility
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
from .api.users import router as users_router
from .api.auth import router as auth_router
from .api.lab_settings import router as lab_settings_router
from .api.analytics import router as analytics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables and seed demonstration records if database is empty
    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)
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

# Production-ready CORS configuration using environment variables
cors_origins = settings.CORS_ORIGINS or ["*"]
if "*" in cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"^https?:\/\/.*",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_origin_regex=settings.CORS_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Root-level health check for cloud platform monitoring probes (Render, AWS, GCP, etc.)
app.include_router(health_router)

# Include API v1 routers
app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(instruments_router, prefix=settings.API_V1_STR)
app.include_router(tests_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(rules_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(lab_settings_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)


@app.get("/")
def root_redirect():
    return {
        "project": settings.PROJECT_NAME,
        "team": settings.TEAM_NAME,
        "problem_id": settings.PROBLEM_STATEMENT_ID,
        "api_docs": "/docs",
        "api_status": "/api/health",
    }

