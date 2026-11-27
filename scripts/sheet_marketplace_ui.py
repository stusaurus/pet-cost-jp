"""Optional fresh two-mall section; never alter the Rakuten ranking."""
import html
import os
from common.sheet_marketplace import collect_exact, free_shipping
from common.rakuten import fetch_items
from common.yahoo_shopping import YahooShopping

SIZES = {"regular": "レギュラー", "wide": "ワイド", "super_wide": "スーパーワイド"}
CREDIT = '<a href="https://developer.yahoo.co.jp/sitemap/">Webサービス by Yahoo! JAPAN</a>'
CSS = """<style id="sheet-marketplace-style">
#sheet-marketplace{scroll-margin-top:90px;border:1px solid #c9dcd0;border-radius:16px;padding:clamp(14px,3vw,24px);background:#f4f8f5;margin:24px 0}
#sheet-marketplace h2{font-size:clamp(20px,4vw,26px);line-height:1.4;margin:0 0 8px}
.sheet-mall-pair{background:white;border:1px solid #d4e0d7;border-radius:12px;padding:12px;margin:12px 0}
.sheet-mall-pair h3{font-size:17px;margin:0 0 8px}
.sheet-mall-offers{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
.sheet-mall-offer{min-width:0;border:1px solid #d4e0d7;border-radius:8px;padding:10px;overflow-wrap:anywhere}
.sheet-mall-offer h4{margin:0;font-size:14px}
.sheet-mall-price{font-size:clamp(18px,4vw,25px);font-weight:750;margin:6px 0}
.sheet-mall-offer p{font-size:13px;margin:5px 0}
.sheet-mall-offer a{display:flex;align-items:center;justify-content:center;min-height:44px;border:1px solid #426553;border-radius:8px;text-align:center;padding:5px;font-size:13px;font-weight:700;color:#234b38}
.sheet-mall-nav{display:inline-flex;min-height:44px;align-items:center;color:#234b38;font-weight:700}
.sheet-mall-note{font-size:13px;line-height:1.65}
</style>"""


def esc(value):
    return html.escape(str(value), quote=True)


def offer(mall, row, product, client):
    jan, group, count, family, _ = product
    price = row["price"]
    if mall == "rakuten":
        name, shop, url = row["name"], row.get("shop"), row["url"]
        free = type(row.get("postage_flag")) is int and row["postage_flag"] == 0 and free_shipping(name)
    else:
        name, url = row["name"], client.affiliate_link(row)
        seller = row.get("seller")
        shop = seller.get("name") if isinstance(seller, dict) else None
        shipping = row.get("shipping")
        terms = " ".join(str(row.get(k) or "") for k in ("name", "description", "headline"))
        free = isinstance(shipping, dict) and shipping.get("code") == 2 and free_shipping(terms)
    if not url or not isinstance(shop, str) or not shop.strip() or type(price) is not int or not .5 <= price / count <= 10000:
        return None
    return {"mall": mall, "name": name, "shop": shop, "price": price, "url": url,
            "free": free, "jan": jan, "count": count}


def select_pairs(rows, client):
    pairs = []
    for product, rakuten, yahoo in rows:
        offers = [[o for row in source if (o := offer(mall, row, product, client))]
                  for mall, source in (("rakuten", rakuten), ("yahoo", yahoo))]
        if all(offers):
            pairs.append((product, [min(items, key=lambda o: (o["price"], not o["free"], o["shop"], o["url"])) for items in offers]))
    return pairs


def render_offer(o):
    mall = o["mall"]
    label = "楽天市場" if mall == "rakuten" else "Yahoo!ショッピング"
    price, count = o["price"], o["count"]
    shipping = "送料無料表示（地域条件は要確認）" if o["free"] else "送料・条件は販売店で確認"
    total = f'{price:,}円（送料無料表示の場合）' if o["free"] else "送料未確定"
    return (f'<div class="sheet-mall-offer"><h4>{label}</h4><p>{esc(o["shop"])}</p>'
            f'<p class="sheet-mall-price">{price:,}円</p><p>商品価格の1枚単価 {price/count:,.1f}円</p>'
            f'<p>送料：{shipping}</p><p>購入総額：{total}</p>'
            f'<a data-affiliate-link data-merchant="{mall}" data-category-id="pet-sheets" '
            f'data-item-id="{esc(o["jan"])}" data-item-name="{esc(o["name"])}" data-metric="per_sheet" '
            f'data-unit-price="{price/count:.4f}" data-position="1" data-conversion-source="marketplace_comparison" '
            f'href="{esc(o["url"])}" target="_blank" rel="nofollow sponsored noopener">{label}で確認</a></div>')


def render(pairs, updated, group=None):
    cards = []
    for product, offers in pairs:
        jan, size, count, family, source = product
        if group and group != size:
            continue
        name = "デオシート しっかり超吸収 無香消臭" if family == "deo" else "ネオシーツ FX 薄型"
        a, b = offers
        diff = abs(a["price"] - b["price"])
        if diff:
            cheaper = "楽天市場" if a["price"] < b["price"] else "Yahoo!ショッピング"
            note = f"商品価格では{cheaper}が{diff:,}円低い"
        else:
            note = "商品価格は同額"
        cards.append(f'<article class="sheet-mall-pair" data-sheet-marketplace-jan="{jan}"><h3>{name} {SIZES[size]} {count}枚</h3>'
                     f'<p class="sheet-mall-note">{note}（送料差は未反映）</p><div class="sheet-mall-offers">'
                     + "".join(render_offer(o) for o in offers)
                     + f'</div><p class="sheet-mall-note">JAN {jan} · <a href="{esc(source)}" rel="noopener" target="_blank">メーカー規格</a></p></article>')
    if not cards:
        return ""
    return (CSS + '<section class="section" id="sheet-marketplace" aria-labelledby="sheet-marketplace-heading">'
            '<h2 id="sheet-marketplace-heading">同じペットシーツを楽天・Yahoo!で比較</h2>'
            '<p>JAN・サイズ・枚数を確認した同一規格のうち、取得できた各モールの商品価格最小の販売店を掲載します。</p>'
            + "".join(cards) + f'<p class="sheet-mall-note">取得日時：{esc(updated)}。広告リンクを含みます。'
            '送料・配送地域・在庫・ポイント・クーポンは購入先で確認してください。送料が未確定の場合、支払総額の最安値は判定しません。既存の楽天単価ランキングとは別の比較です。</p>'
            f'<p class="sheet-mall-note">{CREDIT}</p></section>')


def inject(page, section):
    if not section:
        return page
    anchor = '<section class="section" id="product-ranking"'
    if page.count(anchor) != 1 or 'id="sheet-marketplace"' in page:
        raise ValueError("marketplace section anchor")
    return page.replace(anchor, section + anchor, 1)


def build_pairs(category):
    try:
        client = YahooShopping(os.getenv("YAHOO_APP_ID", ""), os.getenv("YAHOO_AFFILIATE_ID", ""))
        pairs = select_pairs(collect_exact(client, category, fetch_items), client)
    except Exception:
        # Network errors may include credentials. Never print them or reuse stale prices.
        print("Sheet marketplace unavailable; Rakuten comparison preserved.")
        return []
    print("Sheet marketplace verified pairs:", len(pairs))
    return pairs
