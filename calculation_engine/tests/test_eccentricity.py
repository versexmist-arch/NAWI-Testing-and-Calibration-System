import pytest
from calculation_engine.eccentricity import calculate_eccentricity


def test_eccentricity_standard_run():
    # Test load 1000g, verification interval e = 1g
    observations = [
        {"position_id": "pos_1", "position_name": "Center", "indication": 1000.0, "zero_indication": 0.0},
        {"position_id": "pos_2", "position_name": "Front-Left", "indication": 1000.2, "zero_indication": 0.0},
        {"position_id": "pos_3", "position_name": "Back-Left", "indication": 999.8, "zero_indication": 0.0},
        {"position_id": "pos_4", "position_name": "Back-Right", "indication": 1000.1, "zero_indication": 0.0},
        {"position_id": "pos_5", "position_name": "Front-Right", "indication": 999.9, "zero_indication": 0.0},
    ]

    res = calculate_eccentricity(test_load=1000.0, unit="g", observations=observations, instrument_e=1.0)

    assert res["test_category"] == "eccentricity"
    assert res["center_error"] == 0.0
    assert res["positions_evaluated"] == 5
    # Max deviation is Front-Left (+0.2) or Back-Left (-0.2), absolute = 0.2
    assert pytest.approx(res["max_absolute_eccentricity_deviation"], 0.0001) == 0.2
    assert pytest.approx(res["max_absolute_indication_error"], 0.0001) == 0.2


def test_eccentricity_zero_offset():
    # Non-zero zero_indication
    observations = [
        {"position_id": "center", "position_name": "Center", "indication": 500.5, "zero_indication": 0.5},
        {"position_id": "pos_2", "position_name": "Corner 1", "indication": 501.0, "zero_indication": 0.5},
    ]

    res = calculate_eccentricity(test_load=500.0, unit="g", observations=observations)
    # Center net indication = 500.5 - 0.5 = 500.0 -> center error = 0.0
    assert res["center_error"] == 0.0
    # Corner 1 net indication = 501.0 - 0.5 = 500.5 -> error = +0.5
    assert pytest.approx(res["max_absolute_eccentricity_deviation"], 0.0001) == 0.5


def test_eccentricity_validation_errors():
    with pytest.raises(ValueError, match="strictly greater than 0"):
        calculate_eccentricity(0, "g", [{"position_id": "p1", "indication": 10}])

    with pytest.raises(ValueError, match="at least a Center position"):
        calculate_eccentricity(100, "g", [{"position_id": "p1", "indication": 100}])
