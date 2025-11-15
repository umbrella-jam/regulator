# ======================================================
# Base Crawler
# ======================================================

import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime


class BaseCrawler:
    BASE_URL = None
    PAGE_URL = None
    HEADERS = {}
    SLEEP = 1

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    # ---- override this: build URL for page N
    def make_page_url(self, page: int) -> str:
        return self.PAGE_URL.format(page)

    # ---- override this: parse BeautifulSoup → list of dicts
    def parse_page(self, soup, existing_links):
        raise NotImplementedError

    # ---- optional: override if "no more articles" logic differs
    def no_more_results(self, items):
        return len(items) == 0

    def crawl(self, existing_links):
        print(f"\n=== Crawling {self.__class__.__name__} ===")

        results = []
        page = 0

        while True:
            url = self.make_page_url(page)
            print(f"[{self.__class__.__name__}] Page {page}: {url}")

            try:
                resp = self.session.get(url, timeout=10)
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"Stopping on page {page}: {e}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            new_items = self.parse_page(soup, existing_links)

            if self.no_more_results(new_items):
                print("No more results. Stopping.")
                break

            results.extend(new_items)
            page += 1
            time.sleep(self.SLEEP)

        print(f"{self.__class__.__name__}: added {len(results)}")
        return results