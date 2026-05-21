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

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
