import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend and root paths are in sys.path
ROOT_PATH = str(Path(__file__).resolve().parent.parent.parent)
BACKEND_PATH = str(Path(__file__).resolve().parent.parent)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)
if BACKEND_PATH not in sys.path:
    sys.path.insert(0, BACKEND_PATH)

from app.main import app
from app.database import Base, engine


@pytest.fixture(scope="module")
def client():
    # Setup test client with lifespan triggered
    with TestClient(app) as test_client:
        yield test_client


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
    # Check that demo instruments exist
    serials = [i["serial_number"] for i in instruments]
    assert "SN-PRC-2026-042" in serials


def test_instrument_lifecycle(client):
    import uuid
    test_serial = f"SN-TEST-{uuid.uuid4().hex[:6].upper()}"
    # 1. Create unique instrument
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

    # 2. Reject duplicate serial number
    dup_res = client.post("/api/instruments", json=payload)
    assert dup_res.status_code == 409

    # 3. Retrieve instrument details
    get_res = client.get(f"/api/instruments/{inst_id}")
    assert get_res.status_code == 200
    assert get_res.json()["instrument"]["serial_number"] == test_serial

    # 4. Update instrument
    upd_res = client.put(f"/api/instruments/{inst_id}", json={"location": "Updated Calibration Bay"})
    assert upd_res.status_code == 200
    assert upd_res.json()["location"] == "Updated Calibration Bay"


def test_complete_test_workflow_eccentricity(client):
    # Fetch an instrument
    inst_res = client.get("/api/instruments")
    inst = inst_res.json()[0]

    # 1. Create Eccentricity Test Session
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

    # 2. Submit observations
    obs_payload = {
        "observations": [
            {"position_id": "pos_1", "position_name": "Center", "indication": 50.0, "zero_indication": 0.0},
            {"position_id": "pos_2", "position_name": "Front-Left", "indication": 50.01, "zero_indication": 0.0},
            {"position_id": "pos_3", "position_name": "Back-Left", "indication": 49.99, "zero_indication": 0.0},
        ]
    }
    res_obs = client.post(f"/api/tests/{test_id}/observations", json=obs_payload)
    assert res_obs.status_code == 200

    # 3. Run Calculation
    res_calc = client.post(f"/api/tests/{test_id}/calculate")
    assert res_calc.status_code == 200
    calc_data = res_calc.json()
    assert "calculation_result" in calc_data
    assert "rule_evaluation" in calc_data

    # 4. Generate PDF report
    res_rep = client.post(f"/api/tests/{test_id}/report")
    assert res_rep.status_code == 200
    report_id = res_rep.json()["report_id"]

    # 5. Download report
    res_dl = client.get(f"/api/reports/{report_id}/download")
    assert res_dl.status_code == 200
    assert res_dl.headers["content-type"] == "application/pdf"
    assert len(res_dl.content) > 1000  # valid PDF bytes


def test_dashboard_stats(client):
    res = client.get("/api/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert data["metrics"]["total_instruments"] >= 3
    assert len(data["recent_tests"]) > 0
    assert len(data["recent_reports"]) > 0
