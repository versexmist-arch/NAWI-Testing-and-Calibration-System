import pytest
from calculation_engine.repeatability import calculate_repeatability


def test_repeatability_10_runs():
    # 10 runs around 1500g
    readings = [
        1500.0, 1500.1, 1499.9, 1500.0, 1500.2,
        1500.0, 1499.8, 1500.1, 1500.0, 1500.1
    ]
    observations = [{"run_number": idx + 1, "indication": val} for idx, val in enumerate(readings)]

    res = calculate_repeatability(test_load=1500.0, observations=observations, unit="g", instrument_e=0.1)

    assert res["runs_count"] == 10
    assert pytest.approx(res["min_indication"], 0.0001) == 1499.8
    assert pytest.approx(res["max_indication"], 0.0001) == 1500.2
    # Repeatability range = 1500.2 - 1499.8 = 0.4g
    assert pytest.approx(res["repeatability_range"], 0.0001) == 0.4
    # Mean = sum(readings) / 10 = 15000.2 / 10 = 1500.02
    assert pytest.approx(res["mean_indication"], 0.0001) == 1500.02
    # Std dev > 0
    assert res["standard_deviation"] > 0
    # Repeatability range in e = 0.4 / 0.1 = 4.0
    assert pytest.approx(res["repeatability_range_in_e"], 0.0001) == 4.0


def test_repeatability_invalid_inputs():
    with pytest.raises(ValueError, match="strictly positive"):
        calculate_repeatability(test_load=0, observations=[{"indication": 10}, {"indication": 10}], unit="g")

    with pytest.raises(ValueError, match="at least two"):
        calculate_repeatability(test_load=100, observations=[{"indication": 100}], unit="g")

