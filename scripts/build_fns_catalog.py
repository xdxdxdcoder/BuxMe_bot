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
MAX_PER_REGION = 250
CATEGORY = {"1": "Микропредприятие", "2": "Малое предприятие", "3": "Среднее предприятие"}


def _core(name: str) -> str:
    name = name.casefold().replace("ё", "е")
    name = re.sub(r"\b(республика|область|край|автономная|автономный|округ|город)\b", "", name)
    return re.sub(r"[^а-я0-9]+", "", name)


def _region_name(raw: str, region_names: list[str]) -> str:
    if not raw:
        return ""
    core = _core(raw)
    matches = [name for name in region_names if _core(name) == core]
    return matches[0] if len(matches) == 1 else raw


def _company(doc: ET.Element, region_names: list[str]) -> dict[str, object] | None:
    org = doc.find("ОргВклМСП")
    if org is None:
        return None  # Do not collect sole proprietors or personal tax identifiers.
    activities = doc.find("СвОКВЭД")
    if activities is None:
        return None
    primary = activities.find("СвОКВЭДОсн")
    if primary is None:
        return None
    primary_code = primary.get("КодОКВЭД", "")
    is_primary = primary_code.startswith("46.45")
    has_additional = any(
        activity.get("КодОКВЭД", "").startswith("46.45")
        for activity in activities.findall("СвОКВЭДДоп")
    )
    # A secondary cosmetics code is relevant only for another trade business.
    if not is_primary and not (has_additional and primary_code.startswith(("46.", "47."))):
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
    city = city_tag.get("Наим", "") if city_tag is not None else ""
    name = org.get("НаимОргСокр") or org.get("НаимОрг") or ""
    inn = org.get("ИННЮЛ", "")
    if not name or not inn or not region:
        return None
    employees_raw = doc.get("ССЧР", "")
    return {
        "inn": inn,
        "name": name,
        "region": region,
        "regionCode": place.get("КодРегион", ""),
        "city": city,
        "okvedCode": primary_code,
        "okved_descr": primary.get("НаимОКВЭД", ""),
        "targetActivity": "primary" if is_primary else "additional",
        "employeesCount": int(employees_raw) if employees_raw.isdigit() else None,
        "employeesYear": 2025 if employees_raw.isdigit() else None,
        "mspCategory": CATEGORY.get(doc.get("КатСубМСП", ""), ""),
        "mspSince": doc.get("ДатаВклМСП", ""),
    }


def build(archive: Path, *, check_hash: bool = True) -> dict[str, object]:
    if check_hash:
        digest = hashlib.sha256()
        with archive.open("rb") as stream:
            for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != ARCHIVE_SHA256:
            raise ValueError("FNS archive checksum differs from the official download metadata")
    regions = json.loads(LOCATIONS.read_text(encoding="utf-8"))["regions"]
    by_region: dict[str, list[dict[str, object]]] = defaultdict(list)
    seen_inn: set[str] = set()
    with zipfile.ZipFile(archive) as zf:
        for index, member in enumerate(zf.infolist(), 1):
            if not member.filename.endswith(".xml"):
                continue
            root = ET.fromstring(zf.read(member))
            for doc in root.findall("Документ"):
                company = _company(doc, regions)
                if company and company["inn"] not in seen_inn:
                    seen_inn.add(str(company["inn"]))
                    by_region[str(company["region"])].append(company)
            if index % 1000 == 0:
                print(f"Parsed {index} of {len(zf.infolist())} XML files", flush=True)
    available = Counter({region: len(items) for region, items in by_region.items()})
    selected = []
    for region, items in sorted(by_region.items()):
        items.sort(key=lambda company: (
            company["targetActivity"] != "primary",
            company["mspCategory"] == "Микропредприятие",
            -(company["employeesCount"] or 0),
            company["inn"],
        ))
        selected.extend(items[:MAX_PER_REGION])
    return {
        "source": "ФНС России, Единый реестр субъектов МСП",
        "sourceUrl": SOURCE_URL,
        "archiveUrl": ARCHIVE_URL,
        "releasedAt": RELEASED_AT,
        "selection": f"Юридические лица с ОКВЭД 46.45; не более {MAX_PER_REGION} на регион",
        "availableByRegion": dict(sorted(available.items())),
        "companies": selected,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--skip-checksum", action="store_true")
    args = parser.parse_args()
    catalog = build(args.archive, check_hash=not args.skip_checksum)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(catalog, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Saved {len(catalog['companies'])} companies across {len(catalog['availableByRegion'])} regions to {OUTPUT}")


if __name__ == "__main__":
    main()
