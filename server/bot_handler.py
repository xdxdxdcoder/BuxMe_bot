from __future__ import annotations

from typing import Any, Protocol

from server.config import Settings


WELCOME_TEXT = """Привет! Я Buxme AI-Scout.

Помогаю находить потенциальных B2B-клиентов с полевыми торговыми командами.

Как пользоваться:
1. Нажмите «Открыть AI-Scout».
2. Введите код сотрудника.
3. Укажите регион или город.
4. Запустите поиск и изучите рейтинг компаний.

Сейчас приложение работает в демонстрационном режиме на тестовых данных."""


class MessageSender(Protocol):
    async def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]: ...


def build_open_app_keyboard(settings: Settings) -> list[dict[str, Any]]:
    """Формирует официальную inline-кнопку MAX для запуска привязанной Mini App."""

    return [
        {
            "type": "inline_keyboard",
            "payload": {
                "buttons": [
                    [
                        {
                            "type": "open_app",
                            "text": "Открыть AI-Scout",
                            "web_app": settings.max_bot_username.lstrip("@"),
                            "payload": "welcome",
                        }
                    ]
                ]
            },
        }
    ]


def _extract_message_text(update: dict[str, Any]) -> str:
    message = update.get("message")
    if not isinstance(message, dict):
        return ""
    body = message.get("body")
    if not isinstance(body, dict):
        return ""
    text = body.get("text")
    return text.strip() if isinstance(text, str) else ""


async def handle_update(
    update: dict[str, Any],
    sender: MessageSender,
    settings: Settings,
) -> bool:
    """Обрабатывает события MAX и сообщает, было ли отправлено сообщение."""

    update_type = update.get("update_type")
    chat_id = update.get("chat_id")
    if not isinstance(chat_id, int):
        return False

    should_greet = update_type == "bot_started"
    if update_type == "message_created":
        command = _extract_message_text(update).casefold().split(maxsplit=1)[0]
        should_greet = command in {"/start", "/help", "помощь"}

    if not should_greet:
        return False

    await sender.send_message(
        chat_id,
        WELCOME_TEXT,
        attachments=build_open_app_keyboard(settings),
    )
    return True
