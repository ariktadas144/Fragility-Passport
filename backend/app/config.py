"""Application settings, loaded from environment variables / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Fragility Passport API"
    environment: str = "development"

    database_url: str = f"sqlite:///{BASE_DIR / 'fragility_passport.db'}"

    evidence_dir: Path = BASE_DIR / "evidence"

    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Auto-escalate an unacknowledged HIGH/CRITICAL alert after this many seconds.
    escalation_seconds: int = 15
    escalation_poll_interval_seconds: int = 5

    # Optional shared-secret header for write endpoints. Empty string disables the check
    # (fine for a hackathon demo; set API_KEY to turn it on before a public deploy).
    api_key: str = ""

    # Injected by Workstream 2 in a real deployment; unused by the backend directly.
    gemini_api_key: str = ""

    seed_data_dir: Path = BASE_DIR.parent / "data" / "seed"


@lru_cache
def get_settings() -> Settings:
    return Settings()
