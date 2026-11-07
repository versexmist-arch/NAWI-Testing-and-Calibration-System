import sys
from pathlib import Path
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException

# Ensure calculation_engine and rules packages are on sys.path
ROOT_PATH = str(Path(__file__).resolve().parent.parent.parent.parent)
if ROOT_PATH not in sys.path:
    sys.path.insert(0, ROOT_PATH)

from calculation_engine.eccentricity import calculate_eccentricity
from calculation_engine.linearity import calculate_linearity
from calculation_engine.repeatability import calculate_repeatability
from rules import OIMLRuleEvaluator
from ..models import TestSession, Observation, CalculationResult, RuleEvaluation
from .audit_service import record_audit_event


def calculate_test_session(db: Session, test_session_id: str) -> Dict[str, Any]:
    """Execute metrological calculations for the session's recorded observations."""
    session = db.query(TestSession).filter(TestSession.id == test_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    obs_record = db.query(Observation).filter(Observation.test_session_id == test_session_id).first()
    if not obs_record or not obs_record.data:
        raise HTTPException(
            status_code=400,
            detail="No recorded observations found for this test session. Please submit observations first."
        )

    instrument = session.instrument
    if not instrument:
        raise HTTPException(status_code=404, detail="Associated instrument not found.")

    category = session.test_category.lower().strip()
    obs_list = obs_record.data
    config = session.test_configuration or {}
    unit = instrument.unit
    e_val = instrument.verification_scale_interval

    try:
        # BUG-4 FIX: Validate that no observation load exceeds the instrument's
        # rated maximum capacity before invoking any calculation engine.
        # An over-capacity load is physically impossible for the instrument and
        # must be rejected with HTTP 422 regardless of whether an MPE bracket
        # mathematically exists for that load.
        max_cap = instrument.max_capacity
        over_cap = [
            obs for obs in obs_list
            if float(obs.get("load", 0)) > max_cap + 1e-9
        ]
        if over_cap:
            worst = max(float(o["load"]) for o in over_cap)
            raise HTTPException(
                status_code=422,
                detail=(
                    f"Observation load {worst} {unit} exceeds the instrument's rated "
                    f"maximum capacity of {max_cap} {unit}. Remove or correct the "
                    f"over-capacity observation before submitting for calculation."
                ),
            )

        if category == "eccentricity":
            test_load = config.get("test_load")
            if not test_load:
                # Default to 1/3 Max per OIML R-76-1 3.6.2
                test_load = round(instrument.max_capacity / 3.0, 2)
            calc_output = calculate_eccentricity(
                test_load=float(test_load),
                unit=unit,
                observations=obs_list,
                instrument_e=e_val,
            )
        elif category == "linearity":
            use_changeover = config.get("use_changeover_points", False)
            calc_output = calculate_linearity(
                observations=obs_list,
                unit=unit,
                instrument_e=e_val,
                use_changeover_points=use_changeover,
            )
        elif category == "repeatability":
            test_load = config.get("test_load")
            if not test_load:
                # Default to 0.5 Max
                test_load = round(instrument.max_capacity * 0.5, 2)
            calc_output = calculate_repeatability(
                test_load=float(test_load),
                observations=obs_list,
                unit=unit,
                instrument_e=e_val,
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported test category: {category}")
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=f"Calculation validation error: {str(ve)}")

    # Store calculation result in database
    calc_db = db.query(CalculationResult).filter(CalculationResult.test_session_id == test_session_id).first()
    if not calc_db:
        calc_db = CalculationResult(
            test_session_id=test_session_id,
            calculation_version=calc_output.get("calculation_version", "1.0"),
            method=calc_output.get("method", "OIML R-76"),
            summary_data={k: v for k, v in calc_output.items() if k not in ("position_results", "point_results", "run_records")},
            full_data=calc_output,
        )
        db.add(calc_db)
    else:
        calc_db.calculation_version = calc_output.get("calculation_version", "1.0")
        calc_db.method = calc_output.get("method", "OIML R-76")
        calc_db.summary_data = {k: v for k, v in calc_output.items() if k not in ("position_results", "point_results", "run_records")}
        calc_db.full_data = calc_output

    session.status = "Calculated"
    db.commit()
    db.refresh(calc_db)

    record_audit_event(
        db=db,
        action="CALCULATION_EXECUTED",
        actor=session.operator_name,
        test_session_id=session.id,
        instrument_id=instrument.id,
        details={
            "category": category,
            "version": calc_db.calculation_version,
            "summary": calc_db.summary_data,
        }
    )

    # Automatically evaluate rules right after calculation
    eval_output = evaluate_test_session(db, test_session_id)

    return {
        "calculation_result": calc_output,
        "rule_evaluation": eval_output,
        "status": session.status,
    }


def evaluate_test_session(db: Session, test_session_id: str) -> Dict[str, Any]:
    """Evaluate calculated results against versioned OIML R-76 requirements."""
    session = db.query(TestSession).filter(TestSession.id == test_session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Test session not found.")

    calc_record = db.query(CalculationResult).filter(CalculationResult.test_session_id == test_session_id).first()
    if not calc_record or not calc_record.full_data:
        raise HTTPException(status_code=400, detail="Calculation results missing. Run calculation first.")

    instrument = session.instrument
    if not instrument:
        raise HTTPException(status_code=404, detail="Associated instrument not found.")

    evaluator = OIMLRuleEvaluator()
    instrument_metadata = {
        "accuracy_class": instrument.accuracy_class,
        "verification_scale_interval": instrument.verification_scale_interval,
        "max_capacity": instrument.max_capacity,
        "unit": instrument.unit,
    }

    eval_summary = evaluator.evaluate_test(
        test_category=session.test_category,
        calc_result=calc_record.full_data,
        instrument_metadata=instrument_metadata,
        service_type=session.service_type or "initial",
    )

    eval_dict = eval_summary.model_dump()

    eval_db = db.query(RuleEvaluation).filter(RuleEvaluation.test_session_id == test_session_id).first()
    if not eval_db:
        eval_db = RuleEvaluation(
            test_session_id=test_session_id,
            rule_version=eval_summary.rule_version,
            overall_outcome=eval_summary.overall_outcome.value,
            summary_text=eval_summary.summary_text,
            evaluations_data=eval_dict,
        )
        db.add(eval_db)
    else:
        eval_db.rule_version = eval_summary.rule_version
        eval_db.overall_outcome = eval_summary.overall_outcome.value
        eval_db.summary_text = eval_summary.summary_text
        eval_db.evaluations_data = eval_dict

    session.status = "Completed"
    db.commit()
    db.refresh(eval_db)

    record_audit_event(
        db=db,
        action="RULES_EVALUATED",
        actor=session.operator_name,
        test_session_id=session.id,
        instrument_id=instrument.id,
        details={
            "outcome": eval_summary.overall_outcome.value,
            "rule_version": eval_summary.rule_version,
            "summary": eval_summary.summary_text,
        }
    )

    return eval_dict

