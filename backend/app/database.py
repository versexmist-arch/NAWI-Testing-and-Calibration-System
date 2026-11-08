from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

# If SQLite, ensure connect_args includes check_same_thread=False
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_schema_compatibility(db_engine):
    """
    Ensure newly introduced columns exist in SQLite database tables without
    dropping, modifying, or compromising existing records or historical data.
    """
    try:
        with db_engine.connect() as conn:
            cursor = conn.connection.cursor()
            # 1. generated_reports: version, is_superseded, superseded_by
            gr_cols = [c[1] for c in cursor.execute("PRAGMA table_info(generated_reports)").fetchall()]
            if gr_cols:
                if "version" not in gr_cols:
                    cursor.execute("ALTER TABLE generated_reports ADD COLUMN version INTEGER DEFAULT 1")
                if "is_superseded" not in gr_cols:
                    cursor.execute("ALTER TABLE generated_reports ADD COLUMN is_superseded BOOLEAN DEFAULT 0")
                if "superseded_by" not in gr_cols:
                    cursor.execute("ALTER TABLE generated_reports ADD COLUMN superseded_by VARCHAR(50)")
            conn.connection.commit()
    except Exception:
        pass
