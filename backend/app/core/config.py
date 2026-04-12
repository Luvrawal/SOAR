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
    SECURITY_HEADERS_ENABLED: bool = True
    FORCE_HTTPS_HSTS: bool = False

    JWT_SECRET: str = "change-me-in-production-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

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
    CELERY_WORKER_CONCURRENCY: int = 4
    PLAYBOOK_QUEUE_CAPACITY: int = 200
    CELERY_TASK_MAX_RETRIES: int = 3
    CELERY_RETRY_BACKOFF_SECONDS: int = 2
    CELERY_QUEUE_DEFAULT: str = "playbook_default"
    CELERY_QUEUE_EMAIL: str = "playbook_email"
    CELERY_QUEUE_ENDPOINT: str = "playbook_endpoint"
    CELERY_QUEUE_FILE: str = "playbook_file"

    VIRUSTOTAL_API_KEY: str | None = None
    ABUSEIPDB_API_KEY: str | None = None
    ALIENVAULT_API_KEY: str | None = None
    MALWAREBAZAAR_API_KEY: str | None = None
    SOAR_REPORTS_DIR: str = "./reports"
    SOAR_REPORT_PROFILE: Literal["full", "redacted"] = "full"
    SOAR_DATASET_DIR: str | None = None
    THREAT_INTEL_TIMEOUT_SECONDS: int = 10
    THREAT_INTEL_MAX_RETRIES: int = 1
    THREAT_INTEL_RETRY_BACKOFF_SECONDS: float = 0.5

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


def production_safety_issues(cfg: Settings) -> list[str]:
    if cfg.ENVIRONMENT != "production":
        return []

    issues: list[str] = []
    if cfg.DEBUG:
        issues.append("DEBUG must be false in production")
    if cfg.JWT_SECRET == "change-me-in-production-min-32-chars":
        issues.append("JWT_SECRET must be overridden in production")
    if cfg.BACKEND_CORS_ORIGINS.strip() == "*":
        issues.append("BACKEND_CORS_ORIGINS cannot be wildcard (*) in production")

    return issues


def validate_production_safety() -> None:
    issues = production_safety_issues(settings)

    if issues:
        raise RuntimeError("Production safety checks failed: " + "; ".join(issues))
