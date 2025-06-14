from feedgen.feed import FeedGenerator
import json
from datetime import datetime

with open("docs/data.json") as f:
    items = json.load(f)

fg = FeedGenerator()
fg.title("My Feed")
fg.link(href="https://yoursite.netlify.app/rss.xml", rel="self")
fg.description("Updates from my scraper")

for item in items:
    fe = fg.add_entry()
    fe.title(item["title"])
    fe.link(href=item["link"])
    fe.description(item["summary"])
    fe.pubDate(datetime.fromisoformat(item["pubDate"]))

fg.rss_file("docs/rss.xml")
