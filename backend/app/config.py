from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Mawso3a Fiqh Maliki"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/mawso3a_fiqh"
    ANTHROPIC_API_KEY: str = ""  # Only used by batch scripts, not at runtime
    SHAMELA_BASE_URL: str = "https://shamela.ws"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
