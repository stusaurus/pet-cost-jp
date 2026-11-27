"""Read-only pilot for exact single-bag cat litter offers; no public prices."""
import re
from urllib.parse import urlsplit, parse_qs
from common.engine import category_matches
from common.quantity import normalize_text, parse_liters
from common.sheet_marketplace import rakuten_link

IRIS = "https://www.irisohyama.co.jp/products/pet-supplies-pet-food/cat-sand/"
# Manufacturer JAN, title, nominal contents in liters, material, name/model, source,
# and independently reviewed *single bag* seller paths. Never infer volume from kg.
PRODUCTS = (
    ("4905009714353", "紙の猫砂 KMN-70N", 7, "paper", "紙の猫砂", "kmn-70n",
     IRIS+"kamisuna/paper-cat-sand", ("/matsukiyo/4905009714353",)),
    ("4905009714346", "お茶の猫砂 OCN-70N", 7, "okara", "お茶の猫砂", "ocn-70n",
     IRIS+"okara-cypress-sand/cat-sand-of-tea", ("/nishimutapetslove/4905009714346",)),
    ("4905009778515", "ひのきでつくった猫砂 HKT-70", 7, "wood", "ひのきでつくった猫砂", "hkt-70",
     IRIS+"okara-cypress-sand/cat-sand-made-with-cypress", ("/chanet/238113", "/chanet3980/238113")),
    ("4905009869466", "クリーン＆フレッシュ Ag+ KFAG-80", 8, "mineral", "クリーン", "kfag-80",
     IRIS+"mineral-sand/clean-fresh", ("/nishimutapetslove/4905009869466")),
    ("4990968215744", "クリーンミュウ 白い紙製の砂", 12.5, "paper", "クリーンミュウ", "",
     "https://www.cs-jp.net/pet/cat/product20.html", ("/dogworld01/csihtt5744", "/plantz/4990968215744", "/chanet3980/247589")),
)


def identity(row, product, category):
    jan, _, liters, group, marker, model, _, _ = product
    title = normalize_text(row.get("name", ""))
    # All candidates already have independently verified JAN evidence.
    # Retain general exclusion rules, even if a brand alias replaces the generic noun.
    if not category_matches(title, {**category, "include_any": [*category["include_any"], marker]}):
        return False
    if re.search(r"セット|まとめ買い|まとめ売り|ケース|箱売り|選べ|選択|アソート|お試し|おまけ|旧品|旧パッケージ|システムトイレ|デオトイレ|ニャンとも|固まらない", title):
        return False
    title = re.sub(r"(?:お一人様|おひとり様|お1人様)\s*\d+\s*(?:個|点|袋)\s*(?:まで|限り)", "", title)
    # Reject multipacks even when the title also repeats the single-bag volume.
    if re.search(r"\d+(?:\.\d+)?\s*l\s*(?:入り|入)?\s*x\s*\d+|(?<!\d)[2-9]\d*\s*(?:袋|個|パック|箱)|(?<!\d)1\d+\s*(?:袋|個|パック|箱)", title):
        return False
    codes = set(re.findall(r"(?<!\d)\d{13}(?!\d)", title))
    if codes and codes != {jan}:
        return False
    # Explicit single-bag quantity and separately worded per-customer limit are not a multipack.
    # Multipack matching below still operates on all other title text.
    # Explicit "1袋" is compatible with a single bag. Strip only that exact count.
    qty = parse_liters(re.sub(r"(?<!\d)1\s*袋", "", title))
    if not qty or qty["quantity"] != liters or qty["confidence"] < .9:
        return False
    models = set(re.findall(r"(?<![a-z0-9])(?:p?kmn|ocn|hkt|kfag)-\d+[a-z]*(?![a-z0-9])", title))
    allowed_models = {model, "ocn-70"} if jan == "4905009714346" else {model}
    if models and not models <= allowed_models:
        return False
    if marker not in title:
        return False
    if group == "mineral" and not (model in models or ("フレッシュ" in title and ("ag+" in title or "銀イオン" in title))):
        return False
    if group == "paper" and any(x in title for x in ("おから", "ベントナイト", "木製", "シリカ")):
        return False
    if group == "paper" and not model and ("白" not in title or "紙" not in title):
        return False
    return True


def verified_rakuten(row, product, category):
    if not rakuten_link(row) or not identity(row, product, category):
        return False
    target = urlsplit(parse_qs(urlsplit(row["url"]).query)["pc"][0]).path.rstrip("/")
    codes = set(re.findall(r"(?<!\d)\d{13}(?!\d)", normalize_text(row["name"])))
    return product[0] in codes or target in product[7]


def inspect(client, category, fetch_items):
    report = {}
    for product in PRODUCTS:
        jan, label, liters, group, _, _, _, paths = product
        raw = fetch_items(jan, pages=1)
        for shop in sorted({p.split("/")[1] for p in paths}):
            raw += fetch_items(f"{label} {liters:g}L", pages=1, shop_code=shop)
        rakuten = {}
        for row in raw:
            if type(row.get("price")) is int and 5 <= row["price"]/liters <= 10000 and verified_rakuten(row, product, category):
                target = urlsplit(parse_qs(urlsplit(row["url"]).query)["pc"][0]).path.rstrip("/")
                rakuten[target] = row["price"]
        yahoo = {}
        for hit in client.search(jan=jan, results=50):
            code, price, name = hit.get("code"), hit.get("price"), hit.get("name")
            if (hit.get("janCode") != jan or hit.get("inStock") is not True
                    or hit.get("condition") != "new" or not isinstance(code, str)
                    or type(price) is not int or not 5 <= price/liters <= 10000 or not isinstance(name, str)):
                continue
            url = client.affiliate_link(hit)
            if url and identity({"name": name}, product, category):
                yahoo[code] = price
        report[jan] = {"material": group, "liters": liters, "rakuten_verified": len(rakuten),
                       "yahoo_verified": len(yahoo), "matched": bool(rakuten and yahoo),
                       "rakuten_min_item_price": min(rakuten.values(), default=None),
                       "yahoo_min_item_price": min(yahoo.values(), default=None)}
    return report
