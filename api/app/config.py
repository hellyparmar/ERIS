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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14

    # Browser sessions: the refresh token travels only in an HTTP-only cookie (never readable by page scripts).
    # SameSite=none is needed when the web app is on another site than the API (e.g. Vercel + Render); it requires Secure.
    REFRESH_COOKIE_NAME: str = "eris_refresh"
    REFRESH_COOKIE_SAMESITE: str = "lax"   # set "none" for a cross-site web app (render.yaml does)
    REFRESH_COOKIE_SECURE: bool | None = None  # None: Secure in production, not in development

    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173"
    # optional pattern for extra web origins, e.g. Vercel previews: https://my-project-[a-z0-9-]+\.vercel\.app
    CORS_ORIGIN_REGEX: str | None = None

    # Demo data: generated automatically the first time the API starts on an empty database.
    SEED_DEMO_DATA: bool = True
    SEED_DAYS: int = 730  # two years of history
    SEED_OUTLETS: int = 5  # 1-7 outlets in the demo company
    SEED_RANDOM_STATE: int = 42
    SEED_END_DATE: str | None = None  # YYYY-MM-DD; default = yesterday (business time zone)
    # Move an old, untouched demo forward to yesterday at start-up. It rewrites every dated row, which takes
    # minutes (and drops the pre-computed answers) on a small hosted server: render.yaml turns it off there.
    DEMO_SHIFT_DATES: bool = True
    # Start without demo data: the first admin is created from these on an empty database
    INITIAL_ADMIN_EMAIL: str | None = None
    INITIAL_ADMIN_PASSWORD: str | None = None

    # Transport and abuse protection (app/hardening.py). Limits are per client address and per process.
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_API_PER_MINUTE: int = 1200      # every /api request
    RATE_LIMIT_LOGIN_PER_MINUTE: int = 60      # sign-in attempts per address (an office may share one address)
    RATE_LIMIT_HEAVY_PER_MINUTE: int = 120     # forecasts, assistant questions, imports, exports
    MAX_BODY_MB: int = 20                      # imports are capped at 15 MB; this is the request ceiling

    # Model fitting is the heaviest work the API does. At most this many fits run at once, so a burst of forecast
    # requests cannot take every worker thread (or the whole CPU of a small server) from the other pages; a
    # request that cannot start a fit within FORECAST_WAIT_SECONDS gets a quick "busy, try again" (HTTP 503).
    FORECAST_WORKERS: int = 1
    FORECAST_WAIT_SECONDS: float = 20.0
    # Exports (CSV and Excel) build whole files in memory. At most EXPORT_WORKERS run at once.
    EXPORT_WORKERS: int = 2
    EXPORT_WAIT_SECONDS: float = 10.0

    # Optional local LLM (free, open source) via Ollama: https://ollama.com
    # The assistant works fully without it (built-in analytics engine);
    # when available the LLM is used to understand free-form questions and phrase answers.
    OLLAMA_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    LLM_ENABLED: bool = True
    LLM_TIMEOUT_SECONDS: float = 45.0

    # Project documentation the assistant may quote (definitions, how-tos, model and dataset cards)
    KNOWLEDGE_DIR: str = str(API_DIR.parent / "docs" / "knowledge")

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cookie_secure(self) -> bool:
        return self.ENVIRONMENT == "production" if self.REFRESH_COOKIE_SECURE is None else self.REFRESH_COOKIE_SECURE

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
