"""
Repeatability Test Calculator.
Compliant with OIML R-76-1:2006 Clause 3.6.1 and OIML R-76-2 Clause A.4.4.1.
"""
from typing import Dict, List, Any, Optional
import math
from decimal import Decimal
from ..common.precision import sanitize_number, display_rounded
from ..common.units import normalize_unit_str

CALCULATION_VERSION = "OIML-R76-REP-v1.0"
METHOD_DESCRIPTION = "OIML R-76-1:2006 Clause 3.6.1 Repeatability of Weighing Instruments"


def calculate_repeatability(
    test_load: float,
    observations: List[Dict[str, Any]],
    unit: str,
    instrument_e: Optional[float] = None
) -> Dict[str, Any]:
    """
    Calculate repeatability metrics: range (max - min), mean, standard deviation, and per-run errors.

    Parameters:
    - test_load: Applied constant reference load across repeated cycles.
    - observations: List of dicts containing 'run_number' and 'indication'.
    - unit: Measurement unit (e.g., 'g', 'kg').
    - instrument_e: Verification scale interval e (optional).

    Returns:
    - Dict with statistics (range, mean, std dev, variance), per-run errors, and calculation metadata.
    """
    if test_load <= 0:
        raise ValueError("Test load must be strictly positive.")
    if not observations:
        raise ValueError("At least one repeated reading is required.")
    if len(observations) < 2:
        raise ValueError("Repeatability testing requires at least two repeated weighings.")

    clean_unit = normalize_unit_str(unit)
    L = sanitize_number(test_load)
    e_dec = sanitize_number(instrument_e) if instrument_e else None

    indications = []
    run_records = []

    for idx, obs in enumerate(observations):
        run_no = obs.get("run_number", idx + 1)
        ind_val = sanitize_number(obs.get("indication"))
        if ind_val is None:
            raise ValueError(f"Run #{run_no} is missing a valid numeric indication.")

        error_val = ind_val - L
        run_records.append({
            "run_number": int(run_no),
            "indication": float(ind_val),
            "reference_load": float(L),
            "error": float(error_val),
            "unit": clean_unit,
        })
        indications.append(ind_val)

    n = len(indications)
    max_val = max(indications)
    min_val = min(indications)
    repeatability_range = max_val - min_val  # Range = I_max - I_min

    # Mean: I_bar = (1/n) * sum(I_i)
    total_sum = sum(indications)
    mean_val = total_sum / Decimal(str(n))

    # Sample variance and standard deviation: s = sqrt( (1 / (n - 1)) * sum((I_i - mean)^2) )
    sum_sq_diff = sum((val - mean_val) ** 2 for val in indications)
    variance_val = sum_sq_diff / Decimal(str(n - 1)) if n > 1 else Decimal("0")
    std_dev_val = Decimal(str(math.sqrt(float(variance_val))))

    # Enrich run records with deviation from mean
    for r in run_records:
        dev_from_mean = Decimal(str(r["indication"])) - mean_val
        r["deviation_from_mean"] = float(dev_from_mean)

    result = {
        "calculation_version": CALCULATION_VERSION,
        "method": METHOD_DESCRIPTION,
        "test_category": "repeatability",
        "reference_load": float(L),
        "unit": clean_unit,
        "runs_count": n,
        "min_indication": float(min_val),
        "max_indication": float(max_val),
        "repeatability_range": float(repeatability_range),  # Max - Min
        "mean_indication": float(mean_val),
        "sample_variance": float(variance_val),
        "standard_deviation": float(std_dev_val),
        "mean_error": float(mean_val - L),
        "max_absolute_error": float(max(abs(r["error"]) for r in run_records)),
        "run_records": run_records,
        "verification_scale_interval_e": float(e_dec) if e_dec else None,
    }

    if e_dec and e_dec > 0:
        result["repeatability_range_in_e"] = float(repeatability_range / e_dec)

    return result

