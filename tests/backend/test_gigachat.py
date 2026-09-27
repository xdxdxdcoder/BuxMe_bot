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

    async def post(self, *args, **kwargs) -> httpx.Response:
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


if __name__ == "__main__":
    unittest.main()
