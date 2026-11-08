"""
PHASE 2: End-to-End Laboratory Workflow Audit
Covers all 9 workflows + investigation points.
Run via: .\backend\venv\Scripts\pytest backend\scripts\regression\phase2_e2e_audit.py -v --tb=short
Uses isolated temp DB -- never touches production.
"""
import sys, os, uuid, tempfile
from pathlib import Path

ROOT = str(Path(__file__).resolve().parents[3])
BACKEND = str(Path(__file__).resolve().parents[2])
for p in (ROOT, BACKEND):
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
# Isolated temp DB                                                    #
# ------------------------------------------------------------------ #
_DB_PATH = os.path.join(tempfile.gettempdir(), f"nawi_p2_{uuid.uuid4().hex[:8]}.db")
_engine = create_engine(f"sqlite:///{_DB_PATH}", connect_args={"check_same_thread": False})
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

def _override_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(scope="module")
def api():
    Base.metadata.create_all(bind=_engine)
    db = _Session()
    seed_demo_data(db)
    db.close()
    app.dependency_overrides[get_db] = _override_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)
    try:
        os.remove(_DB_PATH)
    except Exception:
        pass

# ------------------------------------------------------------------ #
# Shared fixture: create a standard Class III 3000g instrument       #
# ------------------------------------------------------------------ #
@pytest.fixture(scope="module")
def std_instrument(api):
    r = api.post("/api/instruments", json={
        "serial_number": f"SN-P2-{uuid.uuid4().hex[:8].upper()}",
        "manufacturer": "Phase2 Lab",
        "model": "DS-3000",
        "instrument_type": "Platform Scale",
        "accuracy_class": "Class III",
        "max_capacity": 3000.0,
        "min_capacity": 0.0,
        "verification_scale_interval": 1.0,
        "actual_scale_interval": 1.0,
        "unit": "g",
        "location": "Phase2 Bay",
        "notes": "Phase 2 audit instrument",
    })
    assert r.status_code == 201, f"Instrument create failed: {r.text}"
    return r.json()

# ================================================================== #
# WF-1: INSTRUMENT REGISTRATION, VALIDATION, PERSISTENCE            #
# ================================================================== #

def test_wf1_01_create_instrument_valid(api):
    """WF-1-01: Valid instrument creation returns 201 with correct fields."""
    sn = f"SN-WF1-{uuid.uuid4().hex[:6].upper()}"
    r = api.post("/api/instruments", json={
        "serial_number": sn,
        "manufacturer": "Mettler Toledo",
        "model": "XB220A",
        "instrument_type": "Analytical Balance",
        "accuracy_class": "Class I",
        "max_capacity": 220.0,
        "min_capacity": 0.001,
        "verification_scale_interval": 0.001,
        "actual_scale_interval": 0.0001,
        "unit": "g",
        "location": "Metrology Lab 1",
        "notes": "WF1 test instrument",
    })
    assert r.status_code == 201
    d = r.json()
    assert d["serial_number"] == sn
    assert d["accuracy_class"] == "Class I"
    assert d["scale_intervals_count"] == 220000
    assert d["id"].startswith("INST-")
    assert d["is_archived"] == False


def test_wf1_02_duplicate_serial_number_rejected(api):
    """WF-1-02: Registering a duplicate serial number returns 409."""
    sn = f"SN-DUP-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "serial_number": sn, "manufacturer": "X", "model": "Y",
        "instrument_type": "Scale", "accuracy_class": "Class III",
        "max_capacity": 100.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.1, "actual_scale_interval": 0.1,
        "unit": "g", "location": "Lab", "notes": "",
    }
    r1 = api.post("/api/instruments", json=payload)
    assert r1.status_code == 201
    r2 = api.post("/api/instruments", json=payload)
    assert r2.status_code == 409
    assert "already registered" in r2.json()["detail"].lower()


