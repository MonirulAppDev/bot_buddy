import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Bot Buddy"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "bot-buddy-secret-key-change-in-production-123456"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./bot_buddy.db"
    
    # SMM API Defaults
    MOCK_BALANCE: float = 1000.00
    MOCK_CURRENCY: str = "USD"
    
    # Drip-Feed & Pacing
    DEFAULT_MIN_INTERVAL_SECONDS: int = 2
    DEFAULT_MAX_INTERVAL_SECONDS: int = 15
    
    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
