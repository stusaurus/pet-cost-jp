import json
import os
import time
import urllib.parse
import urllib.request

API_URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20260701"


def first_image(item):
    value = item.get("mediumImageUrls") or item.get("smallImageUrls") or []
    if not isinstance(value, list) or not value:
        return ""
    first = value[0]
    if isinstance(first, dict):
        first = first.get("imageUrl") or first.get("url") or ""
    return str(first or "").replace("http://", "https://")


def fetch_items(keyword: str, pages: int = 2, hits: int = 30):
    app_id = os.environ.get("RAKUTEN_APPLICATION_ID")
    access_key = os.environ.get("RAKUTEN_ACCESS_KEY")
    affiliate_id = os.environ.get("RAKUTEN_AFFILIATE_ID", "")
    if not app_id or not access_key:
        raise RuntimeError("RAKUTEN_APPLICATION_ID and RAKUTEN_ACCESS_KEY are required")

    out = []
    for page in range(1, pages + 1):
        params = {
            "applicationId": app_id,
            "keyword": keyword,
            "hits": hits,
            "page": page,
            "format": "json",
            "formatVersion": 2,
            "availability": 1,
            "field": 0,
        }
        if affiliate_id:
            params["affiliateId"] = affiliate_id
        url = API_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(
            url,
            headers={
                "accessKey": access_key,
                "Origin": "https://stusaurus.github.io",
                "Referer": "https://stusaurus.github.io/pet-cost-jp/",
                "User-Agent": "pet-cost-jp/0.1",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as res:
            payload = json.loads(res.read().decode("utf-8"))
        rows = payload.get("items") or payload.get("Items") or []
        for row in rows:
            item = row.get("Item", row) if isinstance(row, dict) else {}
            if not isinstance(item, dict):
                continue
            out.append({
                "name": str(item.get("itemName") or ""),
                "price": int(float(item.get("itemPrice") or 0)),
                "url": str(item.get("affiliateUrl") or item.get("itemUrl") or ""),
                "shop": str(item.get("shopName") or ""),
                "image": first_image(item),
                "review_average": float(item.get("reviewAverage") or 0),
                "review_count": int(float(item.get("reviewCount") or 0)),
                "postage_flag": item.get("postageFlag"),
            })
        if page < pages:
            time.sleep(1.1)
    return out
