"""Audit every record in nawi_calibration.db for dashboard accuracy review."""
import sqlite3

con = sqlite3.connect('nawi_calibration.db')
con.row_factory = sqlite3.Row

print("=" * 70)
print("INSTRUMENTS (8 expected)")
print("=" * 70)
rows = con.execute("SELECT id, serial_number, model, accuracy_class, is_demo, is_archived FROM instruments ORDER BY created_at").fetchall()
for r in rows:
    print(dict(r))
print(f"\nTotal: {len(rows)}")
print(f"  is_demo=1: {sum(1 for r in rows if r['is_demo'])}")
print(f"  is_demo=0: {sum(1 for r in rows if not r['is_demo'])}")

print("\n" + "=" * 70)
print("ACCURACY CLASS DISTRIBUTION")
print("=" * 70)
for r in con.execute("SELECT accuracy_class, COUNT(*) as cnt FROM instruments GROUP BY accuracy_class"):
    print(dict(r))

print("\n" + "=" * 70)
print("TEST SESSIONS")
print("=" * 70)
sessions = con.execute("SELECT id, instrument_id, test_category, status, is_demo, operator_name FROM test_sessions ORDER BY created_at").fetchall()
for r in sessions:
    print(dict(r))
print(f"\nTotal: {len(sessions)}")
print(f"  is_demo=1: {sum(1 for s in sessions if s['is_demo'])}")
print(f"  is_demo=0: {sum(1 for s in sessions if not s['is_demo'])}")
print(f"  status=Completed: {sum(1 for s in sessions if s['status'] == 'Completed')}")
print(f"  status=Draft: {sum(1 for s in sessions if s['status'] == 'Draft')}")
print(f"  status=In Progress: {sum(1 for s in sessions if s['status'] == 'In Progress')}")

print("\n" + "=" * 70)
print("CATEGORY DISTRIBUTION")
print("=" * 70)
for r in con.execute("SELECT test_category, COUNT(*) as cnt FROM test_sessions GROUP BY test_category"):
    print(dict(r))

print("\n" + "=" * 70)
print("RULE EVALUATIONS (outcome source)")
print("=" * 70)
re_cols = [d[1] for d in con.execute("PRAGMA table_info(rule_evaluations)").fetchall()]
print(f"Columns: {re_cols}")
rule_evals = con.execute("SELECT id, test_session_id, overall_outcome FROM rule_evaluations").fetchall()
print(f"Total rule_evaluations rows: {len(rule_evals)}")
for r in rule_evals:
    print(f"  {r['test_session_id']} -> overall_outcome={r['overall_outcome']}")
# Summary
outcomes_list = [r['overall_outcome'] for r in rule_evals]
from collections import Counter
print(f"\nOutcome distribution: {dict(Counter(outcomes_list))}")

print("\n" + "=" * 70)
print("CALCULATION RESULTS")
print("=" * 70)
calc_cols = [d[1] for d in con.execute("PRAGMA table_info(calculation_results)").fetchall()]
print(f"Columns: {calc_cols}")
calcs = con.execute("SELECT id, test_session_id FROM calculation_results").fetchall()
print(f"Total: {len(calcs)}")
for c in calcs:
    print(f"  {dict(c)}")

print("\n" + "=" * 70)
print("OBSERVATIONS")
print("=" * 70)
obs = con.execute("SELECT test_session_id, COUNT(*) as cnt FROM observations GROUP BY test_session_id").fetchall()
print(f"Sessions with observations: {len(obs)}")
for o in obs:
    print(f"  {dict(o)}")

print("\n" + "=" * 70)
print("GENERATED REPORTS")
print("=" * 70)
reports = con.execute("SELECT id, instrument_id, test_session_id, report_type, generated_by, file_name FROM generated_reports ORDER BY created_at").fetchall()
for r in reports:
    print(dict(r))
print(f"\nTotal reports: {len(reports)}")

print("\n" + "=" * 70)
print("USERS")
print("=" * 70)
users = con.execute("SELECT id, username, full_name, role, is_demo FROM users").fetchall()
for r in users:
    print(dict(r))
print(f"Total users: {len(users)}")

print("\n" + "=" * 70)
print("AUDIT LOGS count")
print("=" * 70)
print(con.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0])

print("\n" + "=" * 70)
print("LAB SETTINGS count")
print("=" * 70)
print(con.execute("SELECT COUNT(*) FROM laboratory_settings").fetchone()[0])

con.close()
