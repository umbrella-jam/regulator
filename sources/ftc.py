# ftc.py
# Spider for FTC news, speeches, press releases, and commission actions
# Returns articles in the common format: title, link, summary, pubDate, source

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict
import requests

BASE_URL = "https://www.ftc.gov"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

SECTION_URLS = {
    "press_releases": "https://www.ftc.gov/news-events/news/press-releases",
    "speeches": "https://www.ftc.gov/news-events/news/speeches",
    "commission_actions": "https://www.ftc.gov/news-events/news/commission-actions"
}

def fetch_ftc_page(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.text

def parse_page(html: str, source_name: str) -> Dict:
    """
    Parses a single FTC listing page.
    Returns dict with:
        - items: list of dicts
        - next_page: str | None
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []

    rows = soup.select("div.views-row")
    for row in rows:
        title_el = row.select_one("h3.node-title a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        link = urljoin(BASE_URL, title_el.get("href", ""))

        summary_el = row.select_one("div.field--name-body .field__item")
        summary = summary_el.get_text(strip=True) if summary_el else ""

        time_el = row.select_one("time")
        pubDate = time_el.get("datetime") if time_el else ""

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "pubDate": pubDate,
            "source": source_name
        })

    next_link = soup.select_one('a[rel="next"]')
    next_page = urljoin(BASE_URL, next_link.get("href")) if next_link else None

    return {
        "items": items,
        "next_page": next_page
    }

def ftc_spider(start_url: str, source_name: str) -> List[Dict]:
    """
    Fetches all articles from a given FTC section,
    following pagination automatically.
    """
    all_items = []
    url = start_url

    while url:
        html = fetch_ftc_page(url)
        data = parse_page(html, source_name)
        all_items.extend(data["items"])
        url = data["next_page"]

    return all_items

def fetch_all_sections() -> List[Dict]:
    """
    Fetches all three FTC sections at once and combines them.
    """
    all_articles = []
    for section, url in SECTION_URLS.items():
        all_articles.extend(ftc_spider(url, "FTC"))
    return all_articles

# Optional standalone test
if __name__ == "__main__":
    articles = fetch_all_sections()
    print(f"Fetched {len(articles)} articles.")
    for a in articles[:5]:
        print(a)
