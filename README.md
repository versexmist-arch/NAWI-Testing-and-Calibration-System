# NAWI Testing & Calibration Management System

**Smart India Hackathon (SIH) 2026**
- **Problem Statement ID:** SIH26035
- **Team:** VisionVerity
- **Application Type:** Browser-Based Laboratory Calibration & Metrological Testing SaaS Platform
- **Metrological Framework:** OIML R-76 (Non-Automatic Weighing Instruments: R-76-1, R-76-2, R-76-3)

---

## 1. Project Overview

The **NAWI Testing & Calibration Management System** is a professional, full-stack laboratory calibration platform engineered to support metrologists, verification officers, and quality control laboratories in the registration, testing, calculation, evaluation, reporting, and archival of Non-Automatic Weighing Instruments (NAWI) in accordance with **OIML R-76 recommendations**.

### Key Capabilities
- **End-to-End Metrological Workflow**: Instrument Registration → Test Session Creation → Observation Recording → Computation via Isolated Calculation Engine → OIML R-76 Rule Evaluation → Interactive Analytics & Error Curves → Laboratory-Grade PDF Report Generation → Tamper-Evident Audit Archival.
- **Dedicated Test Workflows**:
  - **Eccentricity Test** (*OIML R-76-1 Clause 3.6.2*): Multi-position receptor evaluation (Center and eccentric points e.g. 4 corners), determining center errors, position indication errors, and eccentricity deviations relative to center.
  - **Linearity & Weighing Performance Test** (*OIML R-76-1 Clause 3.5.1, Clause A.4.4*): Multi-point loading and unloading passes, zero-load correction, turning-point changeover calculations ($P = I + 0.5e - \Delta L$, $E = P - L$), and hysteresis determination ($|I_{\text{dec}} - I_{\text{inc}}|$).
  - **Repeatability Test** (*OIML R-76-1 Clause 3.6.1*): Series of repeated weighings ($\ge 10$ runs) at nominal load, computing minimum, maximum, range ($I_{\max} - I_{\min}$), arithmetic mean ($\bar{I}$), sample standard deviation ($s$), and variance.
- **Configurable & Versioned Rule Layer**: Versioned OIML rules (`OIML-R76-2006-v1.0`) stored decoupled from computation code. Evaluates Class I, Class II, Class III, and Class IIII step intervals against Maximum Permissible Errors (MPE Table 6: $\pm 0.5e, \pm 1.0e, \pm 1.5e$). Distinguishes between `PASS`, `FAIL`, `INCOMPLETE`, `NOT_APPLICABLE`, and `PENDING_VERIFICATION` (ensuring unverified rules never render false compliance).
- **Official Laboratory PDF Reports**: ReportLab-powered publication-grade PDF reports with complete instrument specifications, ambient conditions, observations, calculated extrema, OIML rule evaluation breakdowns, metrological limitation notices, and formal review sign-off blocks.
- **Traceability & Audit Logging**: Immutable audit logging recording all instrument registrations, modifications, observation submissions, calculation executions, rule evaluations, and PDF generation events.
- **Synthetic Demonstration Suite**: Pre-seeded demonstration datasets (Class I Analytical Balance, Class II Precision Balance, Class III Industrial Scale) with realistic test sessions, calculations, and pre-generated PDF certificates. A 1-click safe demo reset clears only demonstration records while preserving real user laboratory data.

---

## 2. Technology Stack

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling:** Tailwind CSS (Laboratory SaaS theme: dark navy sidebar `#0b1329`, slate workspace `#f8fafc`, crisp white cards, restrained shadows)
- **Routing:** React Router v7
- **Charts & Visualization:** Recharts (Dynamic error curves, MPE boundary lines, distribution donuts, repeatability sequence plots)
- **Icons:** Lucide Icons (`lucide-react`)
- **API Client:** Axios

### Backend
- **Framework:** Python 3.13 / FastAPI
- **Data Validation:** Pydantic v2
- **Database / ORM:** SQLAlchemy 2.0 with SQLite (structured for plug-and-play PostgreSQL migration)
- **PDF Generation:** ReportLab 5.1 Platypus
- **Testing:** Pytest (100% pass across calculation engine, rules engine, and API integration suites)

---

## 3. Project Directory Structure

