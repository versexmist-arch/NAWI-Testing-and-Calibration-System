import pytest
from calculation_engine.linearity import calculate_linearity


def test_linearity_standard_curve():
    # Weighing test from 0 to 3000g with e = 1g
    observations = [
        {"load": 0.0, "indication": 0.0, "direction": "increasing"},
        {"load": 500.0, "indication": 500.2, "direction": "increasing"},
        {"load": 1000.0, "indication": 1000.5, "direction": "increasing"},
        {"load": 2000.0, "indication": 1999.8, "direction": "increasing"},
        {"load": 3000.0, "indication": 3000.1, "direction": "increasing"},
        # Decreasing points
        {"load": 2000.0, "indication": 2000.0, "direction": "decreasing"},
        {"load": 1000.0, "indication": 1000.6, "direction": "decreasing"},
        {"load": 0.0, "indication": 0.0, "direction": "decreasing"},
    ]

    res = calculate_linearity(observations=observations, unit="g", instrument_e=1.0)

    assert res["points_count"] == 8
    assert res["zero_load_error"] == 0.0
    # Max error was +0.6 at load 1000 (decreasing)
    assert pytest.approx(res["max_positive_error"], 0.0001) == 0.6
    # Min error was -0.2 at load 2000 (increasing, 1999.8 - 2000)
    assert pytest.approx(res["max_negative_error"], 0.0001) == -0.2
    assert pytest.approx(res["max_absolute_error"], 0.0001) == 0.6
    # Hysteresis at 2000: |2000.0 - 1999.8| = 0.2
    # Hysteresis at 1000: |1000.6 - 1000.5| = 0.1
    assert res["has_hysteresis_data"] is True
    assert pytest.approx(res["max_hysteresis"], 0.0001) == 0.2


def test_linearity_zero_correction():
    # If initial zero indication is 0.1, it should correct subsequent points
    observations = [
        {"load": 0.0, "indication": 0.1, "direction": "increasing"},
        {"load": 100.0, "indication": 100.3, "direction": "increasing"},
    ]
    res = calculate_linearity(observations=observations, unit="g")
    assert res["zero_load_error"] == 0.1
    # Point 2 indication error = 100.3 - 100.0 = 0.3. Corrected error = 0.3 - 0.1 = 0.2
    p2 = res["point_results"][1]
    assert pytest.approx(p2["corrected_error"], 0.0001) == 0.2


def test_linearity_empty_validation():
    with pytest.raises(ValueError, match="At least one load observation is required"):
        calculate_linearity(observations=[], unit="g")

