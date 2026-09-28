from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

os.environ.setdefault("PLAYWRIGHT_BROWSERS_PATH", "0")

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from api.auth.max import AuthRequest, EmployeeResponse, authenticate
from backend.gigachat import GigaChatError, GigaChatScorer
from backend.parser import Parser, ParserError
from server.config import get_settings

logger = logging.getLogger(__name__)
app = FastAPI(title="Buxme AI-Scout", docs_url="/docs", redoc_url=None)
app.add_api_route(
    "/api/auth/max",
    authenticate,
    methods=["POST"],
    response_model=EmployeeResponse,
)


class SearchRequest(BaseModel):
    region: str = Field(min_length=1, max_length=120)
    limit: int = Field(default=8, ge=1, le=20)


def _candidate(company: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    source_path = company.get("source_url") or company.get("url") or company.get("link") or ""
    source_url = (
        source_path
        if str(source_path).startswith("http")
        else f"https://www.rusprofile.ru{source_path}"
    )
    return {
        "id": company.get("inn") or company.get("aci_id") or str(uuid4()),
        "name": company.get("name", ""),
        "region": company.get("region", ""),
        "inn": company.get("inn", ""),
        "phone": company.get("phone", ""),
        "email": company.get("email", ""),
        "website": company.get("website", ""),
        "description": company.get("snippet_string", ""),
        "industry": company.get("okved_descr", ""),
        "employeesRange": company.get("employees_range", ""),
        "score": {
            "value": score["value"],
            "level": score["level"],
            "label": score["label"],
            "explanation": score["explanation"],
        },
        "signals": score["signals"],
        "reasons": score["reasons"],
        "sources": [
            {
                "id": "rusprofile",
                "title": "Rusprofile",
                "category": "registry",
                "url": source_url or None,
                "checkedAt": datetime.now(timezone.utc).isoformat(),
            }
        ],
        "status": score["status"],
    }


@app.get("/")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "buxme-ai-scout"}


@app.post("/")
@app.post("/api/scout/search")
async def search_companies(
    request: SearchRequest,
    response: Response,
) -> dict[str, Any]:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    settings = get_settings()
    if not settings.gigachat_api_key.get_secret_value():
        raise HTTPException(status_code=503, detail="AI-поиск ещё не настроен")
    try:
        companies = await asyncio.to_thread(
            Parser().parse_rusprofile,
            request.region,
            request.limit,
        )
        scorer = GigaChatScorer(settings)
        try:
            candidates = [
                _candidate(company, await scorer.score(company))
                for company in companies
            ]
        finally:
            await scorer.close()
    except GigaChatError as exc:
        logger.error("AI scoring failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI scoring service failed") from exc
    except ParserError as exc:
        logger.error("Rusprofile parsing failed: %s", exc)
        raise HTTPException(status_code=502, detail="Company search failed") from exc
    except Exception as exc:
        logger.exception("Company search failed")
        raise HTTPException(status_code=502, detail="Company search failed") from exc

    return {
        "requestId": str(uuid4()),
        "region": request.region.strip(),
        "companies": candidates,
        "total": len(candidates),
        "searchedAt": datetime.now(timezone.utc).isoformat(),
        "mode": "live",
    }
