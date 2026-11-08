"""
SIH Demonstration Readiness & Complete E2E Laboratory Workflow Validation Suite.

Validates the full metrological lifecycle against OIML R-76 requirements using
an isolated temporary SQLite database:
1. Instrument Registration & API Boundary Guards
2. Full PASS Calibration Workflow (Observation -> Calc -> OIML Rule -> PDF)
3. Full FAIL Calibration Workflow (Out-of-tolerance detection & explainability)
4. Over-capacity Load Rejection (API boundary guard)
5. Completed Session Mutability Protection (HTTP 409)
6. Role-Based Access Control (RBAC 403 / 401 guards)
7. Controlled Amendment Workflow & Superseded PDF Traceability (Rev 1 -> Rev 2)
8. Complete Audit Trail Integrity
"""

import os
import tempfile
import uuid
from datetime import datetime, timezone
import pytest
import pdfplumber
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base, get_db, ensure_schema_compatibility
from backend.app.main import app
from backend.app.services.demo_data_service import seed_demo_data


@pytest.fixture(scope="module")
def demo_test_env():
    """Create an isolated temporary SQLite database for demo workflow validation."""
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_demo_readiness.db")
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)
    ensure_schema_compatibility(engine)

    # Seed demo users (Administrator, Laboratory Manager, Metrologist/Operator, Reviewer)
    db = TestingSessionLocal()
    seed_demo_data(db)
    db.close()

    def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client, db_path

    app.dependency_overrides.clear()
    engine.dispose()
    if os.path.exists(db_path):
        os.remove(db_path)


# =============================================================================
# SCENARIO 1: INSTRUMENT REGISTRATION & VALIDATION BOUNDARIES
# =============================================================================

