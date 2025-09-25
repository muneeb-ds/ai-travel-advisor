from typing import Annotated, Any
from urllib.parse import quote

from pydantic import BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class AppSettings(BaseSettings):
    APP_NAME: str = "Travel Advisor"
    APP_DESCRIPTION: str = "Travel Advisor is a platform for creating and managing travel advisors."
    APP_VERSION: str = "0.1.0"
    LICENSE_NAME: str = "MIT"
    CONTACT_NAME: str = "Travel Advisor"
    SUPPORT_EMAIL: str | None = None
    FRONTEND_URL: str = "http://localhost:8501"
    BACKEND_CORS_ORIGINS: Annotated[list[str] | str, BeforeValidator(parse_cors)] = []
    DEBUG: bool = False


class DatabaseSettings(BaseSettings):
    DATABASE_HOST: str
    DATABASE_PORT: int
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    DATABASE_POOL_SIZE: int
    DATABASE_MAX_OVERFLOW: int
    DATABASE_POOL_TIMEOUT: int
    DATABASE_POOL_RECYCLE: int

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{quote(self.DATABASE_USER)}:{quote(self.DATABASE_PASSWORD)}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


class LLMSettings(BaseSettings):
    OPENAI_API_KEY: str


class AuthSettings(BaseSettings):
    # RS256 keys (PEM). Provide paths via environment variables.
    JWT_PRIVATE_KEY_PATH: str = "certs/private_key.pem"
    JWT_PUBLIC_KEY_PATH: str = "certs/public_key.pem"
    JWT_ALGORITHM: str = "RS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Auth security hygiene
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 5


class RedisSettings(BaseSettings):
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    # REDIS_PASSWORD: str | None = None
    # REDIS_DB: int = 0
    # REDIS_URL: str | None = None
    IDEMPOTENCY_TTL_SECONDS: int = 300  # 5 minutes

    @property
    def REDIS_CACHE_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


class Settings(
    AppSettings,
    DatabaseSettings,
    LLMSettings,
    AuthSettings,
    RedisSettings,
):
    # Pydantic Settings
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", case_sensitive=True)


settings = Settings()