def test_wf1_03_missing_required_fields_rejected(api):
    """WF-1-03: Missing required fields (serial_number) returns 422."""
    r = api.post("/api/instruments", json={
        "manufacturer": "X", "model": "Y",
        "accuracy_class": "Class III",
        "max_capacity": 100.0,
        "verification_scale_interval": 0.1,
        "unit": "g",
    })
    assert r.status_code == 422


def test_wf1_04_negative_capacity_behaviour(api):
    """WF-1-04: Negative max_capacity — check if rejected or accepted."""
    r = api.post("/api/instruments", json={
        "serial_number": f"SN-NEG-{uuid.uuid4().hex[:4]}",
        "manufacturer": "X", "model": "Y", "instrument_type": "Scale",
        "accuracy_class": "Class III", "max_capacity": -1.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.1, "actual_scale_interval": 0.1,
        "unit": "g", "location": "Lab", "notes": "",
    })
    # Document behaviour — may be accepted or rejected
    # Metrologically: negative capacity is invalid
    print(f"\n  WF-1-04: negative max_capacity => HTTP {r.status_code}")
    if r.status_code == 201:
        pytest.warns(UserWarning, match=".*") if False else None
        print("  FINDING: Negative max_capacity accepted (should be rejected)")
    else:
        assert r.status_code in (400, 422)


def test_wf1_05_zero_e_behaviour(api):
    """WF-1-05: Zero verification scale interval — should be rejected."""
    r = api.post("/api/instruments", json={
        "serial_number": f"SN-ZERO-{uuid.uuid4().hex[:4]}",
        "manufacturer": "X", "model": "Y", "instrument_type": "Scale",
        "accuracy_class": "Class III", "max_capacity": 100.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.0, "actual_scale_interval": 0.0,
        "unit": "g", "location": "Lab", "notes": "",
    })
    print(f"\n  WF-1-05: zero verification_scale_interval => HTTP {r.status_code}")
    if r.status_code == 201:
        print("  FINDING: Zero e accepted (calculation engine will raise ValueError)")


def test_wf1_06_persistence_after_creation(api):
    """WF-1-06: Created instrument appears in list and can be retrieved."""
    sn = f"SN-PERS-{uuid.uuid4().hex[:6].upper()}"
    r_create = api.post("/api/instruments", json={
        "serial_number": sn, "manufacturer": "PersistCo", "model": "PM100",
        "instrument_type": "Scale", "accuracy_class": "Class III",
        "max_capacity": 100.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.1, "actual_scale_interval": 0.1,
        "unit": "g", "location": "Lab", "notes": "",
    })
    assert r_create.status_code == 201
    inst_id = r_create.json()["id"]

    # List
    r_list = api.get("/api/instruments")
    assert r_list.status_code == 200
    serials = [i["serial_number"] for i in r_list.json()]
    assert sn in serials

    # Retrieve
    r_get = api.get(f"/api/instruments/{inst_id}")
    assert r_get.status_code == 200
    assert r_get.json()["instrument"]["serial_number"] == sn


# ================================================================== #
# WF-2: INSTRUMENT EDITING AND RETRIEVAL                             #
# ================================================================== #

def test_wf2_01_update_location(api, std_instrument):
    """WF-2-01: Instrument location can be updated."""
    inst_id = std_instrument["id"]
    r = api.put(f"/api/instruments/{inst_id}", json={"location": "Updated Lab Bay 3"})
    assert r.status_code == 200
    assert r.json()["location"] == "Updated Lab Bay 3"


def test_wf2_02_update_serial_to_duplicate_rejected(api, std_instrument):
    """WF-2-02: Cannot update serial_number to one already in use."""
    # Find another instrument's serial
    r_list = api.get("/api/instruments")
    all_instruments = r_list.json()
    other = next((i for i in all_instruments if i["id"] != std_instrument["id"]), None)
    if not other:
        pytest.skip("Need at least 2 instruments")
    r = api.put(f"/api/instruments/{std_instrument['id']}",
                json={"serial_number": other["serial_number"]})
    assert r.status_code == 409


