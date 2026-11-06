"""Ensure all SQLAlchemy tables exist in the production database."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from backend.app.database import engine, Base
from backend.app.models import (
    Instrument, TestSession, Observation, CalculationResult,
    RuleEvaluation, GeneratedReport, AuditLog, User, LaboratorySettings
)

Base.metadata.create_all(bind=engine)
print("✅ All tables ensured in nawi_calibration.db")

import sqlite3
con = sqlite3.connect('nawi_calibration.db')
tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables:", tables)
con.close()

