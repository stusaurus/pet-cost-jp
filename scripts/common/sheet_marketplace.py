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
    ("4972316207557", "regular", 180, "neo", "https://www.kohcho.co.jp/products/neo-loo-life/neosheet/16.html"),
    ("4972316208264", "wide", 50, "neo", "https://www.kohcho.co.jp/products/neo-loo-life/neosheet/19.html"),
)


def identity(row, product, category, *, exact_evidence=False):
    jan, group, count, family, _ = product
    title = normalize_text(row["name"])
    # Only independently verified JAN/retailer evidence permits a series-name
    # alias in place of the generic category noun. All other guards stay active.
    if exact_evidence:
        category = {**category, "include_any": [*category.get("include_any", []),
                                                "デオシート" if family == "deo" else "ネオシーツ"]}
    item = normalize_item(row, category)
    if not item or item["group"] != group or item["quantity"] != count:
        return False
    if re.search(r"おまけ|セット|選べ|選択|アソート|旧品|旧パッケージ|香り付き|フレグランス|プレミアム|フローラル|グリーンの香り|まとめ買い|ケース販売|箱売り|ホワイト|テープ付き|クエン酸", title):
        return False
    codes = set(re.findall(r"(?<!\d)\d{13}(?!\d)", title))
    if codes and codes != {jan}:
        return False
    # Require explicit single-pack sheet quantity; never infer pack count from JAN alone.
    if not re.search(r"(?<!\d)" + str(count) + r"\s*枚(?!\s*[×x*]\s*[2-9])", title):
        return False
    if family == "deo":
        marker = ("しっかり超吸収" in title or (exact_evidence and ("超吸収" in title or "しっかり吸収" in title)))
        return marker and all(x in title for x in ("デオシート", "無香消臭"))
    return bool(re.search(r"ネオシーツ\s*fx", title)) and ("薄型" in title or exact_evidence) and not re.search(r"dx|厚型|中厚|炭入り", title)


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
            if link and identity({"name": name, "price": price, "url": link}, product, category, exact_evidence=True):
                y[code] = hit
        report[jan] = {"size": product[1], "sheets": product[2], "rakuten_candidates": len(r),
                       "yahoo_candidates": len(y), "matched_candidate": bool(r and y),
                       "both_free_shipping_flags": any(totals_known(a,b) for a in r for b in y.values())}
    return report


# Exact seller pages independently checked for their single-pack JAN and specification.
VERIFIED_TARGETS = {
    "4520699667989": {"/petgo/4520699667989", "/r-kojima/4520699667989", "/rakuten24/e448566h"},
    "4520699676066": {"/gooddoglife/4520699676066", "/petgo/4520699676066", "/rakuten24/e448570h"},
    "4972316207557": {"/nyanzaq/4972316207557", "/kohnan-eshop/4972316207557", "/a-price/4972316207557"},
    "4972316208264": {"/petforest/pf-4972316208264", "/marquee/50371"},
    "4520699672143": {"/chanet/246764", "/petgo/4520699672143", "/cocoterrace/icn-rps-00000072"},
    "4972316207571": {"/chanet/202320", "/mapet/4972316207571", "/edenki/ed2910549"},
}


# Shop-specific queries prevent low-price or bulk listings from crowding out singles.
REVIEWED_LOOKUPS = {
    "4520699667989": ("rakuten24", "r-kojima"),
    "4520699672143": ("chanet",),
    "4520699676066": ("rakuten24", "gooddoglife"),
    "4972316207571": ("chanet",),
    "4972316207557": ("nyanzaq", "a-price"),
    "4972316208264": ("petforest", "marquee"),
}


def verified_rakuten(row, product, category):
    if not rakuten_link(row):
        return False
    target = urlsplit(parse_qs(urlsplit(row["url"]).query)["pc"][0])
    jan = product[0]
    # A keyword search by JAN is not itself evidence that a returned listing is exact.
    title = normalize_text(row["name"])
    codes = set(re.findall(r"(?<!\d)\d{13}(?!\d)", title))
    if codes and codes != {jan}:
        return False
    evidence = jan in codes or target.path.rstrip("/") in VERIFIED_TARGETS.get(jan, set())
    return evidence and identity(row, product, category, exact_evidence=True)


def collect_exact(client, category, fetch_items):
    """Fresh, targeted retrieval independent of the unit-price ranking."""
    pairs = []
    for product in PRODUCTS:
        jan = product[0]
        rows = fetch_items(jan, pages=1)
        # A separately verified shop listing may not surface on the JAN query.
        shops = REVIEWED_LOOKUPS.get(jan, ())
        size = {"regular": "レギュラー", "wide": "ワイド", "super_wide": "スーパーワイド"}[product[1]]
        series = "デオシート" if product[3] == "deo" else "ネオシーツ FX"
        query = f"{series} {size} {product[2]}枚"
        for shop in shops:
            rows += fetch_items(query, pages=1, shop_code=shop)
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
            if link and identity({"name": name, "price": price, "url": link}, product, category, exact_evidence=True):
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
