import os
from pathlib import Path
from typing import List
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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