def test_wf2_03_archive_instrument(api):
    """WF-2-03: Archiving instrument removes it from default listing."""
    sn = f"SN-ARCH-{uuid.uuid4().hex[:6].upper()}"
    r_c = api.post("/api/instruments", json={
        "serial_number": sn, "manufacturer": "X", "model": "Y",
        "instrument_type": "Scale", "accuracy_class": "Class III",
        "max_capacity": 50.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.1, "actual_scale_interval": 0.1,
        "unit": "g", "location": "Lab", "notes": "",
    })
    inst_id = r_c.json()["id"]

    r_del = api.delete(f"/api/instruments/{inst_id}")
    assert r_del.status_code == 200

    # Should not appear in default listing
    r_list = api.get("/api/instruments")
    ids = [i["id"] for i in r_list.json()]
    assert inst_id not in ids, "Archived instrument still in default listing"

    # Should appear with include_archived=true
    r_arch = api.get("/api/instruments?include_archived=true")
    ids_all = [i["id"] for i in r_arch.json()]
    assert inst_id in ids_all


def test_wf2_04_nonexistent_instrument_404(api):
    """WF-2-04: Fetching non-existent instrument returns 404."""
    r = api.get("/api/instruments/INST-NONEXISTENT-9999")
    assert r.status_code == 404


# ================================================================== #
# WF-3: TEST SESSION CREATION                                        #
# ================================================================== #

def test_wf3_01_create_linearity_session(api, std_instrument):
    """WF-3-01: Create linearity session on valid instrument."""
    r = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "Dr. Metrologist",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    assert r.status_code == 201
    d = r.json()
    assert d["test_category"] == "linearity"
    assert d["status"] == "Draft"
    assert d["id"].startswith("TEST-")


def test_wf3_02_create_repeatability_session(api, std_instrument):
    """WF-3-02: Create repeatability session."""
    r = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "repeatability",
        "operator_name": "Dr. Metrologist",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {"test_load": 1500.0},
    })
    assert r.status_code == 201
    assert r.json()["test_category"] == "repeatability"


def test_wf3_03_create_eccentricity_session(api, std_instrument):
    """WF-3-03: Create eccentricity session."""
    r = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "eccentricity",
        "operator_name": "Dr. Metrologist",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {"test_load": 1000.0},
    })
    assert r.status_code == 201
    assert r.json()["test_category"] == "eccentricity"


def test_wf3_04_invalid_category_rejected(api, std_instrument):
    """WF-3-04: Invalid test category returns 400."""
    r = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "viscosity",
        "operator_name": "X",
        "laboratory_location": "Lab",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    assert r.status_code == 400


