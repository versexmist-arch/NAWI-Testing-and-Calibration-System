"""
TASK 6 -- PDF Report Verification
Verifies existing PDF report content and generates a fresh report via API.
Run from project root (nawi directory).
Command: .\\backend\\venv\\Scripts\\python.exe backend\\scripts\\regression\\task6_pdf_verify.py
"""
import sys, os, sqlite3, tempfile, uuid, json
ROOT = str(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
BACKEND = os.path.join(ROOT, 'backend')
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

PASS_COUNT = 0
FAIL_COUNT = 0

def chk(test_id, label, ok, detail=""):
    global PASS_COUNT, FAIL_COUNT
    status = "PASS" if ok else "FAIL"
    if ok:
        PASS_COUNT += 1
    else:
        FAIL_COUNT += 1
    print("  [{}] {}: {}{}".format(status, test_id, label, " -- " + detail if detail else ""))
    return ok

print("=" * 70)
print("TASK 6 -- PDF REPORT VERIFICATION")
print("=" * 70)

# ------------------------------------------------------------------ #
# 6-A: Locate existing linearity PDF from production DB              #
# ------------------------------------------------------------------ #
print("\n--- 6-A: Locate existing linearity report ---")
conn = sqlite3.connect(os.path.join(ROOT, 'nawi_calibration.db'))
conn.row_factory = sqlite3.Row
row = conn.execute("""
    SELECT gr.id, gr.file_path, ts.test_category, re.overall_outcome
    FROM generated_reports gr
    JOIN test_sessions ts ON gr.test_session_id = ts.id
    LEFT JOIN rule_evaluations re ON re.test_session_id = ts.id
    WHERE ts.test_category = 'linearity'
    ORDER BY gr.created_at
    LIMIT 1
""").fetchone()
conn.close()

if not row:
    chk("T6-A1", "Linearity report found in DB", False, "No linearity report in DB")
    print("TASK 6 CANNOT PROCEED -- No linearity report found in DB.")
    sys.exit(1)

report_id   = row['id']
file_path   = row['file_path']
db_outcome  = row['overall_outcome']
print("  Report ID  : {}".format(report_id))
print("  File path  : {}".format(file_path))
print("  DB outcome : {}".format(db_outcome))

chk("T6-A1", "Linearity report found in DB", True, "id={}".format(report_id))

# Resolve file path -- could be absolute or relative
if not os.path.isabs(file_path):
    pdf_path = os.path.join(ROOT, file_path)
else:
    pdf_path = file_path

file_exists = os.path.isfile(pdf_path)
chk("T6-A2", "PDF file exists on disk", file_exists, pdf_path)
if not file_exists:
    # Try the reports/ folder
    fname = os.path.basename(file_path)
    alt = os.path.join(ROOT, 'reports', fname)
    if os.path.isfile(alt):
        pdf_path = alt
        file_exists = True
        chk("T6-A2b", "PDF found in reports/ folder", True, alt)

# ------------------------------------------------------------------ #
# 6-B: Extract and verify PDF text content                           #
# ------------------------------------------------------------------ #
print("\n--- 6-B: PDF content extraction ---")
pdf_text = ""
try:
    import pdfplumber
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            pdf_text += t + "\n"
    chk("T6-B1", "PDF readable via pdfplumber", True, "{} chars".format(len(pdf_text)))
    USE_PLUMBER = True
except ImportError:
    try:
        import PyPDF2
        with open(pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                pdf_text += (page.extract_text() or "") + "\n"
        chk("T6-B1", "PDF readable via PyPDF2", True, "{} chars".format(len(pdf_text)))
        USE_PLUMBER = False
    except ImportError:
        chk("T6-B1", "PDF readable (pdfplumber/PyPDF2 not installed)", False,
            "Install pdfplumber: pip install pdfplumber")
        pdf_text = ""
        USE_PLUMBER = False
except Exception as ex:
    chk("T6-B1", "PDF readable", False, str(ex))
    pdf_text = ""

if pdf_text:
    # Check for required content
    chk("T6-B2",  "Report ID present in PDF",          report_id in pdf_text,       "id={}".format(report_id))
    chk("T6-B3",  "OIML-R76-1-LIN-MPE rule reference", "OIML-R76-1-LIN-MPE" in pdf_text)
    chk("T6-B4",  "Overall outcome present",            db_outcome in pdf_text,      "expected={}".format(db_outcome))
    chk("T6-B5",  "No ISO/IEC 17025 accreditation claim",
        "ISO/IEC 17025" not in pdf_text,
        "PRESENT" if "ISO/IEC 17025" in pdf_text else "absent (correct)")
    chk("T6-B6",  "Load values present (0.0 or 0 g)",
        "0.0" in pdf_text or " 0 " in pdf_text or "0 g" in pdf_text)
    chk("T6-B7",  "Indication error values present",
        "Error" in pdf_text or "error" in pdf_text or "Corrected" in pdf_text)
    chk("T6-B8",  "MPE values present",
        "MPE" in pdf_text or "mpe" in pdf_text.lower())
    # Verify no 1000 g phantom error (the original bug)
    # Look for "1000" as an error value -- should not appear as an indication error
    # This is a soft check: if max_error=1000 appears that's the original bug
    has_phantom = "1000.0" in pdf_text and "FAIL" in pdf_text
    chk("T6-B9",  "No phantom 1000 g error (original BUG)",
        not has_phantom,
        "Phantom 1000g error DETECTED" if has_phantom else "clean")

    print("\n  --- First 600 chars of extracted PDF text ---")
    print("  " + pdf_text[:600].replace("\n", "\n  "))

# ------------------------------------------------------------------ #
# 6-C: Generate fresh report via API (using TestClient + temp DB)    #
# ------------------------------------------------------------------ #
print("\n--- 6-C: Fresh report generation via API ---")
try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from fastapi.testclient import TestClient
    from app.main import app
    from app.database import Base, get_db
    from app.services.demo_data_service import seed_demo_data

    _tmp_db = os.path.join(tempfile.gettempdir(), "nawi_t6_{}.db".format(uuid.uuid4().hex[:8]))
    _engine = create_engine("sqlite:///{}".format(_tmp_db), connect_args={"check_same_thread": False})
    _Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

    def _override_db():
        db = _Session()
        try:
            yield db
        finally:
            db.close()

    Base.metadata.create_all(bind=_engine)
    _db = _Session()
    seed_demo_data(_db)
    _db.close()
    app.dependency_overrides[get_db] = _override_db

    with TestClient(app) as api:
        # Create a Class III 3000g instrument
        inst_payload = {
            "serial_number": "SN-T6-{}" .format(uuid.uuid4().hex[:6].upper()),
            "manufacturer": "Task6 Test", "model": "DS-3000", "instrument_type": "Platform Scale",
            "accuracy_class": "Class III", "max_capacity": 3000.0, "min_capacity": 0.0,
            "verification_scale_interval": 1.0, "actual_scale_interval": 1.0,
            "unit": "g", "location": "Task6 Lab", "notes": "PDF regression test"
        }
        inst_res = api.post("/api/instruments", json=inst_payload)
        chk("T6-C1", "Create instrument for fresh report", inst_res.status_code == 201,
            "status={}".format(inst_res.status_code))
        inst_id = inst_res.json()["id"]

        # Create session
        sess_res = api.post("/api/tests", json={
            "instrument_id": inst_id,
            "test_category": "linearity",
            "operator_name": "Reg. Tester",
            "laboratory_location": "Bay A",
            "ambient_temperature": 23.0,
            "relative_humidity": 50.0,
            "service_type": "initial",
            "test_configuration": {}
        })
        chk("T6-C2", "Create linearity test session", sess_res.status_code == 201,
            "status={}".format(sess_res.status_code))
        sess_id = sess_res.json()["id"]

        # Submit good observations
        good_obs = [
            {"load": 0,    "indication": 0.0,    "direction": "increasing"},
            {"load": 500,  "indication": 499.9,  "direction": "increasing"},
            {"load": 1000, "indication": 1000.1, "direction": "increasing"},
            {"load": 2000, "indication": 1999.8, "direction": "increasing"},
            {"load": 3000, "indication": 2999.9, "direction": "increasing"},
        ]
        obs_res = api.post("/api/tests/{}/observations".format(sess_id), json={"observations": good_obs})
        chk("T6-C3", "Submit observations", obs_res.status_code == 200,
            "status={}".format(obs_res.status_code))

        # Calculate
        calc_res = api.post("/api/tests/{}/calculate".format(sess_id))
        chk("T6-C4", "Run calculation", calc_res.status_code == 200,
            "status={}".format(calc_res.status_code))
        if calc_res.status_code == 200:
            outcome = calc_res.json()["rule_evaluation"]["overall_outcome"]
            chk("T6-C5", "Fresh report outcome = PASS", outcome == "PASS", "outcome={}".format(outcome))

        # Generate report
        rep_res = api.post("/api/tests/{}/report".format(sess_id))
        chk("T6-C6", "Generate PDF report", rep_res.status_code == 200,
            "status={}".format(rep_res.status_code))
        if rep_res.status_code == 200:
            new_rep_id = rep_res.json().get("report_id", "?")
            chk("T6-C7", "Report ID returned", new_rep_id != "?", "id={}".format(new_rep_id))

            # Download
            dl_res = api.get("/api/reports/{}/download".format(new_rep_id))
            chk("T6-C8", "PDF download succeeds", dl_res.status_code == 200,
                "status={}, bytes={}".format(dl_res.status_code, len(dl_res.content)))
            if dl_res.status_code == 200:
                chk("T6-C9", "Response is PDF content-type",
                    "pdf" in dl_res.headers.get("content-type", "").lower(),
                    dl_res.headers.get("content-type", ""))
                chk("T6-C10", "PDF size > 2 KB (valid generated document)", len(dl_res.content) > 2000,
                    "{} bytes".format(len(dl_res.content)))

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=_engine)
    try:
        os.remove(_tmp_db)
    except Exception:
        pass

except Exception as ex:
    FAIL_COUNT += 1
    print("  [FAIL] T6-C: Fresh report generation failed -- {}: {}".format(type(ex).__name__, ex))

# ------------------------------------------------------------------ #
# Summary                                                            #
# ------------------------------------------------------------------ #
print()
print("=" * 70)
print("TASK 6 SUMMARY: PASS={}  FAIL={}".format(PASS_COUNT, FAIL_COUNT))
if FAIL_COUNT == 0:
    print("OK All PDF verification checks passed.")
else:
    print("WARNING {} PDF checks failed.".format(FAIL_COUNT))
print("=" * 70)
