from __future__ import annotations

import unittest
import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.scout.search import app
from server.config import get_settings


class ScoutSearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        get_settings.cache_clear()

    def tearDown(self) -> None:
        self.client.close()
        get_settings.cache_clear()

    def test_search_returns_candidate_cards_with_ai_score(self) -> None:
        companies = [
            {
                "name": "ООО Альфа",
                "region": "Москва",
                "inn": "1234567890",
                "phone": "+79990000000",
                "source_url": "https://www.rusprofile.ru/company/1",
            }
        ]
        score = {
            "value": 82,
            "level": "high",
            "label": "Подходит",
            "explanation": "Есть оптовый профиль и контакт.",
            "signals": ["оптовый профиль"],
            "reasons": ["доступен телефон"],
            "status": "promising",
        }
        with (
            patch.dict(os.environ, {"GIGACHAT_API_KEY": "test-key"}),
            patch("backend.parser.Parser.parse_rusprofile", return_value=companies),
            patch("backend.gigachat.GigaChatScorer.score", new_callable=AsyncMock, return_value=score),
        ):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": "Москва"})

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["companies"][0]["score"]["value"], 82)
        self.assertEqual(body["companies"][0]["status"], "promising")
        self.assertEqual(body["companies"][0]["sources"][0]["category"], "registry")

    def test_missing_ai_key_has_clear_configuration_error(self) -> None:
        with patch.dict(os.environ, {"GIGACHAT_API_KEY": ""}):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": "Москва"})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "AI-поиск ещё не настроен")

    def test_dated_snapshot_is_labeled_and_keeps_original_region(self) -> None:
        score = {
            "value": 70,
            "level": "medium",
            "label": "Проверить",
            "explanation": "Нужна проверка",
            "signals": [],
            "reasons": [],
            "status": "in_progress",
        }
        with (
            patch.dict(os.environ, {"GIGACHAT_API_KEY": "test-key", "SCOUT_DATA_SOURCE": "snapshot"}),
            patch("backend.parser.Parser.parse_rusprofile") as parser,
            patch("backend.gigachat.GigaChatScorer.score", new_callable=AsyncMock, return_value=score),
        ):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": "Москва", "limit": 1})

        parser.assert_not_called()
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "snapshot")
        self.assertEqual(body["total"], 1)
        self.assertEqual(body["companies"][0]["region"], "Москва")
        self.assertEqual(body["companies"][0]["sources"][0]["checkedAt"], body["sourceDate"])
        self.assertEqual(body["companies"][0]["score"]["value"], 60)
        self.assertIn("не подтверждены", body["companies"][0]["score"]["explanation"])

    def test_empty_region_is_rejected(self) -> None:
        response = self.client.post("/api/scout/search", json={"region": ""})
        self.assertEqual(response.status_code, 422)

        response = self.client.post("/api/scout/search", json={"region": "   "})
        self.assertEqual(response.status_code, 422)

    def test_proxy_forwards_search_to_configured_docker_backend(self) -> None:
        class BackendClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *_args):
                return None

            async def post(self, url, *, json):
                self.url = url
                self.payload = json
                return type("BackendResponse", (), {
                    "status_code": 200,
                    "json": lambda _self: {"mode": "live", "companies": [], "total": 0},
                })()

        backend = BackendClient()
        with (
            patch.dict(os.environ, {"SCOUT_BACKEND_URL": "https://backend.example", "GIGACHAT_API_KEY": ""}),
            patch("api.scout.search.httpx.AsyncClient", return_value=backend),
        ):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": " Москва "})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(backend.url, "https://backend.example/api/scout/search")
        self.assertEqual(backend.payload["region"], "Москва")
        self.assertEqual(response.json()["mode"], "live")


if __name__ == "__main__":
    unittest.main()
