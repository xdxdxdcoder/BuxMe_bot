from __future__ import annotations

from typing import Any, Protocol

from server.config import Settings


WELCOME_TEXT = """Привет! Я Buxme AI-Scout.

Помогаю находить оптовых продавцов косметики и парфюмерии для проверки как дистрибьюторов Buxme. Их ассортимент и каналы продаж уточняются при контакте.

Как пользоваться:
1. Нажмите «Открыть AI-Scout».
2. Введите код сотрудника.
3. Укажите регион или город.
4. Запустите поиск и изучите рейтинг компаний.

В приложении отмечено, какие данные и функции демонстрационные."""


class MessageSender(Protocol):
    async def send_message(
        self,
        recipient_id: int,
        text: str,
        *,
        attachments: list[dict[str, Any]] | None = None,
        recipient_kind: str = "chat",
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


def _extract_recipient(update: dict[str, Any]) -> tuple[str, int] | None:
    """Находит адресата для разных вариантов событий MAX."""

    chat_id = update.get("chat_id")
    if isinstance(chat_id, int) and chat_id:
        return "chat", chat_id

    message = update.get("message")
    if not isinstance(message, dict):
        return None

    recipient = message.get("recipient")
    if isinstance(recipient, dict):
        nested_chat_id = recipient.get("chat_id")
        if isinstance(nested_chat_id, int) and nested_chat_id:
            return "chat", nested_chat_id

    # В личном диалоге надёжный fallback — ID пользователя-отправителя.
    sender = message.get("sender")
    if isinstance(sender, dict):
        user_id = sender.get("user_id")
        if isinstance(user_id, int) and user_id:
            return "user", user_id

    return None


async def handle_update(
    update: dict[str, Any],
    sender: MessageSender,
    settings: Settings,
) -> bool:
    """Обрабатывает события MAX и сообщает, было ли отправлено сообщение."""

    update_type = update.get("update_type")
    recipient = _extract_recipient(update)
    if recipient is None:
        return False

    should_greet = update_type == "bot_started"
    if update_type == "message_created":
        command = _extract_message_text(update).casefold().split(maxsplit=1)[0]
        should_greet = command in {"/start", "/help", "помощь"}

    if not should_greet:
        return False

    recipient_kind, recipient_id = recipient
    await sender.send_message(
        recipient_id,
        WELCOME_TEXT,
        attachments=build_open_app_keyboard(settings),
        recipient_kind=recipient_kind,
    )
    return True
