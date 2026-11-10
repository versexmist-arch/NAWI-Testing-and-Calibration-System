"""
Cloud Deployment Readiness Test Suite.

Verifies:
1. Root health check (/health) and API health check (/api/health)
2. Database connection status and engine reporting
3. DATABASE_URL normalization (postgres:// -> postgresql://)
4. CORS_ORIGINS parsing from environment variable formats (comma-separated, JSON, wildcard)
5. CORS headers on preflight requests
6. PDF report download path resilience and fallback resolution
"""

import os
import tempfile
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pydantic import ValidationError
from backend.app.config import Settings
from backend.app.database import Base, get_db, ensure_schema_compatibility
from backend.app.main import app
from backend.app.models import GeneratedReport, TestSession, Instrument


@pytest.fixture(scope="module")
def deployment_test_client():
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_deploy.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client, TestingSessionLocal, temp_dir

    app.dependency_overrides.clear()
    engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)


def test_root_and_api_health_endpoints(deployment_test_client):
    """Both /health (for cloud probes like Render) and /api/health must return 200 OK."""
    client, _, _ = deployment_test_client

    # 1. Root /health
    res_root = client.get("/health")
    assert res_root.status_code == 200
    data_root = res_root.json()
    assert data_root["status"] == "healthy"
    assert data_root["database"]["status"] == "connected"
    assert data_root["database"]["engine"] == "sqlite"

    # 2. API /api/health
    res_api = client.get("/api/health")
    assert res_api.status_code == 200
    data_api = res_api.json()
    assert data_api["status"] == "healthy"
    assert data_api["problem_id"] == "SIH26035"


def test_database_url_normalization():
    """PostgreSQL URLs must be normalized to 'postgresql+psycopg2://' to bind the installed psycopg2 driver."""
    # 1. Render/Heroku 'postgres://' scheme
    s1 = Settings(DATABASE_URL="postgres://user:pass@ep-hostname.render.com:5432/nawidb")
    assert s1.DATABASE_URL == "postgresql+psycopg2://user:pass@ep-hostname.render.com:5432/nawidb"

    # 2. Generic 'postgresql://' scheme (which SQLAlchemy 2.0 otherwise defaults to missing 'psycopg')
    s2 = Settings(DATABASE_URL="postgresql://user:pass@ep-hostname.render.com:5432/nawidb")
    assert s2.DATABASE_URL == "postgresql+psycopg2://user:pass@ep-hostname.render.com:5432/nawidb"

    # 3. Explicit 'postgresql+psycopg://' scheme
    s3 = Settings(DATABASE_URL="postgresql+psycopg://user:pass@ep-hostname.render.com:5432/nawidb")
    assert s3.DATABASE_URL == "postgresql+psycopg2://user:pass@ep-hostname.render.com:5432/nawidb"

    # 4. Explicit 'postgresql+psycopg2://' scheme remains intact
    s4 = Settings(DATABASE_URL="postgresql+psycopg2://user:pass@ep-hostname.render.com:5432/nawidb")
    assert s4.DATABASE_URL == "postgresql+psycopg2://user:pass@ep-hostname.render.com:5432/nawidb"

    # 5. SQLite local development scheme remains completely intact
    s5 = Settings(DATABASE_URL="sqlite:///./test.db")
    assert s5.DATABASE_URL == "sqlite:///./test.db"

    # 6. Verify SQLAlchemy engine creation loads psycopg2 driver without ModuleNotFoundError
    from sqlalchemy import create_engine
    engine_psycopg2 = create_engine(s1.DATABASE_URL)
    assert engine_psycopg2.dialect.name == "postgresql"
    assert engine_psycopg2.dialect.driver == "psycopg2"


