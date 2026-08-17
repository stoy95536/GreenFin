"""
GreenFin application configuration.

Loads settings from environment variables / .env file.
"""

from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # Application
    APP_ENV: str = "development"
    APP_NAME: str = "GreenFin"
    APP_TIMEZONE: str = "Asia/Taipei"

    # Backend
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./greenfin_demo.db"

    # Demo
    DEMO_MODE: bool = True

    # Rule Set
    RULE_VERSION: str = "GREENFIN_DEMO_V1"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Project root is backend/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

settings = Settings(_env_file=PROJECT_ROOT / ".env")
