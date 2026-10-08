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


class OutboxSettings(BaseModel):
    poll_interval: float = Field(default=1.0, gt=0)
    batch_size: int = Field(default=100, ge=1)


class GatewaySettings(BaseModel):
    min_delay: float = 2.0
    max_delay: float = 5.0
    success_rate: float = Field(default=0.9, ge=0, le=1)


class WebhookSettings(BaseModel):
    timeout: float = Field(default=10.0, gt=0)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_nested_delimiter="__",
        extra="ignore"
    )

    db: DatabaseSettings
    rabbit: RabbitSettings
    api_key: str = Field(min_length=1)
    outbox: OutboxSettings = OutboxSettings()
    gateway: GatewaySettings = GatewaySettings()
    webhook: WebhookSettings = WebhookSettings()
    debug: bool


settings = Settings()
