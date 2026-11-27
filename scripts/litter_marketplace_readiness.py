import json
import os
from pathlib import Path
from common.litter_marketplace import inspect
from common.rakuten import fetch_items
from common.yahoo_shopping import YahooShopping

ROOT = Path(__file__).resolve().parents[1]


def main():
    try:
        category = next(c for c in json.loads((ROOT / "config/categories.json").read_text(encoding="utf-8")) if c["id"] == "cat-litter")
        client = YahooShopping(os.getenv("YAHOO_APP_ID", ""), os.getenv("YAHOO_AFFILIATE_ID", ""))
        report = inspect(client, category, fetch_items)
    except Exception:
        print("Cat litter marketplace diagnostic unavailable.")
        return 1
    print("LITTER_VERIFIED_OFFERS " + json.dumps(report, ensure_ascii=False, sort_keys=True))
    print("Aggregate item prices only; shipping and address-specific checkout totals are not verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
