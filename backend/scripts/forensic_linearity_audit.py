"""
Forensic audit script: Linearity test session — read-only DB inspection.
No writes. No modifications.
"""
import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent.parent / "nawi_calibration.db"
print(f"Database: {DB_PATH}\n{'='*70}")

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row

# 1. Find all linearity test sessions
print("\n[1] LINEARITY TEST SESSIONS")
print("-"*70)
sessions = conn.execute("""
    SELECT ts.id, ts.instrument_id, ts.operator_name, ts.status, ts.test_category,
           ts.service_type, ts.test_configuration, ts.created_at, ts.is_demo,
           i.serial_number, i.model, i.accuracy_class, i.max_capacity,
           i.verification_scale_interval, i.unit
    FROM test_sessions ts
    JOIN instruments i ON ts.instrument_id = i.id
    WHERE ts.test_category = 'linearity'
    ORDER BY ts.created_at
""").fetchall()

for s in sessions:
    print(f"  Session ID   : {s['id']}")
    print(f"  Instrument   : {s['serial_number']} / {s['model']}")
    print(f"  Accuracy Class: {s['accuracy_class']}")
    print(f"  Max Capacity : {s['max_capacity']} {s['unit']}")
    print(f"  e (interval) : {s['verification_scale_interval']} {s['unit']}")
    print(f"  Operator     : {s['operator_name']}")
    print(f"  Status       : {s['status']}")
    print(f"  Service Type : {s['service_type']}")
    print(f"  Is Demo      : {s['is_demo']}")
    cfg = json.loads(s['test_configuration']) if s['test_configuration'] else {}
    print(f"  Config       : {cfg}")
    print(f"  Created At   : {s['created_at']}")
    print()

# 2. For each linearity session, dump raw observations
print("\n[2] RAW OBSERVATIONS PER LINEARITY SESSION")
print("-"*70)
for s in sessions:
    obs = conn.execute("""
        SELECT data FROM observations WHERE test_session_id = ?
    """, (s['id'],)).fetchone()
    print(f"\n  Session: {s['id']}")
    if obs:
        data = json.loads(obs['data']) if isinstance(obs['data'], str) else obs['data']
        print(f"  Observation count: {len(data)}")
        for i, row in enumerate(data, 1):
            print(f"    Row {i:2d}: load={row.get('load')}, indication={row.get('indication')}, "
                  f"direction={row.get('direction', 'increasing')}, "
                  f"zero_indication={row.get('zero_indication', 'NOT SET')}, "
                  f"delta_load={row.get('delta_load', 'NOT SET')}")
    else:
        print("  NO OBSERVATIONS FOUND")

# 3. Dump full calculation results
print("\n\n[3] CALCULATION RESULTS PER LINEARITY SESSION")
print("-"*70)
for s in sessions:
    calc = conn.execute("""
        SELECT full_data, summary_data FROM calculation_results WHERE test_session_id = ?
    """, (s['id'],)).fetchone()
    print(f"\n  Session: {s['id']}")
    if calc:
        full = json.loads(calc['full_data']) if isinstance(calc['full_data'], str) else calc['full_data']
        print(f"  zero_load_error       : {full.get('zero_load_error')}")
        print(f"  max_positive_error    : {full.get('max_positive_error')}")
        print(f"  max_negative_error    : {full.get('max_negative_error')}")
        print(f"  max_absolute_error    : {full.get('max_absolute_error')}")
        print(f"  max_hysteresis        : {full.get('max_hysteresis')}")
        print(f"  verification_scale_e  : {full.get('verification_scale_interval_e')}")
        print(f"  use_changeover_points : {full.get('use_changeover_points')}")
        pts = full.get('point_results', [])
        print(f"  Point results ({len(pts)} points):")
        for pt in pts:
            print(f"    idx={pt['index']}, load={pt['load']}, indication={pt['indication']}, "
                  f"dir={pt['direction']}, zero_ind={pt['zero_indication']}, "
                  f"E={pt['indication_error']:+.4f}, Ec={pt['corrected_error']:+.4f}, "
                  f"load_in_e={pt.get('load_in_e','N/A')}")
    else:
        print("  NO CALCULATION RESULTS FOUND")

# 4. Dump rule evaluations
print("\n\n[4] RULE EVALUATIONS PER LINEARITY SESSION")
print("-"*70)
for s in sessions:
    ev = conn.execute("""
        SELECT overall_outcome, summary_text, evaluations_data FROM rule_evaluations WHERE test_session_id = ?
    """, (s['id'],)).fetchone()
    print(f"\n  Session: {s['id']}")
    if ev:
        print(f"  Overall Outcome : {ev['overall_outcome']}")
        print(f"  Summary         : {ev['summary_text']}")
        evals_data = json.loads(ev['evaluations_data']) if isinstance(ev['evaluations_data'], str) else ev['evaluations_data']
        for item in evals_data.get('evaluations', []):
            print(f"\n    Rule ID         : {item.get('rule_id')}")
            print(f"    Criterion       : {item.get('applicable_criterion')}")
            print(f"    Observed Value  : {item.get('observed_value')}")
            print(f"    Tolerance Limit : {item.get('tolerance_limit')}")
            print(f"    Outcome         : {item.get('outcome')}")
            print(f"    Explanation     : {item.get('explanation')}")
            if item.get('details'):
                print(f"    Per-point details ({len(item['details'])} points):")
                for d in item['details']:
                    status = "PASS" if d.get('passed') else "FAIL"
                    print(f"      load={d['load']}, dir={d.get('direction','?')}, "
                          f"Ec={d.get('corrected_error',0):+.4f}, "
                          f"MPE={d.get('mpe_mass',0):.4f}, "
                          f"MPE_e={d.get('mpe_in_e','?')}, [{status}]")
    else:
        print("  NO RULE EVALUATIONS FOUND")

# 5. Manually replay the MPE lookup for each load point of each linearity session
print("\n\n[5] MANUAL MPE REPLAY (using rules/evaluator logic)")
print("-"*70)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from rules.evaluator import get_mpe_for_load, load_rules_config

cfg = load_rules_config()
for s in sessions:
    e_val = s['verification_scale_interval']
    acc_class = s['accuracy_class']
    print(f"\n  Session: {s['id']} | Class={acc_class} | e={e_val} {s['unit']}")
    calc = conn.execute("""
        SELECT full_data FROM calculation_results WHERE test_session_id = ?
    """, (s['id'],)).fetchone()
    if not calc:
        print("  (no calc data)")
        continue
    full = json.loads(calc['full_data']) if isinstance(calc['full_data'], str) else calc['full_data']
    pts = full.get('point_results', [])
    for pt in pts:
        load = pt['load']
        ec = pt['corrected_error']
        abs_ec = abs(ec)
        try:
            mult, mpe_mass, desc = get_mpe_for_load(load, e_val, acc_class, cfg, "initial")
            verdict = "PASS" if abs_ec <= (mpe_mass + 1e-9) else "FAIL"
            print(f"    load={load:>8.2f} {s['unit']}, m/e={load/e_val:>8.1f}e, "
                  f"Ec={ec:+.4f}, |Ec|={abs_ec:.4f}, MPE={mpe_mass:.4f} ({mult}e), [{verdict}]")
        except Exception as ex:
            print(f"    load={load}: MPE lookup failed: {ex}")

conn.close()
print("\n\n[AUDIT COMPLETE — No files or database modified]")

