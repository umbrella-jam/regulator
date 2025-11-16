import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def irs_spider(html: str) -> list[dict]:
    """
    Parse IRS Criminal Investigation press releases from HTML.
    Returns a list of dicts with 'date', 'title', and 'url'.
    """
    articles = []
    soup = BeautifulSoup(html, "html.parser")

    # 1. Extract press releases on current page
    for month_section in soup.select("div.accordion-panel"):
        for date_block in month_section.select("h4"):
            date_text = date_block.get_text(strip=True)
            ul = date_block.find_next_sibling("ul")
            if not ul:
                continue
            for li in ul.select("li"):
                a_tag = li.find("a")
                if not a_tag:
                    continue
                articles.append({
                    "date": date_text,
                    "title": a_tag.get_text(strip=True),
                    "link": urljoin("https://www.irs.gov", a_tag.get("href"))
                })

    return articles
