from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

from api.max.webhook import app
from server.config import get_settings


class WebhookTests(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["BOT_TOKEN"] = "test-token"
        os.environ["MAX_WEBHOOK_SECRET"] = "test-secret"
        get_settings.cache_clear()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        os.environ.pop("BOT_TOKEN", None)
        os.environ.pop("MAX_WEBHOOK_SECRET", None)
        get_settings.cache_clear()

    def test_healthcheck_does_not_expose_secrets(self) -> None:
        response = self.client.get("/api/max/webhook")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["configured"])
        self.assertNotIn("test-token", response.text)

    def test_invalid_webhook_secret_is_rejected(self) -> None:
        response = self.client.post(
            "/api/max/webhook",
            headers={"X-Max-Bot-Api-Secret": "wrong-secret"},
            json={"update_type": "bot_started", "chat_id": 519},
        )

        self.assertEqual(response.status_code, 401)

    def test_unknown_update_is_acknowledged(self) -> None:
        response = self.client.post(
            "/api/max/webhook",
            headers={"X-Max-Bot-Api-Secret": "test-secret"},
            json={"update_type": "bot_stopped", "chat_id": 519},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True, "handled": False})


if __name__ == "__main__":
    unittest.main()
