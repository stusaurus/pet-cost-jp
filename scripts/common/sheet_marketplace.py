"""Manufacturer-backed single-pack sheet comparison."""
import re
from urllib.parse import urlsplit, parse_qs
from common.engine import normalize_item
from common.quantity import normalize_text

# Single-pack JANs and quantities from manufacturer product pages.
PRODUCTS = (
    ("4520699667989", "regular", 112, "deo", "https://www.d-unicharm.jp/item/200690.html"),
    ("4520699672143", "wide", 54, "deo", "https://www.d-unicharm.jp/item/200692.html"),
    ("4520699676066", "super_wide", 23, "deo", "https://www.d-unicharm.jp/item/200694.html"),
    ("4972316207571", "super_wide", 36, "neo", "https://www.kohcho.co.jp/products/neo-loo-life/neosheet/20.html"),
)


def identity(row, product, category):
    jan, group, count, family, _ = product
    item = normalize_item(row, category)
    if not item or item["group"] != group or item["quantity"] != count:
        return False
    title = normalize_text(row["name"])
    if re.search(r"おまけ|セット|選べ|選択|アソート|旧品|旧パッケージ|香り付き|フレグランス|プレミアム|フローラル|グリーンの香り", title):
        return False
    # Require explicit single-pack sheet quantity; never infer pack count from JAN alone.
    if not re.search(r"(?<!\d)" + str(count) + r"\s*枚(?!\s*[×x*]\s*[2-9])", title):
        return False
    if family == "deo":
        return all(x in title for x in ("デオシート", "しっかり超吸収", "無香消臭"))
    return bool(re.search(r"ネオシーツ\s*fx", title)) and "薄型" in title and not re.search(r"dx|厚型|炭入り", title)


def rakuten_link(row):
    try:
        url = urlsplit(row["url"])
        targets = parse_qs(url.query).get("pc", [])
        if url.scheme != "https" or url.netloc != "hb.afl.rakuten.co.jp" or len(targets) != 1:
            return False
        target = urlsplit(targets[0])
        return target.scheme == "https" and target.netloc == "item.rakuten.co.jp" and bool(re.fullmatch(r"/[\w-]+/[\w.-]+/?", target.path))
    except (KeyError, ValueError, TypeError):
        return False


def free_shipping(text):
    return not re.search(r"送料|配送|離島|沖縄|北海道|一部地域|別途|条件", normalize_text(text).replace("送料無料", ""))


def totals_known(row, hit):
    # Free-shipping flags are not proof of an actual address-specific checkout total.
    terms = " ".join(str(hit.get(k) or "") for k in ("name", "description", "headline"))
    shipping = hit.get("shipping")
    return (type(row.get("postage_flag")) is int and row.get("postage_flag") == 0 and free_shipping(row["name"])
            and isinstance(shipping, dict) and shipping.get("code") == 2 and free_shipping(terms))


def inspect(rows, client, category):
    report = {}
    for product in PRODUCTS:
        jan = product[0]
        r = [row for row in rows if rakuten_link(row) and identity(row, product, category)]
        hits = client.search(jan=jan, results=50)
        y = {}
        for hit in hits:
            code, price, name = hit.get("code"), hit.get("price"), hit.get("name")
            if (hit.get("janCode") != jan or hit.get("inStock") is not True
                    or hit.get("condition") != "new" or not isinstance(code, str)
                    or type(price) is not int or price <= 0 or not isinstance(name, str)):
                continue
            link = client.affiliate_link(hit)
            if link and identity({"name": name, "price": price, "url": link}, product, category):
                y[code] = hit
        report[jan] = {"size": product[1], "sheets": product[2], "rakuten_candidates": len(r),
                       "yahoo_candidates": len(y), "matched_candidate": bool(r and y),
                       "both_free_shipping_flags": any(totals_known(a,b) for a in r for b in y.values())}
    return report


# Exact seller pages independently checked for their single-pack JAN and specification.
VERIFIED_TARGETS = {
    "4520699672143": {"/chanet/246764", "/petgo/4520699672143", "/cocoterrace/icn-rps-00000072"},
    "4972316207571": {"/chanet/202320", "/mapet/4972316207571", "/edenki/ed2910549"},
}


def verified_rakuten(row, product, category):
    if not rakuten_link(row) or not identity(row, product, category):
        return False
    target = urlsplit(parse_qs(urlsplit(row["url"]).query)["pc"][0])
    jan = product[0]
    # A keyword search by JAN is not itself evidence that a returned listing is exact.
    title = normalize_text(row["name"])
    codes = set(re.findall(r"(?<!\d)\d{13}(?!\d)", title))
    if codes and codes != {jan}:
        return False
    return jan in codes or target.path.rstrip("/") in VERIFIED_TARGETS.get(jan, set())


def collect_exact(client, category, fetch_items):
    """Fresh, targeted retrieval independent of the unit-price ranking."""
    pairs = []
    for product in PRODUCTS:
        jan = product[0]
        rows = fetch_items(jan, pages=1)
        # A separately verified shop listing may not surface on the JAN query.
        if jan in VERIFIED_TARGETS:
            query = "デオシート ワイド 54枚" if product[3] == "deo" else "ネオシーツ FX スーパーワイド 36枚"
            rows += fetch_items(query, pages=1, shop_code="chanet")
        rows = {parse_qs(urlsplit(row["url"]).query)["pc"][0]: row
                for row in rows if verified_rakuten(row, product, category)}
        r = list(rows.values())
        y = {}
        for hit in client.search(jan=jan, results=50):
            code, price, name = hit.get("code"), hit.get("price"), hit.get("name")
            if (hit.get("janCode") != jan or hit.get("inStock") is not True
                    or hit.get("condition") != "new" or not isinstance(code, str)
                    or type(price) is not int or price <= 0 or not isinstance(name, str)):
                continue
            link = client.affiliate_link(hit)
            if link and identity({"name": name, "price": price, "url": link}, product, category):
                y[code] = hit
        pairs.append((product, r, list(y.values())))
    return pairs


def inspect_exact(client, category, fetch_items):
    report = {}
    for product, r, y in collect_exact(client, category, fetch_items):
        report[product[0]] = {"size": product[1], "sheets": product[2],
                       "rakuten_verified": len(r), "yahoo_verified": len(y),
                       "rakuten_min_item_price": min((row["price"] for row in r), default=None),
                       "yahoo_min_item_price": min((hit["price"] for hit in y), default=None),
                       "both_free_shipping_flags": any(totals_known(a,b) for a in r for b in y)}
    return report
