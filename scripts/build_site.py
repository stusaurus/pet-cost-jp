import argparse
import html
import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from statistics import median
from zoneinfo import ZoneInfo

from common.engine import choose_ranked
from common.rakuten import fetch_items
from common.catalog import collect as collect_catalog, audit as audit_catalog
from discovery import journey, catalog_body, profile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
CONFIG = ROOT / 'config' / 'categories.json'
FIXTURE = ROOT / 'fixtures' / 'demo_products.json'
BASE_URL = 'https://stusaurus.github.io/pet-cost-jp/'
SITE_NAME = 'ペット用品コスパ比較'
CSS = (ROOT / 'assets' / 'comparison.css').read_text(encoding='utf-8')
CSS += '\n' + (ROOT / 'assets' / 'living.css').read_text(encoding='utf-8')


def yen(value):
    if value is None:
        return '-'
    if value < 10:
        return f'¥{value:.2f}'
    if value < 100:
        return f'¥{value:.1f}'
    return f'¥{value:,.0f}'


def esc(value):
    return html.escape(str(value or ''), quote=True)


def display_name(name):
    """Trim promotional brackets for display; retain original titles in data/GA4."""
    def bracket(match):
        return ' ' if re.search(r'クーポン|ポイント|SALE|セール|限定|当選|OFF|オフ|円引', match.group(0), re.I) else match.group(0)
    text = re.sub(r'【[^】]*】|\[[^\]]*\]', bracket, name)
    text = re.sub(r'当選確率\S*\s*1等最大\S*\s*', '', text)
    return re.sub(r'\s+', ' ', text).strip() or name


def load_categories():
    return json.loads(CONFIG.read_text(encoding='utf-8'))


def load_fixture(category_id):
    return json.loads(FIXTURE.read_text(encoding='utf-8')).get(category_id, []) if FIXTURE.exists() else []


def analytics_head():
    measurement = os.environ.get('GA_MEASUREMENT_ID', '').strip()
    runtime = (ROOT / 'scripts' / 'analytics_runtime.js').read_text(encoding='utf-8')
    runtime += '\n' + (ROOT / 'scripts' / 'living_runtime.js').read_text(encoding='utf-8')
    if not measurement:
        return f'<script>{runtime}</script>'
    return f'''<script async src="https://www.googletagmanager.com/gtag/js?id={esc(measurement)}"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments)}};gtag('js',new Date());gtag('config','{esc(measurement)}');</script><script>{runtime}</script>'''


def schema_script(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False).replace('<', '\\u003c') + '</script>'


def shell(title, description, body, category_id='', schema=None):
    url = f"{BASE_URL}{'categories/'+category_id+'/' if category_id else ''}"
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#426553"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{esc(url)}"><link rel="icon" href="{BASE_URL}assets/favicon.svg" type="image/svg+xml"><link rel="manifest" href="{BASE_URL}assets/site.webmanifest"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(url)}"><meta property="og:image" content="{BASE_URL}assets/living/home.webp"><meta property="og:image:alt" content="朝の光の中でくつろぐ犬と猫、いつもの用品がある暮らし"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{BASE_URL}assets/living/home.webp">{schema_script(schema) if schema else ''}{analytics_head()}<style>{CSS}</style></head><body data-category-id="{esc(category_id)}" data-ui-version="pet-living-1" class="page-{esc(category_id or 'home')}"><a class="skip-link" href="#main">比較へ進む</a>{body}</body></html>'''


def icon(kind):
    shapes = {
        'home': '<path d="m3 10 9-7 9 7v11h-7v-7h-4v7H3z"/>',
        'pet-sheets': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 7h8M8 11h8M8 15h5"/>',
        'cat-litter': '<path d="M3 10h18l-2 11H5zM7 6h.01M12 3h.01M17 6h.01M8 15h.01M13 17h.01M17 14h.01"/>',
        'system-toilet-sheets': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 9h10M7 15h4m3-2 2 2 4-4"/>',
        'fit': '<path d="M8 3H3v5m13-5h5v5M3 16v5h5m13-5v5h-5M7 12l3 3 7-7"/>',
        'quantity': '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h3m4 0h1M8 16h3m4 0h1"/>',
        'audit': '<path d="M20 8a8 8 0 1 0 0 8M20 3v5h-5M8 12l3 3 6-6"/>',
        'unit': '<circle cx="12" cy="12" r="8"/><path d="m8 8 4 4 4-4m-4 4v5m-3-3h6"/>',
        'total': '<path d="M4 7V5h14v3M4 8h16v12H4zM15 12h5v5h-5zM17 14h.01"/>',
        'bulk': '<path d="m3 8 9-5 9 5v12H3zM3 8h18M12 3v5m-5 4h10M7 16h6"/>',
    }
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">' + shapes.get(kind, shapes['home']) + '</svg>'


def care_art(category_id, group='', role='home'):
    """Purpose-made editorial assets; labels, dimensions and fit come from data.

    These concept illustrations never establish actual size, material composition,
    manufacturer compatibility or quality. Empty alt preserves existing UI names.
    """
    illustrated_groups = {
        'pet-sheets': {'regular', 'wide', 'super_wide'},
        'cat-litter': {'paper', 'okara', 'wood', 'mineral', 'mixed', 'system'},
        'system-toilet-sheets': {'deotoilet', 'nyantomo', 'universal'},
    }
    if group in illustrated_groups.get(category_id, set()):
        family = {'pet-sheets': 'sheet', 'cat-litter': 'litter',
                  'system-toilet-sheets': 'system'}[category_id]
        filename = f'filter-{family}-{group}.webp'
        width, height = 240, 180
    else:
        # New/unspecified conditions use a neutral scene, not a guessed material.
        prefix = 'key' if role == 'category' or group else 'scene'
        filename = f'{prefix}-{category_id}.webp'
        width, height = 352, 264
    if not group:
        living_name = {'pet-sheets': 'sheets', 'cat-litter': 'litter', 'system-toilet-sheets': 'system'}[category_id]
        prefix = 'header-' if role == 'category' else ''
        return (f'<img class="editorial-art" src="{BASE_URL}assets/living/{prefix}{living_name}.webp" '
                'width="320" height="240" alt="" aria-hidden="true" data-art-version="pet-living-2" decoding="async">')
    return (f'<img class="editorial-art" src="{BASE_URL}assets/illustrations/{filename}" '
            f'width="{width}" height="{height}" alt="" aria-hidden="true" '
            'data-art-version="editorial-art-1" decoding="async" draggable="false">')


