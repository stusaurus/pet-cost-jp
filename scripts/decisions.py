"""Current catalog, honest observed prices, and publication regression gates."""
import hashlib
import json
from urllib.parse import urlparse, parse_qs
from pathlib import Path

BASE = 'https://stusaurus.github.io/pet-cost-jp/'

def catalog(site):
    products = []
    for path in sorted((site / 'data').glob('*.json')):
        if path.stem in ('price-history', 'decision-catalog'):
            continue
        payload = json.loads(path.read_text())
        groups = payload if path.stem == 'discovery' else {path.stem: payload}
        for category, data in groups.items():
            for item in data.get('items', []):
                direct = parse_qs(urlparse(item['url']).query).get('pc', [''])[0]
                group = item.get('family') or item.get('group') or item.get('play', '')
                quantity = item.get('quantity', item.get('quantity_100g', 0))
                key = hashlib.sha256(f'{category}|{direct}|{group}|{quantity}'.encode()).hexdigest()[:24]
                products.append({'key': key, 'id': item['product_id'], 'category': category,
                    'name': item.get('review_label', item['name']), 'image': item.get('image', ''),
                    'group': group, 'price': item['price'], 'quantity': quantity,
                    'unit': item.get('unit_price'), 'metric': '100g' if 'food' in category else data.get('category', {}).get('metric_label', ''),
                    'shipping': '送料込み' if str(item.get('postage_flag')) == '0' else '送料別・楽天で確認',
                    'url': item['url'], 'age': item.get('age', ''), 'size': item.get('size', ''),
                    'dimensions': item.get('dimensions', ''),
                    'updated': data.get('updated', payload.get('updated', '')),
                    'page': f'{BASE}categories/{category}/'})
    return products

def regression_errors(site, previous):
    errors = []
    for p in sorted((site / 'data').glob('*.json')):
        if p.stem in ('price-history', 'decision-catalog'): continue
        data = json.loads(p.read_text())
        prior_file = previous / p.name
        old = json.loads(prior_file.read_text()) if prior_file.exists() else {}
        groups = data if p.stem == 'discovery' else {p.stem: data}
        olds = old if p.stem == 'discovery' else {p.stem: old}
        for key, payload in groups.items():
            rows = payload.get('items', [])
            before = olds.get(key, {}).get('items', [])
            if payload.get('research', {}).get('fetch_status'):
                errors.append(f'{key}: discovery fetch failed')
            if before and len(rows) < max(1, len(before) * .5):
                errors.append(f'{key}: product count dropped {len(before)} -> {len(rows)}')
            old_groups = {x.get('group') for x in before if x.get('group') not in ('unknown', 'all', None)}
            new_groups = {x.get('group') for x in rows}
            if old_groups - new_groups:
                errors.append(f'{key}: previously available conditions disappeared: {sorted(old_groups-new_groups)}')
    return errors

def enrich(site, previous):
    rows = catalog(site)
    history_path = previous / 'price-history.json'
    history = json.loads(history_path.read_text()) if history_path.exists() else {}
    for row in rows:
        observations = history.get(row['key'], [])
        # A re-render is not a new price observation. One observation per day.
        day = row['updated'][:10]
        if day:
            observations = [x for x in observations if x['date'] != day]
            observations.append({'date': day, 'price': row['price'], 'unit': row['unit']})
        row['history'] = sorted(observations, key=lambda x: x['date'])[-30:]
    history = {r['key']: r['history'] for r in rows}
    (site / 'data' / 'price-history.json').write_text(json.dumps(history, ensure_ascii=False))
    (site / 'data' / 'decision-catalog.json').write_text(json.dumps(rows, ensure_ascii=False))
    encoded = json.dumps(rows, ensure_ascii=False).replace('<', '\\u003c')
    shelf = '<section class="decision-shelf" aria-labelledby="decision-heading"><h2 id="decision-heading">保存して、じっくり選ぶ</h2><p>気になる商品を保存。同じカテゴリ・条件の候補は3件まで並べて比較できます。</p><p data-decision-status role="status" aria-live="polite"></p><div data-saved-products></div><div data-product-comparison></div></section>'
    for p in [site / 'index.html', *sorted((site / 'categories').glob('*/index.html'))]:
        text = p.read_text()
        text = text.replace('</main>', shelf + '</main>')
        text = text.replace('</body>', f'<script type="application/json" id="decision-data">{encoded}</script></body>')
        p.write_text(text)
