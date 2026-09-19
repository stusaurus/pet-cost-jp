import hashlib
from .quantity import normalize_text, parse_count, parse_liters, parse_100g
from .classify import classify


def category_matches(title, category):
    text = normalize_text(title)
    includes = [normalize_text(x) for x in category.get("include_any", [])]
    excludes = [normalize_text(x) for x in category.get("exclude_any", [])]
    if includes and not any(x in text for x in includes):
        return False
    if any(x in text for x in excludes):
        return False
    return True


def parse_quantity(title, parser):
    if parser == "count":
        return parse_count(title)
    if parser == "volume_liter":
        return parse_liters(title)
    if parser == "weight_100g":
        return parse_100g(title)
    return None


def product_id(name, shop):
    key = normalize_text(name) + "|" + normalize_text(shop)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]


def normalize_item(raw, category):
    title = raw.get("name", "")
    price = int(raw.get("price") or 0)
    if price <= 0 or not raw.get("url") or not category_matches(title, category):
        return None

    parsed = parse_quantity(title, category["parser"])
    if not parsed or parsed["quantity"] <= 0 or parsed["confidence"] < 0.90:
        return None

    group = classify(category.get("group_by", ""), title)
    unit_price = price / parsed["quantity"]
    return {
        **raw,
        "product_id": product_id(title, raw.get("shop", "")),
        "category_id": category["id"],
        "metric": category["metric"],
        "metric_label": category["metric_label"],
        "quantity": parsed["quantity"],
        "quantity_evidence": parsed["evidence"],
        "confidence": parsed["confidence"],
        "group": group,
        "unit_price": round(unit_price, 4),
    }


def choose_ranked(raw_items, category, limit=30):
    normalized = [normalize_item(x, category) for x in raw_items]
    normalized = [x for x in normalized if x]
    normalized.sort(key=lambda x: (x["unit_price"], -x.get("review_count", 0), -x.get("review_average", 0)))

    seen = set()
    ranked = []
    for item in normalized:
        key = normalize_text(item["name"])
        if key in seen:
            continue
        seen.add(key)
        ranked.append(item)
        if len(ranked) >= limit:
            break
    return ranked
