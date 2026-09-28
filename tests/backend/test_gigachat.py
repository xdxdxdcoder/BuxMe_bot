from __future__ import annotations

import unittest

import httpx

from backend.gigachat import GigaChatError, GigaChatScorer
from server.config import Settings


def _response(payload: dict) -> httpx.Response:
    return httpx.Response(200, json=payload)


def _score_payload(label: str) -> dict:
    return {
        "choices": [
            {
                "message": {
                    "content": (
                        '{"value": 80, "level": "high", "label": "'
                        + label
                        + '", "explanation": "Описание", '
                        '"signals": ["Сигнал"], "reasons": ["Причина"], '
                        '"status": "promising"}'
                    )
                }
            }
        ]
    }


class FakeClient:
    def __init__(self, responses: list[httpx.Response]) -> None:
        self.responses = responses
        self.requests: list[dict] = []

    async def post(self, *args, **kwargs) -> httpx.Response:
        self.requests.append({"url": args[0], **kwargs})
        return self.responses.pop(0)


class GigaChatScorerTests(unittest.IsolatedAsyncioTestCase):
    def settings(self) -> Settings:
        return Settings(GIGACHAT_API_KEY="test-key")

    async def test_retries_when_first_result_is_english(self) -> None:
        client = FakeClient(
            [
                _response({"access_token": "token"}),
                _response(_score_payload("Suitable")),
                _response(_score_payload("Подходит")),
            ]
        )
        result = await GigaChatScorer(self.settings(), client).score({"name": "Компания"})
        self.assertEqual(result["label"], "Подходит")

    async def test_rejects_english_result_after_retry(self) -> None:
        client = FakeClient(
            [
                _response({"access_token": "token"}),
                _response(_score_payload("Suitable")),
                _response(_score_payload("Suitable")),
            ]
        )
        with self.assertRaises(GigaChatError):
            await GigaChatScorer(self.settings(), client).score({"name": "Компания"})

    async def test_reuses_oauth_token_and_requests_supported_json_schema(self) -> None:
        client = FakeClient([
            _response({"access_token": "token"}),
            _response(_score_payload("Подходит")),
            _response(_score_payload("Подходит")),
        ])
        scorer = GigaChatScorer(self.settings(), client)
        await scorer.score({"name": "Первая"})
        await scorer.score({"name": "Вторая"})
        self.assertEqual(len(client.requests), 3)
        self.assertEqual(client.requests[1]["json"]["response_format"]["type"], "json_schema")
        self.assertEqual(client.requests[1]["json"]["model"], "GigaChat-2")


if __name__ == "__main__":
    unittest.main()
