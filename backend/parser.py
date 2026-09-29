from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


class ParserError(RuntimeError):
    """Ошибка получения JSON-результата Rusprofile."""


@lru_cache
def load_fns_catalog() -> dict[str, Any]:
    path = Path(__file__).resolve().parent / "data/fns_sme_20260910.json"
    return json.loads(path.read_text(encoding="utf-8"))


class Parser:
    """Адаптер готового сценария поиска Rusprofile через AJAX."""

    search_url = "https://www.rusprofile.ru/search-advanced"
    ajax_url_part = "/ajax/search/advanced"

    def parse_fns_catalog(
        self, region: str, limit: int = 12, offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search the dated, filtered official FNS SME open-data release."""
        if not 1 <= limit <= 20 or offset < 0:
            raise ValueError("Invalid catalog pagination")
        normalize = lambda value: re.sub(r"[^а-я0-9]+", "", value.casefold().replace("ё", "е"))
        requested = normalize(region.strip())
        if not requested:
            return [], 0
        companies = load_fns_catalog()["companies"]
        region_matches = [company for company in companies if normalize(company["region"]) == requested]
        city_matches = [company for company in companies if normalize(company["city"]) == requested]
        matches = region_matches or city_matches
        if not matches:
            matches = [
                company for company in companies
                if requested in normalize(company["region"])
                or requested in normalize(company["city"])
            ]
        return matches[offset : offset + limit], len(matches)

    def parse_rusprofile(self, region: str = "", limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.goto(self.search_url, wait_until="domcontentloaded", timeout=120_000)

                # Это тот же сценарий, что в корневом parser.py: выбран OKВЭД
                # оптовой торговли, а результат приходит в AJAX data.items.
                page.locator('//form[@id="filter-form"]/fieldset[2]').click()
                page.locator(
                    '//input[@placeholder="Название или код"]',
                ).fill("торговля оптовая парфюмерными и косметическими")
                locator = page.locator("ul.sublist")
                box = locator.bounding_box()
                if box is None:
                    raise ParserError("Rusprofile category list is not available")
                page.mouse.click(box["x"] + 50, box["y"] + box["height"] / 2)

                locator = page.locator('ul.sublist[data-level="3"]')
                box = locator.bounding_box()
                if box is None:
                    raise ParserError("Rusprofile OKVED level 3 is not available")
                page.mouse.click(box["x"] + 50, box["y"] + box["height"] / 2)

                with page.expect_response(
                    lambda response: self.ajax_url_part in response.url
                    and response.status == 200,
                    timeout=60_000,
                ) as response_info:
                    page.locator('ul.sublist[data-level="4"]').click()

                response = response_info.value
                data = response.json()
                return self._extract_items(data, limit, region)
            except PlaywrightTimeoutError as exc:
                raise ParserError("Rusprofile search response timed out") from exc
            finally:
                browser.close()

    @staticmethod
    def _extract_items(
        data: Any,
        limit: int,
        region: str = "",
    ) -> list[dict[str, Any]]:
        if not isinstance(data, dict) or data.get("success") is not True:
            raise ParserError("Rusprofile returned an unsuccessful response")

        result = data.get("data")
        items = result.get("items") if isinstance(result, dict) else None
        if not isinstance(items, list):
            raise ParserError("Rusprofile response has no data.items list")

        requested_region = region.strip().casefold()
        companies: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            if requested_region:
                item_region = str(item.get("region", "")).casefold()
                if requested_region not in item_region:
                    continue
            companies.append(item)
            if len(companies) >= limit:
                break
        return companies
