"""Source-owned Mogwan A8 card and optional household cost calculator.

The supplied A8 creative (anchor and impression pixel) is preserved exactly.
The simulator does not guess current prices, feeding needs or suitability.
"""
MARKER = '<!-- pet-a8-mogwan-v1 -->'
INSERT_BEFORE = '<section class="discovery-return">'
AD_CREATIVE = '''<a href="https://px.a8.net/svt/ejp?a8mat=4BGCF1+8M6WHU+3J8+1BMW42" rel="nofollow">手作りレシピを厳選食材で再現！栄養満点愛情フード『モグワン』</a>
<img border="0" width="1" height="1" src="https://www13.a8.net/0.gif?a8mat=4BGCF1+8M6WHU+3J8+1BMW42" alt="">'''

HTML = (
    MARKER
    + '<section class="pet-sponsor pet-sponsor--mogwan" id="a8-mogwan" aria-labelledby="a8-mogwan-title">'
    + '<p class="pet-sponsor-label">広告｜A8.netアフィリエイト</p>'
    + '<h2 id="a8-mogwan-title">モグワンの購入費用を、うちの子の給与量で確かめる</h2>'
    + '<p>モグワンはドッグフードの購入先候補の一つです。'
      '同じフードでも購入する袋数・送料・1日の給与量で支払総額が変わります。'
      '販売ページで最新の商品代金・内容量・送料と、パッケージの給与量表を確認して入力してください。</p>'
    + '<form id="mogwan-cost-form" class="pet-sponsor-calculator" novalidate>'
    + '<fieldset><legend>30日分に必要な購入量を計算（任意）</legend><div class="pet-sponsor-fields">'
    + '<label>1袋の内容量（g）<input name="bag_grams" type="number" inputmode="numeric" min="1" max="100000" step="1" required placeholder="販売ページの値"></label>'
    + '<label>1袋の税込価格（円）<input name="bag_price" type="number" inputmode="numeric" min="0" max="1000000" step="1" required placeholder="最新価格を入力"></label>'
    + '<label>1注文の送料（税込・円）<input name="shipping" type="number" inputmode="numeric" min="0" max="1000000" step="1" required placeholder="送料無料なら0"></label>'
    + '<label>愛犬が1日食べる量（g）<input name="daily_grams" type="number" inputmode="numeric" min="1" max="2000" step="1" required placeholder="給与量表で確認"></label>'
    + '</div><button type="submit">30日分の支払総額を計算</button></fieldset></form>'
    + '<p id="mogwan-cost-error" role="status" aria-live="polite" class="pet-sponsor-disclaimer"></p>'
    + '<div id="mogwan-cost-results" hidden aria-live="polite" class="pet-sponsor-results">'
    + '<p>30日分を一度にまとめ買いした場合：</p>'
    + '<dl><div><dt>必要な購入袋数</dt><dd data-mogwan="bags"></dd></div>'
    + '<div><dt>実際の支払総額（送料込み）</dt><dd data-mogwan="payment"></dd></div>'
    + '<div><dt>購入後に余るフード</dt><dd data-mogwan="surplus"></dd></div>'
    + '<div><dt>使った30日分の概算商品原価（送料除く）</dt><dd data-mogwan="consumed"></dd></div></dl>'
    + '<p class="pet-sponsor-disclaimer">一括注文の計算例です。定期購入やクーポン、配送周期、'
      '保管期限、実際の送料変更は含みません。適切な給与量を自動判定するものではありません。</p>'
    + '</div>'
    + '<div class="pet-sponsor-creative">' + AD_CREATIVE + '</div>'
    + '<p class="pet-sponsor-disclaimer">上記は広告です。楽天の掲載商品ランキング・価格比較結果には含めていません。'
      '購入前に原材料、アレルギー、年齢・体格に合う給与量、通常・定期購入条件を必ず確認してください。'
      '当サイトが食いつきや栄養上の適合を保証するものではありません。'
      '広告リンクから購入すると当サイトに成果報酬が発生する場合があります。</p>'
    + '</section>'
    + '<script id="a8-mogwan-behavior">'
    + 'document.addEventListener("DOMContentLoaded",()=>{'
    + 'const root=document.querySelector("#a8-mogwan"),form=root?.querySelector("#mogwan-cost-form");'
    + 'if(!form)return;'
    + 'const out=root.querySelector("#mogwan-cost-results"),error=root.querySelector("#mogwan-cost-error");'
    + 'const yen=n=>Math.round(n).toLocaleString("ja-JP")+"円";'
    + 'form.addEventListener("submit",e=>{'
    + 'e.preventDefault();out.hidden=true;'
    + 'const values=Object.fromEntries(["bag_grams","bag_price","shipping","daily_grams"].map(k=>[k,form.elements.namedItem(k).value.trim()]));'
    + 'const limits={bag_grams:[1,100000],bag_price:[0,1000000],shipping:[0,1000000],daily_grams:[1,2000]};'
    + 'const parsed={};'
    + 'for(const [key,[min,max]] of Object.entries(limits)){'
    + 'const value=Number(values[key]);'
    + 'if(values[key]===""||!Number.isSafeInteger(value)||value<min||value>max){'
    + 'error.textContent="内容量・価格・送料・1日の給与量を正しい整数で入力してください。";return;}'
    + 'parsed[key]=value;}'
    + 'const need=30*parsed.daily_grams,bags=Math.ceil(need/parsed.bag_grams);'
    + 'const cost=bags*parsed.bag_price+parsed.shipping;'
    + 'const surplus=bags*parsed.bag_grams-need;'
    + 'const consumed=need*parsed.bag_price/parsed.bag_grams;'
    + 'if(!Number.isFinite(cost)||!Number.isFinite(consumed)){error.textContent="計算できませんでした。";return;}'
    + 'root.querySelector(\'[data-mogwan="bags"]\').textContent=bags+"袋";'
    + 'root.querySelector(\'[data-mogwan="payment"]\').textContent=yen(cost);'
    + 'root.querySelector(\'[data-mogwan="surplus"]\').textContent=surplus.toLocaleString("ja-JP")+"g";'
    + 'root.querySelector(\'[data-mogwan="consumed"]\').textContent=yen(consumed);'
    + 'error.textContent="入力した条件だけを使って計算しました。購入時の実額を確認してください。";'
    + 'out.hidden=false;'
    + 'window.petCostTrack?.("mogwan_cost_planner_use",{category_id:"dog-food",program:"mogwan",quantity_result:"user_entered"});'
    + '});'
    + 'const ad=root.querySelector("a[href^=\\"https://px.a8.net/svt/ejp?\\"]");'
    + 'ad?.addEventListener("click",()=>window.petCostTrack?.("affiliate_click",{'
    + 'category_id:"dog-food",affiliate:"a8",merchant:"a8",program:"mogwan",'
    + 'conversion_source:"mogwan_sponsored_cost_planner",click_position:"dog_food_mogwan_ad"}));'
    + '});'
    + '</script>'
)