def trust_strip(target):
    return f'<a class="trust-strip" href="#{target}" data-open-standards aria-label="比較の基準を読む"><span>{icon("fit")}条件別に比較</span><span>{icon("quantity")}数量の根拠を確認</span><span>{icon("audit")}更新ごとに監査</span><span class="trust-more" aria-hidden="true">↗</span></a>'


def category_theme(category_id):
    return {'pet-sheets': 'theme-sheet', 'cat-litter': 'theme-litter', 'system-toilet-sheets': 'theme-system'}.get(category_id, 'theme-sheet')


def short_name(category):
    return category['name'].replace('猫用システムトイレシート', 'システムトイレシート')


def nav(categories, current=''):
    links = ''.join(f'<a class="chip{" current" if c["id"] == current else ""}" href="{BASE_URL}categories/{esc(c["id"])}/" {"aria-current=page" if c["id"] == current else ""}><span class="nav-icon">{icon(c["id"])}</span>{esc(short_name(c))}</a>' for c in categories)
    tool = '<a class="nav-tool" href="#comparison-conditions">うちの条件</a>' if current else f'<a class="nav-tool" href="{BASE_URL}#pet-journey">うちの子から選ぶ</a>'
    return f'<nav class="topnav" aria-label="メインナビ"><div class="wrap"><a class="brand" href="{BASE_URL}" aria-label="ペット用品コスパ比較 トップ"><img class="brand-logo" src="{BASE_URL}assets/pet-cost-logo.svg" alt="ペット用品コスパ比較" width="204" height="40"></a><div class="category-nav">{links}</div>{tool}</div></nav>'


def mobile_dock(categories, current=''):
    links = [f'<a class="dock-link{" current" if not current else ""}" href="{BASE_URL}" {"aria-current=page" if not current else ""}><span class="dock-icon">{icon("home")}</span><span>トップ</span></a>']
    for c in categories:
        label = {'pet-sheets': 'シーツ', 'cat-litter': '猫砂', 'system-toilet-sheets': 'トイレシート'}[c['id']]
        links.append(f'<a class="dock-link{" current" if c["id"] == current else ""}" href="{BASE_URL}categories/{esc(c["id"])}/" aria-label="{esc(c["name"])}" {"aria-current=page" if c["id"] == current else ""}><span class="dock-icon">{icon(c["id"])}</span><span>{label}</span></a>')
    return '<nav class="mobile-dock" aria-label="モバイルナビ">' + ''.join(links) + '</nav>'


def group_label(category, group):
    return category.get('groups', {}).get(group, group or '条件')


def shipping_label(flag):
    if str(flag) == '0':
        return '送料込み'
    return '送料別・金額は楽天で確認' if str(flag) == '1' else '送料は楽天で確認'


def visible_default_items(category, items):
    group = category.get('default_group', 'all')
    return items if group == 'all' else [x for x in items if x.get('group') == group]


def comparison_stats(items):
    prices = sorted(x['unit_price'] for x in items)
    return {'min': prices[0] if prices else None, 'median': median(prices) if prices else None}


def relative_price_label(value, middle):
    if not value or not middle or middle <= 0:
        return '比較対象なし'
    diff = (value - middle) / middle * 100
    if abs(diff) < 2:
        return '中央値付近'
    return f"中央値より{abs(diff):.0f}%{'安い' if diff < 0 else '高い'}"


def deal_percent(min_price, median_price):
    return max(0, round((median_price-min_price)/median_price*100)) if min_price and median_price else 0


def affiliate_attrs(category, item, position, source):
    return f'''data-affiliate-link data-merchant="rakuten" data-category-id="{esc(category['id'])}" data-item-id="{esc(item['product_id'])}" data-item-name="{esc(item['name'])}" data-metric="{esc(category['metric'])}" data-unit-price="{item['unit_price']}" data-position="{position}" data-conversion-source="{source}" href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener"'''


def quantity_text(category, item):
    return f"{item['quantity']:g}{'L' if category['metric'] == 'per_liter' else '枚'}"


def group_counts(category, items):
    counts = {}
    for item in items:
        counts[item.get('group', 'unknown')] = counts.get(item.get('group', 'unknown'), 0) + 1
    if 'all' in category.get('groups', {}):
        counts['all'] = len(items)
    return counts


def filter_label(label):
    if label == 'スーパーワイド':
        return '<span>スーパー</span><span>ワイド</span>'
    return esc(label)


def filter_buttons(category, items):
    counts, default = group_counts(category, items), category.get('default_group', 'all')
    hints = {'pet-sheets': '同じサイズ', 'cat-litter': '同じ素材・用途', 'system-toilet-sheets': '同じ対応シリーズ'}
    def buttons(keys):
        return ''.join(f'''<button type="button" class="filter-chip" data-group-button data-group="{esc(key)}" data-group-label="{esc(label)}" aria-pressed="false"><span class="filter-art">{care_art(category['id'], key)}</span><span class="filter-label">{filter_label(label) if key != 'all' else '素材を問わず'}</span><span class="filter-meta">{hints[category['id']] if key != 'all' else '価格の目安・適合は未指定'}</span><span class="filter-count">{counts.get(key, 0)}件</span><span class="filter-check" aria-hidden="true">✓</span></button>''' for key, label in category.get('groups', {}).items() if key in keys and (counts.get(key, 0) > 0 or key == default))
    if category['id'] == 'cat-litter':
        primary = ['paper', 'okara', 'wood', 'mineral']
        return '<div class="filters">' + buttons(primary) + '</div><details class="other-conditions" data-other-conditions><summary>その他の素材・用途 / 素材を問わず</summary><div class="filters">' + buttons([k for k in category['groups'] if k not in primary]) + '</div><p class="condition-note">素材を問わず見る場合は、用途・相性が違う商品も含む価格の目安です。</p></details>'
    return '<div class="filters">' + buttons(category.get('groups', {})) + '</div>'


