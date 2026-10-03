import hashlib
import re
import urllib.parse

from .quantity import normalize_text, parse_count, parse_liters, parse_100g
from .classify import classify

GLOBAL_EXCLUDE = (
    "ふるさと納税", "定期便", "定期購入", "初回限定", "初回のみ", "お試し価格", "会員限定価格",
    "中古", "訳あり", "訳アリ", "アウトレット",
    "展示品", "開封品", "箱潰れ", "箱つぶれ", "b品"
)


def category_matches(title, category):
    text = normalize_text(title)
    if any(normalize_text(x) in text for x in GLOBAL_EXCLUDE):
        return False
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


def _source_slug(affiliate_url):
    try:
        query = urllib.parse.parse_qs(urllib.parse.urlparse(affiliate_url).query)
        direct = query.get("pc", [""])[0]
        path = urllib.parse.urlparse(direct).path.strip("/").split("/")
        return path[-1].lower() if path else ""
    except Exception:
        return ""


def _variant_marker(text):
    markers = (
        ("ナチュラルガーデン", "garden"),
        ("ナチュラルソープ", "soap"),
        ("複数ねこ", "multi"),
        ("厚型炭入り", "thick-carbon"),
        ("カーボン", "carbon"),
        ("超薄型", "ultrathin"),
        ("中厚", "medium"),
        ("厚型", "thick"),
        ("薄型", "thin"),
        ("無香", "unscented"),
    )
    for needle, value in markers:
        if needle in text:
            return value
    return "base"


def _model_token(text):
    tokens = re.findall(
        r"(?<![a-z0-9])([a-z][a-z0-9_-]{3,}[0-9][a-z0-9_-]*)(?![a-z0-9])",
        text,
    )
    if not tokens:
        return ""
    return sorted(tokens, key=len, reverse=True)[0]


def _family_key(item, category):
    """Conservative product-family key used only to prevent ranking domination."""
    text = normalize_text(item.get("name", ""))
    category_id = category.get("id", "")
    group = item.get("group", "")

    if category_id == "system-toilet-sheets":
        if "デオトイレ" in text:
            if "複数ねこ" in text:
                return "deotoilet:multi"
            if "ナチュラルガーデン" in text:
                return "deotoilet:garden"
            if "ナチュラルソープ" in text:
                return "deotoilet:soap"
            return "deotoilet:standard"
        if "ニャンとも清潔トイレ" in text or "ニャンとも" in text:
            return "nyantomo:sheet"
        if "ラクリーン" in text or "raclean" in text:
            return "raclean:sheet"

    if category_id == "cat-litter":
        if "常陸化工" in text and "ファインブルー" in text:
            return "hitachi:fine-blue"
        if "常陸化工" in text and "ファインホワイト" in text:
            return "hitachi:fine-white"
        if "岩国再生エネルギー" in text and "木質ペレット" in text:
            return "iwakuni:wood-pellet"
        if "お茶の猫砂" in text and ("アイリスオーヤマ" in text or "ocn-" in text):
            return "iris:ocha-litter"

    if category_id == "pet-sheets" and "lifelex" in text:
        for code in ("knps_sw", "knps_w", "knps_r"):
            if code in text:
                return f"lifelex:{code}:{_variant_marker(text)}"

    slug = _source_slug(item.get("url", ""))

    if (
        category_id == "system-toilet-sheets"
        and re.fullmatch(r"\d{5,}", slug)
    ):
        return f"source:{category_id}:{group}:{slug}:{item.get('quantity', 0)}"

    if re.fullmatch(r"\d{7,}", slug):
        return f"source:{category_id}:{group}:{slug}"

    model = _model_token(text)
    if model:
        return f"model:{category_id}:{group}:{model}:{_variant_marker(text)}"
    return ""


def normalize_item(raw, category):
    title = raw.get("name", "")
    price = int(raw.get("price") or 0)
    if price <= 0 or not raw.get("url") or not category_matches(title, category):
        return None

    parsed = parse_quantity(title, category["parser"])
    if not parsed or parsed["quantity"] <= 0 or parsed["confidence"] < 0.90:
        return None

    group = classify(category.get("group_by", ""), title)
    if group == "ambiguous":
        return None

    excluded_groups = set(category.get("exclude_groups", []))
    if group in excluded_groups:
        return None

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


def _family_keep_ids(items, category):
    """Keep max two useful representatives: best unit price and lowest total price."""
    families = {}
    for item in items:
        key = _family_key(item, category)
        if key:
            families.setdefault(key, []).append(item)

    keep = set()
    for members in families.values():
        best_unit = min(members, key=lambda x: (x["unit_price"], x["price"]))
        best_total = min(members, key=lambda x: (x["price"], x["unit_price"]))
        keep.add(best_unit["product_id"])
        keep.add(best_total["product_id"])
    return keep


def choose_ranked(raw_items, category, limit=30):
    normalized = [normalize_item(x, category) for x in raw_items]
    normalized = [x for x in normalized if x]
    normalized.sort(key=lambda x: (x["unit_price"], -x.get("review_count", 0), -x.get("review_average", 0)))

    family_keep = _family_keep_ids(normalized, category)
    seen_names = set()
    seen_targets = set()
    ranked = []
    for item in normalized:
        family = _family_key(item, category)
        if family and item["product_id"] not in family_keep:
            continue

        name_key = normalize_text(item["name"])
        direct = urllib.parse.parse_qs(urllib.parse.urlparse(item['url']).query).get('pc', [''])[0]
        if name_key in seen_names or (direct and direct in seen_targets):
            continue
        seen_names.add(name_key)
        if direct: seen_targets.add(direct)
        ranked.append(item)
        if len(ranked) >= limit:
            break
    return ranked
