from __future__ import annotations

import unittest
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from scripts.build_fns_catalog import _company, _support_keys
from backend.parser import Parser, load_fns_catalog


class FnsCatalogTests(unittest.TestCase):
    def test_checked_in_catalog_supports_regions_cities_and_pages(self) -> None:
        catalog = load_fns_catalog()
        self.assertGreater(len(catalog["companies"]), 1000)
        self.assertTrue(all(company["okvedCode"] in {"46.45", "46.45.1"} for company in catalog["companies"]))
        parser = Parser()
        first, total = parser.parse_fns_catalog("Москва", limit=12)
        second, next_total = parser.parse_fns_catalog("Москва", limit=12, offset=12)
        self.assertEqual(total, next_total)
        self.assertGreater(total, 12)
        self.assertEqual(len(first), 12)
        self.assertTrue({entry["catalogId"] for entry in first}.isdisjoint(entry["catalogId"] for entry in second))
        city_matches, city_total = parser.parse_fns_catalog("Ростов-на-Дону")
        self.assertGreater(city_total, 0)
        self.assertTrue(all(entry["city"] == "Ростов-на-Дону" for entry in city_matches))
        krasnodar_city, city_total = parser.parse_fns_catalog("Краснодар")
        self.assertGreater(city_total, 0)
        self.assertTrue(all(entry["city"] == "Краснодар" for entry in krasnodar_city))
        _page, canonical_total = parser.parse_fns_catalog("Кемеровская область - Кузбасс")
        _page, alternate_total = parser.parse_fns_catalog("Кемеровская область — Кузбасс")
        self.assertEqual(canonical_total, alternate_total)

    def test_all_listed_regions_return_only_local_cosmetics_pages(self) -> None:
        locations = Path(__file__).resolve().parents[2] / "src/data/russian-locations.json"
        regions = json.loads(locations.read_text(encoding="utf-8"))["regions"]
        parser = Parser()
        for region in regions:
            with self.subTest(region=region):
                page, total = parser.parse_fns_catalog(region, limit=2)
                self.assertEqual(len(page), min(2, total))
                self.assertTrue(all(item["region"] == region for item in page))

    def test_selects_legal_cosmetics_wholesaler_and_excludes_personal_records(self) -> None:
        xml = ET.fromstring('''<Файл>
          <Документ КатСубМСП="2" ДатаВклМСП="10.03.2024" ССЧР="18">
            <ОргВклМСП НаимОргСокр="ООО &quot;Пример&quot;" ИННЮЛ="1234567890" />
            <СведМН КодРегион="61"><Регион Наим="Ростовская"/><Город Наим="Ростов-на-Дону"/></СведМН>
            <СвОКВЭД><СвОКВЭДОсн КодОКВЭД="46.45" НаимОКВЭД="Торговля оптовая косметикой"/></СвОКВЭД>
          </Документ>
          <Документ><ИПВклМСП ИННФЛ="123456789012"/></Документ>
        </Файл>''')
        regions = ["Ростовская область"]
        company = _company(xml.findall("Документ")[0], regions)
        self.assertIsNotNone(company)
        self.assertEqual(company["region"], "Ростовская область")
        self.assertEqual(company["city"], "Ростов-на-Дону")
        self.assertEqual(company["employeesCount"], 18)
        self.assertEqual(company["targetActivity"], "primary")
        self.assertIsNone(_company(xml.findall("Документ")[1], regions))

    def test_ip_is_searchable_without_publishing_personal_tax_ids(self) -> None:
        xml = ET.fromstring('''<Документ КатСубМСП="1" ДатаВклМСП="10.03.2024">
            <ИПВклМСП ИННФЛ="123456789012" ОГРНИП="123456789012345"><ФИОИП Фамилия="Иванова" Имя="Мария" Отчество="Петровна"/></ИПВклМСП>
            <СведМН КодРегион="61"><Регион Наим="Ростовская"/><Город Наим="Ростов-на-Дону"/></СведМН>
            <СвОКВЭД><СвОКВЭДОсн КодОКВЭД="46.45" НаимОКВЭД="Торговля оптовая косметикой"/></СвОКВЭД>
          </Документ>''')
        company = _company(xml, ["Ростовская область"])
        self.assertIsNotNone(company)
        self.assertEqual(company["name"], "ИП Иванова Мария Петровна")
        self.assertEqual(company["entityType"], "sole_proprietor")
        self.assertEqual(company["inn"], "")
        self.assertTrue(company["catalogId"].startswith("ip-"))
        self.assertNotIn("123456789012", str(company))

    def test_requires_primary_cosmetics_not_food_construction_or_soap(self) -> None:
        def record(code: str, employees: int) -> ET.Element:
            return ET.fromstring(f'''<Документ ССЧР="{employees}">
              <ОргВклМСП НаимОргСокр="ООО Пример" ИННЮЛ="1234567890"/>
              <СведМН><Регион Наим="Ростовская"/></СведМН>
              <СвОКВЭД><СвОКВЭДОсн КодОКВЭД="{code}" НаимОКВЭД="Оптовая торговля"/></СвОКВЭД>
            </Документ>''')
        self.assertEqual(_company(record("46.45.1", 8), ["Ростовская область"])["targetActivity"], "primary")
        for code in ("46.33", "46.73.6", "46.45.2", "47.75"):
            self.assertIsNone(_company(record(code, 8), ["Ростовская область"]))
        self.assertIsNone(_company(record("46.45", 0), ["Ростовская область"]))

    def test_secondary_cosmetics_code_does_not_admit_unrelated_primary_business(self) -> None:
        doc = ET.fromstring('''<Документ ССЧР="20">
          <ОргВклМСП НаимОргСокр="ООО Рыба" ИННЮЛ="1234567890"/>
          <СведМН><Регион Наим="Самарская"/></СведМН>
          <СвОКВЭД>
            <СвОКВЭДОсн КодОКВЭД="46.38" НаимОКВЭД="Рыба"/>
            <СвОКВЭДДоп КодОКВЭД="46.45"/>
          </СвОКВЭД>
        </Документ>''')
        self.assertIsNone(_company(doc, ["Самарская область"]))

    def test_support_records_match_business_without_exposing_ip_id(self) -> None:
        legal = ET.fromstring('<Документ><СвЮЛ ИННЮЛ="1234567890"/></Документ>')
        person = ET.fromstring('<Документ><СвФЛ ИННФЛ="123456789012" ОГРНИП="123456789012345"/></Документ>')
        self.assertEqual(_support_keys(legal), "1234567890")
        self.assertTrue(_support_keys(person).startswith("ip-"))
        self.assertNotIn("123456789012", _support_keys(person))


if __name__ == "__main__":
    unittest.main()
