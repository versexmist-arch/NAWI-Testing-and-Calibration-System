"""
TASK 3 -- MPE Boundary Testing
Run from project root (nawi directory).
"""
import sys, os
ROOT = str(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from rules import get_mpe_for_load

PASS_COUNT = 0
FAIL_COUNT = 0
e = 1.0
CLASS = "Class III"

CASES = [
    # (test_id, description,           load_g,   exp_mult, exp_mpe_g)
    ("T3-01", "n=0   (zero load)",      0.0,     0.5, 0.5),
    ("T3-02", "n=499 (below B1 edge)",  499.0,   0.5, 0.5),
    ("T3-03", "n=500 (B1 upper edge)",  500.0,   0.5, 0.5),
    ("T3-04", "n=501 (B2 lower edge)",  501.0,   1.0, 1.0),
    ("T3-05", "n=1000 (mid B2)",       1000.0,   1.0, 1.0),
    ("T3-06", "n=1999 (below B2 top)", 1999.0,   1.0, 1.0),
    ("T3-07", "n=2000 (B2 upper edge)",2000.0,   1.0, 1.0),
    ("T3-08", "n=2001 (B3 lower edge)",2001.0,   1.5, 1.5),
    ("T3-09", "n=5000 (mid B3)",       5000.0,   1.5, 1.5),
    ("T3-10", "n=10000 (old hard cap)",10000.0,  1.5, 1.5),
    ("T3-11", "n=50000 (way beyond)",  50000.0,  1.5, 1.5),
]

print("=" * 75)
print("TASK 3 -- MPE BOUNDARY TESTING  (Class III, e=1.0 g)")
print("=" * 75)
print("{:<8} {:<10} {:<10} {:<10} {:<8} {:<8} {}".format(
    "TestID","Load(g)","ExpMult","ActMult","ExpMPE","ActMPE","Status"))
print("-" * 75)

for test_id, desc, load_g, exp_mult, exp_mpe in CASES:
    try:
        result = get_mpe_for_load(load_g, e, CLASS)
        # get_mpe_for_load returns a tuple (mpe_in_e, mpe_in_mass, description)
        if isinstance(result, tuple):
            act_mult, act_mpe, _desc = result
        else:
            act_mult = result.get("multiplier", result.get("mpe_in_e"))
            act_mpe  = result.get("mpe_mass", result.get("mpe_in_mass"))

        ok = (abs(float(act_mult) - exp_mult) < 1e-9) and (abs(float(act_mpe) - exp_mpe) < 1e-9)
        status = "PASS" if ok else "FAIL"
        if ok:
            PASS_COUNT += 1
        else:
            FAIL_COUNT += 1
        print("{:<8} {:<10.1f} {:<10.1f} {:<10.1f} {:<8.2f} {:<8.2f} {}".format(
            test_id, load_g, exp_mult, float(act_mult), exp_mpe, float(act_mpe), status))
        if not ok:
            print("         -- {}".format(desc))
    except Exception as ex:
        FAIL_COUNT += 1
        print("{:<8} {:<10.1f} {:<10.1f} {:<10} {:<8.2f} {:<8} FAIL".format(
            test_id, load_g, exp_mult, "ERROR", exp_mpe, "ERROR"))
        print("         -- {}: {}".format(type(ex).__name__, ex))

print("-" * 75)
print("TASK 3 SUMMARY: PASS={}  FAIL={}".format(PASS_COUNT, FAIL_COUNT))
if FAIL_COUNT == 0:
    print("OK All MPE boundaries correct.")
else:
    print("WARNING MPE boundary failures detected -- review bracket definitions.")
print("=" * 75)
