import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from regulator.utils.storage import load_existing_data, save_data
from regulator.crawlers.doj import DojCrawler
from regulator.crawlers.sec import SecCrawler

DATA_PATH = "docs/data.json"

# ======================================================
# Main
# ======================================================

def main():
    existing_data, existing_links = load_existing_data()
    print(f"Loaded {len(existing_data)} existing.")

    crawlers = [
        DojCrawler(),
        SecCrawler(),
    ]

    new_data = []
    for crawler in crawlers:
        new_data.extend(crawler.crawl(existing_links))

    merged = new_data + existing_data

    # dedupe by link
    merged_dict = {item["link"]: item for item in merged}
    merged_list = sorted(
        merged_dict.values(),
        key=lambda x: x["pubDate"],
        reverse=True,
    )

    save_data(merged_list)


if __name__ == "__main__":
    main()