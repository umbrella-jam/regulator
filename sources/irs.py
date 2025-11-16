# regulator/sources/irs.py

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone

def irs_spider(start_url: str):
    """
    Scrape IRS Criminal Investigation press releases.
    Returns a list of normalized article dicts with:
    'title', 'link', 'pubDate', 'summary', 'source'
    """
    visited_urls = set()
    urls_to_visit = [start_url]

    while urls_to_visit:
        url = urls_to_visit.pop(0)
        if url in visited_urls:
            continue
        visited_urls.add(url)

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            continue

        soup = BeautifulSoup(resp.text, "html.parser")

        # 1. Extract press releases on current page
        for month_section in soup.select("div.accordion-panel"):
            for date_block in month_section.select("h4"):
                date_text = date_block.get_text(strip=True)
                ul = date_block.find_next_sibling("ul")
                if not ul:
                    continue
                for li in ul.select("li"):
                    a_tag = li.find("a")
                    if not a_tag or not a_tag.get("href"):
                        continue

                    # Normalize date to ISO 8601 if possible
                    try:
                        dt = datetime.strptime(date_text, "%b. %d, %Y")
                        pubDate = dt.replace(tzinfo=timezone.utc).isoformat()
                    except Exception:
                        pubDate = ""  # fallback

                    yield {
                        "title": a_tag.get_text(strip=True),
                        "link": urljoin(url, a_tag.get("href")),
                        "pubDate": pubDate,
                        "summary": "",
                        "source": "IRS Criminal Investigation"
                    }

        # 2. Queue links to previous months
        for a_tag in soup.select("div.accordion-panel p a"):
            month_link = urljoin(url, a_tag.get("href"))
            if month_link not in visited_urls:
                urls_to_visit.append(month_link)
