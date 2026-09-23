"""Одноразовая безопасная регистрация production webhook в MAX."""

from __future__ import annotations

import asyncio
import getpass
import os
import sys
from pathlib import Path

# Позволяет запускать скрипт напрямую из корня репозитория без установки пакета.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.config import Settings
from server.max_client import MaxBotClient

WEBHOOK_URL = "https://bux-me-bot.vercel.app/api/max/webhook"
UPDATE_TYPES = ["bot_started", "message_created"]


async def main() -> None:
    # Значения можно передать через окружение; интерактивный ввод не отображает секреты.
    token = os.getenv("BOT_TOKEN") or getpass.getpass("BOT_TOKEN: ")
    secret = os.getenv("MAX_WEBHOOK_SECRET") or getpass.getpass("MAX_WEBHOOK_SECRET: ")
    settings = Settings(BOT_TOKEN=token, MAX_WEBHOOK_SECRET=secret)

    async with MaxBotClient(settings) as client:
        bot = await client.get_me()
        subscriptions_response = await client.request("GET", "/subscriptions")
        subscriptions = subscriptions_response.get("subscriptions", [])

        for subscription in subscriptions:
            if isinstance(subscription, dict) and subscription.get("url") == WEBHOOK_URL:
                print(f"Webhook уже подключён к @{bot.get('username', 'unknown')}")
                return

        result = await client.create_subscription(WEBHOOK_URL, secret, UPDATE_TYPES)
        if not result.get("success", False):
            raise RuntimeError(result.get("message", "MAX не подтвердил подписку"))

        print(f"Webhook успешно подключён к @{bot.get('username', 'unknown')}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as exc:
        print(f"Не удалось подключить webhook: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
