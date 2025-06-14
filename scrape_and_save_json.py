import json
from datetime import datetime, timezone

# Example scraped data
data = [
    {
        "title": "Example Article",
        "link": "https://example.com/article",
        "summary": "This is a summary.",
        "pubDate": datetime.now(timezone.utc).isoformat()
    }
]

with open("public/data.json", "w") as f:
    json.dump(data, f, indent=2)
