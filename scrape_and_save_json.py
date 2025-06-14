import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone

URL = "https://www.justice.gov/news"
BASE_URL = "https://www.justice.gov"

# Fetch the page
response = requests.get(URL)
response.raise_for_status()

# Parse the HTML
soup = BeautifulSoup(response.text, "html.parser")

data = []
for article in soup.select("article.news-content-listing"):
    title_el = article.select_one("h2.news-title a span")
    link_el = article.select_one("h2.news-title a")
    date_el = article.select_one("div.node-date time")

    if title_el and link_el and date_el:
        title = title_el.get_text(strip=True)
        link = BASE_URL + link_el["href"]
        pub_date_str = date_el["datetime"]
        pub_date = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))

        data.append({
            "title": title,
            "link": link,
            "summary": "",  # You can enhance this later if summaries are available
            "pubDate": pub_date.isoformat()
        })

# Save the data
with open("docs/data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