def usage_panel(category):
    period, label, suffix, example = {
        'pet-sheets': ('day', '1日に何枚使いますか？', '枚 / 日', '5'),
        'cat-litter': ('month', '1か月に何L使いますか？', 'L / 月', '10'),
        'system-toilet-sheets': ('week', '1週間に何枚交換しますか？', '枚 / 週', '1'),
    }[category['id']]
    return f'''<details class="usage-panel" data-usage-panel hidden><summary><span>うちの使用量で見る</span><span class="usage-teaser" data-usage-teaser>任意 · どのくらい持つ？</span></summary><form data-usage-form data-usage-period="{period}" novalidate><div class="usage-form-row"><label class="input-label">{label}<span class="usage-input-wrap"><input class="input" type="text" inputmode="decimal" autocomplete="off" data-usage-input aria-label="{label}" aria-describedby="usage-help usage-error" placeholder="例：{example}"><span>{suffix}</span></span></label><button type="submit" class="btn secondary">使用量を反映</button><button type="button" class="text-button" data-usage-clear>入力を消す</button></div><p class="calc-message" data-usage-error id="usage-error" role="status" hidden></p><p class="condition-note" id="usage-help">いつもの使用量を入れると、各商品の持つ期間と30日分の費用が分かります。1か月＝30日、1週間＝7日で換算。交換頻度のおすすめではありません。</p></form></details>'''


def reason_badges(item, items, middle):
    if not items:
        return []
    reasons = []
    if item['unit_price'] == min(x['unit_price'] for x in items):
        reasons.append(('unit', '単価最安'))
    if middle and item['unit_price'] < middle*.98:
        reasons.append(('median', relative_price_label(item['unit_price'], middle)))
    if item['price'] == min(x['price'] for x in items):
        reasons.append(('total', '支払総額が最小'))
    if item['quantity'] == max(x['quantity'] for x in items):
        reasons.append(('bulk', '最大容量'))
    return reasons


def price_chart(value, middle, metric, prefix='', style_class='price-chart'):
    maximum = max(value or 0, middle or 0, 1)
    rows = []
    for key, label, price in [('min', '現在最安', value), ('median', '掲載中央値', middle)]:
        reference = ' is-reference' if key == 'median' else ''
        bar_hook, value_hook = (f'data-{prefix}-{key}-bar', f'data-{prefix}-{key}-value') if prefix else ('', '')
        rows.append(f'<div class="chart-row"><span>{label}</span><span class="bar-track"><i class="bar-fill{reference}" style="--bar:{(price or 0)/maximum*100:.2f}%" {bar_hook}></i></span><b class="chart-value" {value_hook}>{yen(price)}</b></div>')
    return f'<div class="{style_class}" aria-label="{esc(metric)}あたりの価格差">' + ''.join(rows) + '</div>'


def featured_box(category, item, items=None):
    items = items or ([item] if item else [])
    middle = comparison_stats(items)['median']
    label = group_label(category, category.get('default_group', 'all'))
    attrs = affiliate_attrs(category, item, 1, 'featured_product') if item else 'data-affiliate-link'
    image = f'<img class="featured-img" data-featured-image src="{esc(item.get("image", ""))}" alt="{esc(display_name(item["name"]))}" width="64" height="64">' if item and item.get('image') else '<img class="featured-img" data-featured-image alt="" width="64" height="64" hidden>'
    reason_html = ''.join(f'<span class="cover-reason{" is-primary" if i == 0 else ""}" data-reason-role="{role}">{esc(text)}</span>' for i, (role, text) in enumerate(reason_badges(item, items, middle) if item else []) if role != 'median')
    return f'''<div class="answer-surface featured" data-featured-box {'hidden' if not item else ''}>
      <p class="answer-condition" data-featured-condition>{esc(label)} · {len(items)}件を比較</p>
      <div class="answer-layout"><div class="answer-data">
        <h2 class="answer-heading" data-featured-badge>この条件の最安</h2>
        <div class="answer-price-line"><strong class="featured-unit" data-featured-unit>{yen(item['unit_price']) if item else '-'}</strong><span class="metric">/ {esc(category['metric_label'])}</span></div>
        <div class="answer-diff"><strong class="featured-diff" data-featured-diff>{esc(relative_price_label(item['unit_price'], middle)) if item else ''}</strong><span class="diff-amount" data-featured-gap-amount>{yen(middle-item['unit_price']) if item else '-'} / {esc(category['metric_label'])}の差</span></div>
        {price_chart(item['unit_price'] if item else 0, middle, category['metric_label'], 'answer')}
        <p class="chart-note">同条件の掲載商品との比較。過去価格ではありません。</p>
        <div class="answer-reasons"><p class="reason-title">なぜ、この単価になる？</p><p class="reason-formula" data-featured-formula>{yen(item['price']) + ' ÷ ' + quantity_text(category, item) if item else '-'} = {yen(item['unit_price']) if item else '-'}</p><div class="cover-reasons" data-featured-reasons aria-label="安さの理由">{reason_html}</div><details class="answer-proof"><summary>数量・比較の根拠を見る</summary><p class="reason-copy">商品名で確認できた総数量を使って計算しています。サイズ・素材・対応シリーズが曖昧な候補は掲載せず、更新ごとに分類・数量・単価・重複を監査しています。品質やペットとの相性を保証するものではありません。</p></details></div>
      <div class="usage-outcome" data-featured-usage hidden></div></div><div class="answer-product">{image}<div><h3 class="featured-title" data-featured-title>{esc(display_name(item['name'])) if item else ''}</h3><p class="featured-shop" data-featured-shop>{esc(item.get('shop')) if item else ''}</p></div>
        <div class="answer-checkout"><p class="featured-total" data-featured-total>商品総額 {yen(item['price']) if item else '-'}</p><p class="featured-quantity" data-featured-quantity>{quantity_text(category, item) + ' · ' + esc(item['quantity_evidence']) if item else ''}</p><p class="shipping" data-featured-shipping>{shipping_label(item.get('postage_flag')) if item else ''}</p><div class="featured-action"><a class="btn" {attrs}>楽天で確認</a></div></div>
      </div></div><p class="answer-caveat">単価の比較です。品質・吸収力・相性の順位ではありません。送料別の商品は送料を加算していません。</p></div>'''


