# regulator/__main__.py

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Callable

# ------------------------
# Helper Functions
# ------------------------

def fetch_rss_feed(url: str, source_name: str = "") -> List[Dict]:
    """
    Fetch news from an RSS feed using XML parsing (no feedparser).
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    content = response.content

    articles = []
    root = ET.fromstring(content)

    for item in root.findall(".//item"):
        title = item.findtext("title", default="")
        link = item.findtext("link", default="")
        published = item.findtext("pubDate", default="")
        summary = item.findtext("description", default="")

        articles.append({
            "title": title.strip(),
            "link": link.strip(),
            "pubDate": published.strip(),
            "summary": summary.strip(),
            "source": source_name or url
        })
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

def example_news_site_parser(html: str) -> List[Dict]:
    """
    Custom parser for a hypothetical news site.
    """
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    for article_tag in soup.find_all("article")[:5]:
        title_tag = article_tag.find("h2")
        link_tag = article_tag.find("a", href=True)
        summary_tag = article_tag.find("p")

        if title_tag and link_tag:
            articles.append({
                "title": title_tag.get_text(strip=True),
                "link": link_tag['href'],
                "pubDate": "",  # could parse date if available
                "summary": summary_tag.get_text(strip=True) if summary_tag else "",
                "source": ""  # filled later
            })
    return articles

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

def append_to_json(file_path: Path, new_articles: list[dict]):
    existing_articles = load_json(file_path)
    existing_links = {a["link"] for a in existing_articles}
    filtered_new = [a for a in new_articles if a["link"] not in existing_links]

    combined = existing_articles + filtered_new
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
    scraper.add_rss_source("https://www.justice.gov/news/rss?m=1", "DOJ")
        
    # Add web sources (example)
    # scraper.add_web_source("https://example-news-site.com", example_news_site_parser, "Example News")

    # Scrape all sources
    articles = scraper.scrape_all()

    # Append to JSON file
    append_to_json(DATA_FILE, articles)
