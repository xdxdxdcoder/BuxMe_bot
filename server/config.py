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
    gigachat_api_key: SecretStr = Field(default=SecretStr(""), alias="GIGACHAT_API_KEY")
    gigachat_auth_url: str = Field(
        default="https://ngw.devices.sberbank.ru:9443/api/v2/oauth",
        alias="GIGACHAT_AUTH_URL",
    )
    gigachat_chat_url: str = Field(
        default="https://api.giga.chat/v1/chat/completions",
        alias="GIGACHAT_CHAT_URL",
    )
    gigachat_scope: str = Field(default="GIGACHAT_API_PERS", alias="GIGACHAT_SCOPE")
    gigachat_model: str = Field(default="GigaChat-2", alias="GIGACHAT_MODEL")
    scout_backend_url: str = Field(default="", alias="SCOUT_BACKEND_URL")
    scout_data_source: str = Field(default="fns", alias="SCOUT_DATA_SOURCE")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Создаёт один экземпляр настроек на время жизни serverless-функции."""

    return Settings()