def snapshot_cards(category, items):
    middle = comparison_stats(items)['median']
    maximum = max([middle or 0] + [x['unit_price'] for x in items[:3]] + [1])
    parts = []
    for rank, item in enumerate(items[:3], 1):
        delta = item['unit_price'] - items[0]['unit_price']
        difference = '単価が最小' if rank == 1 else ('1位と同じ単価' if abs(delta) < 1e-9 else f"1位より +{yen(delta)} / {category['metric_label']}")
        parts.append(f'''<a class="top3-card" data-top3-card {affiliate_attrs(category, item, rank, 'top3_snapshot')}><span class="top3-rank">{rank}</span><div class="top3-copy"><span class="top3-unit">{yen(item['unit_price'])}<small> / {esc(category['metric_label'])}</small></span><span class="top3-difference">{esc(difference)}</span><span class="top3-name">{esc(display_name(item['name']))}</span><div class="top3-meta"><span>商品総額 {yen(item['price'])}</span><span>{esc(relative_price_label(item['unit_price'], middle))}</span></div></div><div class="top3-chart"><span class="bar-track"><i class="bar-fill" style="--bar:{item['unit_price']/maximum*100:.2f}%"></i></span><div class="top3-chart-label"><span>{'最小' if rank == 1 else '同じ尺度で比較'}</span><span>楽天で確認</span></div></div></a>''')
    return ''.join(parts)


def angle_picks(items):
    if not items:
        return []
    return [('unit', '長く使って安く', '単価重視', min(items, key=lambda x: (x['unit_price'], x['price']))), ('total', '今日は出費を抑える', '支払総額重視', min(items, key=lambda x: (x['price'], x['unit_price']))), ('bulk', '買い足す回数を減らす', 'まとめ買い重視', max(items, key=lambda x: (x['quantity'], -x['unit_price'])))]


def angle_cards(category, items):
    picks = angle_picks(items) or [('unit', '長く使って安く', '単価重視', None), ('total', '今日は出費を抑える', '支払総額重視', None), ('bulk', '買い足す回数を減らす', 'まとめ買い重視', None)]
    def value(role, item):
        if not item:
            return '-'
        return yen(item['unit_price']) + ' / ' + category['metric_label'] if role == 'unit' else yen(item['price']) if role == 'total' else quantity_text(category, item)
    return ''.join(f'''<button type="button" class="angle-card" data-angle-card data-angle-role="{role}" aria-pressed="{'true' if role == 'unit' else 'false'}"><span class="angle-symbol">{icon(role)}</span><span class="angle-label">{label}</span><span class="angle-sub">{reason}</span><span class="angle-value" data-angle-value>{esc(value(role, item))}</span><span class="angle-lifetime" data-angle-lifetime hidden></span><span class="angle-state" aria-hidden="true">この選び方で見る <b>→</b></span></button>''' for role, label, reason, item in picks)


def angle_detail(category, items):
    item = angle_picks(items)[0][3] if items else None
    attrs = affiliate_attrs(category, item, 1, 'comparison_angle_unit') if item else 'data-affiliate-link'
    return f'''<div class="angle-detail" data-angle-detail {'hidden' if not item else ''}><div><p class="angle-detail-reason" data-angle-reason>この条件で、単価が最小</p><h3 class="angle-detail-title" data-angle-name>{esc(display_name(item['name'])) if item else ''}</h3></div><div class="angle-metrics"><div class="angle-metric"><span>単価 / {esc(category['metric_label'])}</span><b data-angle-unit>{yen(item['unit_price']) if item else '-'}</b></div><div class="angle-metric"><span>商品総額</span><b data-angle-total>{yen(item['price']) if item else '-'}</b></div><div class="angle-metric"><span>総数量</span><b data-angle-quantity>{quantity_text(category, item) if item else '-'}</b></div></div><div class="usage-outcome" data-angle-usage hidden></div><div class="angle-detail-foot"><p class="angle-explain" data-angle-explain>1枚・1Lの負担を抑える選び方。購入額・送料も一緒に確認してください。</p><a class="btn secondary" data-angle-link {attrs}>楽天で確認</a></div></div>'''


def product_rows(items, category):
    visible = visible_default_items(category, items)
    middle = comparison_stats(visible)['median']
    parts = []
    for item in items:
        rank = visible.index(item)+1 if item in visible else 0
        classes = 'shop-card' + (f' is-rank-{rank}' if 0 < rank <= 3 else '')
        reasons = reason_badges(item, visible, middle) if rank else []
        reasons_html = ''.join(f'<span class="value-badge{" is-primary" if i == 0 else " value-badge-secondary"}" data-reason-role="{role}">{esc(text)}</span>' for i, (role, text) in enumerate(reasons))
        if not reasons:
            reasons_html = f'<span class="value-badge">{esc(relative_price_label(item["unit_price"], middle)) if rank else ""}</span>'
        image = f'<img class="shop-card-image" src="{esc(item.get("image"))}" alt="" loading="lazy" width="64" height="64">' if item.get('image') else ''
        parts.append(f'''<article class="{classes}" id="product-{esc(item['product_id'])}" data-product-row data-group="{esc(item['group'])}" data-row-unit-price="{item['unit_price']}" data-total-price="{item['price']}" data-quantity="{item['quantity']}" data-quantity-evidence="{esc(item['quantity_evidence'])}" data-image="{esc(item.get('image'))}" data-item-id="{esc(item['product_id'])}" data-item-name="{esc(item['name'])}" data-display-name="{esc(display_name(item['name']))}" data-shop="{esc(item.get('shop'))}" data-shipping="{esc(shipping_label(item.get('postage_flag')))}" data-url="{esc(item['url'])}" {'hidden' if not rank else ''}>
          <span class="shop-card-rank" data-rank-cell aria-label="単価順位">{rank}</span><div class="shop-card-image-wrap">{image}</div><div class="shop-card-prices"><div class="shop-unit">{yen(item['unit_price'])}<small> / {esc(category['metric_label'])}</small></div></div><div class="value-badge-row" data-value-badges aria-label="安さの理由">{reasons_html}</div><div class="shop-card-head"><details class="product-name"><summary><span class="shop-card-title">{esc(display_name(item['name']))}</span><span class="name-toggle" aria-hidden="true"></span></summary><p class="original-name">楽天の商品名：{esc(item['name'])}</p></details><div class="shop-card-shop">{esc(item.get('shop'))}</div><div class="shop-card-tags">{quantity_text(category, item)} · {esc(item['quantity_evidence'])} · {esc(group_label(category, item['group']))}</div><p class="shop-usage" data-row-usage hidden></p></div><div class="shop-checkout"><div class="shop-card-meta"><div class="shop-total"><span>商品総額</span>{yen(item['price'])}</div><div class="shipping">{esc(shipping_label(item.get('postage_flag')))}</div></div><div class="shop-card-action"><a class="btn secondary" {affiliate_attrs(category, item, rank, 'comparison_card')}>楽天で確認</a></div></div></article>''')
    return ''.join(parts)


