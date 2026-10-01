"""Application settings, loaded from environment variables (or an optional .env file)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=API_DIR / ".env", extra="ignore")

    APP_NAME: str = "ERIS"
    ENVIRONMENT: str = "development"

    # SQLite by default so the project runs with zero setup.
    # For PostgreSQL use: postgresql+psycopg2://user:pass@host:5432/eris
    DATABASE_URL: str = f"sqlite:///{(API_DIR / 'data' / 'eris.db').as_posix()}"

    JWT_SECRET_KEY: str = "dev-only-secret-change-me-in-production-0123456789"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"

    # Demo data: generated automatically the first time the API starts on an empty database.
    SEED_DEMO_DATA: bool = True
    SEED_DAYS: int = 540
    SEED_RANDOM_STATE: int = 42

    # Optional local LLM (free, open source) via Ollama: https://ollama.com
    # The assistant works fully without it (built-in analytics engine);
    # when available the LLM is used to understand free-form questions and phrase answers.
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_ENABLED: bool = True
    LLM_TIMEOUT_SECONDS: float = 45.0

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
