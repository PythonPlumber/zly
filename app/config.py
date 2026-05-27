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
    rate_limit_tracking: int = 60
    rate_limit_window: int = 60
    max_upload_size_mb: int = 50
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "no-reply@zly.ai"
    smtp_from_name: str = "Zly"
    domain_verify_prefix: str = "zly-verify"
    click_retention_days: int = 365
    data_retention_enabled: bool = True
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    oauth_redirect_url: str = "http://localhost:8000/api/v1/auth/oauth/callback"
    secure_cookies: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()

if settings.secret_key == "change-me-in-production":
    warn(
        "SECRET_KEY is still the default value 'change-me-in-production'. "
        "Set a strong SECRET_KEY in production (at least 32 bytes).",
        stacklevel=2,
    )

if settings.jwt_secret == "change-me-in-production":
    warn(
        "JWT secret is still the default value 'change-me-in-production'. "
        "Set a strong JWT_SECRET in production (at least 32 bytes).",
        stacklevel=2,
    )
