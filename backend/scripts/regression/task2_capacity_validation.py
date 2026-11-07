"""
TASK 2 -- Instrument Capacity Validation
Run from project root (nawi directory).
"""
import sys, os
# 3 levels up from backend/scripts/regression/ => nawi/
ROOT = str(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from calculation_engine.linearity.calculator import calculate_linearity

PASS_COUNT = 0
FAIL_COUNT = 0
BUG_COUNT  = 0

def report(test_id, description, expected, actual_ok, actual_msg):
    global PASS_COUNT, FAIL_COUNT, BUG_COUNT
    status = "PASS" if actual_ok == expected else "FAIL"
    if status == "FAIL":
        FAIL_COUNT += 1
        if expected == "REJECTED":
            BUG_COUNT += 1
    else:
        PASS_COUNT += 1
    print("  [{}] {}: {}".format(status, test_id, description))
    print("         Expected: {}  |  Got: {}".format(expected, actual_msg))

print("=" * 65)
print("TASK 2 -- INSTRUMENT CAPACITY VALIDATION")
print("Instrument: DS-3000, max_capacity=3000 g, e=1.0 g, Class III")
print("=" * 65)

def run_calc(observations, e=1.0, accuracy_class="III"):
    """Returns (ok, msg)."""
    try:
        result = calculate_linearity(
            observations=observations,
            unit="g",
            instrument_e=e,
        )
        pts = result if isinstance(result, dict) else {}
        lps = pts.get('load_points', pts.get('point_results', []))
        return True, "Returned result with {} load points".format(len(lps))
    except (ValueError, Exception) as ex:
        return False, "{}: {}".format(type(ex).__name__, ex)

def obs(load, indication):
    return {"load": load, "indication": indication, "direction": "increasing"}

GOOD_OBS_3000 = [obs(0,0.0), obs(500,499.9), obs(1000,1000.1), obs(2000,1999.8), obs(3000,2999.9)]
OBS_3001  = [obs(0,0.0), obs(500,499.9), obs(3001,3001.0)]
OBS_10000 = [obs(0,0.0), obs(10000,10000.0)]

print("\n--- Test A: load=3000 g (at max capacity) ---")
ok, msg = run_calc(GOOD_OBS_3000)
report("T2-A", "load=3000 g on 3000 g instrument", "ACCEPTED", "ACCEPTED" if ok else "REJECTED", msg)

print("\n--- Test B: load=3001 g (1 g over capacity) ---")
ok, msg = run_calc(OBS_3001)
report("T2-B", "load=3001 g on 3000 g instrument", "REJECTED", "REJECTED" if not ok else "ACCEPTED", msg)

print("\n--- Test C: load=10000 g ---")
ok, msg = run_calc(OBS_10000)
report("T2-C", "load=10000 g on 3000 g instrument", "REJECTED", "REJECTED" if not ok else "ACCEPTED", msg)

print()
print("=" * 65)
print("TASK 2 SUMMARY: PASS={}  FAIL={}  BUG-4 hits={}".format(PASS_COUNT, FAIL_COUNT, BUG_COUNT))
if BUG_COUNT:
    print("WARNING BUG-4 CONFIRMED: Over-capacity loads are NOT rejected.")
    print("   REQUIRED FIX: Add capacity guard before calculate_linearity() call.")
else:
    print("OK All capacity guards working correctly.")
print("=" * 65)
