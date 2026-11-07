"""
TASK 5 — Full Pipeline Testing via FastAPI TestClient (isolated temp DB).
Mimics the pattern in backend/tests/test_api.py for temp DB isolation.

Run with: .\backend\venv\Scripts\pytest backend\scripts\regression\task5_pipeline.py -v
"""
import sys
import os
import uuid
import tempfile
from pathlib import Path

# Path setup
ROOT_PATH = str(Path(__file__).resolve().parent.parent.parent.parent)
BACKEND_PATH = str(Path(__file__).resolve().parent.parent.parent)
for p in (ROOT_PATH, BACKEND_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.services.demo_data_service import seed_demo_data

# ------------------------------------------------------------------ #
# Isolated temp DB fixture                                            #
# ------------------------------------------------------------------ #
TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"nawi_task5_{uuid.uuid4().hex[:8]}.db")
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
    Base.metadata.create_all(bind=test_engine)
    test_db = TestingSessionLocal()
    try:
        seed_demo_data(test_db)
    finally:
        test_db.close()
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except Exception:
        pass


# ------------------------------------------------------------------ #
# Helpers                                                             #
# ------------------------------------------------------------------ #
def get_class3_instrument_id(client):
    """Return a Class III instrument with max_capacity=3000g for pipeline tests.
    
    The seeded demo INST-DEMO-03 is Class III but only 60g max — unsuitable.
    We always create a fresh 3000g Class III instrument for Task 5.
    """
    payload = {
        "serial_number": f"SN-T5-{uuid.uuid4().hex[:6].upper()}",
        "manufacturer": "Task5 Test", "model": "DS-3000", "instrument_type": "Platform Scale",
        "accuracy_class": "Class III", "max_capacity": 3000.0, "min_capacity": 0.0,
        "verification_scale_interval": 1.0, "actual_scale_interval": 1.0,
        "unit": "g", "location": "Task5 Lab", "notes": "Regression test instrument"
    }
    res = client.post("/api/instruments", json=payload)
    assert res.status_code == 201, f"Could not create Class III test instrument: {res.text}"
    inst = res.json()
    return inst["id"], inst


def create_test_session(client, instrument_id, category="linearity"):
    payload = {
        "instrument_id": instrument_id,
        "test_category": category,
        "operator_name": "Task5 Tester",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {"use_changeover_points": False},
    }
    res = client.post("/api/tests", json=payload)
    assert res.status_code == 201, f"Session create failed: {res.text}"
    return res.json()["id"]


def submit_observations(client, session_id, observations):
    res = client.post(f"/api/tests/{session_id}/observations", json={"observations": observations})
    return res


def run_pipeline(client, session_id):
    res = client.post(f"/api/tests/{session_id}/calculate")
    return res


# ------------------------------------------------------------------ #
# T5-A: Valid linearity test → PASS                                  #
# ------------------------------------------------------------------ #
def test_t5_a_valid_linearity(client):
    """Valid observations on Class III instrument → pipeline completes → PASS."""
    inst_id, inst = get_class3_instrument_id(client)
    session_id = create_test_session(client, inst_id)

    good_obs = [
        {"load": 0,    "indication": 0.0,    "direction": "increasing"},
        {"load": 500,  "indication": 499.9,  "direction": "increasing"},
        {"load": 1000, "indication": 1000.1, "direction": "increasing"},
        {"load": 2000, "indication": 1999.8, "direction": "increasing"},
        {"load": 3000, "indication": 2999.9, "direction": "increasing"},
    ]
    obs_res = submit_observations(client, session_id, good_obs)
    assert obs_res.status_code == 200, f"T5-A obs fail: {obs_res.text}"

    calc_res = run_pipeline(client, session_id)
    assert calc_res.status_code == 200, f"T5-A calc fail: {calc_res.text}"
    data = calc_res.json()
    outcome = data["rule_evaluation"]["overall_outcome"]
    assert outcome == "PASS", f"T5-A: expected PASS, got {outcome}"
    print(f"\n  [PASS] T5-A: Valid linearity → outcome={outcome}")


# ------------------------------------------------------------------ #
# T5-B: Invalid observation (missing 'load' key) → 422               #
# ------------------------------------------------------------------ #
def test_t5_b_invalid_observations(client):
    """Missing 'load' field in observation → 422 Unprocessable Entity."""
    inst_id, _ = get_class3_instrument_id(client)
    session_id = create_test_session(client, inst_id)

    bad_obs = [
        {"indication": 0.0},          # missing 'load'
        {"load": 500, "indication": 499.9},
    ]
    obs_res = submit_observations(client, session_id, bad_obs)
    # Schema validation should catch missing 'load'
    if obs_res.status_code == 422:
        print(f"\n  [PASS] T5-B: Missing 'load' field → 422")
        return
    # If observations accepted, calculation should fail
    calc_res = run_pipeline(client, session_id)
    assert calc_res.status_code in (400, 422), \
        f"T5-B: expected 400/422, got {calc_res.status_code}: {calc_res.text}"
    print(f"\n  [PASS] T5-B: Missing 'load' field → {calc_res.status_code}")


