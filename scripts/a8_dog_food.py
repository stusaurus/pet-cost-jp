"""Source-owned, disclosed A8 small-dog-food advertisement.

Preserves the original advertiser anchor and 1x1 A8 tracking pixel unchanged.
Does not add the advertiser product to the audited Rakuten product rankings.
"""

MARKER = '<!-- pet-a8-small-dog-food-v1 -->'
INSERT_BEFORE = '<section class="discovery-return">'
AD_CREATIVE = '''<a href="https://px.a8.net/svt/ejp?a8mat=4BGCF1+8NZ7B6+4PA6+BWVTE" rel="nofollow">小型犬が食べやすい楕円形の小粒</a>

<img border="0" width="1" height="1" src="https://www14.a8.net/0.gif?a8mat=4BGCF1+8NZ7B6+4PA6+BWVTE" alt="">'''


def inject_dog_food_ad(body: str) -> str:
    """Add one self-contained sponsored card to the existing dog-food page."""
    if MARKER in body:
        return body
    if body.count(INSERT_BEFORE) != 1:
        raise ValueError("dog food page layout changed; refuse to inject ad")
    card = (
        MARKER
        + '<section class="pet-sponsor" id="a8-small-dog-food" aria-labelledby="a8-small-dog-title">'
        + '<p class="pet-sponsor-label">広告｜A8.netアフィリエイト</p>'
        + '<h2 id="a8-small-dog-title">小型犬向けフードも候補に入れたい方へ</h2>'
        + '<p>現在のフードに加えて、小粒タイプの選択肢も確認できます。'
        + 'リンク先で原材料・栄養区分・対象年齢・袋の容量・通常価格・定期購入条件・送料を確認し、'
        + 'このページの計算機で1日あたり・30日分の費用に換算してください。</p>'
        + '<div class="pet-sponsor-creative">'
        + AD_CREATIVE
        + '</div>'
        + '<p class="pet-sponsor-disclaimer">上記は広告であり、楽天の掲載商品ランキングや価格・品質の比較結果には含めていません。'
        + '年齢・体格・栄養上の適合は保証しません。療法食・アレルギーの対応は獣医師に相談してください。</p>'
        + '</section>'
        + '<script>'
        + 'document.addEventListener("DOMContentLoaded",()=>{'
        + 'const ad=document.querySelector("#a8-small-dog-food a[href^=\\"https://px.a8.net/svt/ejp?\\"]");'
        + 'if(!ad)return;ad.addEventListener("click",()=>{'
        + 'window.petCostTrack?.("affiliate_click",{'
        + 'category_id:"dog-food",affiliate:"a8",merchant:"a8",'
        + 'conversion_source:"small_dog_food_sponsored_card",'
        + 'click_position:"dog_food_ad",program:"small_dog_food_a8"});'
        + '});});'
        + '</script>'
    )
    return body.replace(INSERT_BEFORE, card + INSERT_BEFORE, 1)


def check_ad_integrity(body: str) -> None:
    """Fail closed on accidental A8 markup editing or duplicate creatives."""
    if body.count(AD_CREATIVE) != 1:
        raise ValueError("official A8 code missing or duplicated")
    if body.count(MARKER) != 1:
        raise ValueError("sponsored card missing or duplicated")
    if body.count('href="https://px.a8.net/svt/ejp?a8mat=4BGCF1+8NZ7B6+4PA6+BWVTE"') != 1:
        raise ValueError("unexpected A8 destination")
    if body.count('src="https://www14.a8.net/0.gif?a8mat=4BGCF1+8NZ7B6+4PA6+BWVTE"') != 1:
        raise ValueError("unexpected A8 impression pixel")