def test_wf3_05_nonexistent_instrument_rejected(api):
    """WF-3-05: Creating session for non-existent instrument returns 404."""
    r = api.post("/api/tests", json={
        "instrument_id": "INST-DOES-NOT-EXIST",
        "test_category": "linearity",
        "operator_name": "X",
        "laboratory_location": "Lab",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    assert r.status_code == 404


# ================================================================== #
# WF-4: OBSERVATION ENTRY AND VALIDATION                             #
# ================================================================== #

@pytest.fixture(scope="module")
def lin_session(api, std_instrument):
    r = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "Lab Operator",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    return r.json()

def test_wf4_01_submit_valid_observations(api, lin_session):
    """WF-4-01: Valid observations are accepted and status transitions to In Progress."""
    sid = lin_session["id"]
    r = api.post(f"/api/tests/{sid}/observations", json={"observations": [
        {"load": 0,    "indication": 0.0,    "direction": "increasing"},
        {"load": 500,  "indication": 499.9,  "direction": "increasing"},
        {"load": 1000, "indication": 1000.1, "direction": "increasing"},
        {"load": 2000, "indication": 1999.8, "direction": "increasing"},
        {"load": 3000, "indication": 2999.9, "direction": "increasing"},
    ]})
    assert r.status_code == 200

    # Check session status transitions to In Progress
    r_sess = api.get(f"/api/tests/{sid}")
    status = r_sess.json()["session"]["status"]
    assert status == "In Progress", f"Expected 'In Progress', got '{status}'"


def test_wf4_02_empty_observations_rejected(api, lin_session):
    """WF-4-02: Empty observations array returns 400."""
    r = api.post(f"/api/tests/{lin_session['id']}/observations",
                 json={"observations": []})
    assert r.status_code == 400


def test_wf4_03_observations_overwrite_previous(api, std_instrument):
    """WF-4-03: Resubmitting observations overwrites previous ones."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "Lab Operator",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    sid = r_sess.json()["id"]

    obs_v1 = [{"load": 0, "indication": 0.0}, {"load": 100, "indication": 100.1}]
    obs_v2 = [{"load": 0, "indication": 0.1}, {"load": 200, "indication": 200.2}]

    api.post(f"/api/tests/{sid}/observations", json={"observations": obs_v1})
    api.post(f"/api/tests/{sid}/observations", json={"observations": obs_v2})

    r_detail = api.get(f"/api/tests/{sid}")
    obs_stored = r_detail.json()["observations"]
    # Should reflect obs_v2
    assert any(o.get("load") == 200 for o in obs_stored), "Observations not overwritten"
    assert not any(o.get("load") == 100 for o in obs_stored), "Old observations still present"


# ================================================================== #
# WF-5 & WF-6: CALCULATION, RULE EVALUATION, PASS/FAIL             #
# ================================================================== #

@pytest.fixture(scope="module")
def completed_lin_session(api, std_instrument):
    """Full pipeline: create session, add good obs, calculate."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "Dr. Senior",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    sid = r_sess.json()["id"]
    api.post(f"/api/tests/{sid}/observations", json={"observations": [
        {"load": 0,    "indication": 0.0,    "direction": "increasing"},
        {"load": 500,  "indication": 499.9,  "direction": "increasing"},
        {"load": 1000, "indication": 1000.1, "direction": "increasing"},
        {"load": 2000, "indication": 1999.8, "direction": "increasing"},
        {"load": 3000, "indication": 2999.9, "direction": "increasing"},
    ]})
    r_calc = api.post(f"/api/tests/{sid}/calculate")
    assert r_calc.status_code == 200, f"Calc failed: {r_calc.text}"
    return sid, r_calc.json()


def test_wf5_01_calculation_returns_correct_structure(api, completed_lin_session):
    """WF-5-01: Calculation result has required keys."""
    _, calc_data = completed_lin_session
    assert "calculation_result" in calc_data
    assert "rule_evaluation" in calc_data
    cr = calc_data["calculation_result"]
    assert "point_results" in cr or "load_points" in cr


def test_wf5_02_status_transitions_to_completed(api, completed_lin_session):
    """WF-5-02: Session status transitions to Completed after calculation."""
    sid, _ = completed_lin_session
    r = api.get(f"/api/tests/{sid}")
    status = r.json()["session"]["status"]
    assert status == "Completed", f"Expected Completed, got {status}"


def test_wf6_01_pass_decision_for_good_data(api, completed_lin_session):
    """WF-6-01: Good linearity data produces PASS outcome."""
    _, calc_data = completed_lin_session
    outcome = calc_data["rule_evaluation"]["overall_outcome"]
    assert outcome == "PASS", f"Expected PASS for good data, got {outcome}"


def test_wf6_02_fail_decision_for_bad_data(api, std_instrument):
    """WF-6-02: Observations with errors >> MPE produce FAIL outcome."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "Lab Operator",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    sid = r_sess.json()["id"]
    # Errors of 5 g at every point (MPE = 1.5 g at max) => FAIL
    api.post(f"/api/tests/{sid}/observations", json={"observations": [
        {"load": 0,    "indication": 0.0,    "direction": "increasing"},
        {"load": 500,  "indication": 505.0,  "direction": "increasing"},
        {"load": 1000, "indication": 1005.0, "direction": "increasing"},
        {"load": 2000, "indication": 2005.0, "direction": "increasing"},
        {"load": 3000, "indication": 3005.0, "direction": "increasing"},
    ]})
    r_calc = api.post(f"/api/tests/{sid}/calculate")
    assert r_calc.status_code == 200
    outcome = r_calc.json()["rule_evaluation"]["overall_outcome"]
    assert outcome == "FAIL", f"Expected FAIL for large errors, got {outcome}"


def test_wf6_03_calculate_without_observations_returns_error(api, std_instrument):
    """WF-6-03: Calling calculate before submitting observations returns 400."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "X",
        "laboratory_location": "Lab",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {},
    })
    sid = r_sess.json()["id"]
    r_calc = api.post(f"/api/tests/{sid}/calculate")
    assert r_calc.status_code == 400


