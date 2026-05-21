from warnings import warn

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./zly.db"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    jwt_secret: str = "change-me-in-production"
    cors_origins: str = "http://localhost:8000"
    default_domain: str = "localhost:8000"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 15
    jwt_refresh_expire_days: int = 7
    rate_limit_enabled: bool = True
    rate_limit_redirect: int = 100
    rate_limit_api: int = 60
    rate_limit_auth: int = 10
    rate_limit_window: int = 60
    max_upload_size_mb: int = 50

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

if settings.jwt_secret == "change-me-in-production":
    warn(
        "JWT secret is still the default value 'change-me-in-production'. "
        "Set a strong JWT_SECRET in production (at least 32 bytes).",
        stacklevel=2,
    )