def guide_html(category):
    return '<div class="guide-grid">' + ''.join(f'<p class="guide-item">{esc(x)}</p>' for x in category.get('guide', [])) + '</div>'


def faq_html(category):
    return '<div class="faq">' + ''.join(f'<details><summary>{esc(x["q"])}</summary><p>{esc(x["a"])}</p></details>' for x in category.get('faq', [])) + '</div>'


def footer():
    return f'''<footer class="footer"><div class="wrap footer-box"><div class="footer-brand"><img class="footer-logo" src="{BASE_URL}assets/pet-cost-logo.svg" alt="ペット用品コスパ比較" width="184" height="36"></div><div>当サイトはアフィリエイト広告を利用しています。価格・在庫・送料・商品仕様は取得後に変更される場合があるため、購入前に楽天市場の商品ページでご確認ください。</div><div class="rakuten-credit"><!-- Rakuten Web Services Attribution Snippet FROM HERE --><a href="https://developers.rakuten.com/" target="_blank" rel="noopener">Supported by Rakuten Developers</a><!-- Rakuten Web Services Attribution Snippet TO HERE --></div></div></footer>'''


def category_page(category, items, categories, updated):
    initial = visible_default_items(category, items)
    stats = comparison_stats(initial)
    label = group_label(category, category.get('default_group', 'all'))
    prompt = {'pet-sheets': '使っているサイズは？', 'cat-litter': '普段使っている素材は？', 'system-toilet-sheets': '使っているトイレは？'}[category['id']]
    fit_note = {'pet-sheets': 'いつものサイズだけで比較します。厚さ・吸収力は商品ごとに確かめてください。', 'cat-litter': 'いつもの素材・用途だけで比較します。kgからLへの推測換算はしません。', 'system-toilet-sheets': '本体に合うシリーズだけで比較します。寸法・対応機種は購入前に商品ページで確認してください。'}[category['id']]
    suffix = 'L' if category['metric'] == 'per_liter' else '枚'
    schema = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
        {'@type': 'ListItem', 'position': 1, 'name': 'トップ', 'item': BASE_URL},
        {'@type': 'ListItem', 'position': 2, 'name': category['name'], 'item': f"{BASE_URL}categories/{category['id']}/"},
    ]}
    body = f'''{nav(categories, category['id'])}
    <header class="page-intro wrap"><div class="category-intro-copy"><p class="home-kicker">うちの子の、いつもの用品</p><h1>{esc(short_name(category))}</h1><p class="intro-copy">うちの条件で、次の買い足しを。</p><span class="updated">最終更新 {esc(updated)}</span></div><div class="category-art">{care_art(category['id'], role='category')}</div></header>
    <main id="main" class="main wrap" data-metric="{category['metric']}" data-metric-label="{category['metric_label']}">
      <a class="text-link" href="{BASE_URL}#pet-journey">うちの子と用品を選び直す →</a>
      {profile('dog' if category['id'] == 'pet-sheets' else 'cat')}
      <section class="condition-panel" id="comparison-conditions" aria-labelledby="condition-heading" data-condition-panel>
        <div class="condition-heading-row"><div><div class="step-label"><span class="step-number">01</span>まずは、いつも使うものから</div><h2 id="condition-heading">{prompt}</h2></div><span class="condition-progress" data-condition-progress>条件を選ぶ <span aria-hidden="true">→</span> 比較する</span></div>
        <p class="condition-note">{fit_note}</p>
        <div class="filter-wrap"><div data-group-filter data-default-group="{esc(category.get('default_group', 'all'))}" data-rank-all="{1 if category.get('rank_all') else 0}">{filter_buttons(category, items)}</div></div>
        <div class="condition-foot"><p class="result-status" data-result-status role="status" aria-live="polite" aria-atomic="true">選ぶと、うちの条件の比較に切り替わります。</p><span class="condition-save">次回もこの端末で引き継げます</span></div>
        {usage_panel(category)}
      </section>
      <div class="condition-start" data-condition-start><span class="start-mark">{icon('fit')}</span><div><p>いつもの条件が、比較のスタート。</p><span>選んだあとに、単価・買う量・今回の出費を比べられます。使用量の入力は任意です。</span></div></div>
      <noscript><style>[data-comparison-results][hidden]{{display:block!important}}[data-condition-start],[data-group-filter],.condition-foot{{display:none!important}}</style><p class="condition-note">JavaScriptが無効のため、{esc(label)}の比較例を表示しています。条件・使用量の変更にはJavaScriptを有効にしてください。</p></noscript>
      <div data-comparison-results hidden>
      <aside class="comparison-sticky" data-comparison-sticky aria-label="現在の比較条件"><div class="comparison-sticky-inner">
        <a class="sticky-cell sticky-condition" href="#comparison-conditions" aria-label="比較条件を変更"><span class="sticky-label" data-sticky-condition-title>比較例の条件</span><strong class="sticky-value" data-sticky-condition>{esc(label)}</strong></a>
        <div class="sticky-cell sticky-price"><span class="sticky-label">現在最安</span><strong class="sticky-value" data-sticky-min>{yen(stats['min'])} / {esc(category['metric_label'])}</strong></div>
        <div class="sticky-cell sticky-gap"><span class="sticky-label">中央値との差</span><strong class="sticky-value" data-sticky-gap>{relative_price_label(stats['min'], stats['median'])}</strong></div>
        <div class="sticky-cell sticky-count"><span class="sticky-label">表示件数</span><strong class="sticky-value" data-sticky-count>{len(initial)}件</strong></div><a class="sticky-jump" href="#product-ranking" aria-label="商品ランキングへ移動">一覧</a>
      </div></aside>
      <section class="answer-section" id="comparison-answer" aria-label="この条件の比較結果">
        {featured_box(category, initial[0] if initial else None, initial)}
        <p class="empty-result" data-empty-result {'hidden' if initial else ''}>この条件では、安全に単価を比較できる掲載商品がありません。別の条件を選んでください。</p>
        <div class="results-bridge"><a class="text-link" href="#top-three">2位・3位の差を見る</a><a class="text-link" href="#comparison-angles">別の選び方で比べる</a></div>
      </section>
      <section class="section snapshot-section" id="top-three" aria-labelledby="top3-heading">
        <div class="section-head"><div><div class="step-label"><span class="step-number">02</span>うちに合う買い方を比べる</div><h2 id="top3-heading">1位・2位・3位、どのくらい違う？</h2><p class="section-sub">バーの長さは単価。同じ尺度、0円から表示しています。</p></div></div>
        <div class="top3-strip" data-top3-strip>{snapshot_cards(category, initial)}</div><p class="snapshot-note">同じ単価なら、バーも同じ長さ。順位は価格順で、品質のおすすめではありません。</p>
      </section>
      <section class="section buying-section" id="comparison-angles" aria-labelledby="angle-heading">
        <div class="section-head"><div><p class="section-eyebrow">暮らしに合わせて、選び方も。</p><h2 id="angle-heading">次の買い足し、どう買う？</h2><p class="section-sub">今日はどれを大切にしますか？ 押すと、その選び方の候補へ。</p></div><a class="text-link" href="#comparison-conditions" data-open-usage>使用量を入れる</a></div>
        <div class="angle-grid" data-angle-grid>{angle_cards(category, initial)}</div><p class="condition-note" data-usage-scale-note hidden>細いバーは持つ期間。3候補を同じ尺度で比べています。</p>{angle_detail(category, initial)}
        <p class="angle-note">品質のおすすめではなく、数値による選び方です。同じ商品が複数の候補になることもあります。商品総額に送料別の送料は未加算です。</p>
      </section>
      <section class="section" id="product-ranking" aria-labelledby="ranking-heading">
        <div class="section-head list-heading"><div><div class="step-label"><span class="step-number">03</span>買う量と今回の出費を確かめる</div><h2 id="ranking-heading">うちの条件で、単価が安い順</h2><p class="section-sub" data-list-context>{esc(label)} · {len(initial)}件 · {esc(category['metric_label'])}あたり</p></div><a class="text-link" href="#comparison-conditions">条件を変更</a></div>
        <div class="product-grid" data-product-grid>{product_rows(items, category)}</div><p class="empty-result" data-list-empty {'hidden' if initial else ''}>比較できる商品がありません。</p>
      </section>
      <section class="section calc-section" id="store-calculator" aria-labelledby="calculator-heading">
        <div class="section-head"><div><p class="step-label">お店で同じ条件の商品を見つけたら</p><h2 id="calculator-heading">店頭の商品も、うちの条件で比較</h2></div></div>
        <div class="calc-steps" aria-label="店頭比較の流れ"><span>値段と数量を入力</span><span>{category['metric_label']}単価に換算</span><span>掲載最安と比較</span></div>
        <div class="calc-layout"><form class="calculator" data-calculator novalidate><div class="calc-inputs">
          <label class="input-label">店頭の値段<span class="input-unit">（税込・円）</span><input class="input" type="text" inputmode="decimal" autocomplete="off" data-calc-price aria-label="店頭商品の総額" aria-describedby="calc-error" placeholder="例：980"></label>
          <label class="input-label">総数量<span class="input-unit">（{suffix}）</span><input class="input" type="text" inputmode="decimal" autocomplete="off" data-calc-qty aria-label="店頭商品の数量" aria-describedby="calc-error" placeholder="例：{'10' if suffix == 'L' else '100'}"></label>
        </div><button class="btn secondary" data-calc-button type="submit">この価格を比較する</button><p class="calc-message" id="calc-error" data-calc-error role="status" hidden></p><p class="calc-context">比較する条件：<strong data-calc-condition>{esc(label)}</strong> <a href="#comparison-conditions" class="text-link">変更</a></p></form>
        <div class="calc-output" aria-live="polite" aria-atomic="true"><p class="calc-placeholder" data-calc-placeholder><b>袋の値段を、同じ単位に。</b>値段 ÷ 総数量で{category['metric_label']}単価に換算し、現在掲載中の楽天商品と比べます。</p><div data-calc-result hidden></div></div></div>
        <p class="calc-disclaimer">店頭商品も選択中の条件と合うか確認してください。送料別の掲載商品は送料未加算です。吸収力・素材の質・ペットとの相性は価格比較に含みません。</p>
      </section>
      <section class="section method-section" id="comparison-method" aria-label="比較方法とよくある質問">
        <details class="method-details"><summary>比較するときのポイント</summary>{guide_html(category)}</details>
        <details class="method-details"><summary>このランキングの作り方</summary><p class="method">楽天市場の商品名に明記された枚数・容量だけを使い、「掲載商品価格 ÷ 総数量」で単価を計算します。</p><ul class="method method-list"><li>サイズ・容量が一意に確定できない選択式商品は除外</li><li>kgしかない猫砂はLへ推測換算しない</li><li>中古・訳あり・定期便・ふるさと納税などは除外</li><li>同じ商品ファミリーは最安単価と最小総額の最大2件まで</li><li>中央値は単価を安い順に並べた中央の値。偶数件では中央2件の平均</li><li>表示単価は小数点以下を丸めています。順位と価格差は丸める前の値で計算</li></ul><p class="method">これは価格の順位です。吸収力・消臭力・原材料・ペットとの相性の評価ではありません。</p></details>
        <h2>よくある質問</h2>{faq_html(category)}
      </section></div>
    </main>{footer()}{mobile_dock(categories, category['id'])}'''
    title = f"{category['name']}はどれが安い？{category['metric_label']}あたりで比較 | {SITE_NAME}"
    desc = f"{category['name']}を{category['metric_label']}あたりに換算して安い順に比較。数量が曖昧な商品は除外し、条件別の最安値・総額・数量根拠まで確認できます。"
    return shell(title, desc, body, category['id'], schema)


