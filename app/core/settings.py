from pathlib import Path

from pydantic import AmqpDsn, BaseModel, Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class DatabaseSettings(BaseModel):
    url: PostgresDsn


class RabbitSettings(BaseModel):
    url: AmqpDsn
    max_attempts: int = Field(default=3, ge=1)
    retry_base_delay: float = Field(default=2.0, gt=0)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_nested_delimiter="__",
        extra="ignore"
    )

    db: DatabaseSettings
    rabbit: RabbitSettings
    debug: bool


settings = Settings()
