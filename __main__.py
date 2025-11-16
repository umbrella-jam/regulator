# regulator/__main__.py

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Callable
import html
from datetime import datetime, timezone



# ------------------------
# Helper Functions
# ------------------------

def load_rss_sources():
    path = Path(__file__).parent / "sources" / "rss_sources.json"
    return json.load(path.open())

def fetch_rss_feed(url: str, source_name: str = "") -> List[Dict]:
    """
    Fetch RSS feed using BeautifulSoup XML parser for leniency.
    Skips feeds that cannot be parsed.
    """
    headers = {"User-Agent": "Individual Marion <marion.umbel@gmail.com>"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch RSS feed {url}: {e}")
        return []

    # Parse with BeautifulSoup for leniency
    try:
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
    except Exception as e:
        print(f"Failed to parse RSS feed {url}: {e}")
        return []

    articles = []
    for item in items:
        try:
            title = item.title.text if item.title else ""
            link = item.link.text if item.link else ""
            pubDate = item.pubDate.text if item.pubDate else ""
            description = item.description.text if item.description else ""

            articles.append({
                "title": title.strip(),
                "link": link.strip(),
                "pubDate": pubDate.strip(),
                "summary": description.strip(),
                "source": source_name or url
            })
        except Exception as e:
            print(f"Skipping invalid item in {url}: {e}")
            continue

    return articles

def fetch_webpage(url: str) -> str:
    """
    Fetch HTML content from a webpage.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def scrape_news_page(url: str, parser: Callable[[str], List[Dict]], source_name: str = "") -> List[Dict]:
    """
    Scrape a news page using a custom parser function.
    """
    html = fetch_webpage(url)
    articles = parser(html)
    for a in articles:
        if "source" not in a or not a["source"]:
            a["source"] = source_name or url
    return articles

# ------------------------
# Example Parser
# ------------------------

from sources.fema import parse_all as fema_spider
from sources.irs import irs_spider

# ------------------------
# JSON Management
# ------------------------

DATA_FILE = Path(__file__).parent / "docs" / "data.json"

def load_json(file_path: Path) -> list[dict]:
    if file_path.exists():
        try:
            return json.load(file_path.open("r", encoding="utf-8"))
        except json.JSONDecodeError:
            print(f"Warning: {file_path} is corrupted. Starting fresh.")
            return []
    return []

def save_json(file_path: Path, data: list[dict]):
    file_path.parent.mkdir(parents=True, exist_ok=True)  # ensure docs/ exists
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def append_to_json(file_path: Path, new_articles: List[Dict]):
    existing_articles = load_json(file_path)
    existing_links = {a["link"] for a in existing_articles}

    # Only keep new articles not already in existing
    filtered_new = [a for a in new_articles if a["link"] not in existing_links]

    # Combine old + new
    combined = existing_articles + filtered_new

    # Sort by pubDate descending (newest first)
    def parse_date(article):
        raw = article.get("pubDate", "")
        if not raw:
            return datetime.min.replace(tzinfo=timezone.utc)

        # Try RSS format (e.g. "Fri, 15 Nov 2025 12:00:00 +0000")
        try:
            return datetime.strptime(raw, "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            pass

        # Try ISO 8601 like FEMA (e.g. "2025-11-14T10:30:00Z")
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

        # Fallback
        return datetime.min.replace(tzinfo=timezone.utc)



    combined.sort(key=parse_date, reverse=True)

    # Save and print
    save_json(file_path, combined)
    print(f"Added {len(filtered_new)} new articles. Total articles: {len(combined)}")

# ------------------------
# Main Scraper Class
# ------------------------

class NewsScraper:
    def __init__(self):
        self.sources = []

    def add_rss_source(self, url: str, source_name: str = ""):
        self.sources.append(("rss", url, source_name))

    def add_web_source(self, url: str, parser: Callable[[str], List[Dict]], source_name: str = ""):
        self.sources.append(("web", url, parser, source_name))

    def scrape_all(self) -> List[Dict]:
        all_articles = []
        for source in self.sources:
            try:
                if source[0] == "rss":
                    all_articles.extend(fetch_rss_feed(source[1], source_name=source[2]))
                elif source[0] == "web":
                    all_articles.extend(scrape_news_page(source[1], source[2], source_name=source[3]))
            except Exception as e:
                print(f"Failed to scrape {source}: {e}")
        return all_articles

# ------------------------
# Main Execution
# ------------------------

if __name__ == "__main__":
    scraper = NewsScraper()

    # Add RSS feeds
    for src in load_rss_sources():
        scraper.add_rss_source(src["url"], src["name"])
        
    # Add web sources
    # Add FEMA as a web source
    scraper.add_web_source(
        "https://www.fema.gov/about/news-multimedia/press-releases",
        lambda _: fema_spider("https://www.fema.gov/about/news-multimedia/press-releases"),
        "FEMA"
    )

    # Add IRS Criminal Investigation as a web source
    scraper.add_web_source(
        "https://www.irs.gov/compliance/criminal-investigation/criminal-investigation-press-releases",
        lambda html: irs_spider(html),
        "IRS Criminal Investigation"
    )



    # Scrape all sources
    articles = scraper.scrape_all()

    # Append to JSON file
    append_to_json(DATA_FILE, articles)
