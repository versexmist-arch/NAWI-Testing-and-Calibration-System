"""
Comprehensive unit tests for the NAWI Linearity Test calculation engine.

Coverage:
  - All four OIML accuracy class MPE table lookups
  - Class III bracket boundaries: loads immediately below, at and above each step
  - Open-ended last bracket (loads beyond original hard max_e)
  - Negative and out-of-range load guards (ValueError)
  - Zero-load E0 detection and correction
  - Increasing-only, decreasing-only, and mixed observations
  - Hysteresis calculation and reporting
  - PASS and FAIL scenarios against MPE
  - Hysteresis evaluation (OIML R-76-1 Clause 3.5.1 ¶2)
  - In-service MPE doubling
  - Missing / invalid observation rows
  - Missing verification scale interval (INCOMPLETE outcome)
  - Empty observations (ValueError)
"""
import pytest
from calculation_engine.linearity import calculate_linearity
from rules import OIMLRuleEvaluator, EvaluationOutcome, get_mpe_for_load


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — MPE LOOKUP: ALL CLASSES, ALL BRACKETS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMPELookupClassIII:
    """Class III: 0≤m≤500e → 0.5e | 500e<m≤2000e → 1.0e | m>2000e → 1.5e"""

    E = 1.0  # e = 1 g

    # ── Bracket 1: 0 ≤ m ≤ 500e ──────────────────────────────────────────────

    def test_zero_load(self):
        mult, mpe, _ = get_mpe_for_load(0.0, self.E, "Class III")
        assert mult == 0.5
        assert mpe == pytest.approx(0.5)

    def test_load_well_inside_bracket_1(self):
        mult, mpe, _ = get_mpe_for_load(200.0, self.E, "Class III")
        assert mult == 0.5
        assert mpe == pytest.approx(0.5)

    def test_load_just_below_boundary_1(self):
        # 499e — still in bracket 1
        mult, mpe, _ = get_mpe_for_load(499.0, self.E, "Class III")
        assert mult == 0.5

    def test_load_exactly_at_boundary_1(self):
        # 500e — inclusive upper edge of bracket 1
        mult, mpe, _ = get_mpe_for_load(500.0, self.E, "Class III")
        assert mult == 0.5
        assert mpe == pytest.approx(0.5)

    # ── Bracket 2: 500e < m ≤ 2000e ──────────────────────────────────────────

    def test_load_just_above_boundary_1(self):
        # 501e — first step into bracket 2
        mult, mpe, _ = get_mpe_for_load(501.0, self.E, "Class III")
        assert mult == 1.0
        assert mpe == pytest.approx(1.0)

    def test_load_mid_bracket_2(self):
        mult, mpe, _ = get_mpe_for_load(1000.0, self.E, "Class III")
        assert mult == 1.0

    def test_load_just_below_boundary_2(self):
        mult, mpe, _ = get_mpe_for_load(1999.0, self.E, "Class III")
        assert mult == 1.0

    def test_load_exactly_at_boundary_2(self):
        # 2000e — inclusive upper edge of bracket 2
        mult, mpe, _ = get_mpe_for_load(2000.0, self.E, "Class III")
        assert mult == 1.0
        assert mpe == pytest.approx(1.0)

    # ── Bracket 3: m > 2000e (open-ended) ────────────────────────────────────

    def test_load_just_above_boundary_2(self):
        # 2001e — first step into open-ended bracket 3
        mult, mpe, _ = get_mpe_for_load(2001.0, self.E, "Class III")
        assert mult == 1.5
        assert mpe == pytest.approx(1.5)

    def test_load_mid_bracket_3(self):
        mult, mpe, _ = get_mpe_for_load(5000.0, self.E, "Class III")
        assert mult == 1.5

    def test_load_at_old_hard_limit(self):
        # 10000e — was the old finite max_e, now must still resolve to 1.5e
        mult, mpe, _ = get_mpe_for_load(10000.0, self.E, "Class III")
        assert mult == 1.5
        assert mpe == pytest.approx(1.5)

    def test_load_beyond_old_hard_limit(self):
        # 10001e — previously returned wrong 1.0e (BUG-1). Must now return 1.5e.
        mult, mpe, _ = get_mpe_for_load(10001.0, self.E, "Class III")
        assert mult == 1.5
        assert mpe == pytest.approx(1.5)

    def test_load_well_beyond_old_hard_limit(self):
        mult, mpe, _ = get_mpe_for_load(50000.0, self.E, "Class III")
        assert mult == 1.5


