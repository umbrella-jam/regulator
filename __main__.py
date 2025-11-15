# regulator/__main__.py

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Callable
import html

# ------------------------
# Helper Functions
# ------------------------

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

def append_to_json(file_path: Path, new_articles: List[Dict]):
    existing_articles = load_json(file_path)
    existing_links = {a["link"] for a in existing_articles}

    # Only keep new articles not already in existing
    filtered_new = [a for a in new_articles if a["link"] not in existing_links]

    # Combine old + new
    combined = existing_articles + filtered_new

    # Sort by pubDate descending (newest first)
    def parse_date(article):
        try:
            return datetime.strptime(article["pubDate"], "%a, %d %b %Y %H:%M:%S %z")
        except Exception:
            return datetime.min  # fallback for bad/missing date

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
    scraper.add_rss_source("https://www.justice.gov/news/rss?m=1", "DOJ")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=blog_post&m=1", "DOJ Blog")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&m=1", "DOJ Press Release")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=speech&m=1", "DOJ Speech")
    scraper.add_rss_source("https://www.sec.gov/enforcement-litigation/litigation-releases/rss", "SEC Litigation")
    scraper.add_rss_source("https://www.sec.gov/enforcement-litigation/administrative-proceedings/rss", "SEC Administrative")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=361&field_component=1871&search_api_language=en&require_all=0", "DOJ Massachusetts")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=166&field_component=1691&search_api_language=en&require_all=0", "DOJ Middle Alabama")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=171&field_component=1696&search_api_language=en&require_all=0", "DOJ Northern Alabama")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=176&field_component=1701&search_api_language=en&require_all=0", "DOJ Southern Alabama")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=1686&search_api_language=en&require_all=0", "DOJ Alaska")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=186&field_component=1716&search_api_language=en&require_all=0", "DOJ Arizona")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=191&field_component=1706&search_api_language=en&require_all=0", "DOJ Eastern Arkansas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=196&field_component=1711&search_api_language=en&require_all=0", "DOJ Western Arkansas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=201&field_component=1721&search_api_language=en&require_all=0", "DOJ Central California")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=206&field_component=1726&search_api_language=en&require_all=0", "DOJ Eastern California")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=211&field_component=1731&search_api_language=en&show_public_archived=0&require_all=0", "DOJ Northern California")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=216&field_component=1736&search_api_language=en&require_all=0", "DOJ Southern California")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=221&field_component=1741&search_api_language=en&require_all=0", "DOJ Colorado")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=226&field_component=1746&search_api_language=en&require_all=0", "DOJ Connecticut")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=231&field_component=1756&search_api_language=en&require_all=0", "DOJ Delaware")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=236&field_component=1751&search_api_language=en&require_all=0", "DOJ Columbia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=1761&search_api_language=en&require_all=0", "DOJ Middle Florida")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&field_component=1766&search_api_language=en&show_public_archived=0&require_all=0", "DOJ Northern Florida")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&field_component=1771&search_api_language=en&show_public_archived=0&require_all=0", "DOJ Southern Florida")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=256&field_component=1776&search_api_language=en&require_all=0", "DOJ Middle Georgia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=261&field_component=1781&search_api_language=en&require_all=0", "DOJ Northern Georgia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=266&field_component=1786&search_api_language=en&require_all=0", "DOJ Southern Georgia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=271&field_component=1791&search_api_language=en&require_all=0", "DOJ Guam, Mariana Islands")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=276&field_component=1796&search_api_language=en&show_public_archived=0&require_all=0", "DOJ Hawaii")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=281&field_component=1811&search_api_language=en&require_all=0", "DOJ Idaho")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=286&field_component=1816&search_api_language=en&require_all=0", "DOJ Central Illinois")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=291&field_component=1821&search_api_language=en&require_all=0", "DOJ Northern Illinois")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=296&field_component=1826&search_api_language=en&require_all=0", "DOJ Southern Illinois")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=301&field_component=1831&search_api_language=en&require_all=0", "DOJ Northern Indiana")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=311&field_component=1801&search_api_language=en&require_all=0", "DOJ Northern Iowa")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=316&field_component=1806&search_api_language=en&require_all=0", "DOJ Southern Iowa")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=321&field_component=1841&search_api_language=en&require_all=0", "DOJ Kansas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=326&field_component=1846&search_api_language=en&require_all=0", "DOJ Eastern Kentucky")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=331&field_component=1851&search_api_language=en&require_all=0", "DOJ Western Kentucky")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=336&field_component=1856&search_api_language=en&require_all=0", "DOJ Eastern Louisiana")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=341&field_component=1861&search_api_language=en&require_all=0", "DOJ Middle Louisiana")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=346&field_component=1866&search_api_language=en&require_all=0", "DOJ Western Louisiana")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&field_component=1881&search_api_language=en&show_public_archived=0&require_all=0", "DOJ Maine")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=356&field_component=1876&search_api_language=en&require_all=0", "DOJ Maryland")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=361&field_component=1871&search_api_language=en&require_all=0", "DOJ Massachusetts")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=366&field_component=1886&search_api_language=en&require_all=0", "DOJ Eastern Michigan")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=371&field_component=1891&search_api_language=en&require_all=0", "DOJ Western Michigan")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=376&field_component=1896&search_api_language=en&require_all=0", "DOJ Minnesota")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=381&field_component=1911&search_api_language=en&require_all=0", "DOJ Northern Mississippi")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=386&field_component=1916&search_api_language=en&require_all=0", "DOJ Southern Mississippi")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=391&field_component=1901&search_api_language=en&require_all=0", "DOJ Eastern Missouri")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=396&field_component=1906&search_api_language=en&require_all=0", "DOJ Western Missouri")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=401&field_component=1921&search_api_language=en&require_all=0", "DOJ Montana")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=406&field_component=1946&search_api_language=en&require_all=0", "DOJ Nebraska")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=411&field_component=1966&search_api_language=en&require_all=0", "DOJ Nevada")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=1951&search_api_language=en&require_all=0", "DOJ New Hampshire")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=421&field_component=1956&search_api_language=en&show_public_archived=0&require_all=0", "DOJ New Jersey")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=426&field_component=1961&search_api_language=en&require_all=0", "DOJ New Mexico")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=431&field_component=1971&search_api_language=en&require_all=0", "DOJ Eastern New York")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=436&field_component=1976&search_api_language=en&require_all=0", "DOJ Northern New York")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=441&field_component=1981&search_api_language=en&require_all=0", "DOJ Southern New York")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=446&field_component=1986&search_api_language=en&require_all=0", "DOJ Western New York")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=451&field_component=1926&search_api_language=en&require_all=0", "DOJ Eastern North Carolina")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=456&field_component=1931&search_api_language=en&require_all=0", "DOJ Middle North Carolina")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=461&field_component=1936&search_api_language=en&require_all=0", "DOJ Western North Carolina")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=466&field_component=1941&search_api_language=en&require_all=0", "DOJ North Dakota")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=471&field_component=1991&search_api_language=en&require_all=0", "DOJ Northern Ohio")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=476&field_component=1996&search_api_language=en&require_all=0", "DOJ Southern Ohio")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&field_component=2001&search_api_language=en&show_public_archived=0&require_all=0", "DOJ Eastern Oklahoma")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=486&field_component=2006&search_api_language=en&require_all=0", "DOJ Northern Oklahoma")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=491&field_component=2011&search_api_language=en&require_all=0", "DOJ Western Oklahoma")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=496&field_component=2016&search_api_language=en&require_all=0", "DOJ Oregon")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=501&field_component=2021&search_api_language=en&require_all=0", "DOJ Eastern Pennsylvania")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=506&field_component=2031&search_api_language=en&require_all=0", "DOJ Middle Pennsylvania")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=511&field_component=2036&search_api_language=en&require_all=0", "DOJ Western Pennsylvania")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=2041&search_api_language=en&require_all=0", "DOJ Puerto Rico")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=521&field_component=2046&search_api_language=en&require_all=0", "DOJ Rhode Island")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=526&field_component=2051&search_api_language=en&require_all=0", "DOJ South Carolina")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=531&field_component=2056&search_api_language=en&require_all=0", "DOJ South Dakota")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=2061&search_api_language=en&require_all=0", "DOJ Eastern Tennessee")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=541&field_component=2066&search_api_language=en&require_all=0", "DOJ Middle Tennessee")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=546&field_component=2071&search_api_language=en&require_all=0", "DOJ Western Tennessee")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=551&field_component=2076&search_api_language=en&require_all=0", "DOJ Eastern Texas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=556&field_component=2081&search_api_language=en&require_all=0", "DOJ Northern Texas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=561&field_component=2091&search_api_language=en&require_all=0", "DOJ Southern Texas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=2096&field_date=2013-01-01&search_api_language=en&require_all=0", "DOJ Western Texas")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=571&field_component=2101&search_api_language=en&require_all=0", "DOJ Utah")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=576&field_component=2121&search_api_language=en&require_all=0", "DOJ Vermont")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=581&field_component=2116&search_api_language=en&require_all=0", "DOJ Virgin Islands")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=586&field_component=2106&search_api_language=en&require_all=0", "DOJ Eastern Virginia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=591&field_component=2111&search_api_language=en&require_all=0", "DOJ Western Virginia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=596&field_component=2126&search_api_language=en&require_all=0", "DOJ Eastern Washington")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&groupname=601&field_component=2131&search_api_language=en&require_all=0", "DOJ Western Washington")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=606&field_component=2146&search_api_language=en&require_all=0", "DOJ Northern West Virginia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=611&field_component=2151&search_api_language=en&require_all=0", "DOJ Southern West Virginia")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type%5B0%5D=press_release&type%5B1%5D=speech&field_component=2136&search_api_language=en&require_all=0", "DOJ Eastern Wisconsin")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=621&field_component=2141&search_api_language=en&require_all=0", "DOJ Western Wisconsin")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=626&field_component=2156&search_api_language=en&require_all=0", "DOJ Wyoming")
    scraper.add_rss_source("https://www.justice.gov/news/rss?type=press_release&groupname=306&field_component=1836&search_api_language=en&require_all=0", "DOJ Southern Indiana")


        
    # Add web sources (example)
    # scraper.add_web_source("https://example-news-site.com", example_news_site_parser, "Example News")

    # Scrape all sources
    articles = scraper.scrape_all()

    # Append to JSON file
    append_to_json(DATA_FILE, articles)
