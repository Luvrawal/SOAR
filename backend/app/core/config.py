from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "SOAR Platform"
    API_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    BACKEND_CORS_ORIGINS: str = "*"

    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "soar"
    POSTGRES_USER: str = "soar_user"
    POSTGRES_PASSWORD: str = "soar_password"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB_BROKER: int = 0
    REDIS_DB_RESULT: int = 1

    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    SQLALCHEMY_DATABASE_URI: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()


def build_database_url() -> str:
    if settings.SQLALCHEMY_DATABASE_URI:
        return settings.SQLALCHEMY_DATABASE_URI

    return (
        f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )


def build_redis_url(db: int) -> str:
    return f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/{db}"


def build_celery_broker_url() -> str:
    return settings.CELERY_BROKER_URL or build_redis_url(settings.REDIS_DB_BROKER)


def build_celery_result_backend() -> str:
    return settings.CELERY_RESULT_BACKEND or build_redis_url(settings.REDIS_DB_RESULT)


def get_cors_origins() -> list[str]:
    origins = [origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",") if origin.strip()]
    return origins or ["*"]
