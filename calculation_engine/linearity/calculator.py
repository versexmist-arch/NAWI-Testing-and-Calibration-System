"""
Linearity and Weighing Performance Test Calculator.
Compliant with OIML R-76-1:2006 Clause 3.5.1 (Errors of indication) and Clause A.4.4 (Weighing test).
"""
from typing import Dict, List, Any, Optional
from decimal import Decimal
from ..common.precision import sanitize_number, display_rounded
from ..common.units import normalize_unit_str

CALCULATION_VERSION = "OIML-R76-LIN-v1.0"
METHOD_DESCRIPTION = "OIML R-76-1:2006 Clause 3.5.1 Determination of Errors and Weighing Performance"


def calculate_linearity(
    observations: List[Dict[str, Any]],
    unit: str,
    instrument_e: Optional[float] = None,
    use_changeover_points: bool = False
) -> Dict[str, Any]:
    """
    Calculate errors of indication, corrected errors, and hysteresis across load points.

    Parameters:
    - observations: List of dictionaries containing:
        - load: Reference test load.
        - indication: Measured indication.
        - direction: 'increasing' or 'decreasing' (default 'increasing').
        - zero_indication: (optional) Zero reading before or at start.
        - delta_load: (optional) Additional weight for changeover turning point.
    - unit: Measurement unit (e.g., 'g', 'kg').
    - instrument_e: Verification scale interval e (optional).
    - use_changeover_points: Whether turning-point / changeover method is applied.

    Returns:
    - Dict with per-point errors, hysteresis, summary extrema, and calculation trace.
    """
    if not observations:
        raise ValueError("At least one load observation is required for linearity testing.")

    clean_unit = normalize_unit_str(unit)
    e_dec = sanitize_number(instrument_e) if instrument_e else None

    # Step 1: Detect zero-load error (E0) if any observation has load == 0.
    #
    # E0 is the indication error at zero load: E0 = I(0) - 0 = I(0).
    # Per OIML R-76-1:2006 Clause 3.5.1, the corrected error is defined as:
    #   Ec(L) = E(L) - E(0)
    # This means Ec at the zero-load point itself is always 0 by definition:
    #   Ec(0) = E(0) - E(0) = 0
    # This is mathematically correct — the zero point is the reference.
    # It is NOT a calculation error that the zero-load point shows Ec = 0;
    # the zero-load error E(0) is separately reported as 'zero_load_error'.
    zero_error = Decimal("0")
    for obs in observations:
        load_val = sanitize_number(obs.get("load"))
        if load_val == Decimal("0"):
            ind = sanitize_number(obs.get("indication"))
            if ind is not None:
                zero_error = ind
                break

    point_results = []
    max_pos_error = Decimal("-999999999")
    max_neg_error = Decimal("999999999")
    max_abs_error = Decimal("0")

    # Map for hysteresis calculation: load -> {'increasing': ind, 'decreasing': ind}
    hysteresis_map: Dict[str, Dict[str, Decimal]] = {}

    for idx, obs in enumerate(observations):
        L = sanitize_number(obs.get("load"))
        I = sanitize_number(obs.get("indication"))
        if L is None or I is None:
            raise ValueError(f"Observation row #{idx + 1} has missing load or indication.")

        direction = str(obs.get("direction", "increasing")).strip().lower()
        if direction not in ("increasing", "decreasing"):
            direction = "increasing"

        I0 = sanitize_number(obs.get("zero_indication")) or Decimal("0")
        delta_L = sanitize_number(obs.get("delta_load")) or Decimal("0")

        # Error computation
        if use_changeover_points and e_dec:
            # OIML R-76-1 Clause A.4.4.3: P = I + 0.5e - ΔL, E = P - L
            P = I + (Decimal("0.5") * e_dec) - delta_L
            E = P - L
        else:
            # Direct indication error: E = (I - I0) - L
            E = (I - I0) - L

        # Corrected error: Ec = E - E0
        Ec = E - zero_error
        abs_Ec = abs(Ec)

        if Ec > max_pos_error:
            max_pos_error = Ec
        if Ec < max_neg_error:
            max_neg_error = Ec
        if abs_Ec > max_abs_error:
            max_abs_error = abs_Ec

        point_dict = {
            "index": idx + 1,
            "load": float(L),
            "indication": float(I),
            "direction": direction,
            "zero_indication": float(I0),
            "delta_load": float(delta_L),
            "indication_error": float(E),
            "corrected_error": float(Ec),
            "abs_corrected_error": float(abs_Ec),
            "unit": clean_unit,
        }

        if e_dec and e_dec > 0:
            point_dict["load_in_e"] = float(L / e_dec)
            point_dict["corrected_error_in_e"] = float(Ec / e_dec)

        point_results.append(point_dict)

        # Track for hysteresis
        load_key = str(L)
        if load_key not in hysteresis_map:
            hysteresis_map[load_key] = {}
        hysteresis_map[load_key][direction] = I

    # Calculate hysteresis differences
    max_hysteresis = Decimal("0")
    hysteresis_points = []
    for l_key, dir_data in hysteresis_map.items():
        if "increasing" in dir_data and "decreasing" in dir_data:
            diff = abs(dir_data["decreasing"] - dir_data["increasing"])
            if diff > max_hysteresis:
                max_hysteresis = diff
            hysteresis_points.append({
                "load": float(Decimal(l_key)),
                "increasing_indication": float(dir_data["increasing"]),
                "decreasing_indication": float(dir_data["decreasing"]),
                "hysteresis": float(diff),
                "unit": clean_unit,
            })

    if max_pos_error == Decimal("-999999999"):
        max_pos_error = Decimal("0")
    if max_neg_error == Decimal("999999999"):
        max_neg_error = Decimal("0")

    return {
        "calculation_version": CALCULATION_VERSION,
        "method": METHOD_DESCRIPTION,
        "test_category": "linearity",
        "unit": clean_unit,
        "points_count": len(point_results),
        "zero_load_error": float(zero_error),
        "max_positive_error": float(max_pos_error),
        "max_negative_error": float(max_neg_error),
        "max_absolute_error": float(max_abs_error),
        "max_hysteresis": float(max_hysteresis) if hysteresis_points else None,
        "has_hysteresis_data": len(hysteresis_points) > 0,
        "hysteresis_results": hysteresis_points,
        "point_results": point_results,
        "verification_scale_interval_e": float(e_dec) if e_dec else None,
        "use_changeover_points": use_changeover_points,
    }

