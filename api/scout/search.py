from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from api.auth.max import AuthRequest, EmployeeResponse, authenticate
from server.config import get_settings

logger = logging.getLogger(__name__)
app = FastAPI(title="Buxme AI-Scout", docs_url="/docs", redoc_url=None)
DIST_DIR = Path(__file__).resolve().parents[2] / "dist"
if DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=DIST_DIR / "assets"), name="assets")
    app.mount("/brand", StaticFiles(directory=DIST_DIR / "brand"), name="brand")
VERIFIED_CONTACTS = {
    # Public contact of the company, checked against its official website.
    "2225147567": {
        "phone": "+7 800 775-80-72",
        "website": "https://meitanglobal.com/contacts/",
        "source": "https://meitanglobal.com/contacts/",
        "checked_at": "2026-09-30T00:00:00+03:00",
    },
    "7806577036": {
        "phone": "+7 800 550-98-50",
        "email": "b2b@parisnail.ru",
        "website": "https://parisnail.ru/contacts.html",
        "source": "https://parisnail.ru/contacts.html",
        "checked_at": "2026-09-30T00:00:00+03:00",
    },
    "9715397054": {
        "email": "sales@carely.group",
        "website": "https://art-fact-products.com/contacts/",
        "source": "https://art-fact-products.com/contacts/",
        "checked_at": "2026-09-30T00:00:00+03:00",
    },
}
app.add_api_route(
    "/api/auth/max",
    authenticate,
    methods=["POST"],
    response_model=EmployeeResponse,
)


class SearchRequest(BaseModel):
    region: str = Field(min_length=1, max_length=120)
    limit: int = Field(default=12, ge=1, le=20)
    offset: int = Field(default=0, ge=0, le=1000)

    @field_validator("region")
    @classmethod
    def region_is_not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Укажите регион или город")
        return value


@lru_cache
def _snapshot() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "backend/data/rusprofile_snapshot.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot_companies(region: str, limit: int, offset: int) -> tuple[list[dict[str, Any]], int]:
    requested = region.strip().casefold()
    matches = [
        company for company in _snapshot()["companies"]
        if requested in company["region"].casefold()
    ]
    return matches[offset : offset + limit], len(matches)


def _grounded_score(
    company: dict[str, Any], score: dict[str, Any], *, ai_used: bool = True,
) -> dict[str, Any]:
    """Blend the model's priority with verifiable signals, without invented claims."""
    activity = company.get("targetActivity", "primary")
    primary = activity == "primary"
    employees = company.get("employeesCount") or 0
    category = company.get("mspCategory", "")
    since = company.get("mspSince", "")
    years = max(0, 2026 - int(since[-4:])) if len(since) == 10 and since[-4:].isdigit() else 0
    evidence = (
        25 + {"primary": 20, "additional": 15, "wholesale": 13}.get(activity, 8)
        + {"Малое предприятие": 8, "Среднее предприятие": 12}.get(category, 0)
        + min(15, round(employees * 0.15))
        + min(6, years)
    )
    value = min(79, round(0.45 * score["value"] + 0.55 * evidence)) if ai_used else min(79, evidence)
    signals = [
        (
            f"ОКВЭД {company.get('okvedCode') or '46.45'} — {'основной' if primary else 'дополнительный'}"
            if activity in {"primary", "additional"}
            else f"Основной ОКВЭД {company.get('okvedCode', '')} — оптовая торговля"
        ),
    ]
    if company.get("employeesCount") is not None:
        signals.append(f"Среднесписочная численность за 2025 год: {employees}")
    if company.get("entityType") == "sole_proprietor":
        signals.append("ИП: численность и формат продаж требуют проверки")
    if category:
        signals.append(f"Категория МСП: {category.lower()}")
    if company.get("supportRegistry"):
        signals.append("Есть запись в реестре получателей поддержки МСП ФНС")
    signals.append(f"Регион: {company['region']}")
    code = company.get("okvedCode", "")
    profile = (
        f"основной ОКВЭД {code} — оптовая торговля парфюмерией и косметикой"
        if code in {"46.45", "46.45.1"}
        else f"основной оптовый ОКВЭД {code}" if code else "оптовый профиль"
    )
    team = (
        f"Среднесписочная численность за 2025 год — {employees}. "
        if company.get("employeesCount") is not None else
        "Численность в источнике не указана. "
    )
    return {
        "value": value,
        "level": "high" if value >= 70 else "medium" if value >= 45 else "low",
        "label": "Приоритет проверки" if value >= 60 else "Требуется проверка",
        "explanation": (
            ("AI-оценка приоритета" if ai_used else "Расчёт приоритета")
            + f": {profile}. {team}Наличие полевой команды и интерес к продукту "
            "не подтверждены; индекс не является вероятностью покупки."
        ),
        "signals": signals,
        "reasons": ["Уточнить структуру продаж и потребность компании перед контактом."],
        "status": "in_progress",
    }