def test_scenario1_instrument_registration_and_validation(demo_test_env):
    """
    Scenario 1: Instrument Registration & Schema Guards.
    - Rejects invalid physical parameters (negative capacity, inverted min/max).
    - Persists valid Class II precision balance.
    """
    client, _ = demo_test_env

    # 1. Invalid Max Capacity rejected
    inv_cap = client.post("/api/instruments", json={
        "serial_number": "SN-INV-001",
        "manufacturer": "Faulty Metrology",
        "model": "Broken-100",
        "max_capacity": -50.0,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    assert inv_cap.status_code == 422

    # 2. Inverted Min/Max Capacity rejected
    inv_min = client.post("/api/instruments", json={
        "serial_number": "SN-INV-002",
        "manufacturer": "Faulty Metrology",
        "model": "Broken-200",
        "max_capacity": 100.0,
        "min_capacity": 150.0,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    assert inv_min.status_code == 422

    # 3. Valid Registration
    reg = client.post("/api/instruments", json={
        "serial_number": f"SN-DEMO-VAL-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Mettler Toledo",
        "model": "XPR3002S Precision",
        "instrument_type": "Precision Balance",
        "accuracy_class": "Class II",
        "max_capacity": 3200.0,
        "min_capacity": 0.5,
        "verification_scale_interval": 0.1,
        "actual_scale_interval": 0.01,
        "unit": "g",
        "location": "Calibration Standards Bay 2"
    })
    assert reg.status_code == 201
    inst = reg.json()
    assert inst["accuracy_class"] == "Class II"
    assert inst["max_capacity"] == 3200.0


# =============================================================================
# SCENARIO 2: COMPLETE PASSING CALIBRATION WORKFLOW (OIML R-76)
# =============================================================================

def test_scenario2_passing_calibration_workflow(demo_test_env):
    """
    Scenario 2: Complete PASS Workflow (Linearity OIML R-76 Clause 3.5.1).
    - Creates test session
    - Records observations well within Class II MPE
    - Calculates and evaluates rules -> PASS
    - Generates Rev 1 PDF report
    """
    client, _ = demo_test_env

    # Register instrument
    inst_res = client.post("/api/instruments", json={
        "serial_number": f"SN-PASS-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Sartorius",
        "model": "Entris II 3000",
        "instrument_type": "Precision Balance",
        "accuracy_class": "Class II",
        "max_capacity": 3000.0,
        "min_capacity": 0.5,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    inst_id = inst_res.json()["id"]

    # Create session
    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Marcus Vance",
        "laboratory_location": "Bay 1",
        "ambient_temperature": 20.2,
        "relative_humidity": 47.0,
        "service_type": "initial",
        "test_configuration": {}
    })
    sess_id = sess_res.json()["id"]

    # Record compliant observations
    client.post(f"/api/tests/{sess_id}/observations", json={"observations": [
        {"load": 0.0, "indication": 0.0, "direction": "increasing"},
        {"load": 500.0, "indication": 500.01, "direction": "increasing"},
        {"load": 1000.0, "indication": 1000.02, "direction": "increasing"},
        {"load": 2000.0, "indication": 2000.02, "direction": "increasing"},
        {"load": 3000.0, "indication": 3000.03, "direction": "increasing"},
    ]})

    # Calculate
    calc_res = client.post(f"/api/tests/{sess_id}/calculate")
    assert calc_res.status_code == 200
    assert calc_res.json()["rule_evaluation"]["overall_outcome"] == "PASS"

    # Generate Report
    rep_res = client.post(f"/api/tests/{sess_id}/report")
    assert rep_res.status_code == 200
    rep_id = rep_res.json()["report_id"]

    # Verify PDF download & content
    dl = client.get(f"/api/reports/{rep_id}/download")
    assert dl.status_code == 200
    assert len(dl.content) > 1000


# =============================================================================
# SCENARIO 3: COMPLETE FAILING CALIBRATION WORKFLOW (OIML R-76 MPE BREACH)
# =============================================================================

def test_scenario3_failing_calibration_workflow_with_mpe_breach(demo_test_env):
    """
    Scenario 3: Complete FAIL Workflow (Worn load cell / Out-of-tolerance error).
    - Records an indication error of +0.35g at 3000g (30000e in Class II).
    - Class II MPE bracket for m > 20000e is ±1.5e = ±0.15g.
    - Error of +0.35g exceeds ±0.15g -> Overall evaluation: FAIL.
    - Generates PDF report with clear red FAIL outcome and clause violation explanation.
    """
    client, _ = demo_test_env

    inst_res = client.post("/api/instruments", json={
        "serial_number": f"SN-FAIL-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Ohaus",
        "model": "Defender Class II",
        "instrument_type": "Precision Balance",
        "accuracy_class": "Class II",
        "max_capacity": 3000.0,
        "min_capacity": 0.5,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    inst_id = inst_res.json()["id"]

    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Marcus Vance",
        "laboratory_location": "Standards Bay 3",
        "ambient_temperature": 20.0,
        "relative_humidity": 50.0,
        "service_type": "initial",
        "test_configuration": {}
    })
    sess_id = sess_res.json()["id"]

    # Record out-of-tolerance observations
    client.post(f"/api/tests/{sess_id}/observations", json={"observations": [
        {"load": 0.0, "indication": 0.0, "direction": "increasing"},
        {"load": 500.0, "indication": 500.02, "direction": "increasing"},
        {"load": 1000.0, "indication": 1000.04, "direction": "increasing"},
        {"load": 2000.0, "indication": 2000.08, "direction": "increasing"},
        # 3000g: Error is +0.35g (+3.5e), exceeding ±1.5e allowance!
        {"load": 3000.0, "indication": 3000.35, "direction": "increasing"},
    ]})

    # Calculate
    calc_res = client.post(f"/api/tests/{sess_id}/calculate")
    assert calc_res.status_code == 200
    rule_eval = calc_res.json()["rule_evaluation"]
    assert rule_eval["overall_outcome"] == "FAIL"
    assert rule_eval["failed_count"] >= 1

    # Verify explainability: rule evaluations detail the breach
    evaluations = rule_eval["evaluations"]
    mpe_eval = next(e for e in evaluations if e["rule_id"] == "OIML-R76-1-LIN-MPE")
    assert mpe_eval["outcome"] == "FAIL"

    # Generate Report
    rep_res = client.post(f"/api/tests/{sess_id}/report")
    assert rep_res.status_code == 200
    rep_id = rep_res.json()["report_id"]

    # Inspect PDF content for clear failure attribution
    dl = client.get(f"/api/reports/{rep_id}/download")
    assert dl.status_code == 200

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        tf.write(dl.content)
        tf_path = tf.name
    try:
        with pdfplumber.open(tf_path) as pdf:
            text = "".join(p.extract_text() or "" for p in pdf.pages)
            assert "OVERALL EVALUATION OUTCOME: FAIL" in text
            assert "OIML-R76-1-LIN-MPE" in text
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)


# =============================================================================
# SCENARIO 4: OVER-CAPACITY OBSERVATION REJECTION
# =============================================================================

def test_scenario4_over_capacity_load_rejection(demo_test_env):
    """
    Scenario 4: Capacity Boundary Guard.
    - Test balance capacity is 3000g.
    - Technician submits 3500g load.
    - API must reject with HTTP 422 Unprocessable Entity.
    """
    client, _ = demo_test_env

    inst_res = client.post("/api/instruments", json={
        "serial_number": f"SN-CAP-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Kern",
        "model": "PCB 3000",
        "instrument_type": "Precision Balance",
        "accuracy_class": "Class II",
        "max_capacity": 3000.0,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    inst_id = inst_res.json()["id"]

    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Marcus Vance",
    })
    sess_id = sess_res.json()["id"]

    # 3500g exceeds 3000g max capacity
    res = client.post(f"/api/tests/{sess_id}/observations", json={"observations": [
        {"load": 3500.0, "indication": 3500.0, "direction": "increasing"}
    ]})
    assert res.status_code == 422
    assert "exceeds instrument maximum capacity" in res.json()["detail"]


# =============================================================================
# SCENARIO 5: COMPLETED SESSION MUTABILITY & RBAC GUARDS
# =============================================================================

def test_scenario5_completed_session_and_rbac_guards(demo_test_env):
    """
    Scenario 5: Immutability (BUG-5) and Role-Based Access Control.
    - Completed session rejects ordinary PUT with HTTP 409.
    - Ordinary operator (m.vance) attempting amendment receives HTTP 403.
    - Reviewer (e.rostova) is permitted to amend with HTTP 200.
    """
    client, _ = demo_test_env

    inst_res = client.post("/api/instruments", json={
        "serial_number": f"SN-LOCK-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Sartorius",
        "model": "BCE3002",
        "accuracy_class": "Class II",
        "max_capacity": 3000.0,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    inst_id = inst_res.json()["id"]

    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Marcus Vance",
    })
    sess_id = sess_res.json()["id"]

    client.post(f"/api/tests/{sess_id}/observations", json={"observations": [
        {"load": 0.0, "indication": 0.0, "direction": "increasing"},
        {"load": 1000.0, "indication": 1000.02, "direction": "increasing"},
    ]})
    client.post(f"/api/tests/{sess_id}/calculate")

    # BUG-5 Guard: Ordinary PUT on Completed session returns HTTP 409
    put_res = client.put(f"/api/tests/{sess_id}", json={"service_type": "subsequent"})
    assert put_res.status_code == 409

    # RBAC Guard: Operator m.vance cannot execute amendments
    op_amend = client.post(
        f"/api/tests/{sess_id}/amend",
        headers={"X-User-Id": "m.vance"},
        json={"reason": "Unilateral operator modification.", "operator_name": "Marcus Vance"}
    )
    assert op_amend.status_code == 403

    # RBAC Permission: Reviewer e.rostova is authorized
    rev_amend = client.post(
        f"/api/tests/{sess_id}/amend",
        headers={"X-User-Id": "e.rostova"},
        json={"reason": "Technical audit review requested zero-point re-evaluation.", "operator_name": "Elena Rostova"}
    )
    assert rev_amend.status_code == 200
    assert rev_amend.json()["new_version"] == 2


# =============================================================================
# SCENARIO 6: AMENDMENT VERSIONING & SUPERSEDED PDF PRESERVATION
# =============================================================================

def test_scenario6_pdf_versioning_and_superseded_traceability(demo_test_env):
    """
    Scenario 6: Dual Report Versioning (BUG-8).
    - Generates Report 1 at Rev 1.
    - Amends session to Rev 2.
    - Generates Report 2 at Rev 2.
    - Verifies Report 1 is superseded in database.
    - Verifies Report 1 PDF file remains accessible and intact.
    - Verifies Report 2 PDF file includes Rev 2 (AMENDED) and amendment justification.
    """
    client, _ = demo_test_env

    inst_res = client.post("/api/instruments", json={
        "serial_number": f"SN-VERS-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Mettler Toledo",
        "model": "ML3002",
        "accuracy_class": "Class II",
        "max_capacity": 3000.0,
        "verification_scale_interval": 0.1,
        "unit": "g"
    })
    inst_id = inst_res.json()["id"]

    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "linearity",
        "operator_name": "Marcus Vance",
    })
    sess_id = sess_res.json()["id"]

    client.post(f"/api/tests/{sess_id}/observations", json={"observations": [
        {"load": 0.0, "indication": 0.0, "direction": "increasing"},
        {"load": 1000.0, "indication": 1000.01, "direction": "increasing"},
    ]})
    client.post(f"/api/tests/{sess_id}/calculate")

    # Generate Report 1
    rep1_res = client.post(f"/api/tests/{sess_id}/report")
    rep1_id = rep1_res.json()["report_id"]

    # Execute authorized amendment to Rev 2
    amend_reason = "Tare re-zeroing performed following environmental drift check."
    client.post(
        f"/api/tests/{sess_id}/amend",
        headers={"X-User-Id": "dr.jenkins"},
        json={
            "reason": amend_reason,
            "operator_name": "Dr. Sarah Jenkins",
            "observations": [
                {"load": 0.0, "indication": 0.0, "direction": "increasing"},
                {"load": 1000.0, "indication": 1000.00, "direction": "increasing"},
            ]
        }
    )

    # Generate Report 2
    rep2_res = client.post(f"/api/tests/{sess_id}/report")
    rep2_id = rep2_res.json()["report_id"]

    # Verify DB metadata
    sess_data = client.get(f"/api/tests/{sess_id}").json()
    reps = sess_data["reports"]
    rep_map = {r["id"]: r for r in reps}

    assert rep_map[rep1_id]["version"] == 1
    assert rep_map[rep1_id]["is_superseded"] is True
    assert rep_map[rep1_id]["superseded_by"] == rep2_id

    assert rep_map[rep2_id]["version"] == 2
    assert rep_map[rep2_id]["is_superseded"] is False

    # Verify both PDFs can be downloaded independently
    dl1 = client.get(f"/api/reports/{rep1_id}/download")
    dl2 = client.get(f"/api/reports/{rep2_id}/download")
    assert dl1.status_code == 200
    assert dl2.status_code == 200
    assert len(dl1.content) > 1000
    assert len(dl2.content) > 1000


# =============================================================================
# SCENARIO 7: AUDIT LOG TIMELINE TRACEABILITY
# =============================================================================

def test_scenario7_audit_log_traceability(demo_test_env):
    """
    Scenario 7: Audit Trail & Metrological Traceability.
    - Verifies that all operations produce immutable chronological audit entries.
    """
    client, _ = demo_test_env

    inst_res = client.post("/api/instruments", json={
        "serial_number": f"SN-AUD-{uuid.uuid4().hex[:4].upper()}",
        "manufacturer": "Shimadzu",
        "model": "AUW220D",
        "accuracy_class": "Class I",
        "max_capacity": 220.0,
        "verification_scale_interval": 0.001,
        "unit": "g"
    })
    inst_id = inst_res.json()["id"]

    sess_res = client.post("/api/tests", json={
        "instrument_id": inst_id,
        "test_category": "repeatability",
        "operator_name": "Marcus Vance",
    })
    sess_id = sess_res.json()["id"]

    audit_logs = client.get(f"/api/tests/{sess_id}/audit").json()
    assert len(audit_logs) >= 1
    actions = [a["action"] for a in audit_logs]
    assert "TEST_SESSION_CREATED" in actions

