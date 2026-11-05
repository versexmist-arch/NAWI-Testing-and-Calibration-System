"""
Unit conversion and validation utilities for metrological calculation.
Supported mass units: mg, g, kg, t.
"""
from typing import Dict, Union
from decimal import Decimal, ROUND_HALF_UP

# Conversion factors to grams (canonical internal base for comparison if needed)
UNIT_TO_GRAM: Dict[str, Decimal] = {
    "mg": Decimal("0.001"),
    "g": Decimal("1.0"),
    "kg": Decimal("1000.0"),
    "t": Decimal("1000000.0"),
}

SUPPORTED_UNITS = list(UNIT_TO_GRAM.keys())


def normalize_unit_str(unit: str) -> str:
    """Normalize unit string representation."""
    cleaned = (unit or "").strip().lower()
    if cleaned in ("gram", "grams", "gm"):
        return "g"
    if cleaned in ("kilogram", "kilograms", "kgs"):
        return "kg"
    if cleaned in ("milligram", "milligrams"):
        return "mg"
    if cleaned in ("tonne", "tonnes", "metric ton", "t"):
        return "t"
    return cleaned


def convert_unit(value: Union[float, Decimal, int], from_unit: str, to_unit: str) -> Decimal:
    """
    Accurately convert a mass value between supported units using Decimal.
    """
    u_from = normalize_unit_str(from_unit)
    u_to = normalize_unit_str(to_unit)

    if u_from not in UNIT_TO_GRAM:
        raise ValueError(f"Unsupported source unit: '{from_unit}'. Supported: {SUPPORTED_UNITS}")
    if u_to not in UNIT_TO_GRAM:
        raise ValueError(f"Unsupported target unit: '{to_unit}'. Supported: {SUPPORTED_UNITS}")

    if u_from == u_to:
        return Decimal(str(value))

    dec_val = Decimal(str(value))
    # Convert from -> grams -> to
    in_grams = dec_val * UNIT_TO_GRAM[u_from]
    converted = in_grams / UNIT_TO_GRAM[u_to]
    return converted


def normalize_to_grams(value: Union[float, Decimal, int], unit: str) -> Decimal:
    """Convert any supported mass quantity to grams."""
    return convert_unit(value, unit, "g")


def calculate_scale_intervals(max_capacity: float, e: float) -> int:
    """
    Calculate number of verification scale intervals: n = Max / e.
    OIML R-76-1 Clause 2.1.2.
    """
    if e <= 0:
        raise ValueError("Verification scale interval 'e' must be strictly positive.")
    if max_capacity <= 0:
        raise ValueError("Maximum capacity must be strictly positive.")
    return int(Decimal(str(max_capacity)) / Decimal(str(e)))