def _candidate(
    company: dict[str, Any], score: dict[str, Any], checked_at: str | None = None,
    source_mode: str = "live", source_url: str | None = None,
    support_source_url: str | None = None, support_date: str | None = None,
) -> dict[str, Any]:
    contact = VERIFIED_CONTACTS.get(str(company.get("inn", "")), {})
    if source_mode == "registry":
        source = {"id": "fns", "title": "ФНС России, реестр МСП"}
    else:
        source = {"id": "rusprofile", "title": "Rusprofile"}
        source_path = company.get("source_url") or company.get("url") or company.get("link") or ""
        source_url = (
            source_path if str(source_path).startswith("http")
            else f"https://www.rusprofile.ru{source_path}" if source_path else None
        )
    sources = [{
        "id": source["id"],
        "title": source["title"],
        "category": "registry",
        "url": source_url or None,
        "checkedAt": checked_at or datetime.now(timezone.utc).isoformat(),
    }]
    if company.get("supportRegistry") and support_source_url and support_date:
        sources.append({
            "id": "fns-support",
            "title": "ФНС России, реестр получателей поддержки МСП",
            "category": "registry",
            "url": support_source_url,
            "checkedAt": support_date,
        })
    if contact:
        sources.append({
            "id": "company-contacts",
            "title": "Контакты на сайте компании",
            "category": "website",
            "url": contact["source"],
            "checkedAt": contact["checked_at"],
        })
    return {
        "id": company.get("catalogId") or company.get("inn") or company.get("aci_id") or str(uuid4()),
        "entityType": company.get("entityType", "legal_entity"),
        "name": company.get("name", ""),
        "region": company.get("region", ""),
        "city": company.get("city", ""),
        "inn": company.get("inn", ""),
        "phone": contact.get("phone") or company.get("phone", ""),
        "email": contact.get("email") or company.get("email", ""),
        "website": contact.get("website") or company.get("website", ""),
        "description": company.get("snippet_string", ""),
        "industry": company.get("okved_descr", ""),
        "employeesRange": (
            str(company["employeesCount"]) if company.get("employeesCount") is not None
            else company.get("employees_range", "")
        ),
        "employeesYear": company.get("employeesYear"),
        "score": {
            "value": score["value"],
            "level": score["level"],
            "label": score["label"],
            "explanation": score["explanation"],
        },
        "signals": score["signals"],
        "reasons": score["reasons"],
        "sources": sources,
        "status": score["status"],
    }


@app.get("/healthz")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "buxme-ai-scout"}


