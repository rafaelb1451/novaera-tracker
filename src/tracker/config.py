from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Ambiente
    environment: str = Field("development", alias="ENVIRONMENT")

    # Banco
    database_url: str = Field(..., alias="DATABASE_URL")

    # API
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    api_secret_key: str = Field(..., alias="API_SECRET_KEY")
    api_access_token_expire_minutes: int = Field(1440, alias="API_ACCESS_TOKEN_EXPIRE_MINUTES")

    # Coletor
    novaera_base_url: str = Field(..., alias="NOVAERA_BASE_URL")
    user_agent: str = Field(..., alias="USER_AGENT")
    request_delay_seconds: float = Field(1.0, alias="REQUEST_DELAY_SECONDS")
    max_paginas_por_categoria: int = Field(20, alias="MAX_PAGINAS_POR_CATEGORIA")

    # Logs
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()