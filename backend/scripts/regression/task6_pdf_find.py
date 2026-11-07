import sqlite3, os
os.chdir(os.path.join(os.path.dirname(__file__), '..', '..'))
conn = sqlite3.connect('nawi_calibration.db')
conn.row_factory = sqlite3.Row

# Check table names
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print("Tables:", [t['name'] for t in tables])

# Get linearity reports with file paths
rows = conn.execute("""
    SELECT ts.id, ts.test_category, r.id as rep_id, r.file_path
    FROM test_sessions ts
    JOIN reports r ON r.test_session_id = ts.id
    WHERE ts.test_category = 'linearity'
    LIMIT 5
""").fetchall()
print("\nLinearity Reports:")
for r in rows:
    print(f"  session={r['id']}  report={r['rep_id']}  file={r['file_path']}")

