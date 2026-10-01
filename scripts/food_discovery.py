"""Reviewed food families: confirm fit before comparing purchase sizes."""
import html
BASE='https://stusaurus.github.io/pet-cost-jp/'
def esc(x): return html.escape(str(x or ''),quote=True)
def image(name):
    return f'<img class="living-art" src="{BASE}assets/living/{name}.webp" width="320" height="240" alt="" loading="lazy">'

def food_choices(key,config,payload):
    pet=config['species']
    age_labels=['子犬','成犬','シニア'] if pet=='dog' else ['子猫','成猫','シニア']
    ages=''.join(f'<button type="button" class="portrait-choice" data-food-age="{a}" aria-pressed="false">{image(pet+"-"+a)}<span>{l}</span></button>' for a,l in zip(['young','adult','senior'],age_labels))
    sizes=''.join(f'<button type="button" class="portrait-choice" data-food-size="{s}" aria-pressed="false">{image("size-"+s)}<span>{l}</span></button>' for s,l in [('small','小型'),('medium','中型'),('large','大型')]) if pet=='dog' else ''
    families=[]
    for fid,f in config.get('food_families',{}).items():
        families.append(f'<div class="food-family" data-food-family-option="{fid}" data-age="{f["age"]}" data-size="{f["size"]}" hidden><p class="section-eyebrow">ドライ・総合栄養食</p><h3>{esc(f["label"])}</h3><p>{esc(f["target"])}</p><p class="condition-note">いつも使っている製品か、パッケージの対象条件を確認してください。</p><a class="text-link" href="{esc(f["manufacturer_source"])}" target="_blank" rel="noopener">メーカーの対象条件・給与量表を見る ↗</a><button type="button" class="btn secondary" data-food-family="{fid}" aria-pressed="false">このごはんを比べる</button></div>')
    cards=[]
    for i,item in enumerate(payload.get('items',[]),1):
        grams=item['quantity_100g']*100
        count=item['pack_count']; pack=item['pack_grams']/1000
        quantity=f'{pack:g}kg × {count}袋' if count>1 else f'{pack:g}kg・1袋'
        unit=item['price']/item['quantity_100g']
        cards.append(f'<article class="food-candidate" data-food-candidate data-family="{esc(item["family"])}" data-age="{item["age"]}" data-size="{item["size"]}" data-grams="{grams:g}" data-price="{item["price"]}" data-unit="{unit}" hidden><div class="food-price"><span data-food-reason>同じごはんの容量違い</span><b>¥{unit:,.1f}<small> / 100g</small></b><span>1kgあたり ¥{unit*10:,.0f}</span></div><img src="{esc(item.get("image"))}" alt="{esc(item["review_label"])}" width="80" height="80" loading="lazy"><div class="food-candidate-info"><h3>{esc(item["review_label"])}</h3><p>{quantity} · 今回の商品総額 <b>¥{item["price"]:,}</b></p><p data-food-duration>使用量を入れると、持つ期間と30日分の費用が分かります。</p><p class="condition-note">{esc(item["shop"])} · {"送料込み表示（配送先の条件は楽天で確認）" if str(item.get("postage_flag"))=="0" else "送料別・楽天で確認"}</p><details><summary>掲載根拠と商品の表示</summary><p>メーカーの年齢・食種・栄養区分と、販売ページの内容量・袋数を個別照合。確認日：{esc(item["reviewed_on"])}</p><p>{esc(item["name"])}</p><p>{esc(item["review_warning"])}</p></details><a class="btn secondary" data-affiliate-link data-category-id="{key}" data-item-id="{item["product_id"]}" data-item-name="{esc(item["name"])}" data-metric="100g" data-unit-price="{unit}" data-position="{i}" data-conversion-source="food_family" href="{esc(item["url"])}" target="_blank" rel="nofollow sponsored noopener">楽天で価格・対象条件を確認</a></div></article>')
    return f'''<section class="food-discovery">
<div class="living-step-heading"><span>01</span><h2>うちの子の年齢は？</h2></div><div class="portrait-grid">{ages}</div>
{('<p>現在の体格は？</p><div class="portrait-grid">'+sizes+'</div>') if sizes else ''}
<p class="living-status" data-food-fit-status role="status" aria-live="polite">年齢と、商品の対象条件から確認しましょう。</p>
<div class="living-step-heading"><span>02</span><h2>いつものごはんを確認</h2></div>
<p class="condition-note">確認できた銘柄だけを掲載しています。価格が低いことは、栄養や品質の優劣を意味しません。</p>
{''.join(families)}
<div data-food-results hidden>
<div class="living-step-heading"><span>03</span><h2>うちの使い方で、袋を選ぶ</h2></div>
<form data-food-usage-form novalidate><label class="food-daily-label">1日に使う量（g・任意）<input type="text" inputmode="decimal" data-food-usage aria-label="候補比較の1日量" placeholder="例：120"></label><button type="submit" class="btn secondary">持つ期間も見る</button></form>
<p class="living-status" data-food-usage-status role="status">量を入れなくても単価で比較できます。</p>
<label class="profile-save"><input type="checkbox" data-food-save>いつもの銘柄・条件・使用量をこの端末に保存</label><button type="button" class="text-button" data-food-clear>ごはんの保存条件を消す</button>
<div class="food-buying" aria-label="ごはんの買い方">{''.join(f'<button type="button" data-food-order="{value}" aria-pressed="{str(value=="unit").lower()}">{label}<small>{hint}</small></button>' for value,label,hint in [('unit','長く使って安く','100g単価の小さい順'),('price','今日は出費を抑える','商品総額の小さい順'),('amount','買い足す回数を減らす','合計量の多い順')])}</div>
<p class="food-answer" data-food-answer role="status" aria-live="polite"></p><div class="food-candidates">{''.join(cards)}</div>
<p class="condition-note">同じ銘柄の掲載候補内で比較。単価・費用は商品価格のみで、送料・ポイント・クーポンは未加算。期間は使用量による概算で、保存できる期間ではありません。</p>
</div><noscript><p>条件選択と日数の換算にはJavaScriptが必要です。メーカーの対象条件を確認してからお選びください。</p></noscript>
</section>'''
