"""Evidence-only discovery; no inferred suitability or toy price ranking."""
import re
import math
from datetime import date
from urllib.parse import urlparse, parse_qs
from .quantity import normalize_text
from .engine import GLOBAL_EXCLUDE, parse_quantity, product_id

EXCLUDE = GLOBAL_EXCLUDE + ('選べる', '選択', 'ランダム', '種類おまかせ', '色おまかせ', 'サイズ展開', 'よりどり', '福袋', '詰め合わせ', '交換用', '替え用', 'パーツ', 'セット内容', '各種', 'sサイズ', 'mサイズ', 'lサイズ', '点セット', '中大型犬')
MEDICAL = ('療法', '腎臓', '尿路', '消化器', '糖尿', 'アレルギー', '肥満', '治療', '減量', 'ダイエット', '処方', 'おやつ', 'スナック', 'サプリ')
AGE = {'young':('子犬', '子猫', 'パピー', 'キトン'), 'adult':('成犬', '成猫', 'アダルト'), 'senior':('シニア', '高齢', '老犬', '老猫')}
SIZE = {'small':('小型犬', '超小型犬'), 'medium':('中型犬',), 'large':('大型犬',)}
PLAY = {'chew':('噛む', 'かむ', 'カミカミ'), 'chase':('ボール', 'フリスビー'), 'together':('ロープ', '引っ張り'), 'puzzle':('知育', 'パズル'), 'teaser':('じゃらし',), 'hide':('トンネル', '蹴りぐるみ')}

def matching(text, mapping):
    return {key: next((word for word in words if normalize_text(word) in text), '') for key, words in mapping.items()}

def reviewed(item, config):
    direct = parse_qs(urlparse(item.get('url','')).query).get('pc',[''])[0]
    review = config.get('approved_products',{}).get(direct)
    if not review: return None
    try:
        age = (date.today() - date.fromisoformat(review['reviewed_on'])).days
    except (KeyError,ValueError): return None
    if not 0 <= age <= 180: return None
    title = normalize_text(item['name'])
    if not all(normalize_text(term) in title for term in review['required_title_terms']): return None
    if any(normalize_text(term) in title for term in review.get('forbidden_title_terms',[])): return None
    if config['kind']=='food':
        family=config.get('food_families',{}).get(review.get('family'),{})
        if not family or family.get('species')!=config['species'] or family.get('age') not in AGE: return None
        if family.get('form')!='dry' or family.get('nutrition')!='complete': return None
        source=urlparse(family.get('manufacturer_source',''))
        if source.scheme!='https' or source.hostname!='www.royalcanin.com': return None
        if any(item.get(k)!=review.get(k) for k in ('family','pack_grams','pack_count','quantity_100g')): return None
        if any(item.get(k)!=family.get(k) for k in ('species','age','size','form','nutrition')): return None
        if review['pack_grams'] * review['pack_count'] / 100 != item['quantity_100g']: return None
    elif any(item.get(k) != review.get(k) for k in ('play','age','size','dimensions')): return None
    return review

