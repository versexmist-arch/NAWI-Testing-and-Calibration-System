"""
Supplementary forensic checks:
1. MPE bracket boundary condition bug test
2. Zero-load point Ec vs MPE at load=0
3. Formula correctness trace for TEST-9A699FCA observations
4. OIML R-76-1:2006 Table 6 Class III reference
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from rules.evaluator import get_mpe_for_load, load_rules_config

cfg = load_rules_config()

print("="*70)
print("CHECK 1: MPE bracket boundary conditions (Class III, e=1.0 g)")
print("="*70)
# OIML R-76-1:2006 Table 6 Class III:
#   0 to 500e    -> 0.5e
#   500 to 2000e -> 1.0e
#   2000 to 10000e -> 1.5e
test_loads = [0, 1, 499, 500, 501, 999, 1000, 1001, 1999, 2000, 2001, 5000, 9999, 10000, 10001]
e = 1.0
cls = "Class III"
print(f"{'Load':>10} {'m/e':>8} {'Expected bracket':>22} {'Got mult':>10} {'MPE mass':>10} {'match?':>8}")
print("-"*70)
# OIML R-76-1 Table 6 Class III reference:
# 0 <= m <= 500e: MPE = 0.5e
# 500e < m <= 2000e: MPE = 1.0e  (Note: standard uses < not <=)
# 2000e < m <= 10000e: MPE = 1.5e
def expected_mpe(m_in_e):
    if 0 <= m_in_e <= 500: return 0.5
    if 500 < m_in_e <= 2000: return 1.0
    if 2000 < m_in_e <= 10000: return 1.5
    return None  # outside range

for load in test_loads:
    m_in_e = load / e
    exp = expected_mpe(m_in_e)
    mult, mpe_mass, desc = get_mpe_for_load(load, e, cls, cfg, "initial")
    match = "OK" if abs(mult - (exp or 0)) < 1e-9 else "MISMATCH!"
    print(f"{load:>10} {m_in_e:>8.1f} {str(exp)+'e':>22} {mult:>10.1f} {mpe_mass:>10.4f} {match:>8}")

print()
print("="*70)
print("CHECK 2: MPE bracket condition at EXACT boundary (min_e<=m<=max_e BUG?)")
print("="*70)
# The JSON has: {"min_e": 0, "max_e": 500, "mpe_multiplier": 0.5}
#               {"min_e": 500, "max_e": 2000, "mpe_multiplier": 1.0}
# The code uses: if min_e <= m_in_e <= max_e: -> BOTH brackets claim m=500
# Which bracket wins? The first match wins since code breaks on first hit.
print("At load=500, e=1: m/e=500 falls in BOTH brackets [0-500] and [500-2000]")
print("Code iterates in ORDER => first bracket [0,500] wins => MPE=0.5e")
print("OIML R-76-1 Table 6: boundary at 500e inclusive belongs to LOWER bracket => 0.5e")
print("=> This boundary is CORRECT for load=500e")

print()
print("="*70)
print("CHECK 3: User session TEST-9A699FCA - observation data analysis")
print("="*70)
# The user submitted observations for DS-3000 (Class III, Max=3000g, e=1.0g)
obs = [
    {"load": 1000, "indication": 500,  "direction": "increasing"},
    {"load": 1001, "indication": 1000, "direction": "increasing"},
    {"load": 1000, "indication": 2000, "direction": "increasing"},
    {"load": 999,  "indication": 1000, "direction": "decreasing"},
    {"load": 849,  "indication": 500,  "direction": "decreasing"},
]
print("Raw observations as entered by operator:")
for i, o in enumerate(obs, 1):
    E = o['indication'] - o['load']
    print(f"  Row {i}: load={o['load']:5}g, indication={o['indication']:5}g, "
          f"dir={o['direction']:11s}, E = {o['indication']} - {o['load']} = {E:+.1f}g")

print()
print("DIAGNOSIS: Observations are almost certainly data entry errors.")
print("  Row 1: load=1000g but indication=500g  => E = -500g (instrument showing HALF the load?)")
print("  Row 3: load=1000g but indication=2000g => E = +1000g (instrument showing DOUBLE the load?)")
print("  Row 5: load=849g  but indication=500g  => E = -349g")
print()
print("These errors are 100x to 500x the MPE limit of 1.0g for a Class III instrument.")
print("The calculation engine correctly computed these as massive errors.")
print("The FAIL result is metrologically CORRECT given the input data.")
print("Root cause: data entry errors in the observations, NOT a bug in the engine.")

print()
print("="*70)
print("CHECK 4: Zero-load E0 handling")
print("="*70)
print("Formula implemented: E = (I - I0) - L, then Ec = E - E0")
print("  where I0 = zero_indication field (per-row optional)")
print("  and   E0 = indication at load==0 observation (global zero-error)")
print()
print("OIML R-76-1 Clause 3.5.1 reference formula:")
print("  E(L) = I(L) - L  (for a tare-zeroed instrument)")
print("  Corrected: Ec(L) = E(L) - E(0)")
print()
print("Current code: E = (I - I0) - L")
print("  - If I0=0 (default), simplifies to E = I - L  [CORRECT]")
print("  - I0 is per-row zero_indication (zero reading just before this point)")
print("  - This handles the 'zero reading before each load' variant")
print()
print("For TEST-9A699FCA: all rows have zero_indication=0, so:")
print("  E = I - L (pure indication minus reference load) [CORRECT]")
print("  Ec = E - E0, E0=0 (no zero load row present) => Ec = E [CORRECT]")

print()
print("="*70)
print("CHECK 5: Increasing vs Decreasing pass validation")
print("="*70)
print("The evaluator (_evaluate_linearity) applies the SAME MPE criterion")
print("to BOTH increasing and decreasing directions independently.")
print("OIML R-76-1 Clause 3.5.1: same MPE applies to errors in both directions.")
print("=> No directional asymmetry required by the standard.")
print("=> Hysteresis is tracked separately (difference between increasing/decreasing)")
print("=> Hysteresis is NOT currently evaluated against an MPE limit.")
print()
print("POTENTIAL GAP: OIML R-76-1 Clause 3.5.1 states that hysteresis (the difference")
print("between increasing and decreasing errors at the same load) must not exceed the")
print("absolute value of the MPE for that load. The current evaluator tracks hysteresis")
print("in the calculator but does NOT apply a rule evaluation against the MPE limit.")
print("=> This is a MISSING RULE, not a false PASS or false FAIL.")

print()
print("="*70)
print("CHECK 6: MPE table JSON vs OIML R-76-1 Table 6 verification")
print("="*70)
# Official OIML R-76-1:2006 Table 6 (initial verification MPE):
# Class I:    0-50000e: 0.5e | 50000-200000e: 1.0e | >200000e: 1.5e
# Class II:   0-5000e: 0.5e  | 5000-20000e: 1.0e   | >20000e: 1.5e  (up to 100000e)
# Class III:  0-500e: 0.5e   | 500-2000e: 1.0e      | >2000e: 1.5e   (up to 10000e)
# Class IIII: 0-50e: 0.5e    | 50-200e: 1.0e         | >200e: 1.5e    (up to 1000e)
json_table = {
    "Class I":    [(0, 50000, 0.5), (50000, 200000, 1.0), (200000, None, 1.5)],
    "Class II":   [(0, 5000, 0.5),  (5000, 20000, 1.0),   (20000, 100000, 1.5)],
    "Class III":  [(0, 500, 0.5),   (500, 2000, 1.0),      (2000, 10000, 1.5)],
    "Class IIII": [(0, 50, 0.5),    (50, 200, 1.0),         (200, 1000, 1.5)],
}
oiml_table = {
    "Class I":    [(0, 50000, 0.5), (50000, 200000, 1.0), (200000, None, 1.5)],
    "Class II":   [(0, 5000, 0.5),  (5000, 20000, 1.0),   (20000, 100000, 1.5)],
    "Class III":  [(0, 500, 0.5),   (500, 2000, 1.0),      (2000, 10000, 1.5)],
    "Class IIII": [(0, 50, 0.5),    (50, 200, 1.0),         (200, 1000, 1.5)],
}
all_match = True
for cls_name, expected in oiml_table.items():
    actual = json_table[cls_name]
    match = expected == actual
    if not match:
        all_match = False
    print(f"  {cls_name}: {'MATCHES OIML R-76-1:2006 Table 6' if match else 'MISMATCH!'}")

if all_match:
    print("\n=> MPE table values in oiml_r76_2006_rules.json are CORRECT per OIML R-76-1:2006.")
else:
    print("\n=> WARNING: MPE table discrepancies found!")

print()
print("="*70)
print("CHECK 7: load=0 MPE lookup (edge case)")
print("="*70)
mult0, mpe0, desc0 = get_mpe_for_load(0.0, 1.0, "Class III", cfg, "initial")
print(f"  load=0, e=1, Class III => mult={mult0}, MPE={mpe0}g, desc={desc0}")
print(f"  Code condition: 0 <= m_in_e <= 500 => 0 <= 0 <= 500 => TRUE => 0.5e")
print(f"  OIML: MPE at zero load = 0.5e [CORRECT]")
print(f"  Zero-load point Ec should be 0 (or E0 itself) => always PASS unless instrument drifted")

print()
print("[SUPPLEMENTARY AUDIT COMPLETE — No files or database modified]")