def test_cors_origins_env_parsing():
    """CORS_ORIGINS must accept JSON arrays, comma-separated strings, and reject invalid configs."""
    # 1. Empty JSON list (Render default)
    s_empty = Settings(CORS_ORIGINS="[]")
    assert s_empty.CORS_ORIGINS == []

    # 2. Valid JSON list of origins
    s_json = Settings(CORS_ORIGINS='["https://nawi-cal.vercel.app", "https://visionverity.org"]')
    assert s_json.CORS_ORIGINS == ["https://nawi-cal.vercel.app", "https://visionverity.org"]

    # 3. Comma-separated origins
    s_csv = Settings(CORS_ORIGINS="https://nawi.vercel.app, http://localhost:5173")
    assert s_csv.CORS_ORIGINS == ["https://nawi.vercel.app", "http://localhost:5173"]

    # 4. Default local development origins preserved
    s_default = Settings()
    assert "http://localhost:5173" in s_default.CORS_ORIGINS

    # 5. Invalid CORS configuration - JSON object must raise ValidationError
    with pytest.raises(ValidationError):
        Settings(CORS_ORIGINS='{"not": "a list"}')

    # 6. Invalid CORS configuration - malformed JSON must raise ValidationError
    with pytest.raises(ValidationError):
        Settings(CORS_ORIGINS='["unclosed json string')

    # 7. Invalid CORS configuration - invalid type (e.g. dict) must raise ValidationError
    with pytest.raises(ValidationError):
        Settings(CORS_ORIGINS={"a": 1})


def test_cors_preflight_headers(deployment_test_client):
    """OPTIONS preflight requests from Vercel origins must return valid CORS headers, while unauthorized origins are rejected."""
    client, _, _ = deployment_test_client

    # Authorized Vercel deployment origin
    headers = {
        "Origin": "https://nawi-calibration.vercel.app",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, X-User-Id",
    }
    res = client.options("/api/instruments", headers=headers)
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://nawi-calibration.vercel.app"
    assert res.headers.get("access-control-allow-credentials") == "true"

    # Unauthorized origin must not receive Access-Control-Allow-Origin
    unauth_headers = {
        "Origin": "https://unauthorized-malicious-domain.com",
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "Content-Type, X-User-Id",
    }
    unauth_res = client.options("/api/instruments", headers=unauth_headers)
    assert unauth_res.status_code == 400
    assert "access-control-allow-origin" not in unauth_res.headers


def test_pdf_report_path_fallback(deployment_test_client):
    """
    If a report's recorded file_path was generated on another OS (e.g. Windows absolute path),
    download_report must fallback to active REPORTS_DIR resolution.
    """
    client, SessionLocal, temp_dir = deployment_test_client
    from backend.app.config import settings

    db = SessionLocal()
    # Create dummy instrument and session
    inst = Instrument(
        id="INST-FALLBACK-01",
        serial_number="SN-FB-01",
        manufacturer="Mettler",
        model="FB-1",
        accuracy_class="Class II",
        max_capacity=1000.0,
        verification_scale_interval=0.1,
    )
    db.add(inst)
    sess = TestSession(
        id="TEST-FALLBACK-01",
        instrument_id=inst.id,
        test_category="linearity",
        status="Completed",
    )
    db.add(sess)

    # Simulate report generated on different filesystem with non-existent path
    dummy_pdf_name = "test_download_fallback.pdf"
    actual_disk_path = os.path.join(settings.REPORTS_DIR, dummy_pdf_name)
    with open(actual_disk_path, "wb") as f:
        f.write(b"%PDF-1.4 dummy pdf content for testing")

    rep = GeneratedReport(
        id="REP-FALLBACK-01",
        test_session_id=sess.id,
        instrument_id=inst.id,
        version=1,
        file_name=dummy_pdf_name,
        # Intentionally non-existent foreign absolute path:
        file_path="/var/different/path/nonexistent/" + dummy_pdf_name,
    )
    db.add(rep)
    db.commit()
    db.close()

    res = client.get("/api/reports/REP-FALLBACK-01/download")
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert b"%PDF-1.4" in res.content

    # Clean up dummy file
    if os.path.exists(actual_disk_path):
        os.remove(actual_disk_path)

