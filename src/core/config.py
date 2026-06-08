"""
Configuration management using pydantic-settings.
Centralizes all environment variables and app settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Sistema de Captação de Leads"
    app_version: str = "0.1.0"
    debug: bool = False
    environment: str = "development"  # development, staging, production

    # API
    api_prefix: str = "/api/v1"
    cors_origins: list[str] = ["*"]
    allowed_hosts: list[str] = ["*"]

    # Firestore
    firestore_project_id: Optional[str] = None
    firestore_credentials_path: Optional[str] = None
    firestore_emulator_host: Optional[str] = None

    # Firebase Auth
    firebase_project_id: Optional[str] = None
    firebase_service_account_path: Optional[str] = None

    # Logging
    log_level: str = "INFO"

    # Rate limiting (requests per minute)
    rate_limit_per_minute: int = 60

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    @property
    def using_firestore_emulator(self) -> bool:
        """Check if using Firestore emulator."""
        return self.firestore_emulator_host is not None


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache ensures settings are loaded only once.
    """
    return Settings()
