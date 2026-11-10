import os
import json
from pathlib import Path
from typing import List, Any, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "NAWI Testing & Calibration Management System"
    TEAM_NAME: str = "VisionVerity"
    PROBLEM_STATEMENT_ID: str = "SIH26035"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"

    DATABASE_URL: str = f"sqlite:///{ROOT_DIR / 'nawi_calibration.db'}"
    REPORTS_DIR: str = str(ROOT_DIR / "reports" / "generated")
    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://localhost:8000",
    ]
    CORS_ORIGIN_REGEX: Optional[str] = r"^https:\/\/.*\.vercel\.app$"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, v: Any) -> str:
        """
        Normalize database connection URLs:
        - Render, Heroku and cloud PostgreSQL providers provide 'postgres://' or 'postgresql://'.
        - SQLAlchemy 2.0 defaults 'postgresql://' to the psycopg (v3) driver, which causes
          ModuleNotFoundError if only psycopg2-binary is installed.
        - Normalizing to 'postgresql+psycopg2://' ensures SQLAlchemy deterministically
          uses the installed psycopg2-binary driver.
        - SQLite URLs (e.g. 'sqlite:///...') are preserved intact for local development.
        """
        if isinstance(v, str):
            val = v.strip()
            if val.startswith("postgres://"):
                return "postgresql+psycopg2://" + val[len("postgres://"):]
            if val.startswith("postgresql+psycopg://"):
                return "postgresql+psycopg2://" + val[len("postgresql+psycopg://"):]
            if val.startswith("postgresql://"):
                return "postgresql+psycopg2://" + val[len("postgresql://"):]
            return val
        return str(v)

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """
        Parse and validate CORS_ORIGINS from:
        - JSON-formatted list string (e.g. '["https://app.vercel.app"]' or '[]')
        - Comma-separated string (e.g. 'https://app.vercel.app,http://localhost:5173')
        - Native list/tuple of strings
        Rejects invalid JSON objects, malformed JSON, and non-list structures.
        """
        if isinstance(v, str):
            val = v.strip()
            if not val or val == "[]":
                return []
            if val.startswith("{"):
                raise ValueError("CORS_ORIGINS cannot be a JSON object; expected a JSON list or comma-separated origins.")
            if val.startswith("["):
                if not val.endswith("]"):
                    raise ValueError("Invalid JSON in CORS_ORIGINS: unclosed bracket.")
                try:
                    loaded = json.loads(val)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format for CORS_ORIGINS: {e}") from e
                if not isinstance(loaded, list):
                    raise ValueError("CORS_ORIGINS JSON must be a list of origin strings.")
                return [str(origin).strip() for origin in loaded if str(origin).strip()]
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        elif isinstance(v, (list, set, tuple)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        raise ValueError(f"Invalid CORS_ORIGINS configuration: {v}")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