def inspect(raw, config):
    title = raw.get('name', '')
    t = normalize_text(title)
    def reject(reason): return None, reason
    if not title or not isinstance(raw.get('price'),(int,float)) or not math.isfinite(raw['price']) or raw['price'] <= 0: return reject('価格・名称不明')
    if any(normalize_text(w) in t for w in EXCLUDE): return reject('除外条件・選択式')
    u = urlparse(raw.get('url', ''))
    direct = parse_qs(u.query).get('pc', [''])[0]
    if u.hostname != 'hb.afl.rakuten.co.jp' or urlparse(direct).hostname != 'item.rakuten.co.jp': return reject('商品URL未確認')
    dog = bool(re.search('犬|ドッグ|dog', t))
    cat = bool(re.search('猫|ねこ|ネコ|キャット|cat', t))
    if dog == cat or (config['species'] == 'dog') != dog: return reject('対象動物不明・混在')
    ages = {k:v for k,v in matching(t, AGE).items() if v}
    sizes = {k:v for k,v in matching(t, SIZE).items() if v}
    species_quote = re.search('犬|ドッグ|dog' if dog else '猫|ねこ|ネコ|キャット|cat', t).group()
    evidence = [{'attribute':'species','quote':species_quote,'source':'商品タイトル'}]
    if config['kind'] == 'food':
        if any(normalize_text(w) in t for w in MEDICAL): return reject('医療・用途対象外')
        review=config.get('approved_products',{}).get(direct)
        if review:
            family=config.get('food_families',{}).get(review.get('family'),{})
            if not family or any(a!=family.get('age') for a in ages) or any(s!=family.get('size') for s in sizes): return reject('対象条件変更')
            # A set expression must not conceal another weight (bonus, mixed recipe, variant).
            weights=[float(n)*(1000 if unit=='kg' else 1) for n,unit in re.findall(r'(?<!\d)(\d+(?:\.\d+)?)\s*(kg|g)',t)]
            if any(w not in (review.get('pack_grams'),review.get('quantity_100g',0)*100) for w in weights): return reject('複数容量・混合セット')
            q=parse_quantity(title,'weight_100g')
            if not q or q['confidence']<.9 or q['quantity']!=review.get('quantity_100g'): return reject('内容量変更・未確定')
            evidence += [{'attribute':'quantity','quote':q['evidence'],'source':'商品タイトル'}]
            evidence += [{'attribute':a,'value':family.get(a,''),'source':family.get('manufacturer_source',''),'method':'個別照合'} for a in ('age','size','form','nutrition') if family.get(a)]
            item={**raw,'product_id':product_id(title,raw.get('shop','')),'species':config['species'],**{k:family.get(k) for k in ('age','size','form','nutrition')},**{k:review.get(k) for k in ('family','pack_grams','pack_count','quantity_100g')},'unit_price':round(raw['price']/q['quantity'],2),'evidence':evidence}
            if not reviewed(item,config): return reject('個別照合未確認・期限切れ')
            return item,''
        if '総合栄養食' not in t or 'ドライ' not in t or len(ages) != 1: return reject('食種・栄養区分・単一年齢未確認')
        q = parse_quantity(title, 'weight_100g')
        if not q or q['confidence'] < .9: return reject('内容量未確定')
        # Automatic title evidence is insufficient for public food approval.
        return {'name':title, 'quantity_100g':q['quantity'], 'age':next(iter(ages))}, '要メーカー照合'
    if not re.search('おもちゃ|玩具|トイ|toy|じゃらし|トンネル', t): return reject('用品違い')
    plays = {k:v for k,v in matching(t, PLAY).items() if v}
    # Two incompatible type labels often indicate selectable listings or SEO stuffing.
    if len(plays) != 1: return reject('遊びタイプ不明・混在')
    dimensions = re.search(r'(?:約)?\d+(?:\.\d+)?(?:\s*[x×*]\s*\d+(?:\.\d+)?){0,2}\s*(?:cm|mm|センチ)', t)
    if not dimensions or len(ages) > 1 or len(sizes) > 1: return reject('寸法・対象条件未確定')
    play = next(iter(plays))
    evidence += [{'attribute':'play','quote':plays[play],'source':'商品タイトル'}, {'attribute':'dimensions','quote':dimensions.group(),'source':'商品タイトル'}]
    evidence += [{'attribute':'age','quote':v,'source':'商品タイトル'} for v in ages.values()]
    evidence += [{'attribute':'size','quote':v,'source':'商品タイトル'} for v in sizes.values()]
    item = {**raw, 'product_id':product_id(title,raw.get('shop','')), 'species':config['species'], 'play':play, 'age':next(iter(ages),''), 'size':next(iter(sizes),''), 'dimensions':dimensions.group(), 'evidence':evidence}
    return item, ''

def collect(raw, config):
    items, rejected, seen = [], {}, set()
    for row in raw:
        item, reason = inspect(row, config)
        if reason: rejected[reason] = rejected.get(reason,0)+1
        if item and not reason:
            direct = parse_qs(urlparse(item['url']).query).get('pc',[''])[0]
            if direct not in seen:
                seen.add(direct); items.append(item)
    # Alphabetical, not cheapest-first or quality-ranked.
    eligible = len(items)
    if config.get('publish_products'):
        approved=[]
        for item in items:
            review=reviewed(item,config)
            if review:
                approved.append({**item,'review_warning':review['warning'],'review_label':review['label'],'reviewed_on':review['reviewed_on'],'review_source':review['source']})
        items=approved
    return {'items':sorted(items,key=lambda x:x['name'])[:12], 'research':{'fetched':len(raw),'eligible':eligible,'published_reviewed':len(items) if config.get('publish_products') else 0,'held_by_reason':rejected}, 'version':1}

def audit(payload, configs):
    errors=[]
    for key,config in configs.items():
        if key == 'version': continue
        items=payload.get(key,{}).get('items',[])
        if not config.get('publish_products') and items: errors.append(key+': publication gate violated')
        seen=set()
        for item in items:
            rebuilt,reason=inspect(item,config)
            attrs=('species','age','size','family','pack_grams','pack_count','quantity_100g','unit_price','form','nutrition','evidence') if config['kind']=='food' else ('species','play','age','size','dimensions','evidence')
            if reason or not rebuilt or any(rebuilt.get(k)!=item.get(k) for k in attrs): errors.append(key+': unsupported attributes')
            review=reviewed(item,config)
            if not review or any(item.get(k)!=review.get(v) for k,v in [('review_warning','warning'),('review_label','label'),('reviewed_on','reviewed_on'),('review_source','source')]): errors.append(key+': manual review missing or changed')
            if item.get('product_id') in seen: errors.append(key+': duplicate')
            seen.add(item.get('product_id'))
    return errors
