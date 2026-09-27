from bs4 import BeautifulSoup as bs
from matplotlib.pyplot import box
from matplotlib.pyplot import box
from requests import get, Session, session
from urllib.parse import quote
from logger import logger
from datetime import datetime, timedelta
from pathlib import Path
from playwright.sync_api import sync_playwright

class Parser:
    def __init__(self):
        pass
    
    def parse_rusprofile(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            def handle_response(response):
                if "/ajax/search/advanced" in response.url:
                    print("URL:", response.url)
                    print("Status:", response.status)

                    try:
                        data = response.json()
                        print(data)
                    except Exception as e:
                        print("Не JSON:", e)

            

            page.goto("https://www.rusprofile.ru/search-advanced")

            
            page.locator('//form[@id="filter-form"]/fieldset[2]').click()
            page.locator('//input[@placeholder="Название или код"]').fill("торговля оптовая парфюмерными и косметическими")
            locator = page.locator('ul.sublist')
            box = locator.bounding_box()
            x = box["x"] + 50
            y = box["y"] + box["height"] / 2
            page.mouse.click(x, y)
            
            locator = page.locator('ul.sublist[data-level="3"]')
            box = locator.bounding_box()
            x = box["x"] + 50
            y = box["y"] + box["height"] / 2
            page.mouse.click(x, y)
            
            page.on("response", handle_response)
            page.locator('ul.sublist[data-level="4"]').click()

            page.pause()

            browser.close()
         

parser = Parser()
parser.parse_rusprofile()