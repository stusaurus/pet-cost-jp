"""Read-only Yahoo readiness: count eligible listings, never publish links or claim exact pairs."""
import json
import os
from pathlib import Path
from urllib.request import urlopen
from common.sheet_marketplace import inspect, inspect_exact
from common.rakuten import fetch_items

from common.engine import normalize_item
from common.yahoo_shopping import YahooShopping, YahooUnavailable

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {"regular": "ペットシーツ レギュラー", "wide": "ペットシーツ ワイド",
           "super_wide": "ペットシーツ スーパーワイド"}


def summarize(hits, client, category, group):
    seen = set()
    eligible = 0
    for hit in hits:
        code = hit.get("code")
        if not isinstance(code, str) or not code or code in seen:
            continue
        link = client.affiliate_link(hit)
        price = hit.get("price")
        name = hit.get("name")
        if not link or not isinstance(name, str) or type(price) is not int or price <= 0:
            continue
        item = normalize_item({"name": name, "price": price, "url": link, "shop": ""}, category)
        if not item or item["group"] != group or not .5 <= item["unit_price"] <= 10000:
            continue
        seen.add(code)
        eligible += 1
    return {"returned": len(hits), "eligible_distinct_listings": eligible}


def main():
    categories = json.loads((ROOT / "config/categories.json").read_text(encoding="utf-8"))
    category = next(c for c in categories if c["id"] == "pet-sheets")
    try:
        client = YahooShopping(os.getenv("YAHOO_APP_ID", ""), os.getenv("YAHOO_AFFILIATE_ID", ""))
        report = {group: summarize(client.search(query=query, results=50), client, category, group)
                  for group, query in QUERIES.items()}
    except YahooUnavailable as error:
        print(f"Yahoo readiness unavailable: {error}")
        return 1
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    print("Counts are candidate listings, not exact cross-mall matches or confirmed checkout totals.")
    try:
        with urlopen("https://stusaurus.github.io/pet-cost-jp/data/pet-sheets.json", timeout=20) as response:
            catalog = json.loads(response.read(2_000_000))
        if not isinstance(catalog, dict) or not isinstance(catalog.get("items"), list) or not all(isinstance(row, dict) for row in catalog["items"]):
            raise ValueError("catalog schema")
        pairs = inspect(catalog["items"], client, category)
    except (OSError, ValueError, TypeError, YahooUnavailable):
        print("Manufacturer-JAN comparison diagnostic unavailable.")
        return 1
    print("JAN_PILOT " + json.dumps(pairs, ensure_ascii=False, sort_keys=True))
    print("Candidate pairs are manufacturer-spec matches; free-shipping flags are not checkout quotes.")
    try:
        exact = inspect_exact(client, category, fetch_items)
    except Exception:
        # Rakuten exceptions may contain the request URL. Never log them.
        print("Verified marketplace lookup unavailable.")
        return 1
    print("VERIFIED_OFFERS " + json.dumps(exact, ensure_ascii=False, sort_keys=True))
    return 0 if any(v["eligible_distinct_listings"] for v in report.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