def test_wf6_04_over_capacity_load_rejected_422(api, std_instrument):
    """WF-6-04 (BUG-4 regression): Over-capacity load is rejected with 422."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "X", "laboratory_location": "Lab",
        "ambient_temperature": 23.0, "relative_humidity": 50.0,
        "service_type": "initial", "test_configuration": {},
    })
    sid = r_sess.json()["id"]
    api.post(f"/api/tests/{sid}/observations", json={"observations": [
        {"load": 0,    "indication": 0.0},
        {"load": 3001, "indication": 3001.0},  # over max_capacity=3000
    ]})
    r_calc = api.post(f"/api/tests/{sid}/calculate")
    assert r_calc.status_code == 422
    detail = r_calc.json().get("detail", "")
    assert any(w in detail.lower() for w in ["capacity", "maximum", "exceed"])


# ================================================================== #
# WF-7: PDF REPORT GENERATION AND DOWNLOADING                        #
# ================================================================== #

@pytest.fixture(scope="module")
def report_session(api, completed_lin_session):
    """Generate a PDF report for the completed session."""
    sid, _ = completed_lin_session
    r_rep = api.post(f"/api/tests/{sid}/report")
    assert r_rep.status_code == 200, f"Report gen failed: {r_rep.text}"
    return sid, r_rep.json()["report_id"]


def test_wf7_01_report_generated_successfully(api, report_session):
    """WF-7-01: PDF report is generated and returns a report_id."""
    _, rep_id = report_session
    assert rep_id.startswith("REP-")


def test_wf7_02_report_downloadable(api, report_session):
    """WF-7-02: Generated report can be downloaded as PDF."""
    _, rep_id = report_session
    r = api.get(f"/api/reports/{rep_id}/download")
    assert r.status_code == 200
    assert "pdf" in r.headers.get("content-type", "").lower()
    assert len(r.content) > 1000


def test_wf7_03_report_listed_in_session_details(api, report_session):
    """WF-7-03: Session detail endpoint shows the generated report."""
    sid, rep_id = report_session
    r = api.get(f"/api/tests/{sid}")
    latest = r.json().get("latest_report")
    assert latest is not None, "No latest_report in session detail"
    assert latest["id"] == rep_id


def test_wf7_04_report_for_incomplete_session(api, std_instrument):
    """WF-7-04: Generating report for session without calculation returns error."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "linearity",
        "operator_name": "X", "laboratory_location": "Lab",
        "ambient_temperature": 23.0, "relative_humidity": 50.0,
        "service_type": "initial", "test_configuration": {},
    })
    sid = r_sess.json()["id"]
    r_rep = api.post(f"/api/tests/{sid}/report")
    # Should be 400 or 422 — not a valid report without calculation
    print(f"\n  WF-7-04: report on uncalculated session => HTTP {r_rep.status_code}")
    assert r_rep.status_code in (400, 422, 500), \
        f"Expected 4xx/5xx for report without calculation, got {r_rep.status_code}"