class TestMPELookupClassII:
    """Class II: 0≤m≤5000e → 0.5e | 5000e<m≤20000e → 1.0e | m>20000e → 1.5e"""

    E = 0.1

    def test_bracket_1(self):
        mult, _, _ = get_mpe_for_load(500.0, self.E, "Class II")   # m/e = 5000
        assert mult == 0.5

    def test_bracket_2(self):
        mult, _, _ = get_mpe_for_load(1000.0, self.E, "Class II")  # m/e = 10000
        assert mult == 1.0

    def test_bracket_3_beyond_old_limit(self):
        # Old max_e was 100000. 100001e must now return 1.5e (open-ended fix).
        mult, _, _ = get_mpe_for_load(100001.0 * self.E, self.E, "Class II")
        assert mult == 1.5


class TestMPELookupClassI:
    """Class I: last bracket was already open-ended — must stay correct."""

    def test_bracket_1(self):
        mult, _, _ = get_mpe_for_load(1000.0, 0.001, "Class I")  # m/e = 1000000 → bracket 3
        assert mult == 1.5

    def test_bracket_3_open_ended(self):
        mult, _, _ = get_mpe_for_load(500.0, 0.001, "Class I")   # m/e = 500000 → bracket 3
        assert mult == 1.5


class TestMPELookupClassIIII:
    """Class IIII: 0≤m≤50e → 0.5e | 50e<m≤200e → 1.0e | m>200e → 1.5e"""

    E = 5.0

    def test_bracket_1(self):
        mult, _, _ = get_mpe_for_load(200.0, self.E, "Class IIII")  # m/e = 40
        assert mult == 0.5

    def test_bracket_2(self):
        mult, _, _ = get_mpe_for_load(500.0, self.E, "Class IIII")  # m/e = 100
        assert mult == 1.0

    def test_bracket_3_beyond_old_limit(self):
        # Old max_e = 1000. 1001e must now return 1.5e.
        mult, _, _ = get_mpe_for_load(1001.0 * self.E, self.E, "Class IIII")
        assert mult == 1.5


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — MPE LOOKUP: GUARD RAILS
# ═══════════════════════════════════════════════════════════════════════════════

class TestMPEGuards:

    def test_negative_e_raises(self):
        with pytest.raises(ValueError, match="strictly positive"):
            get_mpe_for_load(500.0, -1.0, "Class III")

    def test_zero_e_raises(self):
        with pytest.raises(ValueError, match="strictly positive"):
            get_mpe_for_load(500.0, 0.0, "Class III")

    def test_negative_load_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            get_mpe_for_load(-1.0, 1.0, "Class III")

    def test_in_service_doubles_mpe(self):
        mult_init, mpe_init, _ = get_mpe_for_load(200.0, 1.0, "Class III", service_type="initial")
        mult_serv, mpe_serv, _ = get_mpe_for_load(200.0, 1.0, "Class III", service_type="service")
        assert mult_serv == pytest.approx(mult_init * 2.0)
        assert mpe_serv == pytest.approx(mpe_init * 2.0)

    def test_unknown_class_falls_back_to_class_iii(self):
        # Should not raise; falls back gracefully
        mult, mpe, _ = get_mpe_for_load(200.0, 1.0, "Class Xyz")
        assert mult == 0.5  # 200e ≤ 500e → bracket 1 of Class III


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — CALCULATOR: ZERO-LOAD ERROR DETECTION AND CORRECTION
# ═══════════════════════════════════════════════════════════════════════════════

