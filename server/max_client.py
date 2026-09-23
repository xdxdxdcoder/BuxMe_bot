from __future__ import annotations

import logging
from typing import Any

import httpx

from server.config import Settings

logger = logging.getLogger(__name__)


class MaxAPIError(RuntimeError):
    """Безопасная ошибка обращения к MAX Bot API без раскрытия токена."""


class MaxBotClient:
    """Универсальный асинхронный HTTP-клиент для MAX Bot API."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        token = settings.bot_token.get_secret_value()
        if not token:
            raise MaxAPIError("Переменная окружения BOT_TOKEN не настроена")

        self._client = httpx.AsyncClient(
            base_url=settings.max_api_base_url.rstrip("/"),
            headers={
                "Authorization": token,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=httpx.Timeout(10.0),
        )

    async def __aenter__(self) -> "MaxBotClient":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Выполняет JSON-запрос и единообразно обрабатывает ошибки сети/API."""

        try:
            response = await self._client.request(method, path, params=params, json=json)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            logger.warning("MAX API timeout: %s %s", method, path)
            raise MaxAPIError("MAX API не ответил вовремя") from exc
        except httpx.HTTPStatusError as exc:
            # Тело ответа ограничиваем, чтобы логи не разрастались и не содержали лишние данные.
            details = exc.response.text[:300]
            logger.error(
                "MAX API returned %s for %s %s: %s",
                exc.response.status_code,
                method,
                path,
                details,
            )
            raise MaxAPIError(f"MAX API вернул HTTP {exc.response.status_code}") from exc
        except httpx.RequestError as exc:
            logger.exception("Network error while calling MAX API: %s %s", method, path)
            raise MaxAPIError("Сетевая ошибка при обращении к MAX API") from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error("MAX API returned invalid JSON for %s %s", method, path)
            raise MaxAPIError("MAX API вернул некорректный JSON") from exc

        if not isinstance(payload, dict):
            raise MaxAPIError("MAX API вернул JSON неожиданного формата")

        return payload

    async def get_me(self) -> dict[str, Any]:
        """Проверяет токен и возвращает данные текущего бота."""

        return await self.request("GET", "/me")

    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Отправляет текст и необязательные вложения в диалог MAX."""

        body: dict[str, Any] = {"text": text, "notify": True}
        if attachments:
            body["attachments"] = attachments

        return await self.request(
            "POST",
            "/messages",
            params={"chat_id": chat_id},
            json=body,
        )

    async def create_subscription(
        self,
        webhook_url: str,
        webhook_secret: str,
        update_types: list[str],
    ) -> dict[str, Any]:
        """Регистрирует HTTPS webhook для событий бота."""

        return await self.request(
            "POST",
            "/subscriptions",
            json={
                "url": webhook_url,
                "secret": webhook_secret,
                "update_types": update_types,
            },
        )
