"""
OIML R-76 Rule Evaluation Engine.
Evaluates calculation results against versioned OIML rules with full explainability.
Never invents compliance outcomes for unverified rules.
"""
import json
import os
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from .definitions import (
    EvaluationOutcome,
    RuleVerificationStatus,
    RuleItemEvaluation,
    RuleEvaluationSummary,
)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "configurations", "oiml_r76_2006_rules.json")


def load_rules_config() -> Dict[str, Any]:
    """Load configurable rule definitions from JSON storage."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_class_name(cls_str: Optional[str]) -> str:
    """Normalize class designation to 'Class I', 'Class II', etc."""
    if not cls_str:
        return "Class III"  # Default common commercial class if unspecified
    s = cls_str.strip()
    if s.lower() in ("class i", "i", "special"):
        return "Class I"
    if s.lower() in ("class ii", "ii", "high"):
        return "Class II"
    if s.lower() in ("class iii", "iii", "medium"):
        return "Class III"
    if s.lower() in ("class iiii", "iiii", "ordinary", "iv", "class iv"):
        return "Class IIII"
    return "Class III"


def get_mpe_for_load(
    load: float,
    e: float,
    accuracy_class: str,
    rules_config: Optional[Dict[str, Any]] = None,
    service_type: str = "initial"
) -> Tuple[float, float, str]:
    """
    Calculate Maximum Permissible Error (MPE) for a given load and instrument class.

    Returns: (mpe_in_e, mpe_in_mass_units, step_description)

    Raises:
        ValueError: If 'e' is not positive, if load is negative, or if no OIML
                    Table 6 bracket covers the given load/e ratio. A no-match
                    condition means the instrument is operating outside the ranges
                    defined in the standard for its declared accuracy class.
    """
    if e <= 0:
        raise ValueError("Verification scale interval 'e' must be strictly positive to determine MPE.")
    if load < 0:
        raise ValueError(f"Load must be non-negative; received {load}.")

    config = rules_config or load_rules_config()
    lin_rule = next((r for r in config.get("rules", []) if r.get("rule_id") == "OIML-R76-1-LIN-MPE"), None)
    if not lin_rule or "mpe_table" not in lin_rule:
        raise RuntimeError("OIML R-76 MPE rule table configuration is missing.")

    cls_norm = normalize_class_name(accuracy_class)
    table = lin_rule["mpe_table"].get(cls_norm)
    if not table:
        # Fallback to Class III when an unrecognised class string is supplied
        table = lin_rule["mpe_table"]["Class III"]
        cls_norm = "Class III"

    m_in_e = load / e

    # Sentinel: None means no bracket was matched yet
    multiplier: Optional[float] = None
    bracket_desc = ""

    for step in table:
        min_e = step["min_e"]
        max_e = step["max_e"]
        mult = step["mpe_multiplier"]

        if max_e is None:
            # Open-ended upper bracket: matches all m > min_e
            if m_in_e > min_e:
                multiplier = mult
                bracket_desc = f"m > {min_e}e"
                break
        else:
            if min_e <= m_in_e <= max_e:
                multiplier = mult
                bracket_desc = f"{min_e}e ≤ m ≤ {max_e}e"
                break

    # --- BUG-1 FIX ---
    # If no bracket matched, the load/e ratio falls outside every defined step.
    # With open-ended last brackets (max_e=null) this should only occur when
    # load=0 is below the first bracket's min_e, which cannot happen since all
    # tables start at min_e=0. The guard is kept as a strict safety net.
    if multiplier is None:
        raise ValueError(
            f"Load {load} (m/e = {m_in_e:.2f}e) falls outside all OIML R-76-1:2006 Table 6 "
            f"MPE brackets for {cls_norm}. Verify that the test load does not exceed the "
            f"instrument's rated maximum capacity."
        )

    # If in-service, MPE is doubled per OIML R-76-1 Clause 3.5.2
    if service_type.lower() == "service":
        multiplier = multiplier * 2.0
        bracket_desc += " [In-Service 2×MPE]"

    mpe_in_mass = multiplier * e
    return multiplier, mpe_in_mass, f"{bracket_desc} -> ±{multiplier}e (±{mpe_in_mass:.4f})"


class OIMLRuleEvaluator:
    """Evaluates test session calculation outputs against OIML R-76 requirements."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config = config_dict or load_rules_config()
        self.rule_version = self.config.get("version", "OIML-R76-2006-v1.0")

    def evaluate_test(
        self,
        test_category: str,
        calc_result: Dict[str, Any],
        instrument_metadata: Dict[str, Any],
        service_type: str = "initial"
    ) -> RuleEvaluationSummary:
        category = test_category.lower().strip()
        e_val = instrument_metadata.get("verification_scale_interval") or instrument_metadata.get("e")
        acc_class = instrument_metadata.get("accuracy_class", "Class III")
        unit = instrument_metadata.get("unit", calc_result.get("unit", "g"))

        evaluations: List[RuleItemEvaluation] = []

        if category == "eccentricity":
            evaluations = self._evaluate_eccentricity(calc_result, e_val, acc_class, unit, service_type)
        elif category == "linearity":
            evaluations = self._evaluate_linearity(calc_result, e_val, acc_class, unit, service_type)
        elif category == "repeatability":
            evaluations = self._evaluate_repeatability(calc_result, e_val, acc_class, unit, service_type)
        else:
            evaluations.append(
                RuleItemEvaluation(
                    rule_id="OIML-UNKNOWN-CAT",
                    rule_name="Unrecognized Test Category",
                    source_reference="N/A",
                    rule_version=self.rule_version,
                    verification_status=RuleVerificationStatus.PENDING_VERIFICATION,
                    outcome=EvaluationOutcome.NOT_APPLICABLE,
                    applicable_criterion="N/A",
                    observed_value="N/A",
                    tolerance_limit="N/A",
                    explanation=f"No OIML evaluation criteria found for test category '{test_category}'.",
                )
            )

        # Aggregate counts
        pass_count = sum(1 for e in evaluations if e.outcome == EvaluationOutcome.PASS)
        fail_count = sum(1 for e in evaluations if e.outcome == EvaluationOutcome.FAIL)
        incomplete_count = sum(1 for e in evaluations if e.outcome == EvaluationOutcome.INCOMPLETE)
        na_count = sum(1 for e in evaluations if e.outcome == EvaluationOutcome.NOT_APPLICABLE)
        pending_count = sum(1 for e in evaluations if e.outcome == EvaluationOutcome.PENDING_VERIFICATION)

        if fail_count > 0:
            overall = EvaluationOutcome.FAIL
            summary = f"Evaluation FAILED: {fail_count} requirement(s) violated."
        elif incomplete_count > 0:
            overall = EvaluationOutcome.INCOMPLETE
            summary = f"Evaluation INCOMPLETE: {incomplete_count} evaluation step(s) missing required parameters."
        elif pending_count > 0 and pass_count == 0:
            overall = EvaluationOutcome.PENDING_VERIFICATION
            summary = f"Evaluation PENDING VERIFICATION: Contains unverified regulatory rules."
        else:
            overall = EvaluationOutcome.PASS
            summary = f"Evaluation PASSED: All {pass_count} applicable verified criteria satisfied."

        return RuleEvaluationSummary(
            overall_outcome=overall,
            rule_version=self.rule_version,
            rules_evaluated_count=len(evaluations),
            passed_count=pass_count,
            failed_count=fail_count,
            incomplete_count=incomplete_count,
            not_applicable_count=na_count,
            pending_verification_count=pending_count,
            evaluations=evaluations,
            summary_text=summary,
        )

    def _evaluate_eccentricity(
        self,
        calc_result: Dict[str, Any],
        e_val: Optional[float],
        acc_class: str,
        unit: str,
        service_type: str
    ) -> List[RuleItemEvaluation]:
        rule_def = next(
            (r for r in self.config.get("rules", []) if r.get("rule_id") == "OIML-R76-1-ECC-3.6.2"),
            None
        )
        if not rule_def:
            return []

        if not e_val or e_val <= 0:
            return [
                RuleItemEvaluation(
                    rule_id=rule_def["rule_id"],
                    rule_name=rule_def["name"],
                    source_reference=rule_def["source_reference"],
                    rule_version=self.rule_version,
                    verification_status=RuleVerificationStatus.VERIFIED,
                    outcome=EvaluationOutcome.INCOMPLETE,
                    applicable_criterion="Indication errors at all eccentric positions ≤ MPE(L)",
                    observed_value=f"Max deviation: {calc_result.get('max_absolute_eccentricity_deviation', 'N/A')} {unit}",
                    tolerance_limit="MPE unknown: missing verification scale interval (e)",
                    explanation="Verification scale interval 'e' is required to calculate OIML MPE tolerance.",
                )
            ]

        test_load = calc_result.get("reference_load", 0.0)
        mult, mpe_mass, desc = get_mpe_for_load(test_load, e_val, acc_class, self.config, service_type)

        pos_results = calc_result.get("position_results", [])
        sub_details = []
        all_passed = True
        max_observed_err = 0.0

        for pos in pos_results:
            err = abs(pos.get("indication_error", 0.0))
            if err > max_observed_err:
                max_observed_err = err
            passed = err <= (mpe_mass + 1e-9)
            if not passed:
                all_passed = False
            sub_details.append({
                "position": pos.get("position_name"),
                "error": pos.get("indication_error"),
                "mpe": mpe_mass,
                "passed": passed,
            })

        outcome = EvaluationOutcome.PASS if all_passed else EvaluationOutcome.FAIL
        expl = (
            f"All {len(pos_results)} positions satisfied MPE limit of ±{mpe_mass:.4f} {unit} ({mult}e)."
            if all_passed
            else f"One or more positions exceeded MPE limit of ±{mpe_mass:.4f} {unit}. Max error: {max_observed_err:.4f} {unit}."
        )

        return [
            RuleItemEvaluation(
                rule_id=rule_def["rule_id"],
                rule_name=rule_def["name"],
                source_reference=rule_def["source_reference"],
                rule_version=self.rule_version,
                verification_status=RuleVerificationStatus.VERIFIED,
                outcome=outcome,
                applicable_criterion=f"|E_i| ≤ MPE ({desc})",
                observed_value=f"Max error = {max_observed_err:.4f} {unit}",
                tolerance_limit=f"±{mpe_mass:.4f} {unit} (±{mult}e)",
                explanation=expl,
                details=sub_details,
            )
        ]

    def _evaluate_linearity(
        self,
        calc_result: Dict[str, Any],
        e_val: Optional[float],
        acc_class: str,
        unit: str,
        service_type: str
    ) -> List[RuleItemEvaluation]:
        """
        Evaluate linearity test results against OIML R-76-1:2006 requirements.

        Two criteria are applied when data are available:

        1. Per-point indication error criterion (Clause 3.5.1, Table 6):
           |Ec(L)| ≤ MPE(L)  for every load point in both directions.

        2. Hysteresis criterion (Clause 3.5.1 paragraph 2):
           |I_inc(L) − I_dec(L)| ≤ |MPE(L)|  for every load common to both
           increasing and decreasing sequences.
           This criterion is evaluated only when the calculator produced
           hysteresis_results (i.e., both directions were observed at the same load).
           If only one direction was measured the criterion is not applicable.
        """
        rule_def = next(
            (r for r in self.config.get("rules", []) if r.get("rule_id") == "OIML-R76-1-LIN-MPE"),
            None
        )
        if not rule_def:
            return []

        if not e_val or e_val <= 0:
            return [
                RuleItemEvaluation(
                    rule_id=rule_def["rule_id"],
                    rule_name=rule_def["name"],
                    source_reference=rule_def["source_reference"],
                    rule_version=self.rule_version,
                    verification_status=RuleVerificationStatus.VERIFIED,
                    outcome=EvaluationOutcome.INCOMPLETE,
                    applicable_criterion="|E_c| ≤ MPE(L)",
                    observed_value=f"Max abs error: {calc_result.get('max_absolute_error', 'N/A')} {unit}",
                    tolerance_limit="MPE unknown: missing verification scale interval (e)",
                    explanation="Verification scale interval 'e' is required to calculate OIML MPE for load points.",
                )
            ]

        point_results = calc_result.get("point_results", [])
        if not point_results:
            return [
                RuleItemEvaluation(
                    rule_id=rule_def["rule_id"],
                    rule_name=rule_def["name"],
                    source_reference=rule_def["source_reference"],
                    rule_version=self.rule_version,
                    verification_status=RuleVerificationStatus.VERIFIED,
                    outcome=EvaluationOutcome.INCOMPLETE,
                    applicable_criterion="|E_c| ≤ MPE(L)",
                    observed_value="0 points",
                    tolerance_limit="N/A",
                    explanation="No observation points available to evaluate.",
                )
            ]

        evaluations: List[RuleItemEvaluation] = []

        # ── Criterion 1: per-point indication error ──────────────────────────
        sub_details = []
        all_passed = True
        failed_count = 0
        worst_ratio = 0.0

        for pt in point_results:
            load = pt.get("load", 0.0)
            corr_err = abs(pt.get("corrected_error", 0.0))

            try:
                mult, mpe_mass, desc = get_mpe_for_load(load, e_val, acc_class, self.config, service_type)
            except ValueError as exc:
                # Load is outside all defined Table 6 brackets — treat as INCOMPLETE
                evaluations.append(
                    RuleItemEvaluation(
                        rule_id=rule_def["rule_id"],
                        rule_name=rule_def["name"],
                        source_reference=rule_def["source_reference"],
                        rule_version=self.rule_version,
                        verification_status=RuleVerificationStatus.VERIFIED,
                        outcome=EvaluationOutcome.INCOMPLETE,
                        applicable_criterion="|E_c| ≤ MPE(L)",
                        observed_value=f"Load = {load} {unit}",
                        tolerance_limit="No applicable bracket",
                        explanation=f"MPE lookup failed: {exc}",
                    )
                )
                return evaluations

            pt_passed = corr_err <= (mpe_mass + 1e-9)
            if not pt_passed:
                all_passed = False
                failed_count += 1
            ratio = corr_err / mpe_mass if mpe_mass > 0 else 0.0
            if ratio > worst_ratio:
                worst_ratio = ratio

            sub_details.append({
                "point_index": pt.get("index"),
                "load": load,
                "direction": pt.get("direction"),
                "corrected_error": pt.get("corrected_error"),
                "mpe_mass": mpe_mass,
                "mpe_in_e": mult,
                "passed": pt_passed,
                "criterion": desc,
            })

        outcome_1 = EvaluationOutcome.PASS if all_passed else EvaluationOutcome.FAIL
        expl_1 = (
            f"All {len(point_results)} test points are within their applicable OIML Table 6 MPE limits."
            if all_passed
            else f"{failed_count} of {len(point_results)} load points exceeded the applicable MPE limit."
        )

        evaluations.append(
            RuleItemEvaluation(
                rule_id=rule_def["rule_id"],
                rule_name=rule_def["name"],
                source_reference=rule_def["source_reference"],
                rule_version=self.rule_version,
                verification_status=RuleVerificationStatus.VERIFIED,
                outcome=outcome_1,
                applicable_criterion=f"Table 6 step boundaries ({acc_class}): |Ec| ≤ MPE(L)",
                observed_value=f"Max error = {calc_result.get('max_absolute_error', 0.0):.4f} {unit} ({worst_ratio * 100:.1f}% of MPE)",
                tolerance_limit=f"Dynamic MPE (0.5e to 1.5e depending on load bracket)",
                explanation=expl_1,
                details=sub_details,
            )
        )

        # ── Criterion 2: hysteresis (Clause 3.5.1 ¶2) ───────────────────────
        # Only evaluated when both increasing and decreasing sequences share load
        # points — i.e., when the calculator produced hysteresis_results entries.
        hysteresis_results = calc_result.get("hysteresis_results", [])
        if hysteresis_results:
            hys_sub = []
            hys_all_passed = True
            hys_failed = 0
            max_hys_ratio = 0.0

            for hpt in hysteresis_results:
                h_load = hpt.get("load", 0.0)
                h_diff = abs(hpt.get("hysteresis", 0.0))

                try:
                    h_mult, h_mpe, h_desc = get_mpe_for_load(
                        h_load, e_val, acc_class, self.config, service_type
                    )
                except ValueError:
                    # If load is out of range, skip hysteresis check for this point
                    continue

                h_passed = h_diff <= (h_mpe + 1e-9)
                if not h_passed:
                    hys_all_passed = False
                    hys_failed += 1
                h_ratio = h_diff / h_mpe if h_mpe > 0 else 0.0
                if h_ratio > max_hys_ratio:
                    max_hys_ratio = h_ratio

                hys_sub.append({
                    "load": h_load,
                    "increasing_indication": hpt.get("increasing_indication"),
                    "decreasing_indication": hpt.get("decreasing_indication"),
                    "hysteresis": h_diff,
                    "mpe_mass": h_mpe,
                    "mpe_in_e": h_mult,
                    "passed": h_passed,
                    "criterion": h_desc,
                })

            if hys_sub:
                hys_outcome = EvaluationOutcome.PASS if hys_all_passed else EvaluationOutcome.FAIL
                hys_expl = (
                    f"Hysteresis at all {len(hys_sub)} common load point(s) is within |MPE(L)|."
                    if hys_all_passed
                    else f"Hysteresis exceeded |MPE(L)| at {hys_failed} of {len(hys_sub)} common load point(s)."
                )
                max_hys_val = calc_result.get("max_hysteresis") or 0.0
                evaluations.append(
                    RuleItemEvaluation(
                        rule_id="OIML-R76-1-LIN-HYS",
                        rule_name="Hysteresis Limit Between Increasing and Decreasing Loads",
                        source_reference="OIML R-76-1:2006 Clause 3.5.1 ¶2",
                        rule_version=self.rule_version,
                        verification_status=RuleVerificationStatus.VERIFIED,
                        outcome=hys_outcome,
                        applicable_criterion=f"|I_inc − I_dec| ≤ |MPE(L)| at each common load ({acc_class})",
                        observed_value=f"Max hysteresis = {max_hys_val:.4f} {unit} ({max_hys_ratio * 100:.1f}% of MPE)",
                        tolerance_limit=f"Dynamic |MPE(L)| (0.5e to 1.5e depending on load bracket)",
                        explanation=hys_expl,
                        details=hys_sub,
                    )
                )

        return evaluations

    def _evaluate_repeatability(
        self,
        calc_result: Dict[str, Any],
        e_val: Optional[float],
        acc_class: str,
        unit: str,
        service_type: str
    ) -> List[RuleItemEvaluation]:
        rule_def = next(
            (r for r in self.config.get("rules", []) if r.get("rule_id") == "OIML-R76-1-REP-3.6.1"),
            None
        )
        evals = []
        if not rule_def:
            return evals

        rep_range = calc_result.get("repeatability_range")
        if rep_range is None:
            evals.append(
                RuleItemEvaluation(
                    rule_id=rule_def["rule_id"],
                    rule_name=rule_def["name"],
                    source_reference=rule_def["source_reference"],
                    rule_version=self.rule_version,
                    verification_status=RuleVerificationStatus.VERIFIED,
                    outcome=EvaluationOutcome.INCOMPLETE,
                    applicable_criterion="(I_max - I_min) ≤ |MPE(L)|",
                    observed_value="N/A",
                    tolerance_limit="N/A",
                    explanation="No repeatability range calculated.",
                )
            )
            return evals

        if not e_val or e_val <= 0:
            evals.append(
                RuleItemEvaluation(
                    rule_id=rule_def["rule_id"],
                    rule_name=rule_def["name"],
                    source_reference=rule_def["source_reference"],
                    rule_version=self.rule_version,
                    verification_status=RuleVerificationStatus.VERIFIED,
                    outcome=EvaluationOutcome.INCOMPLETE,
                    applicable_criterion="(I_max - I_min) ≤ |MPE(L)|",
                    observed_value=f"Range = {rep_range:.4f} {unit}",
                    tolerance_limit="MPE unknown: missing verification scale interval (e)",
                    explanation="Verification scale interval 'e' is required to calculate OIML MPE for repeatability.",
                )
            )
            return evals

        test_load = calc_result.get("reference_load", 0.0)
        mult, mpe_mass, desc = get_mpe_for_load(test_load, e_val, acc_class, self.config, service_type)

        passed = rep_range <= (mpe_mass + 1e-9)
        outcome = EvaluationOutcome.PASS if passed else EvaluationOutcome.FAIL
        expl = (
            f"Repeatability span ({rep_range:.4f} {unit}) is within MPE limit of {mpe_mass:.4f} {unit} ({mult}e)."
            if passed
            else f"Repeatability span ({rep_range:.4f} {unit}) exceeds MPE limit of {mpe_mass:.4f} {unit} ({mult}e)."
        )

        evals.append(
            RuleItemEvaluation(
                rule_id=rule_def["rule_id"],
                rule_name=rule_def["name"],
                source_reference=rule_def["source_reference"],
                rule_version=self.rule_version,
                verification_status=RuleVerificationStatus.VERIFIED,
                outcome=outcome,
                applicable_criterion=f"(I_max - I_min) ≤ |MPE| ({desc})",
                observed_value=f"Range = {rep_range:.4f} {unit} (Min: {calc_result.get('min_indication')}, Max: {calc_result.get('max_indication')})",
                tolerance_limit=f"≤ {mpe_mass:.4f} {unit} ({mult}e)",
                explanation=expl,
            )
        )

        # Include demonstration pending verification rule to show the system safely flags unverified criteria
        exp_rule = next(
            (r for r in self.config.get("rules", []) if r.get("rule_id") == "OIML-R76-EXPERIMENTAL-DRAFT-2026"),
            None
        )
        if exp_rule:
            evals.append(
                RuleItemEvaluation(
                    rule_id=exp_rule["rule_id"],
                    rule_name=exp_rule["name"],
                    source_reference=exp_rule["source_reference"],
                    rule_version=exp_rule["version"],
                    verification_status=RuleVerificationStatus.PENDING_VERIFICATION,
                    outcome=EvaluationOutcome.PENDING_VERIFICATION,
                    applicable_criterion="Standard deviation / Mean < 0.0001 (Proposed)",
                    observed_value=f"Std Dev = {calc_result.get('standard_deviation', 0.0):.6f}",
                    tolerance_limit="Draft proposed threshold - Unverified",
                    explanation="Rule marked as PENDING VERIFICATION. Under metrological integrity guidelines, unverified rules do not render authoritative compliance outcomes.",
                )
            )

        return evals

