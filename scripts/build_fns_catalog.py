"""Build a small, reproducible B2B catalog from the public FNS SME ZIP release.

Usage: python scripts/build_fns_catalog.py /path/to/data-10092026-structure-12052026.zip
The source archive is not committed; only the filtered, dated JSON catalog is.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "backend/data/fns_sme_20260910.json"
LOCATIONS = ROOT / "src/data/russian-locations.json"
SOURCE_URL = "https://www.nalog.gov.ru/opendata/7707329152-rsmp/"
ARCHIVE_URL = "https://file.nalog.ru/opendata/7707329152-rsmp/data-10092026-structure-12052026.zip"
ARCHIVE_SHA256 = "082fb9645109dc07f73ec9174b3f178d4fece7045ef9c2184065465790d57443"
RELEASED_AT = "2026-09-10T00:00:00+03:00"
SUPPORT_SOURCE_URL = "https://www.nalog.gov.ru/opendata/7707329152-rsmppp/"
SUPPORT_ARCHIVE_URL = "https://file.nalog.ru/opendata/7707329152-rsmppp/data-20260915-structure-20230615.zip"
SUPPORT_SHA256 = "7b651669eac2098256ac9dfd850a1cbedca830a2850e28277212ef06955b89ce"
SUPPORT_RELEASED_AT = "2026-09-15T00:00:00+03:00"
MAX_PER_REGION = 1000
CATEGORY = {"1": "Микропредприятие", "2": "Малое предприятие", "3": "Среднее предприятие"}


def _core(name: str) -> str:
    name = name.casefold().replace("ё", "е")
    name = re.sub(r"\b(республика|область|край|автономная|автономный|округ|город)\b", "", name)
    return re.sub(r"[^а-я0-9]+", "", name)


def _region_name(raw: str, region_names: list[str]) -> str:
    if not raw:
        return ""
    core = _core(raw)
    if core == "байконур":
        return "Байконур"
    matches = [name for name in region_names if _core(name) == core]
    return matches[0] if len(matches) == 1 else raw


def _company(doc: ET.Element, region_names: list[str]) -> dict[str, object] | None:
    org = doc.find("ОргВклМСП")
    proprietor = doc.find("ИПВклМСП")
    if org is None and proprietor is None:
        return None
    activities = doc.find("СвОКВЭД")
    if activities is None:
        return None
    primary = activities.find("СвОКВЭДОсн")
    if primary is None:
        return None
    primary_code = primary.get("КодОКВЭД", "")
    # Buxme sells men's cosmetics to salons and barbershops. A secondary 46.45
    # code on a fish or construction wholesaler does not establish a fit.
    # 46.45.2 is soap-only, so it is outside this cosmetics prospect list.
    if primary_code not in {"46.45", "46.45.1"}:
        return None
    employees_raw = doc.get("ССЧР", "")
    # For legal entities, keep those with an observed team rather than nominal zero-person firms.
    if org is not None and (not employees_raw.isdigit() or int(employees_raw) < 5):
        return None
    place = doc.find("СведМН")
    if place is None:
        return None
    region_tag = place.find("Регион")
    if region_tag is None:
        return None
    region = _region_name(region_tag.get("Наим", ""), region_names)
    city_tag = place.find("Город")
    if city_tag is None:
        city_tag = place.find("НаселПункт")
    city = city_tag.get("Наим", "").strip() if city_tag is not None else ""
    if city.isupper():
        city = city.title()
    if org is not None:
        name = org.get("НаимОргСокр") or org.get("НаимОрг") or ""
        inn = org.get("ИННЮЛ", "")
        catalog_id = inn
        entity_type = "legal_entity"
    else:
        full_name = proprietor.find("ФИОИП") if proprietor is not None else None
        name_parts = [full_name.get(part, "") for part in ("Фамилия", "Имя", "Отчество")] if full_name is not None else []
        name_parts = [part.title() if part.isupper() else part for part in name_parts]
        name = "ИП " + " ".join(part for part in name_parts if part) if any(name_parts) else ""
        identifier = proprietor.get("ОГРНИП") or proprietor.get("ИННФЛ", "")
        # Personal tax identifiers stay out of the checked-in catalog and API.
        catalog_id = "ip-" + hashlib.sha256(identifier.encode()).hexdigest()[:24] if identifier else ""
        inn = ""
        entity_type = "sole_proprietor"
    if not name or not catalog_id or not region:
        return None
    return {
        "catalogId": catalog_id,
        "entityType": entity_type,
        "inn": inn,
        "name": name,
        "region": region,
        "regionCode": place.get("КодРегион", ""),
        "city": city,
        "okvedCode": primary_code,
        "okved_descr": primary.get("НаимОКВЭД", ""),
        "targetActivity": "primary",
        "employeesCount": int(employees_raw) if employees_raw.isdigit() else None,
        "employeesYear": 2025 if employees_raw.isdigit() else None,
        "mspCategory": CATEGORY.get(doc.get("КатСубМСП", ""), ""),
        "mspSince": doc.get("ДатаВклМСП", ""),
    }


def _verify_archive(archive: Path, expected: str) -> None:
    digest = hashlib.sha256()
    with archive.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected:
        raise ValueError("FNS archive checksum differs from the official download metadata")


def _support_keys(doc: ET.Element) -> str:
    legal = doc.find("СвЮЛ")
    if legal is not None:
        return legal.get("ИННЮЛ", "")
    person = doc.find("СвФЛ")
    if person is None or not person.get("ОГРНИП"):
        return ""
    return "ip-" + hashlib.sha256(person.get("ОГРНИП", "").encode()).hexdigest()[:24]


def _enrich_support(companies: list[dict[str, object]], archive: Path) -> int:
    by_id = {str(company["catalogId"]): company for company in companies}
    matched = set()
    with zipfile.ZipFile(archive) as zf:
        for index, member in enumerate(zf.infolist(), 1):
            if not member.filename.endswith(".xml"):
                continue
            root = ET.fromstring(zf.read(member))
            for doc in root.findall("Документ"):
                key = _support_keys(doc)
                if key in by_id:
                    by_id[key]["supportRegistry"] = True
                    matched.add(key)
            if index % 2000 == 0:
                print(f"Matched support records in {index} of {len(zf.infolist())} XML files", flush=True)
    return len(matched)


def build(archive: Path, *, support_archive: Path | None = None, check_hash: bool = True) -> dict[str, object]:
    if check_hash:
        _verify_archive(archive, ARCHIVE_SHA256)
        if support_archive is not None:
            _verify_archive(support_archive, SUPPORT_SHA256)
    regions = json.loads(LOCATIONS.read_text(encoding="utf-8"))["regions"]
    by_region: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen_ids: set[str] = set()
    with zipfile.ZipFile(archive) as zf:
        for index, member in enumerate(zf.infolist(), 1):
            if not member.filename.endswith(".xml"):
                continue
            root = ET.fromstring(zf.read(member))
            for doc in root.findall("Документ"):
                company = _company(doc, regions)
                if company and company["catalogId"] not in seen_ids:
                    seen_ids.add(str(company["catalogId"]))
                    by_region[str(company["region"])].append(company)
            if index % 1000 == 0:
                print(f"Parsed {index} of {len(zf.infolist())} XML files", flush=True)
    available = Counter({region: len(items) for region, items in by_region.items()})
    selected = []
    for region, items in sorted(by_region.items()):
        sort_key = lambda company: (
            {"primary": 0, "additional": 1, "wholesale": 2}[company["targetActivity"]],
            company["mspCategory"] == "Микропредприятие",
            -(company["employeesCount"] or 0),
            company["catalogId"],
        )
        legal = sorted((item for item in items if item["entityType"] == "legal_entity"), key=sort_key)
        proprietors = sorted((item for item in items if item["entityType"] == "sole_proprietor"), key=sort_key)
        preferred = legal[:MAX_PER_REGION // 2] + proprietors[:MAX_PER_REGION // 2]
        used = {item["catalogId"] for item in preferred}
        remaining = sorted((item for item in items if item["catalogId"] not in used), key=sort_key)
        chosen = preferred + remaining[:MAX_PER_REGION - len(preferred)]
        legal_chosen = [item for item in chosen if item["entityType"] == "legal_entity"]
        ip_chosen = [item for item in chosen if item["entityType"] == "sole_proprietor"]
        for index in range(max((len(legal_chosen) + 2) // 3, len(ip_chosen))):
            selected.extend(legal_chosen[index * 3 : index * 3 + 3])
            if index < len(ip_chosen):
                selected.append(ip_chosen[index])
    support_matches = _enrich_support(selected, support_archive) if support_archive is not None else 0
    return {
        "source": "ФНС России, Единый реестр субъектов МСП",
        "sourceUrl": SOURCE_URL,
        "archiveUrl": ARCHIVE_URL,
        "releasedAt": RELEASED_AT,
        "supportSourceUrl": SUPPORT_SOURCE_URL if support_archive is not None else None,
        "supportArchiveUrl": SUPPORT_ARCHIVE_URL if support_archive is not None else None,
        "supportReleasedAt": SUPPORT_RELEASED_AT if support_archive is not None else None,
        "supportMatches": support_matches,
        "selection": f"Основной ОКВЭД 46.45 или 46.45.1 (косметика и парфюмерия, без торговли только мылом); для юрлиц не менее 5 сотрудников за 2025 год; не более {MAX_PER_REGION} на территорию",
        "availableByRegion": dict(sorted(available.items())),
        "companies": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--support-archive", type=Path)
    parser.add_argument("--skip-checksum", action="store_true")
    args = parser.parse_args()
    catalog = build(args.archive, support_archive=args.support_archive, check_hash=not args.skip_checksum)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Saved {len(catalog['companies'])} businesses across {len(catalog['availableByRegion'])} territories, {catalog['supportMatches']} support matches to {OUTPUT}")


if __name__ == "__main__":
    main()
