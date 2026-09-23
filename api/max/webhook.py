from __future__ import annotations

import hmac
import logging
from typing import Any, Optional

from fastapi import FastAPI, Header, HTTPException, Request

from server.bot_handler import handle_update
from server.config import get_settings
from server.max_client import MaxAPIError, MaxBotClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Buxme MAX Bot Webhook",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


# Vercel может передать ASGI-приложению как полный путь функции, так и корневой.
@app.get("/")
@app.get("/api/max/webhook")
async def healthcheck() -> dict[str, Any]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "buxme-max-bot",
        "configured": bool(
            settings.bot_token.get_secret_value()
            and settings.max_webhook_secret.get_secret_value()
        ),
    }


@app.post("/")
@app.post("/api/max/webhook")
async def max_webhook(
    request: Request,
    x_max_bot_api_secret: Optional[str] = Header(default=None),
) -> dict[str, bool]:
    """Принимает событие MAX, проверяет подпись и запускает обработчик бота."""

    settings = get_settings()
    expected_secret = settings.max_webhook_secret.get_secret_value()
    if not expected_secret:
        logger.error("MAX_WEBHOOK_SECRET is not configured")
        raise HTTPException(status_code=503, detail="Webhook is not configured")

    if not x_max_bot_api_secret or not hmac.compare_digest(
        x_max_bot_api_secret,
        expected_secret,
    ):
        logger.warning("Rejected MAX webhook with invalid secret")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    try:
        update = await request.json()
    except ValueError as exc:
        logger.warning("Rejected MAX webhook with invalid JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    if not isinstance(update, dict):
        raise HTTPException(status_code=400, detail="JSON object expected")

    try:
        async with MaxBotClient(settings) as client:
            handled = await handle_update(update, client, settings)
    except MaxAPIError as exc:
        # Не раскрываем клиенту детали и токен, но даём MAX повторить доставку события.
        logger.error("Failed to process MAX update: %s", exc)
        raise HTTPException(status_code=502, detail="MAX API request failed") from exc
    except Exception as exc:
        logger.exception("Unexpected MAX webhook error")
        raise HTTPException(status_code=500, detail="Internal webhook error") from exc

    logger.info("Processed MAX update type=%s handled=%s", update.get("update_type"), handled)
    return {"ok": True, "handled": handled}
