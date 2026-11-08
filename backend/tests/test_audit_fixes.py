"""
Automated regression tests for Phase 2 audit implementations:
- BUG-5: Completed Session Mutability Protection (HTTP 409)
- BUG-6: Unrestricted Recalculation Prevention & Controlled Amendment Workflow
- BUG-7: API Schema Boundary Validation (Field gt=0, HTTP 422)
- BUG-8: PDF and Database Version Synchronization (Report revision tracking & superseding)

Runs against an isolated temporary SQLite database file.
"""
import os
import sys
import uuid
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

ROOT_PATH = str(Path(__file__).resolve().parent.parent.parent)
BACKEND_PATH = str(Path(__file__).resolve().parent.parent)
for p in (ROOT_PATH, BACKEND_PATH):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.main import app
from app.database import Base, get_db, ensure_schema_compatibility
from app.services.demo_data_service import seed_demo_data

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), f"nawi_test_audit_fixes_{uuid.uuid4().hex[:8]}.db")
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
    ensure_schema_compatibility(test_engine)
    test_db = TestingSessionLocal()
    try:
        seed_demo_data(test_db)
    finally:
        test_db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    try:
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
    except Exception:
        pass


@pytest.fixture
def test_instrument(client):
    sn = f"SN-AUD-{uuid.uuid4().hex[:6].upper()}"
    res = client.post("/api/instruments", json={
        "serial_number": sn,
        "manufacturer": "Mettler Toledo",
        "model": "Precision Lab 3000",
        "instrument_type": "Precision Balance",
        "accuracy_class": "Class II",
        "max_capacity": 3000.0,
        "min_capacity": 0.5,
        "verification_scale_interval": 0.1,
        "actual_scale_interval": 0.1,
        "unit": "g",
        "location": "Audit Testing Bay",
        "notes": "Dedicated instrument for audit fixes regression."
    })
    assert res.status_code == 201
    return res.json()


