import pytest
from rules import (
    OIMLRuleEvaluator,
    EvaluationOutcome,
    RuleVerificationStatus,
    get_mpe_for_load,
)


def test_mpe_lookup_class_iii():
    # Class III: e = 1g
    # 0 <= m <= 500e -> MPE = 0.5e (0.5g)
    mult, mpe, _ = get_mpe_for_load(200.0, 1.0, "Class III")
    assert mult == 0.5
    assert mpe == 0.5

    # 500e < m <= 2000e -> MPE = 1.0e (1.0g)
    mult, mpe, _ = get_mpe_for_load(1500.0, 1.0, "Class III")
    assert mult == 1.0
    assert mpe == 1.0

    # 2000e < m <= 10000e -> MPE = 1.5e (1.5g)
    mult, mpe, _ = get_mpe_for_load(3000.0, 1.0, "Class III")
    assert mult == 1.5
    assert mpe == 1.5


def test_mpe_lookup_service_type():
    # In-service inspection doubles MPE
    mult, mpe, _ = get_mpe_for_load(200.0, 1.0, "Class III", service_type="service")
    assert mult == 1.0
    assert mpe == 1.0


def test_linearity_evaluation_pass_fail():
    evaluator = OIMLRuleEvaluator()
    instrument = {"verification_scale_interval": 1.0, "accuracy_class": "Class III", "unit": "g"}

    # Passing test: all corrected errors <= MPE
    calc_pass = {
        "unit": "g",
        "max_absolute_error": 0.4,
        "point_results": [
            {"index": 1, "load": 500.0, "corrected_error": 0.4},
            {"index": 2, "load": 1500.0, "corrected_error": 0.9},
        ]
    }
    res_pass = evaluator.evaluate_test("linearity", calc_pass, instrument)
    assert res_pass.overall_outcome == EvaluationOutcome.PASS
    assert res_pass.failed_count == 0

    # Failing test: error exceeds MPE (e.g. 1.2g at 500g where limit is 0.5g)
    calc_fail = {
        "unit": "g",
        "max_absolute_error": 1.2,
        "point_results": [
            {"index": 1, "load": 500.0, "corrected_error": 1.2},
        ]
    }
    res_fail = evaluator.evaluate_test("linearity", calc_fail, instrument)
    assert res_fail.overall_outcome == EvaluationOutcome.FAIL
    assert res_fail.failed_count == 1


def test_unverified_rule_never_produces_pass():
    evaluator = OIMLRuleEvaluator()
    instrument = {"verification_scale_interval": 1.0, "accuracy_class": "Class III", "unit": "g"}

    calc_rep = {
        "unit": "g",
        "reference_load": 1000.0,
        "repeatability_range": 0.2,
        "min_indication": 1000.0,
        "max_indication": 1000.2,
        "standard_deviation": 0.05,
    }
    res = evaluator.evaluate_test("repeatability", calc_rep, instrument)

    # Check that the experimental unverified rule is flagged as PENDING_VERIFICATION
    exp_eval = next((e for e in res.evaluations if e.rule_id == "OIML-R76-EXPERIMENTAL-DRAFT-2026"), None)
    assert exp_eval is not None
    assert exp_eval.verification_status == RuleVerificationStatus.PENDING_VERIFICATION
    assert exp_eval.outcome == EvaluationOutcome.PENDING_VERIFICATION


def test_incomplete_when_missing_scale_interval():
    evaluator = OIMLRuleEvaluator()
    # Missing verification_scale_interval
    instrument = {"accuracy_class": "Class III", "unit": "g"}
    calc_ecc = {
        "unit": "g",
        "reference_load": 1000.0,
        "max_absolute_eccentricity_deviation": 0.2,
        "position_results": []
    }
    res = evaluator.evaluate_test("eccentricity", calc_ecc, instrument)
    assert res.overall_outcome == EvaluationOutcome.INCOMPLETE

