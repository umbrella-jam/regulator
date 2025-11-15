
# ======================================================
# DOJ Crawler
# ======================================================
from bs4 import BeautifulSoup
from datetime import datetime
from .base import BaseCrawler


class DojCrawler(BaseCrawler):
    BASE_URL = "https://www.justice.gov"
    PAGE_URL = "https://www.justice.gov/news?page={}"
    HEADERS = {
        "User-Agent": "Mozilla/5.0",
    }

    def parse_page(self, soup, existing_links):
        articles = soup.select("article.news-content-listing")
        results = []

        for a in articles:
            title_el = a.select_one("h2.news-title a span")
            link_el = a.select_one("h2.news-title a")
            date_el = a.select_one("div.node-date time")

            if not (title_el and link_el and date_el):
                continue

            link = self.BASE_URL + link_el["href"]
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
                "source": "DOJ",
            })

        return results