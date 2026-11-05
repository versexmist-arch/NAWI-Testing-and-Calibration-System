from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from ..models import (
    Instrument,
    TestSession,
    Observation,
    CalculationResult,
    RuleEvaluation,
    GeneratedReport,
    AuditLog,
)
from .test_service import calculate_test_session
from .report_service import generate_pdf_report


def seed_demo_data(db: Session) -> Dict[str, Any]:
    """Seed comprehensive demonstration instruments and test workflows."""
    # Check if demo instruments already exist
    existing = db.query(Instrument).filter(Instrument.is_demo == True).first()
    if existing:
        return {"status": "already_seeded", "message": "Demo data is already present."}

    # 1. Instruments
    inst1 = Instrument(
        id="INST-DEMO-01",
        serial_number="SN-ANA-2026-001",
        manufacturer="Sartorius Metrology",
        model="Secura 225D Micro-Analytical",
        instrument_type="Analytical Balance",
        accuracy_class="Class I",
        max_capacity=220.0,
        min_capacity=0.01,
        verification_scale_interval=0.001,
        actual_scale_interval=0.0001,
        unit="g",
        scale_intervals_count=220000,
        location="Cleanroom Analytical Suite 4A",
        registration_date=datetime.utcnow() - timedelta(days=12),
        notes="High-precision class I instrument. Demonstration profile for micro-mass verification.",
        is_demo=True,
    )

    inst2 = Instrument(
        id="INST-DEMO-02",
        serial_number="SN-PRC-2026-042",
        manufacturer="Mettler Toledo",
        model="PB3002-S Precision",
        instrument_type="Precision Balance",
        accuracy_class="Class II",
        max_capacity=3100.0,
        min_capacity=0.5,
        verification_scale_interval=0.1,
        actual_scale_interval=0.01,
        unit="g",
        scale_intervals_count=31000,
        location="Main Calibration Standards Bay",
        registration_date=datetime.utcnow() - timedelta(days=8),
        notes="Standard Class II lab balance. Utilized for general laboratory testing and chemical assays.",
        is_demo=True,
    )

    inst3 = Instrument(
        id="INST-DEMO-03",
        serial_number="SN-IND-2026-108",
        manufacturer="Ohaus Industrial",
        model="Defender 3000 Standard",
        instrument_type="Bench Scale",
        accuracy_class="Class III",
        max_capacity=60.0,
        min_capacity=0.4,
        verification_scale_interval=0.02,
        actual_scale_interval=0.02,
        unit="kg",
        scale_intervals_count=3000,
        location="Industrial Inspection Bay B",
        registration_date=datetime.utcnow() - timedelta(days=5),
        notes="Industrial receiving and packaging verification platform scale.",
        is_demo=True,
    )

    db.add_all([inst1, inst2, inst3])
    db.commit()

    # 2. Test Session 1: Eccentricity Test on INST-DEMO-02 (3100g Class II)
    test1 = TestSession(
        id="TEST-DEMO-ECC-01",
        instrument_id=inst2.id,
        test_category="eccentricity",
        operator_name="Dr. Sarah Jenkins (Senior Metrologist)",
        laboratory_location="Standards Lab Bay 1",
        test_date=datetime.utcnow() - timedelta(days=2),
        ambient_temperature=21.2,
        relative_humidity=48.5,
        service_type="initial",
        status="Draft",
        version=1,
        test_configuration={"test_load": 1000.0, "receptor_geometry": "rectangular_4_corners"},
        is_demo=True,
    )
    db.add(test1)
    db.commit()

    obs1_data = [
        {"position_id": "pos_1", "position_name": "Center (1)", "indication": 1000.02, "zero_indication": 0.0},
        {"position_id": "pos_2", "position_name": "Front-Left (2)", "indication": 1000.05, "zero_indication": 0.0},
        {"position_id": "pos_3", "position_name": "Back-Left (3)", "indication": 999.98, "zero_indication": 0.0},
        {"position_id": "pos_4", "position_name": "Back-Right (4)", "indication": 1000.04, "zero_indication": 0.0},
        {"position_id": "pos_5", "position_name": "Front-Right (5)", "indication": 999.97, "zero_indication": 0.0},
    ]
    obs1 = Observation(test_session_id=test1.id, data=obs1_data)
    db.add(obs1)
    db.commit()
    calculate_test_session(db, test1.id)
    generate_pdf_report(db, test1.id, operator_name=test1.operator_name)

    # 3. Test Session 2: Linearity Test on INST-DEMO-02 (3100g Class II)
    test2 = TestSession(
        id="TEST-DEMO-LIN-02",
        instrument_id=inst2.id,
        test_category="linearity",
        operator_name="Dr. Sarah Jenkins (Senior Metrologist)",
        laboratory_location="Standards Lab Bay 1",
        test_date=datetime.utcnow() - timedelta(days=1),
        ambient_temperature=21.4,
        relative_humidity=49.0,
        service_type="initial",
        status="Draft",
        version=1,
        test_configuration={"points_count": 8, "use_changeover_points": False},
        is_demo=True,
    )
    db.add(test2)
    db.commit()

    obs2_data = [
        {"load": 0.0, "indication": 0.0, "direction": "increasing", "zero_indication": 0.0},
        {"load": 500.0, "indication": 500.03, "direction": "increasing", "zero_indication": 0.0},
        {"load": 1000.0, "indication": 1000.06, "direction": "increasing", "zero_indication": 0.0},
        {"load": 2000.0, "indication": 2000.08, "direction": "increasing", "zero_indication": 0.0},
        {"load": 3000.0, "indication": 3000.05, "direction": "increasing", "zero_indication": 0.0},
        {"load": 2000.0, "indication": 2000.09, "direction": "decreasing", "zero_indication": 0.0},
        {"load": 1000.0, "indication": 1000.07, "direction": "decreasing", "zero_indication": 0.0},
        {"load": 0.0, "indication": 0.01, "direction": "decreasing", "zero_indication": 0.0},
    ]
    obs2 = Observation(test_session_id=test2.id, data=obs2_data)
    db.add(obs2)
    db.commit()
    calculate_test_session(db, test2.id)
    generate_pdf_report(db, test2.id, operator_name=test2.operator_name)

    # 4. Test Session 3: Repeatability Test on INST-DEMO-01 (220g Class I)
    test3 = TestSession(
        id="TEST-DEMO-REP-03",
        instrument_id=inst1.id,
        test_category="repeatability",
        operator_name="Marcus Vance (Metrology Specialist)",
        laboratory_location="Cleanroom Analytical Suite 4A",
        test_date=datetime.utcnow() - timedelta(hours=6),
        ambient_temperature=20.1,
        relative_humidity=44.0,
        service_type="initial",
        status="Draft",
        version=1,
        test_configuration={"test_load": 100.0, "runs_count": 10},
        is_demo=True,
    )
    db.add(test3)
    db.commit()

    readings = [100.0002, 100.0003, 100.0001, 100.0002, 100.0004, 100.0002, 100.0001, 100.0003, 100.0002, 100.0002]
    obs3_data = [{"run_number": i + 1, "indication": val} for i, val in enumerate(readings)]
    obs3 = Observation(test_session_id=test3.id, data=obs3_data)
    db.add(obs3)
    db.commit()
    calculate_test_session(db, test3.id)
    generate_pdf_report(db, test3.id, operator_name=test3.operator_name)

    return {
        "status": "success",
        "message": "Demo data successfully seeded with 3 instruments, 3 completed test sessions, calculations, and PDF reports.",
        "instruments_seeded": 3,
        "test_sessions_seeded": 3,
    }


def reset_demo_data(db: Session) -> Dict[str, Any]:
    """
    Safely reset demo data without touching user-entered records.
    Removes demo records and reseeds fresh demonstration datasets.
    """
    demo_tests = db.query(TestSession).filter(TestSession.is_demo == True).all()
    for t in demo_tests:
        db.delete(t)

    demo_insts = db.query(Instrument).filter(Instrument.is_demo == True).all()
    for inst in demo_insts:
        db.delete(inst)

    db.commit()
    return seed_demo_data(db)
