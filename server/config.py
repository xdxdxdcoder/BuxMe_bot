from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки backend, загружаемые только из переменных окружения."""

    bot_token: SecretStr = Field(default=SecretStr(""), alias="BOT_TOKEN")
    max_webhook_secret: SecretStr = Field(default=SecretStr(""), alias="MAX_WEBHOOK_SECRET")
    max_api_base_url: str = Field(
        default="https://platform-api2.max.ru",
        alias="MAX_API_BASE_URL",
    )
    max_bot_username: str = Field(
        default="t519_hakaton_max_bot",
        alias="MAX_BOT_USERNAME",
    )
    mini_app_url: str = Field(
        default="https://bux-me-bot.vercel.app/",
        alias="MINI_APP_URL",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Создаёт один экземпляр настроек на время жизни serverless-функции."""

    return Settings()
