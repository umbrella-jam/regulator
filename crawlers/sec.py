# ======================================================
# SEC Crawler
# ======================================================
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseCrawler

class SecCrawler(BaseCrawler):
    BASE_URL = "https://www.sec.gov"
    PAGE_URL = "https://www.sec.gov/newsroom/press-releases?page={}"
    HEADERS = {
        "User-Agent": "Individual Marion <marion.umbel@gmail.com>",
    }

    def parse_page(self, soup, existing_links):
        rows = soup.select("table.usa-table tbody tr.pr-list-page-row")
        if not rows:
            rows = soup.select("div.view-content tr")  # fallback

        results = []
        for row in rows:
            date_el = row.select_one("time.datetime")
            title_el = row.select_one("td.views-field-field-display-title a")
            if not (date_el and title_el):
                continue

            link = self.BASE_URL + title_el["href"]
            if link in existing_links:
                continue

            pub_date = datetime.fromisoformat(
                date_el["datetime"].replace("Z", "+00:00")
            )

            results.append({
                "title": title_el.text.strip(),
                "link": link,
                "summary": "",
                "pubDate": pub_date.isoformat(),
                "source": "SEC",
            })

        return results