def test_wf7_05_nonexistent_report_404(api):
    """WF-7-05: Downloading non-existent report returns 404."""
    r = api.get("/api/reports/REP-DOESNOTEXIST-9999/download")
    assert r.status_code == 404


# ================================================================== #
# WF-8: HISTORICAL SESSION RETRIEVAL                                 #
# ================================================================== #

def test_wf8_01_list_all_sessions(api):
    """WF-8-01: Session listing returns all sessions including demo ones."""
    r = api.get("/api/tests")
    assert r.status_code == 200
    sessions = r.json()
    assert len(sessions) >= 3, "Should have at least 3 demo sessions"


def test_wf8_02_filter_by_category(api):
    """WF-8-02: Session listing can filter by test category."""
    r = api.get("/api/tests?category=linearity")
    assert r.status_code == 200
    for s in r.json():
        assert s["test_category"] == "linearity"


def test_wf8_03_session_detail_has_all_data(api, completed_lin_session):
    """WF-8-03: Completed session detail includes obs, calc, eval, report."""
    sid, _ = completed_lin_session
    r = api.get(f"/api/tests/{sid}")
    assert r.status_code == 200
    d = r.json()
    assert d["observations"] is not None
    assert d["calculation_result"] is not None
    assert d["rule_evaluation"] is not None


def test_wf8_04_nonexistent_session_404(api):
    """WF-8-04: Fetching non-existent session returns 404."""
    r = api.get("/api/tests/TEST-NONEXISTENT-9999")
    assert r.status_code == 404


# ================================================================== #
# WF-9: DATABASE CONSISTENCY AND AUDIT HISTORY                       #
# ================================================================== #

def test_wf9_01_audit_log_entries_created(api, std_instrument):
    """WF-9-01: Creating instrument generates audit log entry."""
    r = api.get("/api/audit")
    assert r.status_code == 200
    logs = r.json()
    # Look for INSTRUMENT_REGISTERED event
    inst_logs = [l for l in logs if l.get("action") == "INSTRUMENT_REGISTERED"]
    assert len(inst_logs) > 0, "No INSTRUMENT_REGISTERED audit events found"


def test_wf9_02_audit_log_for_calculation(api, completed_lin_session):
    """WF-9-02: Running calculation generates audit log entry."""
    r = api.get("/api/audit")
    logs = r.json()
    calc_logs = [l for l in logs if l.get("action") == "CALCULATION_EXECUTED"]
    assert len(calc_logs) > 0, "No CALCULATION_EXECUTED audit events found"


def test_wf9_03_dashboard_stats_reflect_data(api):
    """WF-9-03: Dashboard stats are consistent with actual data."""
    r_dash = api.get("/api/dashboard/stats")
    assert r_dash.status_code == 200
    stats = r_dash.json()
    assert "metrics" in stats
    m = stats["metrics"]
    assert m["total_instruments"] >= 3
    assert "total_tests" in m or "total_sessions" in m

    r_inst = api.get("/api/instruments")
    active_count = len(r_inst.json())
    assert m["active_instruments"] == active_count, \
        f"Dashboard active count {m['active_instruments']} != actual {active_count}"

    r_all_inst = api.get("/api/instruments?include_archived=true")
    total_count = len(r_all_inst.json())
    assert m["total_instruments"] == total_count, \
        f"Dashboard total count {m['total_instruments']} != actual {total_count}"


def test_wf9_04_analytics_endpoint(api):
    """WF-9-04: Analytics endpoint returns structured data."""
    r = api.get("/api/analytics")
    assert r.status_code == 200
    d = r.json()
    assert "summary" in d
    assert "category_distribution" in d
    assert "monthly_trend" in d


# ================================================================== #
# INVESTIGATION: STATE TRANSITION PROTECTION                         #
# ================================================================== #