```text
NAWI-Testing-System/
│
├── frontend/                     # React + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── components/ui.tsx     # Reusable UI library (Badges, Alerts, Modals, Cards)
│   │   ├── layouts/              # AppLayout, Dark Navy Sidebar, Topbar
│   │   ├── pages/                # Dashboard, Instruments, Register, TestWorkflows, etc.
│   │   ├── services/api.ts       # Axios client with proxy routing
│   │   ├── types/index.ts        # Metrological TypeScript interfaces
│   │   ├── App.tsx               # Route configurations
│   │   └── main.tsx              # React DOM mounting
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
│
├── backend/                      # FastAPI Backend
│   ├── app/
│   │   ├── api/                  # Modular route controllers
│   │   │   ├── health.py         # System health check
│   │   │   ├── instruments.py    # Instrument management & test history
│   │   │   ├── tests.py          # Test session lifecycle & execution
│   │   │   ├── reports.py        # PDF report retrieval & download
│   │   │   ├── audit.py          # Audit trail queries
│   │   │   ├── rules.py          # OIML rule configurations
│   │   │   ├── dashboard.py      # Aggregated metrics & activity stats
│   │   │   └── demo.py           # Safe demo data seeding & reset
│   │   ├── database.py           # SQLAlchemy session & SQLite connection
│   │   ├── config.py             # Environment configuration (Pydantic Settings)
│   │   ├── models/               # SQLAlchemy ORM models (Instrument, TestSession, etc.)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Test calculation, ReportLab PDF, and demo services
│   │   └── main.py               # FastAPI application entrypoint & startup lifecycle
│   ├── tests/test_api.py         # End-to-end API integration tests
│   ├── requirements.txt          # Python dependencies
│   └── venv/                     # Python virtual environment
│
├── calculation_engine/           # Standalone Metrological Calculation Engine
│   ├── common/                   # Unit normalization (mg, g, kg, t) & precision utilities
│   ├── eccentricity/             # OIML R-76-1 3.6.2 Eccentricity calculator
│   ├── linearity/                # OIML R-76-1 3.5.1 Linearity & hysteresis calculator
│   ├── repeatability/            # OIML R-76-1 3.6.1 Repeatability range & statistics
│   └── tests/                    # Independent Pytest verification suites
│
├── rules/                        # OIML R-76 Configurable & Versioned Rule Layer
│   ├── configurations/           # Versioned JSON rule definitions (oiml_r76_2006_rules.json)
│   ├── definitions.py            # Rule schemas & outcome enums
│   ├── evaluator.py              # Rule evaluation engine (PASS, FAIL, PENDING_VERIFICATION)
│   └── tests/                    # Boundary & threshold Pytest test suite
│
├── reports/                      # PDF Reports storage
│   └── generated/                # Output PDF documents
│
├── .env.example                  # Environment template
├── .gitignore                    # Git ignore specifications
└── README.md                     # Documentation
```

---

## 4. Local Execution Instructions (Windows)

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Node.js 18+ (Tested on Node v22.19.0, npm 10.9.3)

### Step 1: Start Backend API Server
Open PowerShell in the project root:
```powershell
cd backend
# Activate virtual environment
.\venv\Scripts\activate
# Start the FastAPI server
uvicorn app.main:app --reload --port 8000
```
*The database tables will initialize automatically and seed initial demonstration datasets on first startup.*

### Step 2: Start Frontend Application
Open a second PowerShell terminal in the project root:
```powershell
cd frontend
npm run dev
```

### Development URLs
- **Web Application:** `http://localhost:5173`
- **Backend API:** `http://localhost:8000`
- **FastAPI Interactive Docs (Swagger UI):** `http://localhost:8000/docs`
- **FastAPI Redoc:** `http://localhost:8000/redoc`

---

## 5. Running Automated Tests

Run the full verification test suite (Calculation Engine + OIML Rule Evaluator + Backend Integration):
```powershell
# From project root:
.\backend\venv\Scripts\pytest calculation_engine\tests rules\tests backend\tests -v
```
**Test Results:**
- `test_eccentricity.py`: 3 passed (Standard 5-point run, zero error offset, input validation)
- `test_linearity.py`: 3 passed (Multi-point weighing curves, zero correction, hysteresis)
- `test_repeatability.py`: 2 passed (10-run repeatability statistics, range, std dev)
- `test_units.py`: 4 passed (Unit conversion, scale intervals calculation, error handling)
- `test_rule_evaluator.py`: 5 passed (MPE lookup, step boundaries, pass/fail, unverified rule rejection)
- `test_api.py`: 5 passed (Health check, instrument registration, duplicate rejection, full test workflow, report download)
- **Total: 22 passed (100% success)**

---

## 6. Regulatory & Metrological Disclaimer

This application is a testing, calculation, and calibration support prototype created for **Smart India Hackathon 2026** (Problem Statement ID: **SIH26035**, Team: **VisionVerity**).
- It provides structured observation capture, deterministic calculation, and rule evaluation against configured OIML R-76 recommendations.
- Any rule designated as `PENDING_VERIFICATION` does not issue an authoritative compliance conclusion.
- **This application does not issue legally binding certificates of verification or replace accredited legal metrology inspection.**
