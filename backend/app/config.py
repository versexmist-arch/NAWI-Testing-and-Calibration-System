import os
import json
from pathlib import Path
from typing import List, Any, Optional
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
    CORS_ORIGINS: List[str] = [
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
        Render, Supabase and Heroku often provide 'postgres://' connection URLs.
        SQLAlchemy 2.0+ requires the explicit driver scheme 'postgresql://'.
        """
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return str(v)

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """
        Support comma-separated strings (e.g. 'https://app.vercel.app,http://localhost:5173'),
        JSON strings (e.g. '["https://app.vercel.app"]'), or lists.
        """
        if isinstance(v, str):
            val = v.strip()
            if not val:
                return []
            if val.startswith("[") and val.endswith("]"):
                try:
                    return json.loads(val)
                except Exception:
                    pass
            return [origin.strip() for origin in val.split(",") if origin.strip()]
        elif isinstance(v, (list, set, tuple)):
            return [str(origin).strip() for origin in v if str(origin).strip()]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
