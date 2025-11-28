import os
from dotenv import load_dotenv

load_dotenv(override=True)


class Settings:
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE: str = os.getenv("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "anthropic/claude-3.5-sonnet")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    SEC_USER_AGENT: str = os.getenv("SEC_USER_AGENT", "sec-tracker contact@example.com")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