def homepage(categories, summaries, updated):
    ordered = sorted(categories, key=lambda c: (summaries.get(c['id'], {}).get('deal_percent', 0), summaries.get(c['id'], {}).get('total_count', 0)), reverse=True)
    entries = []
    for position, category in enumerate(ordered, 1):
        s = summaries.get(category['id'], {})
        gap = s.get('deal_percent', 0)
        entries.append(f'''<a class="category-entry {category_theme(category['id'])}" data-editorial-category="{category['id']}" data-editorial-position="{position}" data-spotlight-link data-category-id="{category['id']}" data-gap-percent="{gap}" href="{BASE_URL}categories/{category['id']}/">
          <div class="entry-top"><span class="entry-icon">{icon(category['id'])}</span><h3>{esc(short_name(category))}</h3></div><p class="entry-condition">{esc(s.get('default_label', ''))} · {esc(category['metric_label'])}あたりで比較</p>
          <div class="entry-price-wrap"><p class="entry-caption">この条件の現在最安</p><p class="entry-price">{yen(s.get('min'))}<small> / {category['metric_label']}</small></p></div>
          <div class="entry-gap"><b>{gap}%</b><span>掲載中央値より低い</span></div><div class="entry-chart">{price_chart(s.get('min'), s.get('median'), category['metric_label'], style_class='price-chart')}</div>
          <div class="entry-cta"><span>条件を選んで比較</span><span class="entry-count">この条件 {s.get('default_count', 0)}件</span></div>
        </a>''')
    starts = []
    for c in categories:
        question, choices, pet = {
            'pet-sheets': ('使っているサイズは？', 'レギュラー / ワイド / スーパーワイド', '犬・猫のトイレに'),
            'cat-litter': ('普段使っている素材は？', '紙 / おから / 木 / 鉱物など', '猫のトイレに'),
            'system-toilet-sheets': ('使っているトイレは？', 'デオトイレ / ニャンとも / 各社共通など', '猫のシステムトイレに'),
        }[c['id']]
        starts.append(f'''<a class="care-entry {category_theme(c['id'])}" data-pet-category="{c['id']}" href="{BASE_URL}categories/{c['id']}/"><span class="care-art">{care_art(c['id'])}</span><div class="care-copy"><span class="care-for">{pet}</span><h3>{esc(short_name(c))}</h3><p class="care-question">{question}</p><p class="care-choices" data-saved-condition>{choices}</p></div><span class="care-arrow" aria-hidden="true">→</span></a>''')
    schema = {'@context': 'https://schema.org', '@type': 'WebSite', 'name': SITE_NAME, 'url': BASE_URL, 'description': 'うちで使えるペット用品を、うちの条件・使用量で比較するサイト'}
    body = f'''{nav(categories)}<main id="main" class="main wrap">
      <header class="home-intro"><div class="home-intro-copy"><p class="home-kicker">ごはんも、遊びも、いつもの用品も。</p><h1>うちの子との毎日を、<br><em>心地よく。</em></h1><p class="home-note">うちの子に使えるものから、暮らしに合う選び方へ。<br>好きな遊びも、買い足す量も、一緒に見つけましょう。</p><a class="hero-start" href="#pet-journey">うちの子から選ぶ <span aria-hidden="true">↓</span></a></div><figure class="home-scene"><img class="home-photo" src="{BASE_URL}assets/living/home.webp" alt="朝の光の中、犬と猫がラグでくつろぐ。ごはんと遊びの道具が自然にある暮らし" width="1200" height="800" fetchpriority="high"><figcaption>その子に使えるものを、その家の暮らしで。</figcaption></figure></header>
      {journey()}
      <section class="home-comparison" id="categories" aria-labelledby="categories-heading"><div class="section-head"><div><p class="section-eyebrow">条件が決まっている方へ</p><h2 id="categories-heading">いつもの用品をすぐ比べる</h2></div><span class="section-count">サイズ・素材・本体から</span></div><div class="care-entry-grid">{''.join(starts)}</div></section>
      {trust_strip('comparison-standards')}
      <section class="home-journey" aria-label="うちの使い方で比較する流れ"><div><span class="journey-icon">{icon('fit')}</span><h3>うちで使える？</h3><p>いつものサイズ・素材・本体から。<br>使える条件だけで価格を比較。</p></div><div><span class="journey-icon">{icon('audit')}</span><h3>どのくらい持つ？</h3><p>使用量を入れれば、期間と月の費用に。<br>単価を、暮らしの数字へ。</p></div><div><span class="journey-icon">{icon('bulk')}</span><h3>買い足すならどれ？</h3><p>今回の出費も、まとめ買いも。<br>うちに合う買い方を選ぶ。</p></div></section>
      <p class="home-usage-note">使用量の入力は任意。条件・使用量は、この端末に保存されます。</p>
      <details class="home-price-details" data-daily-spotlight><summary><span>今日の価格差も見る</span><span class="updated">最終更新 {esc(updated)}</span></summary><p class="section-sub">代表条件での比較例。価格差が大きい順に表示しています。</p><div class="category-entry-grid">{''.join(entries)}</div><p class="home-price-note">価格差は、表示した条件の「現在掲載商品の最安と中央値の差」です。過去価格や値下げを示すものではありません。ご自身の条件は、カテゴリを開いて選んでください。</p></details>
      <section class="home-tools"><details class="home-standards" id="comparison-standards"><summary><span class="standards-icon">{icon('fit')}</span><span>気持ちよく選ぶために、<br><b>比較の基準をそろえています。</b></span><span class="disclosure-mark" aria-hidden="true">+</span></summary><div class="standards-body"><p>サイズ・素材・対応シリーズを混ぜずに比較。数量が曖昧な選択式商品、中古・訳あり商品は除外し、更新ごとに数量・分類・単価・重複を監査しています。</p><p>単価順位は、品質やペットとの相性のおすすめではありません。送料別の送料は未加算。購入前に楽天で仕様・送料・現在価格を確認してください。</p></div></details><div class="store-home-note"><span class="standards-icon">{icon('quantity')}</span><div><h3>お店で見つけた、いつもの用品も。</h3><p>各カテゴリの店頭比較で、値段と数量を同じ単位に。うちの条件の商品と比べられます。</p></div></div></section>
    </main>{footer()}{mobile_dock(categories)}'''
    return shell(f'{SITE_NAME} | うちの条件・使い方で比べる', 'ペットシーツのサイズ、猫砂の素材、システムトイレ本体に合う条件から価格比較。使用量を入れると持つ期間と30日分の費用も分かります。', body, schema=schema)


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def copy_static_verification_files():
    for source in ROOT.glob('google*.html'):
        shutil.copy2(source, SITE / source.name)
    if (ROOT / 'assets').exists():
        shutil.copytree(ROOT / 'assets', SITE / 'assets', dirs_exist_ok=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reuse-data', action='store_true', help='Render committed, audited data without calling the API (local/PR QA only).')
    args = parser.parse_args()
    categories = load_categories()
    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    updated = datetime.now(ZoneInfo('Asia/Tokyo')).strftime('%Y-%m-%d %H:%M JST')
    demo = os.environ.get('PET_COST_DEMO') == '1'
    summaries = {}
    for category in categories:
        category_updated = updated
        if args.reuse_data:
            payload = json.loads((ROOT / 'data' / f"{category['id']}.json").read_text(encoding='utf-8'))
            ranked = payload['items']
            category_updated = payload['updated']
        else:
            raw = load_fixture(category['id']) if demo else []
            if not demo:
                for keyword in category.get('keywords', [category.get('keyword', '')]):
                    if keyword:
                        raw.extend(fetch_items(keyword, pages=int(category.get('pages_per_keyword', 1))))
            ranked = choose_ranked(raw, category)
        write_text(SITE / 'categories' / category['id'] / 'index.html', category_page(category, ranked, categories, category_updated))
        write_text(SITE / 'data' / f"{category['id']}.json", json.dumps({'updated': category_updated, 'category': category, 'items': ranked}, ensure_ascii=False, indent=2))
        spotlight_group = 'paper' if category['id'] == 'cat-litter' else category.get('default_group', 'all')
        initial = [x for x in ranked if x['group'] == spotlight_group]
        stats = comparison_stats(initial)
        summaries[category['id']] = {'total_count': len(ranked), 'default_count': len(initial), **stats, 'deal_percent': deal_percent(stats['min'], stats['median']), 'best': initial[0] if initial else None, 'default_label': group_label(category, spotlight_group)}
    if args.reuse_data:
        updated = max(json.loads((ROOT / 'data' / f"{c['id']}.json").read_text())['updated'] for c in categories)
    discovery_config = json.loads((ROOT / 'config' / 'discovery.json').read_text())
    discovery_data = {}
    prior_path = ROOT / 'data' / 'discovery.json'
    prior = json.loads(prior_path.read_text()) if prior_path.exists() else {}
    for key, config in discovery_config.items():
        if key == 'version':
            continue
        if args.reuse_data or demo:
            result = prior.get(key, {'items': [], 'research': {'fetched': 0, 'eligible': 0, 'held_by_reason': {}}, 'version': 1})
            if config.get('publish_products'):
                result = {**result, 'items': collect_catalog(result.get('items',[]),config)['items']}
        else:
            raw = []
            try:
                for keyword in config['keywords']:
                    raw.extend(fetch_items(keyword, pages=1))
                # Reviewed shops can fall outside the first broad-search page.
                # Use the documented shopCode filter; every result still passes the URL/title gate.
                for lookup in config.get('reviewed_lookups',[]):
                    raw.extend(fetch_items(lookup['keyword'], pages=1, shop_code=lookup['shop_code']))
                result = collect_catalog(raw, config)
            except Exception as error:
                # Never expose request URLs/credentials. Unverified prior prices are not reused.
                result = {'items': [], 'research': {'fetched': len(raw), 'eligible': 0, 'fetch_status': type(error).__name__}, 'version': 1}
        if not args.reuse_data and not demo:
            print('DISCOVERY_REVIEW ' + json.dumps({'category': key, **result}, ensure_ascii=False))
        if not config.get('publish_products'):
            result = {**result, 'items': []}
        discovery_data[key] = result
        body = catalog_body(key, config, result, nav(categories), footer(), mobile_dock(categories))
        schema = {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [{'@type': 'ListItem', 'position': 1, 'name': 'トップ', 'item': BASE_URL}, {'@type': 'ListItem', 'position': 2, 'name': config['name'], 'item': f'{BASE_URL}categories/{key}/'}]}
        write_text(SITE / 'categories' / key / 'index.html', shell(config['name']+' | うちの子との暮らし', '遊び方と確認できる商品表記から候補を探す。ごはんは入力した袋の内容量と1日量から持つ期間と費用を計算。', body, key, schema))
    errors = audit_catalog(discovery_data, discovery_config)
    if errors:
        raise RuntimeError('Discovery quality audit failed: '+ '; '.join(errors))
    write_text(SITE / 'data' / 'discovery.json', json.dumps(discovery_data, ensure_ascii=False, indent=2))
    write_text(SITE / 'index.html', homepage(categories, summaries, updated))
    write_text(SITE / 'robots.txt', f'User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n')
    urls = [BASE_URL] + [f"{BASE_URL}categories/{c['id']}/" for c in categories] + [f'{BASE_URL}categories/{key}/' for key in discovery_data]
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + ''.join(f'<url><loc>{u}</loc></url>' for u in urls) + '</urlset>'
    write_text(SITE / 'sitemap.xml', sitemap)
    copy_static_verification_files()
    print(f'Built {len(categories) + len(discovery_data)} category pages in {SITE}')


if __name__ == '__main__':
    main()
