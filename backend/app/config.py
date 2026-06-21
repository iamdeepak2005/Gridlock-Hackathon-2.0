"""
Application configuration via Pydantic Settings.
Reads from environment variables and .env file.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration for the TRINETRA AI application."""

    # App
    APP_NAME: str = "TRINETRA AI"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://trinetra:trinetra_pass@localhost:5432/trinetra_db"

    # ML Model paths
    MODEL_DIR: str = "./trained_models"
    DATA_PATH: str = "./data/events.csv"

    # OSMnx
    OSMNX_CACHE_DIR: str = "./osmnx_cache"

    # API
    API_PREFIX: str = "/api/v1"
    GEMINI_API_KEY: Optional[str] = None

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }

    @property
    def model_dir_path(self) -> Path:
        path = Path(self.MODEL_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def data_path_resolved(self) -> Path:
        return Path(self.DATA_PATH)


settings = Settings()
