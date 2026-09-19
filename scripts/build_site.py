import html
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from common.engine import choose_ranked
from common.rakuten import fetch_items

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
CONFIG = ROOT / "config" / "categories.json"
FIXTURE = ROOT / "fixtures" / "demo_products.json"
BASE_URL = "https://stusaurus.github.io/pet-cost-jp/"


def yen(value):
    if value < 10:
        return f"¥{value:.2f}"
    if value < 100:
        return f"¥{value:.1f}"
    return f"¥{value:,.0f}"


def esc(value):
    return html.escape(str(value or ""), quote=True)


def load_categories():
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def load_fixture(category_id):
    if not FIXTURE.exists():
        return []
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return data.get(category_id, [])


def analytics_head():
    measurement = os.environ.get("GA_MEASUREMENT_ID", "").strip()
    runtime = (ROOT / "scripts" / "analytics_runtime.js").read_text(encoding="utf-8")
    if not measurement:
        return f"<script>{runtime}</script>"
    return f'''<script async src="https://www.googletagmanager.com/gtag/js?id={esc(measurement)}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}};gtag('js',new Date());gtag('config','{esc(measurement)}');</script>
<script>{runtime}</script>'''


CSS = r'''
:root{--bg:#f7faf8;--card:#fff;--text:#193026;--muted:#63756c;--line:#dce8e1;--accent:#237a57;--accent2:#e9f6ef;--warn:#fff7e6}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Sans","Noto Sans JP",sans-serif;background:var(--bg);color:var(--text);line-height:1.65}a{color:inherit}.wrap{width:min(980px,calc(100% - 28px));margin:auto}.hero{padding:30px 0 22px;background:linear-gradient(150deg,#fff,#edf8f2);border-bottom:1px solid var(--line)}.eyebrow{display:inline-flex;padding:5px 10px;border-radius:999px;background:#fff;border:1px solid var(--line);font-size:12px;font-weight:700;color:var(--accent)}h1{font-size:clamp(28px,8vw,44px);line-height:1.2;margin:12px 0 8px}.lead{margin:0;color:#42564b}.trust{font-size:13px;color:var(--muted);margin-top:12px}.topnav{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}.topnav .wrap{display:flex;gap:8px;overflow:auto;padding:9px 0}.chip{white-space:nowrap;text-decoration:none;border:1px solid var(--line);padding:7px 11px;border-radius:999px;background:#fff;font-size:13px}.main{padding:22px 0 50px}.grid{display:grid;gap:12px}.category-card{display:block;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px;text-decoration:none;box-shadow:0 4px 16px rgba(31,65,49,.04)}.category-card strong{font-size:18px}.category-card p{margin:6px 0 0;color:var(--muted);font-size:14px}.section{background:var(--card);border:1px solid var(--line);border-radius:18px;padding:18px;margin:16px 0}.section h2{margin:0 0 10px;font-size:22px}.kpi{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.kpi div{background:var(--accent2);border-radius:12px;padding:12px}.kpi b{display:block;font-size:20px}.filter{width:100%;padding:12px;border:1px solid var(--line);border-radius:12px;background:#fff;font-size:16px;margin:8px 0 14px}.table-wrap{overflow-x:auto}.compare{width:100%;border-collapse:collapse;min-width:620px}.compare th,.compare td{padding:12px 9px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left}.compare th{font-size:12px;color:var(--muted);position:sticky;top:48px;background:#fff}.rank{font-weight:800;color:var(--accent)}.unit{font-weight:800;font-size:17px;white-space:nowrap}.product{min-width:250px}.product-title{font-weight:700;line-height:1.45}.meta{font-size:12px;color:var(--muted);margin-top:4px}.btn{display:inline-block;text-decoration:none;background:var(--accent);color:#fff;padding:9px 12px;border-radius:10px;font-weight:700;font-size:13px;white-space:nowrap}.note{background:var(--warn);border-radius:12px;padding:12px;font-size:13px;color:#66542a}.footer{padding:28px 0 40px;color:var(--muted);font-size:12px}.method{font-size:14px;color:#485d51}.empty{padding:20px;text-align:center;color:var(--muted)}@media(min-width:720px){.grid{grid-template-columns:repeat(3,1fr)}.kpi{grid-template-columns:repeat(4,1fr)}}
'''


def shell(title, description, body, category_id=""):
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{BASE_URL}{'categories/'+category_id+'/' if category_id else ''}">{analytics_head()}<style>{CSS}</style></head><body data-category-id="{esc(category_id)}">{body}</body></html>'''


