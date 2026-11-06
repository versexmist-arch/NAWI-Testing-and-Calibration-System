import sys
import os
import uuid
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend and root paths are in sys.path
ROOT_PATH = str(Path(__file__).resolve().parent.parent.parent)
BACKEND_PATH = str(Path(__file__).resolve().parent.parent)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app.main import app
from app.database import Base, get_db
from app.services.demo_data_service import seed_demo_data

# Create an ISOLATED temporary test database file to guarantee production database purity
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"nawi_test_isolated_{uuid.uuid4().hex[:8]}.db")
test_engine = create_engine(f"sqlite:///{TEST_DB_PATH}", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    # 1. Build tables in isolated test database
    Base.metadata.create_all(bind=test_engine)
    test_db = TestingSessionLocal()
    try:
        seed_demo_data(test_db)
    finally:
        test_db.close()

    # 2. Override get_db dependency so ALL API requests hit the test database
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # 3. Teardown: clear overrides and delete temporary test database file
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except Exception:
        pass


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["problem_id"] == "SIH26035"
    assert data["team"] == "VisionVerity"


def test_list_demo_instruments(client):
    res = client.get("/api/instruments")
    assert res.status_code == 200
    instruments = res.json()
    assert len(instruments) >= 3
    serials = [i["serial_number"] for i in instruments]
    assert "SN-PRC-2026-042" in serials


def test_instrument_lifecycle(client):
    test_serial = f"SN-TEST-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "serial_number": test_serial,
        "manufacturer": "Precisa Gravimetrics",
        "model": "XB 220A Analytical",
        "instrument_type": "Analytical Balance",
        "accuracy_class": "Class I",
        "max_capacity": 220.0,
        "min_capacity": 0.01,
        "verification_scale_interval": 0.001,
        "actual_scale_interval": 0.0001,
        "unit": "g",
        "location": "Quality Lab 3",
        "notes": "Automated test balance."
    }
    create_res = client.post("/api/instruments", json=payload)
    assert create_res.status_code == 201
    inst_data = create_res.json()
    inst_id = inst_data["id"]
    assert inst_data["scale_intervals_count"] == 220000

    # Reject duplicate serial number
    dup_res = client.post("/api/instruments", json=payload)
    assert dup_res.status_code == 409

    # Retrieve instrument details
    get_res = client.get(f"/api/instruments/{inst_id}")
    assert get_res.status_code == 200
    assert get_res.json()["instrument"]["serial_number"] == test_serial

    # Update instrument
    upd_res = client.put(f"/api/instruments/{inst_id}", json={"location": "Updated Calibration Bay"})
    assert upd_res.status_code == 200
    assert upd_res.json()["location"] == "Updated Calibration Bay"


def test_complete_test_workflow_eccentricity(client):
    inst_res = client.get("/api/instruments")
    inst = inst_res.json()[0]

    # Create Eccentricity Test Session
    test_create_payload = {
        "instrument_id": inst["id"],
        "test_category": "eccentricity",
        "operator_name": "Test Metrologist",
        "laboratory_location": "Bay A",
        "ambient_temperature": 20.5,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {"test_load": 50.0}
    }
    res_test = client.post("/api/tests", json=test_create_payload)
    assert res_test.status_code == 201
    test_id = res_test.json()["id"]

    # Submit observations
    obs_payload = {
        "observations": [
            {"position_id": "pos_1", "position_name": "Center", "indication": 50.0, "zero_indication": 0.0},
            {"position_id": "pos_2", "position_name": "Front-Left", "indication": 50.01, "zero_indication": 0.0},
            {"position_id": "pos_3", "position_name": "Back-Left", "indication": 49.99, "zero_indication": 0.0},
        ]
    }
    res_obs = client.post(f"/api/tests/{test_id}/observations", json=obs_payload)
    assert res_obs.status_code == 200

    # Run Calculation
    res_calc = client.post(f"/api/tests/{test_id}/calculate")
    assert res_calc.status_code == 200
    calc_data = res_calc.json()
    assert "calculation_result" in calc_data
    assert "rule_evaluation" in calc_data

    # Generate PDF report
    res_rep = client.post(f"/api/tests/{test_id}/report")
    assert res_rep.status_code == 200
    report_id = res_rep.json()["report_id"]

    # Download report
    res_dl = client.get(f"/api/reports/{report_id}/download")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    assert len(res_dl.content) > 1000


def test_dashboard_stats(client):
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert data["metrics"]["total_instruments"] >= 3
    assert len(data["recent_tests"]) > 0
    assert len(data["recent_reports"]) > 0


def test_users_management(client):
    res = client.get("/api/users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 1

    new_user = {
        "username": f"test_op_{uuid.uuid4().hex[:4]}",
        "full_name": "Calibration Engineer Test",
        "email": f"test_{uuid.uuid4().hex[:4]}@lab.org",
        "role": "Metrologist/Operator",
        "qualification": "Certified Metrologist",
        "department": "Mass Lab"
    }
    res_create = client.post("/api/users", json=new_user)
    assert res_create.status_code == 201
    assert res_create.json()["username"] == new_user["username"]


def test_laboratory_settings(client):
    res = client.get("/api/lab-settings")
    assert res.status_code == 200
    lab = res.json()
    assert "lab_name" in lab

    # Update lab settings
    res_upd = client.put("/api/lab-settings", json={"city": "Bengaluru"})
    assert res_upd.status_code == 200
    assert res_upd.json()["city"] == "Bengaluru"


def test_analytics_endpoint(client):
    res = client.get("/api/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "category_distribution" in data
    assert "monthly_trend" in data
