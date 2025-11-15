# ======================================================
# Storage Helpers
# ======================================================

# regulator/utils/storage.py

import json
import os

# Get the directory *where main.py lives*
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DATA_PATH = os.path.join(BASE_DIR, "docs", "data.json")


def load_existing_data():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, {item["link"] for item in data}
    except (FileNotFoundError, json.JSONDecodeError):
        return [], set()


def save_data(data):
    # Create /docs/ if missing
    os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)

    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Saved {len(data)} → {DATA_PATH}")