def nav(categories):
    links = ''.join(f'<a class="chip" href="{BASE_URL}categories/{esc(c["id"])}/">{esc(c["emoji"])} {esc(c["name"])}</a>' for c in categories)
    return f'<div class="topnav"><div class="wrap"><a class="chip" href="{BASE_URL}">トップ</a>{links}</div></div>'


def product_rows(items, category):
    rows = []
    for idx, item in enumerate(items, 1):
        postage = "送料込み" if str(item.get("postage_flag")) in ("0", "1") else "送料は商品ページで確認"
        postage = "送料表示は商品ページで確認"
        rows.append(f'''<tr data-product-row data-group="{esc(item['group'])}" data-row-unit-price="{item['unit_price']}"><td class="rank" data-rank-cell>{idx}</td><td class="product"><div class="product-title">{esc(item['name'])}</div><div class="meta">{esc(item['shop'])} / 数量根拠: {esc(item['quantity_evidence'])}</div></td><td>¥{item['price']:,}</td><td class="unit">{yen(item['unit_price'])}<div class="meta">/{esc(category['metric_label'])}</div></td><td><a class="btn" data-affiliate-link data-merchant="rakuten" data-category-id="{esc(category['id'])}" data-item-id="{esc(item['product_id'])}" data-item-name="{esc(item['name'])}" data-metric="{esc(category['metric'])}" data-unit-price="{item['unit_price']}" data-position="{idx}" data-conversion-source="comparison_table" href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener">楽天で価格を見る</a><div class="meta">{postage}</div></td></tr>''')
    return ''.join(rows)


def visible_default_items(category, items):
    default_group = category.get("default_group", "all")
    if default_group == "all":
        return items
    return [x for x in items if x.get("group") == default_group]


