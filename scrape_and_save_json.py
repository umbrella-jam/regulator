import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

BASE_URL = "https://www.justice.gov"
PAGE_URL = "https://www.justice.gov/news?page={}"

# Load existing data (if any)
try:
    with open("docs/data.json", "r", encoding="utf-8") as f:
        existing_data = json.load(f)
        existing_links = set(item["link"] for item in existing_data)
except (FileNotFoundError, json.JSONDecodeError):
    existing_data = []
    existing_links = set()

all_data = []
page = 0
found_existing = False

while not found_existing:
    try:
        headers = {
            "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
            "referer": f"https://www.justice.gov/news?page={max(page - 1, 0)}",  # mimic navigation from previous page
            "referrer-policy": "strict-origin-when-cross-origin"
        }

        response = requests.get(PAGE_URL.format(page), headers=headers)

        response.raise_for_status()
    except Exception as e:
        print(f"Stopping on page {page}: {e}")
        break

    soup = BeautifulSoup(response.text, "html.parser")
    articles = soup.select("article.news-content-listing")

    if not articles:
        print(f"No articles found on page {page}. Ending.")
        break

    new_articles = []
    for article in articles:
        title_el = article.select_one("h2.news-title a span")
        link_el = article.select_one("h2.news-title a")
        date_el = article.select_one("div.node-date time")

        if title_el and link_el and date_el:
            title = title_el.get_text(strip=True)
            link = BASE_URL + link_el["href"]
            pub_date_str = date_el["datetime"]
            pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))

            if link in existing_links:
                print(f"Found already saved link: {link}")
                found_existing = True
                break  # Stop page loop

            new_articles.append({
                "title": title,
                "link": link,
                "summary": "",
                "pubDate": pub_date.isoformat()
            })

    if new_articles:
        all_data.extend(new_articles)
        print(f"Page {page}: added {len(new_articles)} articles.")
    else:
        print(f"Page {page}: no new articles.")
        break

    page += 1
    time.sleep(1)

# Merge + dedupe
merged_data = all_data + existing_data
merged_data = {item['link']: item for item in merged_data}  # deduplicate by link
merged_data = sorted(merged_data.values(), key=lambda x: x["pubDate"], reverse=True)

with open("docs/data.json", "w", encoding="utf-8") as f:
    json.dump(merged_data, f, indent=2)

print(f"Saved {len(merged_data)} total articles to docs/data.json")
