"""
TASK 4 -- Hysteresis Testing
Run from project root (nawi directory).
"""
import sys, os
ROOT = str(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from calculation_engine.linearity.calculator import calculate_linearity
from rules import OIMLRuleEvaluator

PASS_COUNT = 0
FAIL_COUNT = 0
e = 1.0
CLASS = "Class III"
LOAD_TEST = 200.0   # n=200, MPE=0.5 g
HYS_RULE = "OIML-R76-1-LIN-HYS"

INSTRUMENT_META = {
    "accuracy_class": CLASS,
    "verification_scale_interval": e,
    "max_capacity": 3000.0,
    "unit": "g",
}

def run_pipeline(obs_list):
    calc_dict = calculate_linearity(
        observations=obs_list,
        unit="g",
        instrument_e=e,
    )
    evaluator = OIMLRuleEvaluator()
    summary = evaluator.evaluate_test(
        test_category="linearity",
        calc_result=calc_dict,
        instrument_metadata=INSTRUMENT_META,
        service_type="initial",
    )
    evals_by_id = {ev.rule_id: ev for ev in summary.evaluations}
    return calc_dict, summary, evals_by_id


def report(test_id, description, expected_outcome, expected_hys_present,
           actual_outcome, actual_hys_present, extra=""):
    global PASS_COUNT, FAIL_COUNT
    # EvaluationOutcome is a str-Enum, so both .value and str() work
    actual_str = actual_outcome.value if hasattr(actual_outcome, 'value') else str(actual_outcome)
    outcome_ok = actual_str == expected_outcome
    hys_ok     = actual_hys_present == expected_hys_present
    ok = outcome_ok and hys_ok
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print("  [{}] {}: {}".format(status, test_id, description))
    print("         Outcome  expected={:<6}  actual={}".format(expected_outcome, actual_str))
    print("         HYS rule expected={:<4}   actual={}".format(
        "YES" if expected_hys_present else "NO",
        "YES" if actual_hys_present else "NO"))
    if extra:
        print("         {}".format(extra))
    if not ok:
        if not outcome_ok:
            print("         MISMATCH: Outcome!")
        if not hys_ok:
            print("         MISMATCH: Hysteresis rule presence!")

print("=" * 65)
print("TASK 4 -- HYSTERESIS TESTING  (Class III, e=1.0 g, load=200 g)")
print("         MPE at 200 g = 0.5 x 1.0 g = 0.5 g")
print("=" * 65)

# T4-A: Both directions, hysteresis 0.3 g < MPE 0.5 g => PASS
print("\n--- T4-A: Hysteresis=0.3 g < MPE=0.5 g ---")
obs_a = [
    {"load": 0,          "indication": 0.0,   "direction": "increasing"},
    {"load": 0,          "indication": 0.0,   "direction": "decreasing"},
    {"load": LOAD_TEST,  "indication": 200.1, "direction": "increasing"},
    {"load": LOAD_TEST,  "indication": 199.8, "direction": "decreasing"},
]
try:
    _, sum_a, evals_a = run_pipeline(obs_a)
    hys_ev = evals_a.get(HYS_RULE)
    report("T4-A", "hysteresis=0.3 g, MPE=0.5 g",
           "PASS", True, sum_a.overall_outcome, HYS_RULE in evals_a,
           "HYS eval: outcome={}".format(getattr(hys_ev,'outcome','?') if hys_ev else 'absent'))
except Exception as ex:
    FAIL_COUNT += 1
    print("  [FAIL] T4-A: Exception -- {}: {}".format(type(ex).__name__, ex))

# T4-B: Hysteresis exactly 0.5 g = MPE => PASS (at boundary)
print("\n--- T4-B: Hysteresis=0.5 g = MPE=0.5 g (boundary) ---")
obs_b = [
    {"load": 0,          "indication": 0.0,    "direction": "increasing"},
    {"load": 0,          "indication": 0.0,    "direction": "decreasing"},
    {"load": LOAD_TEST,  "indication": 200.25, "direction": "increasing"},
    {"load": LOAD_TEST,  "indication": 199.75, "direction": "decreasing"},
]
try:
    _, sum_b, evals_b = run_pipeline(obs_b)
    hys_ev = evals_b.get(HYS_RULE)
    report("T4-B", "hysteresis=0.5 g, MPE=0.5 g (boundary)",
           "PASS", True, sum_b.overall_outcome, HYS_RULE in evals_b,
           "HYS eval: outcome={}".format(getattr(hys_ev,'outcome','?') if hys_ev else 'absent'))
except Exception as ex:
    FAIL_COUNT += 1
    print("  [FAIL] T4-B: Exception -- {}: {}".format(type(ex).__name__, ex))

# T4-C: Hysteresis 0.6 g > MPE 0.5 g => FAIL
print("\n--- T4-C: Hysteresis=0.6 g > MPE=0.5 g ---")
obs_c = [
    {"load": 0,          "indication": 0.0,   "direction": "increasing"},
    {"load": 0,          "indication": 0.0,   "direction": "decreasing"},
    {"load": LOAD_TEST,  "indication": 200.3, "direction": "increasing"},
    {"load": LOAD_TEST,  "indication": 199.7, "direction": "decreasing"},
]
try:
    _, sum_c, evals_c = run_pipeline(obs_c)
    hys_ev = evals_c.get(HYS_RULE)
    report("T4-C", "hysteresis=0.6 g, MPE=0.5 g",
           "FAIL", True, sum_c.overall_outcome, HYS_RULE in evals_c,
           "HYS eval: outcome={}".format(getattr(hys_ev,'outcome','?') if hys_ev else 'absent'))
except Exception as ex:
    FAIL_COUNT += 1
    print("  [FAIL] T4-C: Exception -- {}: {}".format(type(ex).__name__, ex))

# T4-D: Increasing direction only => no HYS rule expected
print("\n--- T4-D: Increasing direction only ---")
obs_d = [
    {"load": 0,          "indication": 0.0,   "direction": "increasing"},
    {"load": LOAD_TEST,  "indication": 200.1, "direction": "increasing"},
]
try:
    _, sum_d, evals_d = run_pipeline(obs_d)
    report("T4-D", "increasing-only observations",
           "PASS", False, sum_d.overall_outcome, HYS_RULE in evals_d)
except Exception as ex:
    FAIL_COUNT += 1
    print("  [FAIL] T4-D: Exception -- {}: {}".format(type(ex).__name__, ex))

# T4-E: Decreasing direction only => no HYS rule expected
print("\n--- T4-E: Decreasing direction only ---")
obs_e = [
    {"load": 0,          "indication": 0.0,   "direction": "decreasing"},
    {"load": LOAD_TEST,  "indication": 199.9, "direction": "decreasing"},
]
try:
    _, sum_e, evals_e = run_pipeline(obs_e)
    report("T4-E", "decreasing-only observations",
           "PASS", False, sum_e.overall_outcome, HYS_RULE in evals_e)
except Exception as ex:
    FAIL_COUNT += 1
    print("  [FAIL] T4-E: Exception -- {}: {}".format(type(ex).__name__, ex))

print()
print("=" * 65)
print("TASK 4 SUMMARY: PASS={}  FAIL={}".format(PASS_COUNT, FAIL_COUNT))
if FAIL_COUNT == 0:
    print("OK All hysteresis scenarios correct.")
else:
    print("WARNING Hysteresis failures detected.")
print("=" * 65)
