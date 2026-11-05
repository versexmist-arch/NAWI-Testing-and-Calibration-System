"""
Precision and display formatting utilities for metrology calculations.
Preserves internal calculation fidelity while formatting outputs cleanly for operators.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import Union, Optional


def sanitize_number(val: Union[float, int, str, Decimal, None]) -> Optional[Decimal]:
    """Safely convert numeric input to Decimal without precision loss."""
    if val is None or val == "":
        return None
    try:
        return Decimal(str(val).strip())
    except Exception:
        raise ValueError(f"Cannot parse value '{val}' as a valid number.")


def format_decimal(
    val: Union[float, int, Decimal, None],
    decimal_places: int = 4,
    strip_trailing_zeros: bool = False
) -> str:
    """Format decimal for display with standard round-half-up."""
    if val is None:
        return "N/A"
    dec = Decimal(str(val))
    pattern = "0." + "0" * decimal_places if decimal_places > 0 else "0"
    rounded = dec.quantize(Decimal(pattern), rounding=ROUND_HALF_UP)
    res = f"{rounded:f}"
    if strip_trailing_zeros and "." in res:
        res = res.rstrip("0").rstrip(".")
    return res


def display_rounded(val: Union[float, int, Decimal, None], decimals: int = 4) -> Optional[float]:
    """Returns float rounded to specified decimal places for UI charts / displays."""
    if val is None:
        return None
    dec = Decimal(str(val))
    pattern = "0." + "0" * decimals if decimals > 0 else "0"
    return float(dec.quantize(Decimal(pattern), rounding=ROUND_HALF_UP))

