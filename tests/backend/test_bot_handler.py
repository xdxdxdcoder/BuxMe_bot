from __future__ import annotations

import unittest
from typing import Any

from pydantic import SecretStr

from server.bot_handler import handle_update
from server.config import Settings


class FakeSender:
    def __init__(self) -> None:
        self.messages: list[dict[str, Any]] = []

    async def send_message(
        self,
        recipient_id: int,
        text: str,
        *,
        attachments: list[dict[str, Any]] | None = None,
        recipient_kind: str = "chat",
    ) -> dict[str, Any]:
        self.messages.append(
            {
                "recipient_id": recipient_id,
                "recipient_kind": recipient_kind,
                "text": text,
                "attachments": attachments,
            }
        )
        return {"message": {}}


class BotHandlerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.settings = Settings(
            BOT_TOKEN=SecretStr("test-token"),
            MAX_WEBHOOK_SECRET=SecretStr("test-secret"),
            MAX_BOT_USERNAME="t519_hakaton_max_bot",
        )
        self.sender = FakeSender()

    async def test_bot_started_sends_welcome_with_open_app_button(self) -> None:
        handled = await handle_update(
            {"update_type": "bot_started", "chat_id": 519},
            self.sender,
            self.settings,
        )

        self.assertTrue(handled)
        self.assertEqual(self.sender.messages[0]["recipient_id"], 519)
        self.assertEqual(self.sender.messages[0]["recipient_kind"], "chat")
        button = self.sender.messages[0]["attachments"][0]["payload"]["buttons"][0][0]
        self.assertEqual(button["type"], "open_app")
        self.assertEqual(button["web_app"], "t519_hakaton_max_bot")

    async def test_help_command_sends_instructions(self) -> None:
        handled = await handle_update(
            {
                "update_type": "message_created",
                "message": {
                    "recipient": {"chat_id": 519},
                    "sender": {"user_id": 2048},
                    "body": {"text": "/help"},
                },
            },
            self.sender,
            self.settings,
        )

        self.assertTrue(handled)
        self.assertEqual(self.sender.messages[0]["recipient_id"], 519)
        self.assertIn("Как пользоваться", self.sender.messages[0]["text"])

    async def test_direct_message_falls_back_to_user_id(self) -> None:
        handled = await handle_update(
            {
                "update_type": "message_created",
                "message": {
                    "recipient": {"chat_id": 0},
                    "sender": {"user_id": 2048},
                    "body": {"text": "/start"},
                },
            },
            self.sender,
            self.settings,
        )

        self.assertTrue(handled)
        self.assertEqual(self.sender.messages[0]["recipient_id"], 2048)
        self.assertEqual(self.sender.messages[0]["recipient_kind"], "user")

    async def test_unknown_message_is_ignored(self) -> None:
        handled = await handle_update(
            {
                "update_type": "message_created",
                "chat_id": 519,
                "message": {"body": {"text": "Привет"}},
            },
            self.sender,
            self.settings,
        )

        self.assertFalse(handled)
        self.assertEqual(self.sender.messages, [])


if __name__ == "__main__":
    unittest.main()
