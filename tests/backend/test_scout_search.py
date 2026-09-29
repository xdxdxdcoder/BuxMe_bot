from __future__ import annotations

import unittest
import os
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from api.scout.search import _candidate, _grounded_score, app
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
            patch.dict(os.environ, {"GIGACHAT_API_KEY": "test-key", "SCOUT_DATA_SOURCE": "rusprofile"}),
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

    def test_missing_ai_key_uses_labeled_factual_ranking(self) -> None:
        with patch.dict(os.environ, {"GIGACHAT_API_KEY": "", "SCOUT_DATA_SOURCE": "fns", "SCOUT_BACKEND_URL": ""}):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": "Москва", "limit": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scoringMode"], "factual")
        self.assertIn("Расчёт приоритета", response.json()["companies"][0]["score"]["explanation"])

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
        self.assertGreater(body["companies"][0]["score"]["value"], 40)
        self.assertLess(body["companies"][0]["score"]["value"], 80)
        self.assertIn("не подтверждены", body["companies"][0]["score"]["explanation"])

    def test_fns_search_exposes_source_count_and_next_page(self) -> None:
        score = {
            "value": 70, "level": "medium", "label": "Проверить",
            "explanation": "Нужна проверка", "signals": [], "reasons": [],
            "status": "in_progress",
        }
        with (
            patch.dict(os.environ, {"GIGACHAT_API_KEY": "test-key", "SCOUT_DATA_SOURCE": "fns", "SCOUT_BACKEND_URL": ""}),
            patch("backend.gigachat.GigaChatScorer.score", new_callable=AsyncMock, return_value=score),
        ):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": "Москва", "limit": 2})
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["mode"], "registry")
        self.assertEqual(body["total"], 2)
        self.assertGreater(body["availableTotal"], 2)
        self.assertTrue(body["hasMore"])
        self.assertEqual(body["companies"][0]["sources"][0]["id"], "fns")
        self.assertIn("nalog.gov.ru", body["companies"][0]["sources"][0]["url"])

    def test_ai_error_falls_back_to_factual_ranking(self) -> None:
        from backend.gigachat import GigaChatError

        with (
            patch.dict(os.environ, {"GIGACHAT_API_KEY": "test-key", "SCOUT_DATA_SOURCE": "fns", "SCOUT_BACKEND_URL": ""}),
            patch("backend.gigachat.GigaChatScorer.score", new_callable=AsyncMock, side_effect=GigaChatError("unavailable")),
        ):
            get_settings.cache_clear()
            response = self.client.post("/api/scout/search", json={"region": "Москва", "limit": 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["scoringMode"], "factual")
        self.assertEqual(response.json()["total"], 2)

    def test_grounded_ai_priority_varies_with_verified_company_data(self) -> None:
        model_score = {"value": 75}
        small_wholesaler = {
            "region": "Москва", "targetActivity": "primary", "mspCategory": "Малое предприятие",
            "employeesCount": 40, "mspSince": "10.03.2018",
        }
        micro_retailer = {
            "region": "Москва", "targetActivity": "additional", "mspCategory": "Микропредприятие",
            "employeesCount": 2, "mspSince": "10.03.2025",
        }
        high = _grounded_score(small_wholesaler, model_score)
        low = _grounded_score(micro_retailer, model_score)
        self.assertGreater(high["value"], low["value"])
        self.assertLess(high["value"], 80)
        self.assertIn("не подтверждены", high["explanation"])

    def test_support_registry_adds_second_source_without_increasing_score(self) -> None:
        company = {
            "catalogId": "ip-example", "entityType": "sole_proprietor", "name": "ИП Пример",
            "region": "Москва", "inn": "", "supportRegistry": True,
        }
        without_support = _grounded_score({**company, "supportRegistry": False}, {"value": 60})
        with_support = _grounded_score(company, {"value": 60})
        self.assertEqual(with_support["value"], without_support["value"])
        candidate = _candidate(
            company, with_support, "2026-09-10T00:00:00+03:00", "registry",
            "https://www.nalog.gov.ru/opendata/7707329152-rsmp/",
            "https://www.nalog.gov.ru/opendata/7707329152-rsmppp/",
            "2026-09-15T00:00:00+03:00",
        )
        self.assertEqual(candidate["id"], "ip-example")
        self.assertEqual(candidate["entityType"], "sole_proprietor")
        self.assertEqual(len(candidate["sources"]), 2)

    def test_curated_contact_is_attached_only_to_matching_inn(self) -> None:
        company = {"catalogId": "2225147567", "inn": "2225147567", "name": "ООО МЕЙТАН", "region": "Алтайский край"}
        score = _grounded_score(company, {"value": 50}, ai_used=False)
        candidate = _candidate(company, score, source_mode="registry")
        self.assertEqual(candidate["phone"], "+7 800 775-80-72")
        self.assertTrue(any(source["id"] == "company-contacts" for source in candidate["sources"]))
        other = _candidate({**company, "inn": "0000000000"}, score, source_mode="registry")
        self.assertEqual(other["phone"], "")

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
            patch.dict(os.environ, {"SCOUT_BACKEND_URL": "https://backend.example", "SCOUT_DATA_SOURCE": "snapshot", "GIGACHAT_API_KEY": ""}),
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
