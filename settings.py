"""Application configuration via pydantic-settings.

Values are read from environment variables (and an optional `.env` file).
Import the ready-made singleton:  from settings import settings
"""
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    BASE_URL: str = "http://localhost"

    # --- Google OAuth ---
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # --- Admin bootstrap (first run) ---
    ADMIN_LOGIN: str = "admin"
    ADMIN_EMAIL: str = "admin@example.com"
    ADMIN_PASSWORD: Optional[str] = None  # None -> a random one is generated

    # --- Server ---
    COOKIE_SECRET: str = ""  # empty -> a random one is generated
    DEBUG: bool = False
    PORT: int = 8899

    def get(self, key, default=None):
        """dict-style access, e.g. settings.get('GOOGLE_CLIENT_ID')."""
        return getattr(self, key, default)


settings = Settings()
