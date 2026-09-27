from __future__ import annotations

import json
import re
import uuid
from typing import Any

import httpx

from server.config import Settings
from server.max_client import build_ssl_context


SYSTEM_PROMPT = """Ты — аналитик B2B-дистрибуции. Оцени компанию как потенциального
дистрибьютора косметического товара бренда.
Верни ровно один JSON без Markdown. Значения label, explanation, signals и reasons
пиши только на русском языке, с кириллицей. Не выдумывай факты или контакты.
Поля JSON: value (целое 0..100), level (low|medium|high), label, explanation,
signals (массив строк), reasons (массив строк), status (promising|in_progress|not_fit).
Технические значения level и status не переводи."""


class GigaChatError(RuntimeError):
    pass


class GigaChatScorer:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.AsyncClient(
            timeout=30.0,
            verify=build_ssl_context(),
        )
        self._owns_client = client is None

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def score(self, company: dict[str, Any]) -> dict[str, Any]:
        api_key = self.settings.gigachat_api_key.get_secret_value()
        if not api_key:
            raise GigaChatError("GIGACHAT_API_KEY is not configured")

        token_response = await self.client.post(
            self.settings.gigachat_auth_url,
            headers={
                "Authorization": f"Basic {api_key}",
                "Content-Type": "application/x-www-form-urlencoded",
                "RqUID": str(uuid.uuid4()),
            },
            data={"scope": self.settings.gigachat_scope},
        )
        if token_response.is_error:
            raise GigaChatError(f"GigaChat authorization failed: {token_response.status_code}")
        access_token = token_response.json().get("access_token")
        if not isinstance(access_token, str) or not access_token:
            raise GigaChatError("GigaChat authorization response has no access_token")

        result = await self._request_json(
            access_token,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Ответь JSON прямо сейчас. Все текстовые поля только на русском:\n"
                        + json.dumps(company, ensure_ascii=False)
                    ),
                },
            ],
        )
        if not self._has_russian_text(result):
            result = await self._request_json(
                access_token,
                [
                    {
                        "role": "system",
                        "content": (
                            "Верни только JSON. Переведи label, explanation, signals и "
                            "reasons на русский язык с кириллицей. Не меняй value, level "
                            "и status. Не добавляй Markdown."
                        ),
                    },
                    {"role": "user", "content": json.dumps(result, ensure_ascii=False)},
                ],
            )
        if not self._has_russian_text(result):
            raise GigaChatError("GigaChat returned non-Russian scoring text")
        return self._validate_result(result)

    async def _request_json(
        self,
        access_token: str,
        messages: list[dict[str, str]],
    ) -> dict[str, Any]:
        response = await self.client.post(
            self.settings.gigachat_chat_url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "model": "GigaChat",
                "temperature": 0.1,
                "response_format": {"type": "json_object"},
                "messages": messages,
            },
        )
        if response.is_error:
            raise GigaChatError(f"GigaChat scoring failed: {response.status_code}")
        try:
            content = response.json()["choices"][0]["message"]["content"]
            result = json.loads(content)
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise GigaChatError("GigaChat returned invalid scoring JSON") from exc
        if not isinstance(result, dict):
            raise GigaChatError("GigaChat scoring result must be an object")
        return result

    @staticmethod
    def _has_russian_text(result: dict[str, Any]) -> bool:
        texts = [result.get("label", ""), result.get("explanation", "")]
        texts.extend(result.get("signals", []))
        texts.extend(result.get("reasons", []))
        return all(not text or re.search(r"[А-Яа-яЁё]", text) for text in texts)

    @staticmethod
    def _validate_result(result: Any) -> dict[str, Any]:
        if not isinstance(result, dict):
            raise GigaChatError("GigaChat scoring result must be an object")
        if not isinstance(result.get("value"), int) or not 0 <= result["value"] <= 100:
            raise GigaChatError("GigaChat score value must be an integer from 0 to 100")
        if result.get("level") not in {"low", "medium", "high"}:
            raise GigaChatError("GigaChat score level is invalid")
        for field in ("label", "explanation"):
            if not isinstance(result.get(field), str):
                raise GigaChatError(f"GigaChat result field {field} is invalid")
        for field in ("signals", "reasons"):
            if not isinstance(result.get(field), list) or not all(
                isinstance(item, str) for item in result[field]
            ):
                raise GigaChatError(f"GigaChat result field {field} is invalid")
        if result.get("status") not in {"promising", "in_progress", "not_fit"}:
            raise GigaChatError("GigaChat result status is invalid")
        return result
