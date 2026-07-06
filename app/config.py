from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Typed application settings, loaded from environment variables.

    Why a class instead of os.getenv() scattered everywhere?
    - Type validation: if SECRET_KEY is missing, the app fails fast at startup
      with a clear error, instead of failing later with a confusing bug.
    - Autocomplete: settings.database_url works in your editor; os.getenv("DATABASE_URL")
      gives you a typo-prone string with no autocomplete.
    - Single source of truth: every part of the app imports the same `settings` object.
    """

    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    # Comma-separated list of allowed frontend origins for CORS, e.g.
    # "http://localhost:5173,https://your-app.vercel.app". Defaulting to
    # localhost:5173 means local dev keeps working with zero setup, while
    # production sets this via Render's dashboard environment variables.
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


# Created once at import time, reused everywhere via `from app.config import settings`


settings = Settings()