def check_mogwan_ad_integrity(body: str) -> None:
    if body.count(MARKER) != 1 or body.count(AD_CREATIVE) != 1:
        raise ValueError("Mogwan A8 marker/creative missing or duplicated")
    if body.count('href="https://px.a8.net/svt/ejp?a8mat=4BGCF1+8M6WHU+3J8+1BMW42"') != 1:
        raise ValueError("Mogwan A8 outbound link changed")
    if body.count('src="https://www13.a8.net/0.gif?a8mat=4BGCF1+8M6WHU+3J8+1BMW42"') != 1:
        raise ValueError("Mogwan A8 impression pixel changed")
    if body.count('id="a8-mogwan"') != 1 or body.count('id="mogwan-cost-form"') != 1:
        raise ValueError("Mogwan advert and cost calculator missing or duplicated")
    if body.count("広告｜A8.netアフィリエイト") < 1:
        raise ValueError("Mogwan advert label missing")


def inject_mogwan_ad(body: str) -> str:
    if MARKER in body:
        check_mogwan_ad_integrity(body)
        return body
    if body.count(INSERT_BEFORE) != 1:
        raise ValueError("unexpected dog food layout; refuse to insert Mogwan A8 advert")
    # Existing small-dog-food ad stays intact; the Mogwan card is a distinct
    # option with transparent user-entered 30-day purchase calculation.
    result = body.replace(INSERT_BEFORE, HTML + INSERT_BEFORE, 1)
    check_mogwan_ad_integrity(result)
    return result
