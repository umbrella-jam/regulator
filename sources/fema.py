# fema.py
# Spider for FEMA press releases
# Returns articles in the common format: title, link, summary, pubDate, source

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import List, Dict
import requests

BASE_URL = "https://www.fema.gov"

def fetch_fema_page(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.text

def parse_page(html: str) -> Dict:
    """
    Parses a single FEMA press release listing page.
    Returns dict with:
        - items: list of dicts
        - next_page: str | None
    """
    soup = BeautifulSoup(html, "html.parser")
    items = []

    rows = soup.select("div.views-listing.views-row")
    for row in rows:
        title_el = row.select_one(".views-field-title a")
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        url = urljoin(BASE_URL, title_el.get("href", ""))

        summary_el = row.select_one(".views-field-body .field-content")
        summary = summary_el.get_text(strip=True) if summary_el else ""

        time_el = row.select_one("time.datetime")
        pubDate = time_el.get("datetime") if time_el else ""

        items.append({
            "title": title,
            "link": url,           # match common schema
            "summary": summary,
            "pubDate": pubDate,    # match common schema
            "source": "FEMA"
        })

    next_link = soup.select_one('a[rel="next"]')
    next_page = urljoin(BASE_URL, next_link.get("href")) if next_link else None

    return {
        "items": items,
        "next_page": next_page
    }

def parse_all(start_url: str) -> List[Dict]:
    """
    Fetches all FEMA press releases starting from `start_url`,
    following pagination automatically.
    """
    all_items = []
    url = start_url

    while url:
        html = fetch_fema_page(url)
        data = parse_page(html)
        all_items.extend(data["items"])
        url = data["next_page"]

    return all_items