def category_page(category, items, categories, updated):
    groups = category.get("groups", {})
    options = ''.join(f'<option value="{esc(k)}"{" selected" if k == category.get("default_group") else ""}>{esc(v)}</option>' for k, v in groups.items())
    initial_items = visible_default_items(category, items)
    prices = [x["unit_price"] for x in initial_items]
    median = sorted(prices)[len(prices)//2] if prices else None
    body = f'''<header class="hero"><div class="wrap"><span class="eyebrow">価格と数量だけで比較</span><h1>{esc(category['emoji'])} {esc(category['name'])}のコスパ比較</h1><p class="lead">{esc(category['intro'])}</p><p class="trust">最終更新: {esc(updated)} / 推測できない数量はランキングから除外</p></div></header>{nav(categories)}<main class="main"><div class="wrap"><section class="section"><h2>最初に答えを見る</h2><div class="kpi"><div><span>初期表示の商品</span><b>{len(initial_items)}件</b></div><div><span>最安単価</span><b>{yen(min(prices)) if prices else '-'}</b></div><div><span>中央値</span><b>{yen(median) if median else '-'}</b></div><div><span>比較単位</span><b>{esc(category['metric_label'])}</b></div></div></section><section class="section"><h2>安い順に比較</h2><select class="filter" data-group-filter data-rank-all="{1 if category.get('rank_all') else 0}">{options}</select><div class="table-wrap"><table class="compare"><thead><tr><th>順</th><th>商品</th><th>総額</th><th>単価</th><th>確認</th></tr></thead><tbody>{product_rows(items, category) if items else '<tr><td colspan="5" class="empty">安全に単価計算できる商品がまだありません。</td></tr>'}</tbody></table></div></section><section class="section"><h2>店頭価格も同じ単位に直す</h2><p class="method">ドラッグストアやホームセンターで見た価格を、その場で{esc(category['metric_label'])}あたりに換算できます。現在選んでいる条件の表示商品とも比較します。</p><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px"><input data-calc-price inputmode="decimal" placeholder="総額（円）" style="padding:12px;border:1px solid var(--line);border-radius:12px;font-size:16px"><input data-calc-qty inputmode="decimal" placeholder="数量（{esc(category['metric_label'].replace('1',''))}）" style="padding:12px;border:1px solid var(--line);border-radius:12px;font-size:16px"></div><button data-calc-button style="margin-top:8px;width:100%;padding:12px;border:0;border-radius:12px;background:var(--text);color:#fff;font-weight:700;font-size:15px">単価を計算する</button><div data-calc-result class="note" style="display:none;margin-top:10px"></div></section><section class="section"><h2>計算方法</h2><p class="method">商品名に明記された容量・枚数だけを使い、総額 ÷ 総容量（または総枚数）で計算しています。複数容量から選べる商品、容量が曖昧な商品、kgしか書かれていない猫砂などは推測せず除外します。</p><div class="note">単価は安さだけの比較です。吸収力、消臭力、原材料、ペットとの相性、健康効果などを当サイトが評価したものではありません。購入前に販売ページの商品仕様と価格を確認してください。</div></section></div></main><footer class="footer"><div class="wrap">当サイトはアフィリエイト広告を利用しています。価格・在庫は取得時点の情報で、リンク先で変わる場合があります。</div></footer>'''
    title = f"{category['name']}はどれが安い？{category['metric_label']}あたりで比較 | ペット用品コスパ比較"
    desc = f"{category['name']}を{category['metric_label']}あたりの価格に換算して比較。総額では分からない単価を、数量根拠つきで安い順に確認できます。"
    return shell(title, desc, body, category['id'])


def homepage(categories, summaries, updated):
    cards = []
    for c in categories:
        s = summaries[c['id']]
        lowest = yen(s['min']) if s['min'] is not None else '集計中'
        cards.append(f'''<a class="category-card" href="{BASE_URL}categories/{esc(c['id'])}/"><strong>{esc(c['emoji'])} {esc(c['name'])}</strong><p>{esc(c['metric_label'])}あたり最安: {lowest} / 比較 {s['count']}件</p></a>''')
    body = f'''<header class="hero"><div class="wrap"><span class="eyebrow">毎日更新・登録不要</span><h1>ペット用品、本当に安いのはどれ？</h1><p class="lead">袋の値段ではなく、1枚・1Lなど同じ単位に揃えて比較。まずは消耗品だけを、推測を減らして見やすく比べます。</p><p class="trust">最終更新: {esc(updated)} / 楽天市場の商品情報から単価計算</p></div></header>{nav(categories)}<main class="main"><div class="wrap"><section class="section"><h2>比較したいものを選ぶ</h2><div class="grid">{''.join(cards)}</div></section><section class="section"><h2>このサイトのルール</h2><p class="method">①同じ単位に揃える　②比較条件が違う商品はグループを分ける　③数量を読み取れない商品は出さない　④「おすすめ」ではなく数値を見せる。健康効果や品質はAIが勝手に評価しません。</p></section><section class="section"><h2>今後追加する候補</h2><p class="method">キャットフード・ドッグフード・ウェットフードは、年齢・用途・総合栄養食などの条件を混ぜると比較が雑になるため、分類精度を確認してから追加します。</p></section></div></main><footer class="footer"><div class="wrap">当サイトはアフィリエイト広告を利用しています。価格・在庫はリンク先でご確認ください。</div></footer>'''
    return shell("ペット用品コスパ比較 | 1枚・1Lあたりで安さを比較", "ペットシーツ、猫砂、システムトイレシートなどの消耗品を1枚・1Lあたりの単価に揃えて比較します。", body)


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    categories = load_categories()
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    updated = datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M JST")
    demo = os.environ.get("PET_COST_DEMO") == "1"
    summaries = {}

    for category in categories:
        if demo:
            raw = load_fixture(category['id'])
        else:
            raw = []
            for keyword in category.get('keywords', [category.get('keyword', '')]):
                if keyword:
                    raw.extend(fetch_items(keyword, pages=int(category.get('pages_per_keyword', 1))))
        ranked = choose_ranked(raw, category)
        out_dir = SITE / "categories" / category['id']
        write_text(out_dir / "index.html", category_page(category, ranked, categories, updated))
        write_text(SITE / "data" / f"{category['id']}.json", json.dumps({"updated": updated, "category": category, "items": ranked}, ensure_ascii=False, indent=2))
        initial_items = visible_default_items(category, ranked)
        summaries[category['id']] = {
            "count": len(initial_items),
            "min": min([x['unit_price'] for x in initial_items], default=None),
        }

    write_text(SITE / "index.html", homepage(categories, summaries, updated))
    write_text(SITE / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n")
    urls = [BASE_URL] + [f"{BASE_URL}categories/{c['id']}/" for c in categories]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{u}</loc></url>' for u in urls) + '</urlset>'
    write_text(SITE / "sitemap.xml", sitemap)
    print(f"Built {len(categories)} category pages in {SITE}")


if __name__ == "__main__":
    main()