class TestZeroLoadCorrection:

    def test_zero_load_error_detected_from_first_observation(self):
        obs = [
            {"load": 0.0, "indication": 0.1, "direction": "increasing"},
            {"load": 500.0, "indication": 500.4, "direction": "increasing"},
        ]
        res = calculate_linearity(obs, unit="g")
        assert res["zero_load_error"] == pytest.approx(0.1)

    def test_corrected_error_subtracts_e0(self):
        # E(500) = 500.4 - 500 = 0.4; E0 = 0.1; Ec = 0.4 - 0.1 = 0.3
        obs = [
            {"load": 0.0, "indication": 0.1, "direction": "increasing"},
            {"load": 500.0, "indication": 500.4, "direction": "increasing"},
        ]
        res = calculate_linearity(obs, unit="g")
        p2 = res["point_results"][1]
        assert p2["indication_error"] == pytest.approx(0.4)
        assert p2["corrected_error"] == pytest.approx(0.3)

    def test_zero_load_point_corrected_error_is_zero_by_definition(self):
        # Ec(0) = E(0) - E(0) = 0 — this is mathematically correct per OIML Clause 3.5.1
        obs = [
            {"load": 0.0, "indication": 0.3, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.5, "direction": "increasing"},
        ]
        res = calculate_linearity(obs, unit="g")
        p0 = res["point_results"][0]
        assert p0["corrected_error"] == pytest.approx(0.0)
        # But the raw indication error (E0) is still reported
        assert p0["indication_error"] == pytest.approx(0.3)
        # And zero_load_error captures it at the summary level
        assert res["zero_load_error"] == pytest.approx(0.3)

    def test_no_zero_load_observation_means_e0_is_zero(self):
        obs = [
            {"load": 500.0, "indication": 500.2, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.4, "direction": "increasing"},
        ]
        res = calculate_linearity(obs, unit="g")
        assert res["zero_load_error"] == 0.0
        assert res["point_results"][0]["corrected_error"] == pytest.approx(0.2)
        assert res["point_results"][1]["corrected_error"] == pytest.approx(0.4)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — CALCULATOR: DIRECTION HANDLING
# ═══════════════════════════════════════════════════════════════════════════════

class TestDirectionHandling:

    def test_increasing_only(self):
        obs = [
            {"load": 0.0, "indication": 0.0, "direction": "increasing"},
            {"load": 500.0, "indication": 500.2, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.3, "direction": "increasing"},
        ]
        res = calculate_linearity(obs, unit="g", instrument_e=1.0)
        assert res["points_count"] == 3
        assert res["has_hysteresis_data"] is False
        assert res["max_hysteresis"] is None

    def test_decreasing_only(self):
        obs = [
            {"load": 1000.0, "indication": 1000.3, "direction": "decreasing"},
            {"load": 500.0,  "indication": 500.2,  "direction": "decreasing"},
            {"load": 0.0,    "indication": 0.0,     "direction": "decreasing"},
        ]
        res = calculate_linearity(obs, unit="g", instrument_e=1.0)
        assert res["points_count"] == 3
        assert res["has_hysteresis_data"] is False

    def test_increasing_and_decreasing_produces_hysteresis(self):
        obs = [
            {"load": 0.0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.3, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.4, "direction": "decreasing"},
            {"load": 0.0,    "indication": 0.0,    "direction": "decreasing"},
        ]
        res = calculate_linearity(obs, unit="g", instrument_e=1.0)
        assert res["has_hysteresis_data"] is True
        # Hysteresis at 1000g: |1000.4 - 1000.3| = 0.1
        assert res["max_hysteresis"] == pytest.approx(0.1)

    def test_direction_field_defaults_to_increasing_on_unknown(self):
        obs = [{"load": 500.0, "indication": 500.1, "direction": "INVALID_VALUE"}]
        res = calculate_linearity(obs, unit="g")
        assert res["point_results"][0]["direction"] == "increasing"

    def test_max_errors_tracked_across_both_directions(self):
        obs = [
            {"load": 0.0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 500.0,  "indication": 500.2,  "direction": "increasing"},
            {"load": 500.0,  "indication": 500.4,  "direction": "decreasing"},
            {"load": 0.0,    "indication": -0.1,   "direction": "decreasing"},
        ]
        res = calculate_linearity(obs, unit="g")
        # Max positive: 0.4 (decreasing at 500)
        # Max negative: -0.1 (decreasing at 0, corrected: -0.1 - 0 = -0.1)
        assert res["max_positive_error"] == pytest.approx(0.4)
        assert res["max_negative_error"] == pytest.approx(-0.1)
        assert res["max_absolute_error"] == pytest.approx(0.4)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — CALCULATOR: STANDARD LINEARITY CURVE
