"""
Eccentricity Test Calculator.
Compliant with OIML R-76-1:2006 Clause 3.6.2 and OIML R-76-2 Clause A.4.7.
"""
from typing import Dict, List, Any, Optional
from decimal import Decimal
from ..common.precision import sanitize_number, display_rounded
from ..common.units import normalize_unit_str

CALCULATION_VERSION = "OIML-R76-ECC-v1.0"
METHOD_DESCRIPTION = "OIML R-76-1:2006 Clause 3.6.2 Eccentricity of indication on load receptors"


def calculate_eccentricity(
    test_load: float,
    unit: str,
    observations: List[Dict[str, Any]],
    instrument_e: Optional[float] = None
) -> Dict[str, Any]:
    """
    Execute eccentricity calculations across observed receptor positions.

    Parameters:
    - test_load: Reference load applied at each position (typically 1/3 Max).
    - unit: Measurement unit (e.g., 'g', 'kg').
    - observations: List of observations containing:
        - position_id: e.g. "center", "pos_2", etc.
        - position_name: e.g. "Center", "Front-Left", etc.
        - indication: Measured indication.
        - zero_indication: (optional) Tare/zero indication before loading.
    - instrument_e: Verification scale interval e (optional, for e-relative calculations).

    Returns:
    - Dict with intermediate values, aggregate results, metadata, and calculation trace.
    """
    if test_load <= 0:
        raise ValueError("Test load must be strictly greater than 0.")
    if not observations:
        raise ValueError("At least one position observation is required.")
    if len(observations) < 2:
        raise ValueError("Eccentricity testing requires at least a Center position and one eccentric position.")

    clean_unit = normalize_unit_str(unit)
    L = sanitize_number(test_load)
    e_dec = sanitize_number(instrument_e) if instrument_e else None

    # Find center observation (must be position 1 or have 'center' in id/name)
    center_obs = None
    for obs in observations:
        pid = str(obs.get("position_id", "")).lower()
        pname = str(obs.get("position_name", "")).lower()
        if "center" in pid or "center" in pname or pid in ("1", "pos_1", "p1"):
            center_obs = obs
            break

    if not center_obs:
        # Default to first observation if not explicitly labeled
        center_obs = observations[0]

    # Calculate center error
    I_center = sanitize_number(center_obs.get("indication"))
    if I_center is None:
        raise ValueError("Center position indication is missing or invalid.")
    I0_center = sanitize_number(center_obs.get("zero_indication")) or Decimal("0")
    E_center = (I_center - I0_center) - L

    per_position_results = []
    max_ecc_dev = Decimal("0")
    max_ecc_pos = center_obs.get("position_name", "Center")
    max_ind_error = Decimal("0")

    for obs in observations:
        pos_id = str(obs.get("position_id", ""))
        pos_name = str(obs.get("position_name", pos_id))
        I = sanitize_number(obs.get("indication"))
        if I is None:
            raise ValueError(f"Observation for position '{pos_name}' is missing an indication value.")
        I0 = sanitize_number(obs.get("zero_indication")) or Decimal("0")

        # Indication error: E_i = (I_i - I0_i) - L
        E_i = (I - I0) - L
        # Eccentricity deviation relative to center: ΔE_i = E_i - E_center = (I_i - I0_i) - (I_center - I0_center)
        delta_E = E_i - E_center

        abs_delta_E = abs(delta_E)
        abs_E_i = abs(E_i)

        if abs_delta_E > max_ecc_dev:
            max_ecc_dev = abs_delta_E
            max_ecc_pos = pos_name

        if abs_E_i > max_ind_error:
            max_ind_error = abs_E_i

        pos_data = {
            "position_id": pos_id,
            "position_name": pos_name,
            "reference_load": float(L),
            "indication": float(I),
            "zero_indication": float(I0),
            "indication_error": float(E_i),
            "eccentricity_deviation": float(delta_E),
            "abs_eccentricity_deviation": float(abs_delta_E),
            "unit": clean_unit,
        }

        if e_dec and e_dec > 0:
            pos_data["indication_error_in_e"] = float(E_i / e_dec)
            pos_data["eccentricity_deviation_in_e"] = float(delta_E / e_dec)

        per_position_results.append(pos_data)

    return {
        "calculation_version": CALCULATION_VERSION,
        "method": METHOD_DESCRIPTION,
        "test_category": "eccentricity",
        "reference_load": float(L),
        "unit": clean_unit,
        "center_indication": float(I_center),
        "center_error": float(E_center),
        "max_absolute_eccentricity_deviation": float(max_ecc_dev),
        "max_eccentricity_deviation_position": max_ecc_pos,
        "max_absolute_indication_error": float(max_ind_error),
        "positions_evaluated": len(per_position_results),
        "position_results": per_position_results,
        "verification_scale_interval_e": float(e_dec) if e_dec else None,
    }