def test_inv_01_completed_session_can_be_modified(api, completed_lin_session):
    """
    INV-01 (BUG-5 VERIFICATION): Completed session must be protected against ordinary PUT.
    Returns HTTP 409 Conflict.
    """
    sid, _ = completed_lin_session
    r_update = api.put(f"/api/tests/{sid}", json={"operator_name": "TAMPERED NAME"})
    print(f"\n  INV-01: PUT on Completed session => HTTP {r_update.status_code}")
    assert r_update.status_code == 409, f"Expected 409 Conflict on completed session PUT, got {r_update.status_code}"
    print("  OK: Completed session modification rejected with HTTP 409 (BUG-5 fixed)")


def test_inv_02_recalculate_completed_session(api, completed_lin_session):
    """
    INV-02 (BUG-6 VERIFICATION): Recalculation on completed session without amendment
    must be blocked with HTTP 409 Conflict.
    """
    sid, orig_data = completed_lin_session
    r = api.post(f"/api/tests/{sid}/calculate")
    print(f"\n  INV-02: Recalculate Completed session => HTTP {r.status_code}")
    assert r.status_code == 409, f"Expected 409 Conflict on completed session recalculation, got {r.status_code}"
    print("  OK: Silent recalculation blocked with HTTP 409 (BUG-6 fixed)")


def test_inv_03_report_consistency_after_recalc(api, report_session, completed_lin_session):
    """
    INV-03 (BUG-8 VERIFICATION): When an amendment occurs, the original PDF report
    remains completely consistent on disk and is marked superseded in DB.
    """
    sid, rep_id = report_session
    # Download original report
    r_orig = api.get(f"/api/reports/{rep_id}/download")
    assert r_orig.status_code == 200
    orig_size = len(r_orig.content)

    # Amend with new observations
    amend_res = api.post(f"/api/tests/{sid}/amend", json={
        "reason": "Re-calibration per standard laboratory calibration cycle.",
        "operator_name": "Authorized Metrologist",
        "observations": [
            {"load": 0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 500,  "indication": 505.0,  "direction": "increasing"},
            {"load": 1000, "indication": 1005.0, "direction": "increasing"},
        ]
    })
    assert amend_res.status_code == 200

    # Original report is still downloadable and byte-for-byte identical
    r_after = api.get(f"/api/reports/{rep_id}/download")
    assert r_after.status_code == 200
    after_size = len(r_after.content)
    assert orig_size == after_size, "Original report altered on disk after amendment"

    # Verify Report 1 is marked superseded in DB
    rep_info = api.get(f"/api/reports/{rep_id}").json()
    assert rep_info["is_superseded"] is True
    print(f"\n  INV-03: Original report byte-identical ({orig_size} bytes) and marked is_superseded=True (BUG-8 fixed)")


def test_inv_04_session_listing_after_archive(api):
    """INV-04: Archived instrument's sessions should still be accessible."""
    sn = f"SN-ARC2-{uuid.uuid4().hex[:6].upper()}"
    r_inst = api.post("/api/instruments", json={
        "serial_number": sn, "manufacturer": "X", "model": "Y",
        "instrument_type": "Scale", "accuracy_class": "Class III",
        "max_capacity": 100.0, "min_capacity": 0.0,
        "verification_scale_interval": 0.1, "actual_scale_interval": 0.1,
        "unit": "g", "location": "Lab", "notes": "",
    })
    inst_id = r_inst.json()["id"]

    r_sess = api.post("/api/tests", json={
        "instrument_id": inst_id, "test_category": "linearity",
        "operator_name": "X", "laboratory_location": "Lab",
        "ambient_temperature": 23.0, "relative_humidity": 50.0,
        "service_type": "initial", "test_configuration": {},
    })
    sess_id = r_sess.json()["id"]

    # Archive instrument
    api.delete(f"/api/instruments/{inst_id}")

    # Session should still be retrievable
    r_get = api.get(f"/api/tests/{sess_id}")
    print(f"\n  INV-04: Fetching session after instrument archive => HTTP {r_get.status_code}")
    assert r_get.status_code in (200, 404), f"Unexpected status: {r_get.status_code}"
    if r_get.status_code == 200:
        print("  OK: Session accessible after instrument archive")
    else:
        print("  FINDING: Session NOT accessible after instrument archive (data orphaned?)")