# ═══════════════════════════════════════════════════════════════════════════════

class TestStandardLinearityCurve:

    def test_full_increasing_decreasing_sequence(self):
        obs = [
            {"load": 0.0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 500.0,  "indication": 500.2,  "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.5, "direction": "increasing"},
            {"load": 2000.0, "indication": 1999.8, "direction": "increasing"},
            {"load": 3000.0, "indication": 3000.1, "direction": "increasing"},
            {"load": 2000.0, "indication": 2000.0, "direction": "decreasing"},
            {"load": 1000.0, "indication": 1000.6, "direction": "decreasing"},
            {"load": 0.0,    "indication": 0.0,    "direction": "decreasing"},
        ]
        res = calculate_linearity(obs, unit="g", instrument_e=1.0)
        assert res["points_count"] == 8
        assert res["zero_load_error"] == 0.0
        assert res["max_positive_error"] == pytest.approx(0.6)
        assert res["max_negative_error"] == pytest.approx(-0.2)
        assert res["max_absolute_error"] == pytest.approx(0.6)
        # Hysteresis at 2000: |2000.0 - 1999.8| = 0.2
        # Hysteresis at 1000: |1000.6 - 1000.5| = 0.1
        assert res["has_hysteresis_data"] is True
        assert res["max_hysteresis"] == pytest.approx(0.2)

    def test_load_in_e_ratio_reported(self):
        obs = [{"load": 1000.0, "indication": 1000.3, "direction": "increasing"}]
        res = calculate_linearity(obs, unit="g", instrument_e=1.0)
        pt = res["point_results"][0]
        assert pt["load_in_e"] == pytest.approx(1000.0)
        assert pt["corrected_error_in_e"] == pytest.approx(0.3)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — CALCULATOR: ERROR AND EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculatorEdgeCases:

    def test_empty_observations_raises(self):
        with pytest.raises(ValueError, match="At least one load observation is required"):
            calculate_linearity([], unit="g")

    def test_missing_load_field_raises(self):
        obs = [{"indication": 500.0}]
        with pytest.raises(ValueError, match="missing load or indication"):
            calculate_linearity(obs, unit="g")

    def test_missing_indication_field_raises(self):
        obs = [{"load": 500.0}]
        with pytest.raises(ValueError, match="missing load or indication"):
            calculate_linearity(obs, unit="g")

    def test_single_point(self):
        obs = [{"load": 500.0, "indication": 500.3, "direction": "increasing"}]
        res = calculate_linearity(obs, unit="g", instrument_e=1.0)
        assert res["points_count"] == 1
        assert res["max_absolute_error"] == pytest.approx(0.3)

    def test_no_instrument_e_still_calculates_errors(self):
        # Without e, load_in_e and corrected_error_in_e should be absent
        obs = [{"load": 1000.0, "indication": 1001.0, "direction": "increasing"}]
        res = calculate_linearity(obs, unit="g", instrument_e=None)
        pt = res["point_results"][0]
        assert "load_in_e" not in pt
        assert pt["indication_error"] == pytest.approx(1.0)

    def test_per_row_zero_indication_tare(self):
        # I0 per row: each load point has its own tare reading
        obs = [
            {"load": 1000.0, "indication": 1000.5, "zero_indication": 0.1, "direction": "increasing"},
        ]
        res = calculate_linearity(obs, unit="g")
        # E = (I - I0) - L = (1000.5 - 0.1) - 1000.0 = 0.4
        pt = res["point_results"][0]
        assert pt["indication_error"] == pytest.approx(0.4)


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — EVALUATOR: PASS / FAIL SCENARIOS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEvaluatorPassFail:

    def _evaluator(self):
        return OIMLRuleEvaluator()

    def _inst(self, e=1.0, cls="Class III"):
        return {"verification_scale_interval": e, "accuracy_class": cls, "unit": "g"}

    # ── Pass cases ────────────────────────────────────────────────────────────

    def test_all_points_within_mpe_pass(self):
        # 200g load → MPE = 0.5g; error = 0.3g → PASS
        calc = {
            "unit": "g", "max_absolute_error": 0.3,
            "point_results": [{"index": 1, "load": 200.0, "corrected_error": 0.3, "direction": "increasing"}],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.PASS

    def test_error_exactly_at_mpe_passes(self):
        # 200g → MPE = 0.5g; error = 0.5g → PASS (boundary)
        calc = {
            "unit": "g", "max_absolute_error": 0.5,
            "point_results": [{"index": 1, "load": 200.0, "corrected_error": 0.5, "direction": "increasing"}],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.PASS

    def test_mixed_directions_all_pass(self):
        calc = {
            "unit": "g", "max_absolute_error": 0.4,
            "point_results": [
                {"index": 1, "load": 200.0, "corrected_error":  0.3, "direction": "increasing"},
                {"index": 2, "load": 200.0, "corrected_error": -0.4, "direction": "decreasing"},
            ],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.PASS

    # ── Fail cases ────────────────────────────────────────────────────────────

    def test_single_point_exceeds_mpe_fails(self):
        # 200g → MPE = 0.5g; error = 1.2g → FAIL
        calc = {
            "unit": "g", "max_absolute_error": 1.2,
            "point_results": [{"index": 1, "load": 200.0, "corrected_error": 1.2, "direction": "increasing"}],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.FAIL
        assert res.failed_count == 1

    def test_one_failing_point_in_many_causes_overall_fail(self):
        calc = {
            "unit": "g", "max_absolute_error": 0.9,
            "point_results": [
                {"index": 1, "load": 200.0,  "corrected_error": 0.3, "direction": "increasing"},  # PASS 0.5e MPE
                {"index": 2, "load": 1000.0, "corrected_error": 0.9, "direction": "increasing"},  # PASS 1.0e MPE
                {"index": 3, "load": 200.0,  "corrected_error": 0.9, "direction": "decreasing"},  # FAIL 0.5e MPE
            ],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.FAIL
        # Find the per-point details
        lin_eval = next(e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-MPE")
        failed_pts = [d for d in (lin_eval.details or []) if not d["passed"]]
        assert len(failed_pts) == 1
        assert failed_pts[0]["load"] == pytest.approx(200.0)
        assert failed_pts[0]["direction"] == "decreasing"

    def test_negative_corrected_error_magnitude_evaluated(self):
        # Negative error must be evaluated by its absolute value
        calc = {
            "unit": "g", "max_absolute_error": 0.8,
            "point_results": [{"index": 1, "load": 200.0, "corrected_error": -0.8, "direction": "decreasing"}],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        # |−0.8| ≤ 0.5? No → FAIL
        assert res.overall_outcome == EvaluationOutcome.FAIL

    # ── MPE bracket transition test ───────────────────────────────────────────

    def test_bracket_transition_500e_boundary(self):
        # At exactly 500g (500e), MPE = 0.5g; error = 0.4g → PASS
        # At 501g (501e), MPE = 1.0g; error = 0.4g → PASS (larger bracket)
        inst = self._inst()
        for load, err, expected in [(500.0, 0.4, "PASS"), (501.0, 0.4, "PASS"), (500.0, 0.6, "FAIL")]:
            calc = {
                "unit": "g", "max_absolute_error": err,
                "point_results": [{"index": 1, "load": load, "corrected_error": err, "direction": "increasing"}],
            }
            res = self._evaluator().evaluate_test("linearity", calc, inst)
            assert res.overall_outcome.value == expected, \
                f"load={load}, err={err}: expected {expected}, got {res.overall_outcome.value}"

    def test_beyond_old_hard_max_e_no_longer_fails_lookup(self):
        # load=15000g (15000e) was previously outside hard max_e=10000 → silent wrong MPE
        # Now last bracket is open-ended → must return 1.5e, evaluation must succeed
        calc = {
            "unit": "g", "max_absolute_error": 1.0,
            "point_results": [{"index": 1, "load": 15000.0, "corrected_error": 1.0, "direction": "increasing"}],
        }
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        # 1.0g ≤ 1.5g MPE → PASS (not INCOMPLETE or error)
        assert res.overall_outcome == EvaluationOutcome.PASS

    # ── INCOMPLETE cases ──────────────────────────────────────────────────────

    def test_no_scale_interval_gives_incomplete(self):
        inst = {"accuracy_class": "Class III", "unit": "g"}  # no e
        calc = {"unit": "g", "max_absolute_error": 0.3, "point_results": []}
        res = self._evaluator().evaluate_test("linearity", calc, inst)
        assert res.overall_outcome == EvaluationOutcome.INCOMPLETE

    def test_no_point_results_gives_incomplete(self):
        calc = {"unit": "g", "max_absolute_error": 0.0, "point_results": []}
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.INCOMPLETE

    # ── In-service MPE doubling ───────────────────────────────────────────────

    def test_in_service_doubles_mpe_affects_pass_fail(self):
        # At 200g, initial MPE = 0.5g; error = 0.8g → FAIL (initial)
        # In-service MPE = 1.0g; error = 0.8g → PASS
        calc = {
            "unit": "g", "max_absolute_error": 0.8,
            "point_results": [{"index": 1, "load": 200.0, "corrected_error": 0.8, "direction": "increasing"}],
        }
        evaluator = self._evaluator()
        inst = self._inst()

        res_initial = evaluator.evaluate_test("linearity", calc, inst, service_type="initial")
        assert res_initial.overall_outcome == EvaluationOutcome.FAIL

        res_service = evaluator.evaluate_test("linearity", calc, inst, service_type="service")
        assert res_service.overall_outcome == EvaluationOutcome.PASS


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — EVALUATOR: HYSTERESIS CRITERION (Clause 3.5.1 ¶2)
# ═══════════════════════════════════════════════════════════════════════════════

class TestHysteresisCriterion:
    """
    OIML R-76-1:2006 Clause 3.5.1 ¶2:
    The difference between increasing and decreasing indications at the same
    load shall not exceed the absolute value of MPE(L).
    Evaluated only when hysteresis_results are present.
    """

    def _evaluator(self):
        return OIMLRuleEvaluator()

    def _inst(self):
        return {"verification_scale_interval": 1.0, "accuracy_class": "Class III", "unit": "g"}

    def _make_calc(self, hys_results, point_results=None, max_abs_error=0.1):
        return {
            "unit": "g",
            "max_absolute_error": max_abs_error,
            "hysteresis_results": hys_results,
            "point_results": point_results or [
                {"index": 1, "load": 200.0, "corrected_error": 0.1, "direction": "increasing"},
                {"index": 2, "load": 200.0, "corrected_error": 0.1, "direction": "decreasing"},
            ],
        }

    def test_no_hysteresis_data_means_no_hysteresis_rule(self):
        calc = self._make_calc(hys_results=[])
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        hys_eval = next((e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS"), None)
        assert hys_eval is None

    def test_hysteresis_within_mpe_passes(self):
        # 200g → MPE = 0.5g; hysteresis = 0.3g → PASS
        hys = [{"load": 200.0, "increasing_indication": 200.2, "decreasing_indication": 200.5, "hysteresis": 0.3}]
        calc = self._make_calc(hys)
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        hys_eval = next(e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS")
        assert hys_eval.outcome == EvaluationOutcome.PASS

    def test_hysteresis_exactly_at_mpe_passes(self):
        # 200g → MPE = 0.5g; hysteresis = 0.5g → PASS (boundary)
        hys = [{"load": 200.0, "increasing_indication": 200.0, "decreasing_indication": 200.5, "hysteresis": 0.5}]
        calc = self._make_calc(hys)
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        hys_eval = next(e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS")
        assert hys_eval.outcome == EvaluationOutcome.PASS

    def test_hysteresis_exceeds_mpe_fails(self):
        # 200g → MPE = 0.5g; hysteresis = 0.8g → FAIL
        hys = [{"load": 200.0, "increasing_indication": 200.0, "decreasing_indication": 200.8, "hysteresis": 0.8}]
        calc = self._make_calc(hys)
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        hys_eval = next(e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS")
        assert hys_eval.outcome == EvaluationOutcome.FAIL

    def test_hysteresis_fail_causes_overall_fail(self):
        # Indication errors all pass, but hysteresis fails → overall FAIL
        hys = [{"load": 200.0, "increasing_indication": 200.0, "decreasing_indication": 200.9, "hysteresis": 0.9}]
        calc = self._make_calc(hys)
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        assert res.overall_outcome == EvaluationOutcome.FAIL

    def test_multiple_load_points_hysteresis_all_pass(self):
        hys = [
            {"load": 200.0,  "increasing_indication": 200.0,  "decreasing_indication": 200.3,  "hysteresis": 0.3},
            {"load": 1000.0, "increasing_indication": 1000.0, "decreasing_indication": 1000.5, "hysteresis": 0.5},
        ]
        calc = self._make_calc(hys, max_abs_error=0.5)
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        hys_eval = next(e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS")
        assert hys_eval.outcome == EvaluationOutcome.PASS

    def test_hysteresis_reported_in_evaluation_details(self):
        hys = [{"load": 200.0, "increasing_indication": 200.0, "decreasing_indication": 200.3, "hysteresis": 0.3}]
        calc = self._make_calc(hys)
        res = self._evaluator().evaluate_test("linearity", calc, self._inst())
        hys_eval = next(e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS")
        assert hys_eval.details is not None
        d = hys_eval.details[0]
        assert d["load"] == pytest.approx(200.0)
        assert d["hysteresis"] == pytest.approx(0.3)
        assert d["mpe_mass"] == pytest.approx(0.5)
        assert d["passed"] is True


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — INTEGRATION: FULL PIPELINE (calculator → evaluator)
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullPipelineIntegration:
    """Run calculate_linearity then evaluate — mirrors the real service flow."""

    def test_good_data_full_pass(self):
        obs = [
            {"load": 0.0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 500.0,  "indication": 500.2,  "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.3, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.4, "direction": "decreasing"},
            {"load": 500.0,  "indication": 500.3,  "direction": "decreasing"},
            {"load": 0.0,    "indication": 0.0,    "direction": "decreasing"},
        ]
        calc = calculate_linearity(obs, unit="g", instrument_e=1.0)
        inst = {"verification_scale_interval": 1.0, "accuracy_class": "Class III", "unit": "g"}
        res = OIMLRuleEvaluator().evaluate_test("linearity", calc, inst)
        assert res.overall_outcome == EvaluationOutcome.PASS
        # Hysteresis evaluated (both directions present)
        hys_eval = next((e for e in res.evaluations if e.rule_id == "OIML-R76-1-LIN-HYS"), None)
        assert hys_eval is not None
        assert hys_eval.outcome == EvaluationOutcome.PASS

    def test_gross_data_entry_error_full_fail(self):
        """Mirrors the real TEST-9A699FCA scenario that caused the FAIL report."""
        obs = [
            {"load": 1000.0, "indication": 500.0,  "direction": "increasing"},
            {"load": 1001.0, "indication": 1000.0, "direction": "increasing"},
            {"load": 1000.0, "indication": 2000.0, "direction": "increasing"},
            {"load": 999.0,  "indication": 1000.0, "direction": "decreasing"},
            {"load": 849.0,  "indication": 500.0,  "direction": "decreasing"},
        ]
        calc = calculate_linearity(obs, unit="g", instrument_e=1.0)
        assert calc["max_absolute_error"] == pytest.approx(1000.0)
        inst = {"verification_scale_interval": 1.0, "accuracy_class": "Class III", "unit": "g"}
        res = OIMLRuleEvaluator().evaluate_test("linearity", calc, inst)
        assert res.overall_outcome == EvaluationOutcome.FAIL

    def test_demo_session_data_still_passes(self):
        """Mirrors TEST-DEMO-LIN-02 — Class II, e=0.1g. Must still PASS after fixes."""
        obs = [
            {"load": 0.0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 500.0,  "indication": 500.03, "direction": "increasing"},
            {"load": 1000.0, "indication": 1000.06,"direction": "increasing"},
            {"load": 2000.0, "indication": 2000.08,"direction": "increasing"},
            {"load": 3000.0, "indication": 3000.05,"direction": "increasing"},
            {"load": 2000.0, "indication": 2000.09,"direction": "decreasing"},
            {"load": 1000.0, "indication": 1000.07,"direction": "decreasing"},
            {"load": 0.0,    "indication": 0.01,   "direction": "decreasing"},
        ]
        calc = calculate_linearity(obs, unit="g", instrument_e=0.1)
        inst = {"verification_scale_interval": 0.1, "accuracy_class": "Class II", "unit": "g"}
        res = OIMLRuleEvaluator().evaluate_test("linearity", calc, inst)
        assert res.overall_outcome == EvaluationOutcome.PASS