@pytest.fixture
def completed_linearity_session(client, test_instrument):
    inst_id = test_instrument["id"]
    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Senior Metrologist",
        "laboratory_location": "Audit Bay A",
        "ambient_temperature": 21.0,
        "relative_humidity": 45.0,
        "service_type": "initial",
        "test_configuration": {}
    })
    assert sess_res.status_code == 201
    sess_id = sess_res.json()["id"]

    obs_payload = {
        "observations": [
            {"load": 0.0, "indication": 0.0, "direction": "increasing"},
            {"load": 500.0, "indication": 500.02, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.03, "direction": "increasing"},
            {"load": 2000.0, "indication": 1999.98, "direction": "increasing"},
            {"load": 3000.0, "indication": 3000.01, "direction": "increasing"},
        ]
    }
    obs_res = client.post(f"/api/tests/{sess_id}/observations", json=obs_payload)
    assert obs_res.status_code == 200

    calc_res = client.post(f"/api/tests/{sess_id}/calculate")
    assert calc_res.status_code == 200
    calc_data = calc_res.json()
    assert calc_data["rule_evaluation"]["overall_outcome"] == "PASS"

    detail_res = client.get(f"/api/tests/{sess_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["session"]["status"] == "Completed"

    return sess_id, detail_res.json()


# =====================================================================
# BUG-7: API SCHEMA VALIDATION TESTS
# =====================================================================

def test_bug7_reject_negative_max_capacity(client):
    """Negative maximum capacity must be rejected with HTTP 422."""
    res = client.post("/api/instruments", json={
        "serial_number": f"SN-NEG-CAP-{uuid.uuid4().hex[:4]}",
        "manufacturer": "Test Lab",
        "model": "Invalid Scale",
        "max_capacity": -500.0,
        "verification_scale_interval": 1.0,
        "unit": "g"
    })
    assert res.status_code == 422
    errs = str(res.json())
    assert "max_capacity" in errs


def test_bug7_reject_zero_max_capacity(client):
    """Zero maximum capacity must be rejected with HTTP 422."""
    res = client.post("/api/instruments", json={
        "serial_number": f"SN-ZERO-CAP-{uuid.uuid4().hex[:4]}",
        "manufacturer": "Test Lab",
        "model": "Invalid Scale",
        "max_capacity": 0.0,
        "verification_scale_interval": 1.0,
        "unit": "g"
    })
    assert res.status_code == 422
    assert "max_capacity" in str(res.json())


def test_bug7_reject_zero_or_negative_verification_interval(client):
    """Zero or negative verification scale interval e must be rejected with HTTP 422."""
    res_zero = client.post("/api/instruments", json={
        "serial_number": f"SN-ZERO-E-{uuid.uuid4().hex[:4]}",
        "manufacturer": "Test Lab",
        "model": "Invalid Scale",
        "max_capacity": 1000.0,
        "verification_scale_interval": 0.0,
        "unit": "g"
    })
    assert res_zero.status_code == 422
    assert "verification_scale_interval" in str(res_zero.json())

    res_neg = client.post("/api/instruments", json={
        "serial_number": f"SN-NEG-E-{uuid.uuid4().hex[:4]}",
        "manufacturer": "Test Lab",
        "model": "Invalid Scale",
        "max_capacity": 1000.0,
        "verification_scale_interval": -0.5,
        "unit": "g"
    })
    assert res_neg.status_code == 422
    assert "verification_scale_interval" in str(res_neg.json())


def test_bug7_reject_min_capacity_exceeding_max_capacity(client):
    """Minimum capacity >= maximum capacity must be rejected with HTTP 422."""
    res = client.post("/api/instruments", json={
        "serial_number": f"SN-INV-CAP-{uuid.uuid4().hex[:4]}",
        "manufacturer": "Test Lab",
        "model": "Invalid Scale",
        "max_capacity": 100.0,
        "min_capacity": 150.0,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    assert res.status_code == 422
    assert "strictly less than maximum capacity" in str(res.json())


def test_bug7_reject_invalid_update_values(client, test_instrument):
    """Updating an instrument with non-positive values must return HTTP 422."""
    inst_id = test_instrument["id"]
    res_neg_cap = client.put(f"/api/instruments/{inst_id}", json={"max_capacity": -100.0})
    assert res_neg_cap.status_code == 422

    res_neg_e = client.put(f"/api/instruments/{inst_id}", json={"verification_scale_interval": 0.0})
    assert res_neg_e.status_code == 422


# =====================================================================
# BUG-5: COMPLETED SESSION MUTABILITY TESTS
# =====================================================================

def test_bug5_put_on_completed_session_returns_409(client, completed_linearity_session):
    """Ordinary PUT on a completed test session must return HTTP 409 Conflict."""
    sess_id, _ = completed_linearity_session
    res = client.put(f"/api/tests/{sess_id}", json={
        "operator_name": "Unauthorized Tamperer",
        "ambient_temperature": 35.0
    })
    assert res.status_code == 409
    detail = res.json().get("detail", "")
    assert "locked against modification" in detail
    assert "amend" in detail.lower()

    # Verify session remains untampered
    verify_res = client.get(f"/api/tests/{sess_id}")
    assert verify_res.json()["session"]["operator_name"] == "Senior Metrologist"


def test_bug5_save_observations_on_completed_session_returns_409(client, completed_linearity_session):
    """Attempting to overwrite observations on a completed session must return HTTP 409."""
    sess_id, _ = completed_linearity_session
    res = client.post(f"/api/tests/{sess_id}/observations", json={
        "observations": [
            {"load": 0.0, "indication": 5.0, "direction": "increasing"},
            {"load": 1000.0, "indication": 1050.0, "direction": "increasing"}
        ]
    })
    assert res.status_code == 409
    detail = res.json().get("detail", "")
    assert "Cannot modify observations for a completed test session" in detail


def test_bug5_uncompleted_sessions_can_be_updated_normally(client, test_instrument):
    """Draft and In-Progress sessions can still be updated normally via PUT."""
    sess_res = client.post("/api/tests", json={
        "instrument_id": test_instrument["id"],
        "test_category": "linearity",
        "operator_name": "Junior Metrologist",
        "ambient_temperature": 20.0
    })
    assert sess_res.status_code == 201
    draft_id = sess_res.json()["id"]

    # Ordinary PUT succeeds on Draft
    put_res = client.put(f"/api/tests/{draft_id}", json={"ambient_temperature": 22.5})
    assert put_res.status_code == 200
    assert put_res.json()["ambient_temperature"] == 22.5


# =====================================================================
# BUG-6: RECALCULATION PREVENTION & AMENDMENT WORKFLOW TESTS
# =====================================================================

def test_bug6_recalculation_on_completed_session_returns_409(client, completed_linearity_session):
    """Calling POST /calculate on a completed session must return HTTP 409."""
    sess_id, _ = completed_linearity_session
    res = client.post(f"/api/tests/{sess_id}/calculate")
    assert res.status_code == 409
    detail = res.json().get("detail", "")
    assert "Cannot recalculate a completed test session" in detail
    assert "amend" in detail.lower()


def test_bug6_amend_requires_reason_and_operator(client, completed_linearity_session):
    """Amendment requests missing required reason or operator must return HTTP 422."""
    sess_id, _ = completed_linearity_session
    # Missing reason
    res_no_reason = client.post(f"/api/tests/{sess_id}/amend", json={
        "operator_name": "Quality Manager"
    })
    assert res_no_reason.status_code == 422

    # Reason too short (< 5 chars)
    res_short = client.post(f"/api/tests/{sess_id}/amend", json={
        "operator_name": "Quality Manager",
        "reason": "fix"
    })
    assert res_short.status_code == 422


def test_bug6_authorized_amendment_preserves_revision_history(client, completed_linearity_session):
    """
    Authorized amendment must:
    1. Archive Rev 1 snapshot in test_revisions (observations, calculations, rule outcome).
    2. Increment session version from 1 to 2.
    3. Allow updating observations and recalculating under Rev 2.
    4. Provide full revision history via GET /revisions.
    """
    sess_id, orig_detail = completed_linearity_session
    orig_calc = orig_detail["calculation_result"]
    orig_outcome = orig_detail["rule_evaluation"]["overall_outcome"]
    assert orig_outcome == "PASS"

    # Execute authorized amendment with new observations
    amend_payload = {
        "reason": "Re-zeroing balance after thermal equilibrium was re-established per SOP-402.",
        "operator_name": "Dr. Sarah Jenkins (Lead Metrologist)",
        "observations": [
            {"load": 0.0, "indication": 0.0, "direction": "increasing"},
            {"load": 500.0, "indication": 500.01, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.01, "direction": "increasing"},
            {"load": 2000.0, "indication": 2000.02, "direction": "increasing"},
            {"load": 3000.0, "indication": 3000.02, "direction": "increasing"},
        ]
    }
    amend_res = client.post(f"/api/tests/{sess_id}/amend", json=amend_payload)
    assert amend_res.status_code == 200
    amend_data = amend_res.json()
    assert amend_data["previous_version"] == 1
    assert amend_data["new_version"] == 2
    assert amend_data["status"] == "success"

    # Verify session detail reflects Rev 2
    sess_detail = client.get(f"/api/tests/{sess_id}").json()
    assert sess_detail["session"]["version"] == 2
    assert sess_detail["session"]["operator_name"] == "Dr. Sarah Jenkins (Lead Metrologist)"
    assert sess_detail["revisions_count"] == 1

    # Verify revision history endpoint preserves Rev 1 snapshot
    revs_res = client.get(f"/api/tests/{sess_id}/revisions")
    assert revs_res.status_code == 200
    revs = revs_res.json()
    assert len(revs) == 1
    r1 = revs[0]
    assert r1["revision_number"] == 1
    assert r1["amendment_reason"] == amend_payload["reason"]
    assert r1["amended_by"] == amend_payload["operator_name"]
    assert r1["overall_outcome"] == "PASS"
    assert r1["has_calculations"] is True
    assert r1["has_observations"] is True
    assert len(r1["observations"]) == 5


# =====================================================================
# BUG-8: PDF AND DATABASE VERSION SYNCHRONIZATION TESTS
# =====================================================================

def test_bug8_pdf_versioning_and_superseding_workflow(client, test_instrument):
    """
    BUG-8 Full Workflow Test:
    1. Create and complete test session at Version 1.
    2. Generate PDF Report 1 -> Version 1, is_superseded = False.
    3. Verify PDF text contains 'Rev 1 (ORIGINAL)'.
    4. Perform authorized amendment to Version 2.
    5. Generate PDF Report 2 -> Version 2, is_superseded = False.
    6. Verify Report 1 in DB is now is_superseded = True, superseded_by = Report 2 ID.
    7. Verify Report 2 PDF text contains 'Rev 2 (AMENDED)' and the amendment justification.
    8. Verify both Report 1 and Report 2 physical PDF files exist and can be downloaded independently.
    """
    import pdfplumber

    inst_id = test_instrument["id"]
    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Metrologist Alice",
        "laboratory_location": "Bay 1",
        "ambient_temperature": 20.5,
        "relative_humidity": 48.0,
        "service_type": "initial",
        "test_configuration": {}
    })
    sess_id = sess_res.json()["id"]

    # Observations for Rev 1
    client.post(f"/api/tests/{sess_id}/observations", json={"observations": [
        {"load": 0.0, "indication": 0.0, "direction": "increasing"},
        {"load": 500.0, "indication": 500.05, "direction": "increasing"},
        {"load": 1000.0, "indication": 1000.06, "direction": "increasing"},
        {"load": 2000.0, "indication": 2000.08, "direction": "increasing"},
        {"load": 3000.0, "indication": 3000.09, "direction": "increasing"},
    ]})
    client.post(f"/api/tests/{sess_id}/calculate")

    # Generate Report 1 (for Rev 1)
    rep1_res = client.post(f"/api/tests/{sess_id}/report")
    assert rep1_res.status_code == 200
    rep1_id = rep1_res.json()["report_id"]

    # Verify Report 1 in DB
    rep1_info = client.get(f"/api/reports/{rep1_id}").json()
    assert rep1_info["version"] == 1
    assert rep1_info["is_superseded"] is False
    assert rep1_info["superseded_by"] is None

    # Download & inspect Report 1 PDF content
    dl1 = client.get(f"/api/reports/{rep1_id}/download")
    assert dl1.status_code == 200
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f1:
        f1.write(dl1.content)
        f1_path = f1.name
    try:
        with pdfplumber.open(f1_path) as pdf1:
            t1 = "".join(p.extract_text() or "" for p in pdf1.pages)
            assert "REPORT ID:" in t1
            assert rep1_id in t1
            assert "Rev 1 (ORIGINAL)" in t1
    finally:
        if os.path.exists(f1_path):
            os.remove(f1_path)

    # Authorized Amendment to Rev 2
    amend_reason = "Customer requested re-verification at certified reference ambient pressure."
    amend_res = client.post(f"/api/tests/{sess_id}/amend", json={
        "reason": amend_reason,
        "operator_name": "Supervisor Bob",
        "observations": [
            {"load": 0.0, "indication": 0.0, "direction": "increasing"},
            {"load": 500.0, "indication": 500.01, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.01, "direction": "increasing"},
            {"load": 2000.0, "indication": 2000.01, "direction": "increasing"},
            {"load": 3000.0, "indication": 3000.02, "direction": "increasing"},
        ]
    })
    assert amend_res.status_code == 200

    # Generate Report 2 (for Rev 2)
    rep2_res = client.post(f"/api/tests/{sess_id}/report")
    assert rep2_res.status_code == 200
    rep2_id = rep2_res.json()["report_id"]
    assert rep2_id != rep1_id

    # Verify Report 2 in DB
    rep2_info = client.get(f"/api/reports/{rep2_id}").json()
    assert rep2_info["version"] == 2
    assert rep2_info["is_superseded"] is False
    assert rep2_info["superseded_by"] is None

    # Verify Report 1 is now superseded in DB
    rep1_after = client.get(f"/api/reports/{rep1_id}").json()
    assert rep1_after["is_superseded"] is True
    assert rep1_after["superseded_by"] == rep2_id

    # Download & inspect Report 2 PDF content
    dl2 = client.get(f"/api/reports/{rep2_id}/download")
    assert dl2.status_code == 200
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f2:
        f2.write(dl2.content)
        f2_path = f2.name
    try:
        with pdfplumber.open(f2_path) as pdf2:
            t2 = "".join(p.extract_text() or "" for p in pdf2.pages)
            assert rep2_id in t2
            assert "Rev 2 (AMENDED)" in t2
            assert "OFFICIAL AMENDMENT / REVISION RECORD" in t2
            assert amend_reason in t2
            assert "Supervisor Bob" in t2
    finally:
        if os.path.exists(f2_path):
            os.remove(f2_path)

    # Verify session details endpoint lists both reports and identifies superseded status
    detail_res = client.get(f"/api/tests/{sess_id}").json()
    assert detail_res["latest_report"]["id"] == rep2_id
    assert detail_res["latest_report"]["version"] == 2
    assert detail_res["latest_report"]["is_superseded"] is False

    reps = detail_res["reports"]
    assert len(reps) == 2
    rep_map = {r["id"]: r for r in reps}
    assert rep_map[rep1_id]["is_superseded"] is True
    assert rep_map[rep1_id]["superseded_by"] == rep2_id
    assert rep_map[rep2_id]["is_superseded"] is False

    # Historical Report 1 is STILL fully downloadable as an immutable legal artifact
    dl1_again = client.get(f"/api/reports/{rep1_id}/download")
    assert dl1_again.status_code == 200
    assert len(dl1_again.content) > 1000


# =====================================================================
# ROLE-BASED ACCESS CONTROL (RBAC) TESTS
# =====================================================================

def test_rbac_operator_cannot_amend_completed_session(client, completed_linearity_session):
    """
    RBAC GUARD:
    An ordinary laboratory operator ('m.vance', role 'Metrologist/Operator')
    is NOT authorized to amend a completed test session. Must return HTTP 403 Forbidden.
    """
    sess_id, _ = completed_linearity_session
    headers = {"X-User-Id": "m.vance"}

    res = client.post(
        f"/api/tests/{sess_id}/amend",
        headers=headers,
        json={
            "reason": "Unapproved unilateral amendment attempted by field technician.",
            "operator_name": "Marcus Vance",
        }
    )
    assert res.status_code == 403
    assert "Permission Denied" in res.json()["detail"]
    assert "Metrologist/Operator" in res.json()["detail"]


def test_rbac_operator_cannot_archive_instrument(client, test_instrument):
    """
    RBAC GUARD:
    An ordinary operator cannot delete or archive instruments from the laboratory register.
    Must return HTTP 403 Forbidden.
    """
    inst_id = test_instrument["id"]
    headers = {"X-User-Id": "m.vance"}

    res = client.delete(f"/api/instruments/{inst_id}", headers=headers)
    assert res.status_code == 403
    assert "Permission Denied" in res.json()["detail"]


def test_rbac_reviewer_can_amend_completed_session(client, completed_linearity_session):
    """
    RBAC PERMISSION:
    A verified Reviewer ('e.rostova', role 'Reviewer') is authorized
    to amend completed sessions. Must return HTTP 200 OK.
    """
    sess_id, _ = completed_linearity_session
    headers = {"X-User-Id": "e.rostova"}

    res = client.post(
        f"/api/tests/{sess_id}/amend",
        headers=headers,
        json={
            "reason": "Approved technical re-calibration following laboratory review audit.",
            "operator_name": "Elena Rostova",
        }
    )
    assert res.status_code == 200
    assert res.json()["status"] == "success"


def test_rbac_invalid_auth_token_rejected(client, completed_linearity_session):
    """
    AUTHENTICATION GUARD:
    An invalid user identifier in auth header must be rejected with HTTP 401 Unauthorized.
    """
    sess_id, _ = completed_linearity_session
    headers = {"X-User-Id": "USR-FAKE-GHOST"}

    res = client.post(
        f"/api/tests/{sess_id}/amend",
        headers=headers,
        json={
            "reason": "Tampering attempt with fake credentials.",
            "operator_name": "Ghost",
        }
    )
    assert res.status_code == 401
    assert "Authentication failed" in res.json()["detail"]