# ------------------------------------------------------------------ #
# T5-C: Over-capacity load → 422 (BUG-4 test)                        #
# ------------------------------------------------------------------ #
def test_t5_c_over_capacity(client):
    """
    Load exceeding instrument max_capacity must be REJECTED.
    If BUG-4 is not yet fixed, this test FAILS and documents the bug.
    """
    inst_id, inst = get_class3_instrument_id(client)
    max_cap = inst.get("max_capacity", 3000.0)
    session_id = create_test_session(client, inst_id)

    over_cap_obs = [
        {"load": 0,           "indication": 0.0,        "direction": "increasing"},
        {"load": 500,         "indication": 500.0,      "direction": "increasing"},
        {"load": max_cap + 1, "indication": max_cap + 1,"direction": "increasing"},
    ]
    obs_res = submit_observations(client, session_id, over_cap_obs)
    if obs_res.status_code == 422:
        print(f"\n  [PASS] T5-C: Over-capacity → 422 at observations stage")
        return
    calc_res = run_pipeline(client, session_id)
    if calc_res.status_code == 422:
        print(f"\n  [PASS] T5-C: Over-capacity → 422 at calculation stage")
        return
    # BUG-4: over-capacity NOT rejected
    outcome = calc_res.json().get("rule_evaluation", {}).get("overall_outcome", "?")
    print(f"\n  [FAIL] T5-C: BUG-4 — Over-capacity load {max_cap+1}g on {max_cap}g instrument "
          f"NOT rejected! Pipeline returned {calc_res.status_code}, outcome={outcome}")
    pytest.fail(f"BUG-4: Over-capacity load accepted. Status={calc_res.status_code}, outcome={outcome}")


# ------------------------------------------------------------------ #
# T5-D: Hysteresis failure → FAIL with HYS rule                      #
# ------------------------------------------------------------------ #
def test_t5_d_hysteresis_failure(client):
    """
    Exceeding hysteresis limit at a load point → overall outcome FAIL
    with OIML-R76-1-LIN-HYS rule evaluation.
    """
    inst_id, inst = get_class3_instrument_id(client)
    e = inst.get("verification_scale_interval", 1.0)
    # At load=200, MPE=0.5*e. Hysteresis = inc - dec > MPE
    mpe = 0.5 * e

    session_id = create_test_session(client, inst_id)

    hys_obs = [
        {"load": 0,   "indication": 0.0,        "direction": "increasing"},
        {"load": 0,   "indication": 0.0,        "direction": "decreasing"},
        {"load": 200, "indication": 200 + mpe + 0.1,  "direction": "increasing"},
        {"load": 200, "indication": 200 - mpe - 0.1,  "direction": "decreasing"},
    ]
    obs_res = submit_observations(client, session_id, hys_obs)
    assert obs_res.status_code == 200, f"T5-D obs fail: {obs_res.text}"

    calc_res = run_pipeline(client, session_id)
    assert calc_res.status_code == 200, f"T5-D calc fail: {calc_res.text}"
    data = calc_res.json()
    outcome = data["rule_evaluation"]["overall_outcome"]
    evals = data["rule_evaluation"].get("evaluations", [])
    hys_present = any(ev.get("rule_id") == "OIML-R76-1-LIN-HYS" for ev in evals)
    assert outcome == "FAIL", f"T5-D: expected FAIL, got {outcome}"
    assert hys_present, "T5-D: OIML-R76-1-LIN-HYS rule evaluation missing"
    print(f"\n  [PASS] T5-D: Hysteresis failure → outcome={outcome}, HYS rule present")


# ------------------------------------------------------------------ #
# T5-E: Replay historical DEMO session data → PASS                   #
# ------------------------------------------------------------------ #
def test_t5_e_historical_demo_replay(client):
    """
    Replay TEST-DEMO-LIN-02 observation data (Class II, good quality)
    on a fresh Class II instrument → expect PASS.
    """
    # Create a Class II instrument
    payload = {
        "serial_number": f"SN-T5E-{uuid.uuid4().hex[:6].upper()}",
        "manufacturer": "Mettler Toledo", "model": "ICS685", "instrument_type": "Platform Scale",
        "accuracy_class": "Class II", "max_capacity": 3000.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.1, "actual_scale_interval": 0.1,
        "unit": "g", "location": "Task5 Lab", "notes": "Demo replay test"
    }
    res = client.post("/api/instruments", json=payload)
    assert res.status_code == 201, f"T5-E instrument create fail: {res.text}"
    inst_id = res.json()["id"]

    session_id = create_test_session(client, inst_id)

    # TEST-DEMO-LIN-02 had e=0.1g, Class II; observations with errors ~±0.09g
    demo_obs = [
        {"load": 0.0,    "indication": 0.00,   "direction": "increasing"},
        {"load": 500.0,  "indication": 499.95, "direction": "increasing"},
        {"load": 1000.0, "indication": 999.92, "direction": "increasing"},
        {"load": 2000.0, "indication": 1999.95,"direction": "increasing"},
        {"load": 3000.0, "indication": 2999.91,"direction": "increasing"},
    ]
    obs_res = submit_observations(client, session_id, demo_obs)
    assert obs_res.status_code == 200, f"T5-E obs fail: {obs_res.text}"

    calc_res = run_pipeline(client, session_id)
    assert calc_res.status_code == 200, f"T5-E calc fail: {calc_res.text}"
    data = calc_res.json()
    outcome = data["rule_evaluation"]["overall_outcome"]
    assert outcome == "PASS", f"T5-E: expected PASS for demo-quality data, got {outcome}"
    print(f"\n  [PASS] T5-E: Historical demo data replay → outcome={outcome}")

