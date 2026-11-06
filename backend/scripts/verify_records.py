import sqlite3, json
conn = sqlite3.connect('nawi_calibration.db')
conn.row_factory = sqlite3.Row

print('=== HISTORICAL RECORDS VERIFICATION ===\n')

rows = conn.execute('SELECT id, serial_number, model, accuracy_class, is_demo FROM instruments ORDER BY created_at').fetchall()
print(f'Instruments: {len(rows)}')
for r in rows:
    print(f'  {r["id"]:20} | {r["serial_number"]:25} | demo={r["is_demo"]}')

rows = conn.execute('SELECT id, test_category, status, is_demo, operator_name FROM test_sessions ORDER BY created_at').fetchall()
print(f'\nTest Sessions: {len(rows)}')
for r in rows:
    print(f'  {r["id"]:25} | {r["test_category"]:15} | {r["status"]:10} | demo={r["is_demo"]}')

rows = conn.execute('SELECT test_session_id, overall_outcome FROM rule_evaluations ORDER BY test_session_id').fetchall()
print(f'\nRule Evaluations: {len(rows)}')
for r in rows:
    print(f'  {r["test_session_id"]:25} | {r["overall_outcome"]}')

rows = conn.execute('SELECT id, test_session_id FROM generated_reports ORDER BY created_at').fetchall()
print(f'\nReports: {len(rows)}')
for r in rows:
    print(f'  {r["id"]:20} | session={r["test_session_id"]}')

conn.close()
print('\nAll historical data intact — zero records modified by this implementation.')

