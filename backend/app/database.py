from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker
from .config import settings

db_url = settings.DATABASE_URL

# PostgreSQL vs SQLite connection arguments and pool configurations
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
    )
else:
    # PostgreSQL configuration with connection pooling and pre-ping to handle stale cloud connections
    engine = create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
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
    Ensure newly introduced columns exist in tables across both SQLite and PostgreSQL
    without dropping, modifying, or compromising existing records or historical data.
    """
    try:
        inspector = inspect(db_engine)
        tables = inspector.get_table_names()
        if "generated_reports" in tables:
            columns = [col["name"] for col in inspector.get_columns("generated_reports")]
            with db_engine.begin() as conn:
                is_sqlite = db_engine.dialect.name == "sqlite"
                bool_default = "0" if is_sqlite else "FALSE"

                if "version" not in columns:
                    conn.execute(text("ALTER TABLE generated_reports ADD COLUMN version INTEGER DEFAULT 1"))
                if "is_superseded" not in columns:
                    conn.execute(text(f"ALTER TABLE generated_reports ADD COLUMN is_superseded BOOLEAN DEFAULT {bool_default}"))
                if "superseded_by" not in columns:
                    conn.execute(text("ALTER TABLE generated_reports ADD COLUMN superseded_by VARCHAR(50)"))
    except Exception:
        # Pass safely if columns already exist or dialect restricts online DDL
        pass