@app.get("/", response_model=None)
async def index() -> FileResponse | dict[str, str]:
    if (DIST_DIR / "index.html").is_file():
        return FileResponse(DIST_DIR / "index.html")
    return await healthcheck()


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
    # Keep the already bound Vercel URL usable while the Render service performs
    # GigaChat scoring. The bundled FNS catalog remains a fallback if Render
    # is sleeping or unavailable.
    proxy_url = settings.scout_backend_url
    if not proxy_url and os.getenv("VERCEL") and settings.scout_data_source == "fns":
        proxy_url = "https://buxme-scout-backend.onrender.com"
    if proxy_url:
        try:
            async with httpx.AsyncClient(timeout=75.0) as client:
                backend_response = await client.post(
                    f"{proxy_url.rstrip('/')}/api/scout/search",
                    json=request.model_dump(),
                )
            if backend_response.status_code != 200:
                raise ValueError(f"backend status {backend_response.status_code}")
            payload = backend_response.json()
        except (httpx.RequestError, ValueError) as exc:
            if settings.scout_data_source != "fns":
                logger.error("Scout backend proxy failed: %s", type(exc).__name__)
                raise HTTPException(status_code=502, detail="Сервер поиска недоступен") from exc
            logger.warning("AI backend unavailable, using bundled FNS catalog: %s", type(exc).__name__)
        else:
            return JSONResponse(
                status_code=backend_response.status_code,
                content=payload,
                headers={"Cache-Control": "no-store"},
            )

    try:
        from backend.gigachat import GigaChatError, GigaChatScorer
        from backend.parser import Parser, ParserError, load_fns_catalog
    except ImportError as exc:
        raise HTTPException(status_code=503, detail="Сервер поиска ещё не настроен") from exc
    try:
        source_mode = "live"
        source_date = None
        source_url = None
        support_source_url = None
        support_date = None
        if settings.scout_data_source == "fns":
            companies, available_total = Parser().parse_fns_catalog(
                request.region, request.limit, request.offset,
            )
            source_mode = "registry"
            source_date = load_fns_catalog()["releasedAt"]
            source_url = load_fns_catalog()["sourceUrl"]
            support_source_url = load_fns_catalog().get("supportSourceUrl")
            support_date = load_fns_catalog().get("supportReleasedAt")
        elif settings.scout_data_source == "snapshot":
            companies, available_total = _snapshot_companies(
                request.region, request.limit, request.offset,
            )
            source_mode = "snapshot"
            source_date = _snapshot()["capturedAt"]
        else:
            try:
                companies = await asyncio.to_thread(
                    Parser().parse_rusprofile,
                    request.region,
                    min(100, request.limit + request.offset),
                )
                available_total = len(companies)
                companies = companies[request.offset : request.offset + request.limit]
            except ParserError as exc:
                logger.warning("Rusprofile unavailable, using dated snapshot: %s", exc)
                companies, available_total = _snapshot_companies(
                    request.region, request.limit, request.offset,
                )
                source_mode = "snapshot"
                source_date = _snapshot()["capturedAt"]
        raw_scores = []
        if settings.gigachat_api_key.get_secret_value() and companies:
            scorer = GigaChatScorer(settings)
            try:
                for company in companies:
                    try:
                        score_input = {key: value for key, value in company.items() if key != "supportRegistry"}
                        raw_scores.append(await scorer.score(score_input))
                    except (GigaChatError, httpx.RequestError) as exc:
                        logger.warning("AI scoring unavailable, using factual ranking: %s", type(exc).__name__)
                        raw_scores = []
                        break
            finally:
                await scorer.close()
        scoring_mode = "giga" if len(raw_scores) == len(companies) and raw_scores else "factual"
        candidates = []
        for index, company in enumerate(companies):
            score = raw_scores[index] if scoring_mode == "giga" else {"value": 50}
            if source_mode in {"snapshot", "registry"} or scoring_mode == "factual":
                score = _grounded_score(company, score, ai_used=scoring_mode == "giga")
            candidates.append(_candidate(
                    company,
                    score,
                    source_date,
                    source_mode,
                    source_url,
                    support_source_url,
                    support_date,
                ))
    except Exception as exc:
        logger.exception("Company search failed")
        raise HTTPException(status_code=502, detail="Company search failed") from exc

    return {
        "requestId": str(uuid4()),
        "region": request.region.strip(),
        "companies": candidates,
        "total": len(candidates),
        "availableTotal": available_total,
        "offset": request.offset,
        "hasMore": request.offset + len(candidates) < available_total,
        "searchedAt": datetime.now(timezone.utc).isoformat(),
        "mode": source_mode,
        "scoringMode": scoring_mode,
        "sourceDate": source_date,
    }


@app.get("/{path:path}")
async def spa_fallback(path: str) -> FileResponse:
    if path.startswith("api/") or not (DIST_DIR / "index.html").is_file():
        raise HTTPException(status_code=404)
    return FileResponse(DIST_DIR / "index.html")
