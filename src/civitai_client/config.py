from pydantic import PostgresDsn
from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class DatabaseSettings(BaseSettings):
    """Database connection settings with Pydantic validation"""
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "civitai_analytics"
    POSTGRES_SCHEMA: Optional[str] = None

    @property
    def asyncpg_url(self) -> str:
        """Get async PostgreSQL URL for asyncpg"""
        url = PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            path=f"/{self.POSTGRES_DB}"
        )
        if self.POSTGRES_SCHEMA:
            return f"{url}?options=-csearch_path%3D{self.POSTGRES_SCHEMA}"
        return str(url)

    class Config:
        """Pydantic config"""
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_db_settings() -> DatabaseSettings:
    """Get cached database settings"""
    return DatabaseSettings()
