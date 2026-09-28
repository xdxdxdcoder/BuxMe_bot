from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

from scripts.build_fns_catalog import _company
from backend.parser import Parser, load_fns_catalog


class FnsCatalogTests(unittest.TestCase):
    def test_checked_in_catalog_supports_regions_cities_and_pages(self) -> None:
        catalog = load_fns_catalog()
        self.assertGreater(len(catalog["companies"]), 1000)
        parser = Parser()
        first, total = parser.parse_fns_catalog("Москва", limit=12)
        second, next_total = parser.parse_fns_catalog("Москва", limit=12, offset=12)
        self.assertEqual(total, next_total)
        self.assertGreater(total, 12)
        self.assertEqual(len(first), 12)
        self.assertTrue({entry["inn"] for entry in first}.isdisjoint(entry["inn"] for entry in second))
        city_matches, city_total = parser.parse_fns_catalog("Ростов-на-Дону")
        self.assertGreater(city_total, 0)
        self.assertTrue(all(entry["city"] == "Ростов-на-Дону" for entry in city_matches))

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


if __name__ == "__main__":
    unittest.main()