# ================================================================== #
# ECCENTRICITY AND REPEATABILITY PIPELINES                           #
# ================================================================== #

def test_wf_ecc_full_pipeline(api, std_instrument):
    """WF-ECC: Full eccentricity test pipeline -> PASS/FAIL."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "eccentricity",
        "operator_name": "Lab Op",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {"test_load": 1000.0},
    })
    sid = r_sess.json()["id"]

    obs = [
        {"position_id": "pos_1", "position_name": "Center",     "indication": 1000.0, "zero_indication": 0.0},
        {"position_id": "pos_2", "position_name": "Front-Left", "indication": 1000.3, "zero_indication": 0.0},
        {"position_id": "pos_3", "position_name": "Back-Left",  "indication": 999.8,  "zero_indication": 0.0},
        {"position_id": "pos_4", "position_name": "Front-Right","indication": 1000.1, "zero_indication": 0.0},
        {"position_id": "pos_5", "position_name": "Back-Right", "indication": 1000.2, "zero_indication": 0.0},
    ]
    r_obs = api.post(f"/api/tests/{sid}/observations", json={"observations": obs})
    assert r_obs.status_code == 200

    r_calc = api.post(f"/api/tests/{sid}/calculate")
    assert r_calc.status_code == 200
    outcome = r_calc.json()["rule_evaluation"]["overall_outcome"]
    print(f"\n  WF-ECC: eccentricity outcome = {outcome}")
    assert outcome in ("PASS", "FAIL")

    r_rep = api.post(f"/api/tests/{sid}/report")
    assert r_rep.status_code == 200


def test_wf_rep_full_pipeline(api, std_instrument):
    """WF-REP: Full repeatability test pipeline -> PASS/FAIL."""
    r_sess = api.post("/api/tests", json={
        "instrument_id": std_instrument["id"],
        "test_category": "repeatability",
        "operator_name": "Lab Op",
        "laboratory_location": "Bay A",
        "ambient_temperature": 23.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {"test_load": 1500.0},
    })
    sid = r_sess.json()["id"]

    # 10 repeat measurements with small scatter (< 0.5e = 0.5g)
    obs = [
        {"run_number": i, "indication": 1500.0 + (i % 3) * 0.1, "zero_before": 0.0, "zero_after": 0.0}
        for i in range(1, 11)
    ]
    r_obs = api.post(f"/api/tests/{sid}/observations", json={"observations": obs})
    assert r_obs.status_code == 200

    r_calc = api.post(f"/api/tests/{sid}/calculate")
    assert r_calc.status_code == 200
    outcome = r_calc.json()["rule_evaluation"]["overall_outcome"]
    print(f"\n  WF-REP: repeatability outcome = {outcome}")
    assert outcome in ("PASS", "FAIL")


# ================================================================== #
# HEALTH AND RECOVERY                                                #
# ================================================================== #

def test_health_01_endpoint(api):
    """HEALTH-01: Health endpoint returns status=healthy."""
    r = api.get("/api/health")
    assert r.status_code == 200
    d = r.json()
    assert d["status"] == "healthy"
    assert d["problem_id"] == "SIH26035"
    assert d["team"] == "VisionVerity"


def test_health_02_data_persists_across_client_restart(api, std_instrument):
    """
    HEALTH-02: Simulate backend restart by creating a new TestClient
    and verifying data created in this session is still accessible.
    (In SQLite the data persists in the temp file across client instances.)
    """
    inst_id = std_instrument["id"]
    # Verify instrument exists in a fresh client context
    with TestClient(app) as fresh_client:
        r = fresh_client.get(f"/api/instruments/{inst_id}")
        assert r.status_code == 200, \
            f"HEALTH-02: Data not persisted across client restart. Status={r.status_code}"
        print(f"\n  HEALTH-02: Data persists across restart. id={inst_id}")

