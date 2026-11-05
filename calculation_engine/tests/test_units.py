import pytest
from decimal import Decimal
from calculation_engine.common.units import (
    convert_unit,
    normalize_to_grams,
    calculate_scale_intervals,
    normalize_unit_str,
)


def test_unit_normalization():
    assert normalize_unit_str("kg") == "kg"
    assert normalize_unit_str("Grams") == "g"
    assert normalize_unit_str("Milligrams") == "mg"
    assert normalize_unit_str("t") == "t"


def test_unit_conversion():
    # 1 kg = 1000 g
    assert convert_unit(1, "kg", "g") == Decimal("1000.0")
    # 500 mg = 0.5 g
    assert convert_unit(500, "mg", "g") == Decimal("0.5")
    # 2.5 t = 2500 kg
    assert convert_unit(Decimal("2.5"), "t", "kg") == Decimal("2500.0")


def test_unsupported_unit():
    with pytest.raises(ValueError, match="Unsupported source unit"):
        convert_unit(10, "lb", "kg")


def test_calculate_scale_intervals():
    # Max = 3000g, e = 1g -> n = 3000
    assert calculate_scale_intervals(3000, 1) == 3000
    # Max = 220g, e = 0.001g -> n = 220000
    assert calculate_scale_intervals(220, 0.001) == 220000

    with pytest.raises(ValueError, match="strictly positive"):
        calculate_scale_intervals(3000, 0)

