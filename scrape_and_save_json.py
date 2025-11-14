import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

DOJ_BASE = "https://www.justice.gov"
DOJ_PAGE_URL = "https://www.justice.gov/news?page={}"

SEC_BASE = "https://www.sec.gov"
SEC_PAGE_URL = "https://www.sec.gov/newsroom/press-releases?page={}"

DATA_PATH = "docs/data.json"

USER_AGENT_HEADERS = {
    "sec-ch-ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "\"Windows\"",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
}

# -----------------------------
# Load existing JSON
# -----------------------------
def load_existing_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, set(item["link"] for item in data)
    except (FileNotFoundError, json.JSONDecodeError):
        return [], set()


# -----------------------------
# Save JSON
# -----------------------------
def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved {len(data)} total records → {DATA_PATH}")

# -----------------------------
# DOJ Crawler
# -----------------------------
def crawl_doj(existing_links):
    print("\n=== Crawling DOJ ===")

    results = []
    page = 0

    while True:
        url = DOJ_PAGE_URL.format(page)
        print(f"DOJ Page {page}: {url}")

        headers = USER_AGENT_HEADERS.copy()
        headers["referer"] = DOJ_PAGE_URL.format(max(page - 1, 0))

        try:
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Stopping DOJ on page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        articles = soup.select("article.news-content-listing")
        if not articles:
            print("No more DOJ articles found.")
            break

        new_found_on_page = False

        for article in articles:
            title_el = article.select_one("h2.news-title a span")
            link_el = article.select_one("h2.news-title a")
            date_el = article.select_one("div.node-date time")

            if not (title_el and link_el and date_el):
                continue

            title = title_el.text.strip()
            link = DOJ_BASE + link_el["href"]
            pub_date = date_el["datetime"]

            if link not in existing_links:
                results.append({
                    "title": title,
                    "link": link,
                    "summary": "",
                    "pubDate": datetime.fromisoformat(pub_date.replace("Z", "+00:00")).isoformat(),
                    "source": "DOJ",
                })
                new_found_on_page = True

        if not new_found_on_page:
            print(f"DOJ: No new articles found on page {page}. Stopping crawl.")
            break

        page += 1
        time.sleep(1)

    print(f"DOJ: added {len(results)} new articles")
    return results


# -----------------------------
# SEC Crawler
# -----------------------------
def crawl_sec(existing_links, max_pages=10):
    headers_SEC = {
        "User-Agent": "Individual Marion<marion.umbel@gmail.com>",
        "Accept": "gzip, deflate",
        "Host": "www.sec.gov",
    }
    session = requests.Session()
    session.headers.update(headers_SEC)

    results = []
    for page in range(max_pages):
        url = SEC_PAGE_URL.format(page)
        print(f"SEC Page {page}: {url}")

        try:
            resp = session.get(url, allow_redirects=True, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Stopping SEC on page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("table.usa-table tbody tr.pr-list-page-row")
        if not rows:
            rows = soup.select("div.view-content tr")  # fallback
        if not rows:
            print("No more SEC rows found.")
            break

        new_found_on_page = False

        for row in rows:
            date_el = row.select_one("time.datetime")
            title_el = row.select_one("td.views-field-field-display-title a")

            if not (date_el and title_el):
                continue

            pub_date = date_el["datetime"]
            title = title_el.get_text(strip=True)
            link = SEC_BASE + title_el["href"]

            if link not in existing_links:
                results.append({
                    "title": title,
                    "link": link,
                    "summary": "",
                    "pubDate": datetime.fromisoformat(pub_date.replace("Z", "+00:00")).isoformat(),
                    "source": "SEC",
                })
                new_found_on_page = True

        if not new_found_on_page:
            print(f"SEC: No new articles found on page {page}. Stopping crawl.")
            break

        time.sleep(1)

    print(f"SEC: added {len(results)} new articles")
    return results



# -----------------------------
# Main
# -----------------------------
def main():
    existing_data, existing_links = load_existing_data()
    print(f"Loaded {len(existing_data)} existing records.")

    new_doj = crawl_doj(existing_links)
    new_sec = crawl_sec(existing_links)

    merged = new_doj + new_sec + existing_data

    # Deduplicate
    merged = {item["link"]: item for item in merged}
    merged = sorted(merged.values(), key=lambda x: x["pubDate"], reverse=True)

    save_data(merged)


if __name__ == "__main__":
    main()
