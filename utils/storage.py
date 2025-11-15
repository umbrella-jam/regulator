# ======================================================
# Storage Helpers
# ======================================================

import json
DATA_PATH = "docs/data.json"

def load_existing_data(path=DATA_PATH):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data, {item["link"] for item in data}
    except (FileNotFoundError, json.JSONDecodeError):
        return [], set()


def save_data(data, path=DATA_PATH):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved {len(data)} records → {path}")