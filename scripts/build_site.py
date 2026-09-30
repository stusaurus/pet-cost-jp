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
SITE_NAME = "ペット用品コスパ比較"


def yen(value):
    if value is None:
        return "-"
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
:root{--bg:#f5f8f6;--card:#fff;--text:#173126;--muted:#66776e;--line:#dce7e0;--accent:#197451;--accent-dark:#105c3f;--accent-soft:#e8f5ed;--cream:#fffaf0;--warn:#7b5c19;--shadow:0 10px 30px rgba(28,68,49,.07)}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Hiragino Sans","Noto Sans JP",sans-serif;background:var(--bg);color:var(--text);line-height:1.65}a{color:inherit}.wrap{width:min(1060px,calc(100% - 28px));margin:auto}
.hero{padding:34px 0 28px;background:radial-gradient(circle at 90% 10%,#dff3e7 0,transparent 35%),linear-gradient(145deg,#fff,#eef8f2);border-bottom:1px solid var(--line)}.eyebrow{display:inline-flex;align-items:center;gap:6px;padding:6px 11px;border-radius:999px;background:#fff;border:1px solid var(--line);font-size:12px;font-weight:800;color:var(--accent);box-shadow:0 3px 12px rgba(28,68,49,.04)}h1{font-size:clamp(30px,7vw,48px);line-height:1.16;letter-spacing:-.025em;margin:14px 0 10px}.lead{margin:0;max-width:760px;color:#3f564a;font-size:clamp(15px,3.8vw,18px)}.trust-row{display:flex;gap:7px;flex-wrap:wrap;margin-top:16px}.trust-pill{font-size:12px;font-weight:700;color:#496055;background:rgba(255,255,255,.85);border:1px solid var(--line);padding:6px 9px;border-radius:999px}.updated{font-size:12px;color:var(--muted);margin-top:12px}
.topnav{background:rgba(255,255,255,.96);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10;backdrop-filter:blur(10px)}.topnav .wrap{display:flex;align-items:center;gap:8px;overflow:auto;padding:9px 0}.brand{font-weight:850;text-decoration:none;white-space:nowrap;margin-right:4px}.chip{white-space:nowrap;text-decoration:none;border:1px solid var(--line);padding:7px 11px;border-radius:999px;background:#fff;font-size:13px}.chip:hover,.chip:focus-visible{border-color:#a9caba;background:var(--accent-soft)}
.main{padding:18px 0 54px}.section{background:var(--card);border:1px solid var(--line);border-radius:20px;padding:18px;margin:14px 0;box-shadow:0 4px 18px rgba(28,68,49,.035)}.section-head{display:flex;align-items:end;justify-content:space-between;gap:12px;margin-bottom:12px}.section h2{margin:0;font-size:clamp(20px,5vw,25px);letter-spacing:-.015em}.section-sub{font-size:13px;color:var(--muted);margin:3px 0 0}
.home-grid{display:grid;gap:12px}.category-card{display:grid;grid-template-columns:72px 1fr;gap:14px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:15px;text-decoration:none;box-shadow:var(--shadow);transition:transform .15s ease,border-color .15s ease}.category-card:hover{transform:translateY(-2px);border-color:#b9d6c7}.category-thumb{width:72px;height:72px;border-radius:15px;object-fit:contain;background:#f7faf8}.category-icon{width:72px;height:72px;border-radius:15px;background:var(--accent-soft);display:grid;place-items:center;font-size:34px}.card-kicker{display:block;font-size:11px;font-weight:800;color:var(--accent);margin-bottom:2px}.category-card strong{font-size:18px;line-height:1.35}.category-price{font-size:22px;font-weight:900;color:var(--accent-dark);margin-top:4px}.category-meta{color:var(--muted);font-size:12px;margin-top:2px}
.steps{display:grid;gap:9px}.step{display:grid;grid-template-columns:34px 1fr;gap:10px;align-items:start;padding:11px;border-radius:14px;background:#f8fbf9}.step-num{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;background:var(--accent);color:#fff;font-weight:900;font-size:13px}.step b{display:block}.step span{font-size:13px;color:var(--muted)}
.kpi{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}.kpi-card{background:var(--accent-soft);border-radius:14px;padding:12px}.kpi-card span{display:block;font-size:11px;color:#557064;font-weight:700}.kpi-card b{display:block;font-size:21px;line-height:1.25;margin-top:3px}
.filter-wrap{margin:4px -4px 14px;overflow:auto;padding:4px}.filters{display:flex;gap:8px;min-width:max-content}.filter-chip{appearance:none;border:1px solid var(--line);background:#fff;color:var(--text);border-radius:999px;padding:9px 12px;font:inherit;font-size:13px;font-weight:800;cursor:pointer}.filter-chip.active,.filter-chip[aria-pressed="true"]{background:var(--accent);border-color:var(--accent);color:#fff}.filter-chip:focus-visible{outline:3px solid #afd8c5;outline-offset:2px}
.featured{display:grid;grid-template-columns:86px 1fr;gap:14px;align-items:center;background:linear-gradient(145deg,#eff9f3,#fff);border:1px solid #cfe6d8;border-radius:18px;padding:14px;margin:12px 0 17px}.featured-img{width:86px;height:86px;object-fit:contain;border-radius:13px;background:#fff;border:1px solid var(--line)}.featured-badge{display:inline-flex;background:var(--accent);color:#fff;border-radius:999px;padding:4px 8px;font-size:11px;font-weight:900}.featured-title{font-weight:800;line-height:1.42;margin:6px 0 2px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.featured-shop{font-size:12px;color:var(--muted)}.featured-price{display:flex;align-items:baseline;gap:8px;flex-wrap:wrap;margin-top:5px}.featured-unit{font-size:26px;font-weight:950;color:var(--accent-dark)}.featured-total{font-size:12px;color:var(--muted)}.featured-diff{font-size:12px;font-weight:850;color:var(--accent);margin-top:3px}.featured .btn{margin-top:9px}
.table-wrap{overflow-x:auto}.compare{width:100%;border-collapse:collapse;min-width:760px}.compare th,.compare td{padding:11px 8px;border-bottom:1px solid var(--line);vertical-align:middle;text-align:left}.compare th{font-size:11px;color:var(--muted);position:sticky;top:50px;background:#fff;z-index:2}.compare tr:last-child td{border-bottom:0}.rank{font-weight:900;color:var(--accent);text-align:center!important;white-space:nowrap}.rank-badge{display:none}.product-image{width:64px;height:64px;object-fit:contain;border-radius:10px;border:1px solid var(--line);background:#fff}.product{min-width:260px}.product-title{font-weight:750;line-height:1.4;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.meta{font-size:11px;color:var(--muted);margin-top:4px}.condition-tag{display:inline-flex;align-items:center;background:#f0f5f2;color:#496055;border-radius:999px;padding:3px 7px;font-size:10px;font-weight:800;margin-right:4px}.total{white-space:nowrap;font-weight:700}.unit{font-weight:900;font-size:18px;white-space:nowrap;color:var(--accent-dark)}.unit .meta{font-weight:500}.price-diff{font-size:10px;font-weight:750;color:var(--muted);margin-top:2px}.btn{display:inline-flex;justify-content:center;align-items:center;text-decoration:none;background:var(--accent);color:#fff;padding:10px 13px;border-radius:11px;font-weight:850;font-size:13px;white-space:nowrap;border:0;cursor:pointer}.btn:hover{background:var(--accent-dark)}.btn.secondary{background:var(--text)}.shipping{font-size:10px;color:var(--muted);margin-top:4px}
.guide-grid{display:grid;gap:8px}.guide-item{display:flex;gap:9px;align-items:flex-start;padding:10px 11px;background:#f8fbf9;border-radius:12px;font-size:13px}.guide-check{color:var(--accent);font-weight:900}.calculator{display:grid;gap:8px}.calc-inputs{display:grid;grid-template-columns:1fr 1fr;gap:8px}.input{width:100%;padding:12px;border:1px solid var(--line);border-radius:12px;background:#fff;font-size:16px;color:var(--text)}.input:focus{outline:3px solid #d3eadf;border-color:#9fc8b4}.note{background:var(--cream);border:1px solid #f0dfb8;border-radius:12px;padding:12px;font-size:13px;color:#66542a}.method{font-size:14px;color:#485d51}.method-list{margin:8px 0 0;padding-left:20px}.faq{border-top:1px solid var(--line)}.faq details{border-bottom:1px solid var(--line);padding:11px 0}.faq summary{cursor:pointer;font-weight:800}.faq p{margin:7px 0 0;color:#53665c;font-size:13px}
.footer{padding:6px 0 42px;color:var(--muted);font-size:12px}.footer-box{border-top:1px solid var(--line);padding-top:20px}.footer a{color:#395c4a}.rakuten-credit{margin-top:10px}.empty{padding:20px;text-align:center;color:var(--muted)}
@media(min-width:720px){.home-grid{grid-template-columns:repeat(3,1fr)}.category-card{grid-template-columns:1fr}.category-thumb,.category-icon{width:100%;height:130px}.kpi{grid-template-columns:repeat(4,1fr)}.steps{grid-template-columns:repeat(3,1fr)}.featured{grid-template-columns:120px 1fr auto}.featured-img{width:120px;height:120px}.featured .btn{margin-top:0}.guide-grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:719px){.brand{display:none}.section{padding:15px;border-radius:17px}.table-wrap{overflow:visible}.compare{min-width:0;display:block}.compare thead{display:none}.compare tbody{display:grid;gap:11px}.compare tr{display:grid;grid-template-columns:66px minmax(0,1fr);gap:5px 11px;background:#fff;border:1px solid var(--line);border-radius:16px;padding:12px;box-shadow:0 5px 18px rgba(28,68,49,.04)}.compare td{display:block;border:0;padding:0}.compare .rank{grid-column:1;grid-row:1;text-align:left!important}.rank-badge{display:inline-flex;background:var(--accent-soft);color:var(--accent-dark);border-radius:999px;padding:4px 8px;font-size:11px}.rank-number{display:none}.compare .image-cell{grid-column:1;grid-row:2/5}.product-image{width:66px;height:66px}.compare .product{grid-column:2;grid-row:1/3;min-width:0}.compare .total{grid-column:2;grid-row:3;font-size:12px;color:var(--muted)}.compare .unit{grid-column:2;grid-row:4}.compare .action{grid-column:1/-1;grid-row:5;margin-top:5px}.compare .action .btn{width:100%;padding:12px}.shipping{text-align:center}.featured{grid-template-columns:74px 1fr}.featured-img{width:74px;height:74px}.featured .featured-action{grid-column:1/-1}.featured .btn{width:100%}.calc-inputs{grid-template-columns:1fr}.category-card{grid-template-columns:62px 1fr}.category-thumb,.category-icon{width:62px;height:62px}.category-icon{font-size:29px}}
'''

CSS += r'''
/* Visual identity v3 */
body{background:#f4f7f2;background-image:radial-gradient(circle at 12% 8%,rgba(255,206,102,.10) 0 90px,transparent 91px),radial-gradient(circle at 88% 18%,rgba(82,174,145,.09) 0 120px,transparent 121px)}
.hero{position:relative;overflow:hidden;padding:34px 0 30px;background:linear-gradient(135deg,#f7fff9 0%,#eef9f3 44%,#fff8e8 100%)}
.hero:before,.hero:after{content:"";position:absolute;border-radius:50%;pointer-events:none}.hero:before{width:260px;height:260px;right:-90px;top:-120px;background:rgba(255,211,110,.18)}.hero:after{width:180px;height:180px;left:-80px;bottom:-110px;background:rgba(61,160,125,.10)}
.hero-inner{position:relative;z-index:1;display:grid;gap:22px;align-items:center}.hero-copy{min-width:0}.hero-art-shell{position:relative;min-height:250px;border-radius:28px;background:linear-gradient(145deg,#ffffff 0%,#f8fff9 52%,#fff5d9 100%);border:1px solid rgba(44,111,82,.13);box-shadow:0 20px 50px rgba(28,68,49,.10);overflow:hidden;padding:10px}.hero-art-shell:before{content:"";position:absolute;inset:auto -30px -50px auto;width:170px;height:170px;border-radius:50%;background:rgba(255,201,74,.16)}.hero-art{display:block;width:100%;height:100%;min-height:230px}
.hero-copy h1{max-width:650px}.hero-kicker{display:inline-flex;gap:7px;align-items:center;background:#173126;color:#fff;border-radius:999px;padding:6px 11px;font-size:11px;font-weight:850;letter-spacing:.02em}.hero-kicker .dot{width:7px;height:7px;border-radius:50%;background:#ffd66e;box-shadow:0 0 0 4px rgba(255,214,110,.16)}
.visual-section{background:transparent;border:0;box-shadow:none;padding:4px 0 8px}.visual-section .section-head{padding:0 2px 2px}
.home-grid{gap:14px}.category-card{position:relative;overflow:hidden;border:0;min-height:220px;padding:0;grid-template-columns:1fr;align-content:start;box-shadow:0 16px 36px rgba(31,65,49,.09);transition:transform .2s ease,box-shadow .2s ease}.category-card:hover{transform:translateY(-4px);box-shadow:0 20px 44px rgba(31,65,49,.14)}.category-card.theme-sheet{background:linear-gradient(145deg,#dff6e9,#f6fffa)}.category-card.theme-litter{background:linear-gradient(145deg,#fff0cc,#fffaf0)}.category-card.theme-system{background:linear-gradient(145deg,#dff4f7,#f3fbfd)}.category-card:after{content:"";position:absolute;width:120px;height:120px;border-radius:50%;right:-35px;top:-42px;background:rgba(255,255,255,.46)}.category-visual{height:126px;padding:11px 14px 0;position:relative;z-index:1}.category-visual svg{width:100%;height:100%;display:block}.category-card-copy{padding:4px 16px 17px;position:relative;z-index:1}.category-card strong{font-size:19px}.category-price{font-size:27px;letter-spacing:-.02em}.category-price small{font-size:12px;font-weight:750}.category-arrow{position:absolute;right:15px;bottom:15px;width:34px;height:34px;border-radius:50%;display:grid;place-items:center;background:rgba(23,49,38,.90);color:#fff;font-weight:900}
.price-ribbon{display:inline-flex;align-items:center;gap:5px;border-radius:999px;padding:5px 9px;font-size:11px;font-weight:900;background:#fff;color:#b06a00;box-shadow:0 5px 14px rgba(128,88,10,.08)}
.steps{gap:12px}.step{position:relative;overflow:hidden;background:#fff;border:1px solid var(--line);padding:14px;border-radius:18px;box-shadow:0 8px 24px rgba(28,68,49,.045)}.step-illu{width:72px;height:56px;margin:-3px 0 6px}.step-illu svg{width:100%;height:100%}.step-num{position:absolute;right:11px;top:11px;background:#173126}
.featured{position:relative;overflow:hidden;background:linear-gradient(135deg,#f2fff6 0%,#ffffff 64%,#fff5cf 100%);border:1px solid #c9e5d5;box-shadow:0 16px 34px rgba(28,68,49,.07);padding-top:18px}.featured:before{content:"BEST";position:absolute;right:-23px;top:13px;transform:rotate(38deg);background:#ffd76f;color:#745100;font-size:10px;font-weight:950;padding:5px 29px;letter-spacing:.08em}.featured-crown{display:inline-grid;place-items:center;width:28px;height:28px;border-radius:10px;background:#ffd76f;margin-right:6px;vertical-align:middle;box-shadow:0 4px 12px rgba(160,112,0,.14)}.featured-badge{background:#173126}.featured-unit{font-size:30px}.featured-diff{display:inline-flex;margin-top:6px;border-radius:999px;padding:4px 8px;background:#e8f5ed;color:#126142}
.category-hero .hero-art-shell{min-height:210px}.category-hero .hero-art{min-height:190px}.category-hero h1{font-size:clamp(30px,7vw,46px)}
@media(min-width:760px){.hero-inner{grid-template-columns:minmax(0,1.05fr) minmax(330px,.75fr);gap:32px}.hero-art-shell{min-height:315px}.hero-art{min-height:295px}.category-hero .hero-art-shell{min-height:250px}.category-hero .hero-art{min-height:230px}.category-card{min-height:300px}.category-visual{height:165px}}
@media(max-width:759px){.hero{padding-top:24px}.hero-inner{grid-template-columns:1fr}.hero-art-shell{min-height:220px;margin-top:3px}.hero-art{min-height:200px}.category-hero .hero-art-shell{min-height:185px}.category-hero .hero-art{min-height:165px}.category-card{min-height:206px}.category-visual{height:112px}.home-grid{grid-template-columns:1fr}.category-card-copy{padding-top:0}}
'''


def hero_illustration():
    return f'''<div class="hero-photo-wrap">
      <img class="hero-photo" src="{BASE_URL}assets/hero-pet-comparison.webp"
        alt="犬と猫、ペットシーツ・猫砂・システムトイレ用品を天秤で比較するイメージ"
        width="480" height="320" fetchpriority="high">
      <div class="hero-photo-label"><span>PRICE CHECK</span><b>同じ単位で比較</b></div>
    </div>'''


def category_illustration(category_id):
    if category_id == "pet-sheets":
        return '''<svg viewBox="0 0 300 160" role="img" aria-label="ペットシーツのイラスト">
          <ellipse cx="150" cy="143" rx="112" ry="9" fill="#8dbca1" opacity=".22"/>
          <path d="M36 121c21-29 45-39 75-31 19 5 29 17 47 20 31 5 54-10 104-24v44H36z" fill="#cfeedd"/>
          <g transform="translate(36 41)"><rect x="0" y="31" width="88" height="61" rx="14" fill="#fff" stroke="#75b997" stroke-width="3"/><path d="M12 49h64M12 64h46" stroke="#d8eee2" stroke-width="7" stroke-linecap="round"/><rect x="58" y="9" width="54" height="36" rx="10" fill="#2d7f5d"/><path d="M68 20h34M68 30h24" stroke="#d9f1e4" stroke-width="5" stroke-linecap="round"/></g>
          <g transform="translate(144 12)"><circle cx="50" cy="45" r="38" fill="#e7ab75"/><path d="M20 23 7 3l33 14M80 22 94 2 61 16" fill="#b8754a"/><ellipse cx="50" cy="55" rx="23" ry="18" fill="#f7d0a4"/><circle cx="37" cy="41" r="4.5" fill="#173126"/><circle cx="64" cy="41" r="4.5" fill="#173126"/><ellipse cx="50" cy="52" rx="5" ry="4" fill="#173126"/><path d="M42 62q8 7 16 0" fill="none" stroke="#173126" stroke-width="2.7" stroke-linecap="round"/></g>
          <g transform="translate(202 86) rotate(-4)"><path d="M0 0h64l12 16-12 16H0z" fill="#ffd66e"/><circle cx="63" cy="16" r="3" fill="#fff4d0"/><text x="9" y="13" class="scene-label" font-family="sans-serif" fill="#6b4c00">PRICE</text><text x="9" y="26" class="scene-price" font-family="sans-serif" fill="#6b4c00">1枚</text></g>
        </svg>'''
    if category_id == "cat-litter":
        return '''<svg viewBox="0 0 300 160" role="img" aria-label="猫砂のイラスト">
          <ellipse cx="151" cy="143" rx="111" ry="9" fill="#c4aa70" opacity=".25"/>
          <path d="M45 78q0-20 20-20h143q20 0 20 20v47H45z" fill="#fff" stroke="#d4b773" stroke-width="3"/><path d="M59 84h155l-11 35H70z" fill="#ead6a6"/>
          <g fill="#c3a35a"><circle cx="88" cy="99" r="4"/><circle cx="111" cy="110" r="4"/><circle cx="137" cy="96" r="4"/><circle cx="163" cy="109" r="4"/><circle cx="191" cy="98" r="4"/></g>
          <g transform="translate(111 6)"><circle cx="42" cy="42" r="36" fill="#9fb9bf"/><path d="M14 22 18 0l22 16M70 22 67 0 45 16" fill="#708e97"/><circle cx="30" cy="39" r="4.3" fill="#173126"/><circle cx="55" cy="39" r="4.3" fill="#173126"/><path d="m42 48-5 4h10z" fill="#e59a95"/><path d="M33 58q9 6 18 0" fill="none" stroke="#173126" stroke-width="2.4" stroke-linecap="round"/></g>
          <g transform="translate(220 31)"><rect width="57" height="45" rx="12" fill="#fff0c8" stroke="#e1bd66"/><text x="10" y="16" class="scene-label" font-family="sans-serif" fill="#806018">COMPARE</text><text x="13" y="34" class="scene-price" font-family="sans-serif" fill="#806018">1L</text></g>
          <path d="M29 112c9-9 14-21 15-34M31 110c-10-5-16-11-19-20M30 105c13-4 20-10 26-18" stroke="#8aaf6d" stroke-width="5" stroke-linecap="round"/>
        </svg>'''
    return '''<svg viewBox="0 0 300 160" role="img" aria-label="システムトイレシートのイラスト">
      <ellipse cx="150" cy="143" rx="111" ry="9" fill="#78b8c2" opacity=".24"/>
      <rect x="44" y="80" width="173" height="52" rx="17" fill="#fff" stroke="#78bcc7" stroke-width="3"/><rect x="58" y="94" width="145" height="24" rx="8" fill="#ddf1f4"/><path d="M75 106h112" stroke="#9ad1d8" stroke-width="5" stroke-linecap="round"/>
      <g transform="translate(107 7)"><circle cx="43" cy="42" r="36" fill="#9bb7be"/><path d="M15 22 18 0l22 16M71 22 68 0 46 16" fill="#6f8e96"/><circle cx="31" cy="39" r="4.3" fill="#173126"/><circle cx="56" cy="39" r="4.3" fill="#173126"/><path d="m43 48-5 4h10z" fill="#e59a95"/><path d="M34 58q9 6 18 0" fill="none" stroke="#173126" stroke-width="2.4" stroke-linecap="round"/></g>
      <g transform="translate(213 38)"><circle cx="29" cy="29" r="28" fill="#4da9b6"/><path d="m16 30 9 9 18-21" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>
      <g transform="translate(216 100)"><path d="M0 0h61l10 14-10 14H0z" fill="#ffd66e"/><text x="8" y="18" class="scene-label" font-family="sans-serif" fill="#6b4c00">FIT CHECK</text></g>
    </svg>'''

def category_theme(category_id):
    return {"pet-sheets": "theme-sheet", "cat-litter": "theme-litter", "system-toilet-sheets": "theme-system"}.get(category_id, "theme-sheet")


def step_illustration(kind):
    if kind == 1:
        return '''<div class="step-illu"><svg viewBox="0 0 100 70"><rect x="9" y="11" width="30" height="45" rx="8" fill="#dff3e7"/><rect x="35" y="19" width="26" height="37" rx="7" fill="#ffe7ad"/><rect x="58" y="8" width="32" height="48" rx="8" fill="#dff2f5"/><circle cx="24" cy="34" r="7" fill="#237a57"/><circle cx="48" cy="37" r="6" fill="#d59b35"/><circle cx="74" cy="32" r="7" fill="#56aeb8"/></svg></div>'''
    if kind == 2:
        return '''<div class="step-illu"><svg viewBox="0 0 100 70"><rect x="12" y="15" width="76" height="42" rx="11" fill="#fff" stroke="#cfe2d7" stroke-width="3"/><path d="M28 27h45M28 37h34M28 47h51" stroke="#237a57" stroke-width="5" stroke-linecap="round"/><circle cx="18" cy="27" r="4" fill="#ffd064"/><circle cx="18" cy="37" r="4" fill="#ffd064"/><circle cx="18" cy="47" r="4" fill="#ffd064"/></svg></div>'''
    return '''<div class="step-illu"><svg viewBox="0 0 100 70"><rect x="12" y="18" width="76" height="38" rx="10" fill="#173126"/><path d="M29 44V34M45 44V27M61 44V22M77 44V16" stroke="#74caa5" stroke-width="7" stroke-linecap="round"/><circle cx="20" cy="22" r="12" fill="#ffd064"/><path d="M16 22h8M20 18v8" stroke="#725400" stroke-width="3" stroke-linecap="round"/></svg></div>'''

CSS += r'''
/* Visual identity v4 */
.photo-shell{padding:0;background:#fff;border-color:#eadfca;box-shadow:0 22px 56px rgba(54,73,61,.14)}
.photo-shell:before{display:none}
.hero-photo-wrap{position:relative;height:100%;min-height:250px;display:grid;place-items:center;overflow:hidden;border-radius:27px;background:#fff}
.hero-photo{display:block;width:100%;height:100%;min-height:250px;object-fit:cover;object-position:center}
.hero-photo-label{position:absolute;left:15px;bottom:14px;display:flex;align-items:center;gap:8px;background:rgba(23,49,38,.92);color:#fff;border:1px solid rgba(255,255,255,.18);border-radius:999px;padding:7px 11px;box-shadow:0 7px 20px rgba(23,49,38,.18);backdrop-filter:blur(8px)}
.hero-photo-label span{font-size:9px;font-weight:900;letter-spacing:.12em;color:#ffd978}.hero-photo-label b{font-size:12px}
.story-section{position:relative;overflow:hidden;background:linear-gradient(135deg,#fff8e7,#fff 60%);border-color:#f0dfba}.story-section:after{content:"";position:absolute;width:140px;height:140px;border-radius:50%;right:-65px;bottom:-72px;background:rgba(255,207,98,.15);pointer-events:none}
.trust-section{position:relative;overflow:hidden;background:linear-gradient(135deg,#edf9f2,#fff 64%);border-color:#d6ebdf}.trust-section:after{content:"";position:absolute;right:16px;top:14px;width:70px;height:70px;opacity:.09;background:radial-gradient(circle at 25% 25%,#237a57 0 8px,transparent 9px),radial-gradient(circle at 75% 25%,#237a57 0 8px,transparent 9px),radial-gradient(circle at 50% 72%,#237a57 0 18px,transparent 19px)}
.store-section{background:linear-gradient(135deg,#eef8fb,#fff 62%);border-color:#d7ebef}
.visual-section .section-sub{max-width:620px}
.category-card-copy strong{display:block;margin-top:9px}
@media(min-width:760px){.photo-shell,.hero-photo-wrap,.hero-photo{min-height:330px}.hero-photo{object-fit:cover}.story-section,.trust-section,.store-section{padding:24px}}
@media(max-width:759px){.photo-shell,.hero-photo-wrap,.hero-photo{min-height:220px}.hero-photo{object-fit:cover}.hero-photo-label{left:10px;bottom:10px;padding:6px 9px}.hero-photo-label b{font-size:11px}}
'''

CSS += r'''
/* Comparison snapshot v5 */
.snapshot-section{background:linear-gradient(135deg,#173126 0%,#214c39 58%,#2d6b4f 100%);color:#fff;border:0;box-shadow:0 18px 42px rgba(23,49,38,.16);overflow:hidden;position:relative}
.snapshot-section:before{content:"";position:absolute;width:210px;height:210px;border-radius:50%;right:-90px;top:-110px;background:rgba(255,215,111,.10)}
.snapshot-section .section-sub{color:rgba(255,255,255,.72)}.snapshot-section h2{color:#fff}
.deal-meter{position:relative;z-index:1;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.13);border-radius:16px;padding:14px;margin-bottom:13px;backdrop-filter:blur(6px)}
.deal-meter-head{display:flex;justify-content:space-between;gap:12px;align-items:center}.deal-meter-head span{font-size:12px;color:rgba(255,255,255,.74);font-weight:750}.deal-meter-head b{font-size:15px;color:#ffe08a;text-align:right}
.deal-track{height:12px;border-radius:999px;background:linear-gradient(90deg,#6dd0a4 0%,#dbe8df 50%,#ffc978 100%);position:relative;margin:13px 0 5px;box-shadow:inset 0 1px 2px rgba(0,0,0,.16)}
.deal-dot{position:absolute;top:50%;width:22px;height:22px;border-radius:50%;background:#fff;border:5px solid #ffd76f;box-shadow:0 4px 12px rgba(0,0,0,.22);transform:translate(-50%,-50%);left:50%;transition:left .22s ease}
.deal-scale{display:flex;justify-content:space-between;font-size:10px;color:rgba(255,255,255,.65)}
.top3-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px;position:relative;z-index:1}.top3-card{display:flex;gap:10px;align-items:center;min-width:0;background:#fff;color:var(--text);border-radius:16px;padding:10px;text-decoration:none;box-shadow:0 9px 22px rgba(0,0,0,.12);transition:transform .16s ease}.top3-card:hover{transform:translateY(-2px)}
.top3-rank{width:28px;height:28px;flex:0 0 28px;border-radius:9px;display:grid;place-items:center;background:#173126;color:#fff;font-weight:950;font-size:12px}.top3-card:first-child .top3-rank{background:#ffd76f;color:#694d00}
.top3-img{width:50px;height:50px;flex:0 0 50px;border-radius:10px;object-fit:contain;background:#fff;border:1px solid var(--line)}.top3-copy{min-width:0}.top3-name{font-size:11px;font-weight:800;line-height:1.35;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.top3-unit{font-size:18px;font-weight:950;color:var(--accent-dark);line-height:1.2}.top3-total{font-size:10px;color:var(--muted)}
.snapshot-note{position:relative;z-index:1;margin-top:10px;font-size:11px;color:rgba(255,255,255,.66)}
@media(max-width:759px){.snapshot-section{padding:15px}.top3-strip{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;padding:1px 1px 5px}.top3-card{min-width:82%;scroll-snap-align:start}.deal-meter-head{align-items:flex-start;flex-direction:column;gap:3px}.deal-meter-head b{text-align:left}}
'''

CSS += r'''
/* Objective comparison angles v6 */
.angle-panel{margin:14px 0 16px;padding:15px;border-radius:18px;background:linear-gradient(135deg,#fffaf0,#fff 60%);border:1px solid #f0dfbd}
.angle-head{display:flex;justify-content:space-between;gap:12px;align-items:end;margin-bottom:10px}.angle-head h3{margin:0;font-size:17px}.angle-head p{margin:2px 0 0;font-size:11px;color:var(--muted)}
.angle-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}
.angle-card{position:relative;overflow:hidden;display:flex;flex-direction:column;min-height:158px;padding:13px;border-radius:15px;background:#fff;border:1px solid var(--line);text-decoration:none;box-shadow:0 7px 20px rgba(28,68,49,.045);transition:transform .16s ease,border-color .16s ease}.angle-card:hover{transform:translateY(-2px);border-color:#b9d6c7}
.angle-icon{width:38px;height:38px;border-radius:12px;display:grid;place-items:center;font-size:21px;margin-bottom:8px}.angle-card[data-angle-role="unit"] .angle-icon{background:#e5f5eb}.angle-card[data-angle-role="total"] .angle-icon{background:#fff0ca}.angle-card[data-angle-role="bulk"] .angle-icon{background:#e4f3f7}
.angle-label{font-size:11px;font-weight:900;color:#5a6b62}.angle-value{font-size:22px;font-weight:950;color:var(--accent-dark);line-height:1.15;margin-top:2px}.angle-name{font-size:11px;line-height:1.35;color:#53665c;margin-top:6px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.angle-cta{margin-top:auto;padding-top:8px;font-size:11px;font-weight:850;color:var(--accent)}
.angle-note{font-size:10px;color:var(--muted);margin-top:8px}
@media(max-width:759px){.angle-grid{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:4px}.angle-card{min-width:74%;scroll-snap-align:start}.angle-head{align-items:flex-start;flex-direction:column;gap:2px}}
'''

CSS += r'''
/* Brand system v7 */
body{--theme:#197451;--theme-dark:#105c3f;--theme-soft:#e8f5ed;--theme-wash:#f2faf5}
body[data-category-id="pet-sheets"]{--theme:#27845f;--theme-dark:#176548;--theme-soft:#dff6e9;--theme-wash:#f3fbf6}
body[data-category-id="cat-litter"]{--theme:#ad7b27;--theme-dark:#805817;--theme-soft:#fff0cc;--theme-wash:#fffaf0}
body[data-category-id="system-toilet-sheets"]{--theme:#438f9c;--theme-dark:#286d78;--theme-soft:#dff4f7;--theme-wash:#f2fafc}
body[data-category-id] .hero.category-hero{background:radial-gradient(circle at 88% 12%,var(--theme-soft) 0,transparent 34%),linear-gradient(145deg,#fff,var(--theme-wash))}
body[data-category-id] .hero-kicker{background:var(--theme-dark)}
body[data-category-id] .filter-chip.active,body[data-category-id] .filter-chip[aria-pressed="true"]{background:var(--theme);border-color:var(--theme)}
body[data-category-id] .btn{background:var(--theme)}body[data-category-id] .btn:hover{background:var(--theme-dark)}
body[data-category-id] .unit,body[data-category-id] .featured-unit,body[data-category-id] .top3-unit,body[data-category-id] .angle-value{color:var(--theme-dark)}
body[data-category-id] .featured-diff{background:var(--theme-soft);color:var(--theme-dark)}
body[data-category-id] .kpi-card{background:var(--theme-soft)}
body[data-category-id] .condition-tag{background:var(--theme-soft);color:var(--theme-dark)}
body[data-category-id] .rank{color:var(--theme)}
body[data-category-id] .rank-badge{background:var(--theme-soft);color:var(--theme-dark)}
.brand{display:flex;align-items:center;gap:8px}.brand-mark{width:29px;height:29px;border-radius:10px;background:#173126;display:grid;place-items:center;box-shadow:0 5px 13px rgba(23,49,38,.14);position:relative;flex:0 0 29px}.brand-mark:before{content:"";width:14px;height:11px;border-radius:50% 50% 45% 45%;background:#ffd76f;transform:translateY(3px)}.brand-mark:after{content:"";position:absolute;top:5px;left:6px;width:5px;height:5px;border-radius:50%;background:#ffd76f;box-shadow:7px -1px 0 #ffd76f,3.5px -4px 0 -1px #ffd76f}
.brand-name{font-weight:950;letter-spacing:-.03em}.brand-name small{display:block;font-size:8px;letter-spacing:.08em;color:var(--muted);line-height:1;margin-top:1px}
.chip{transition:background .16s ease,border-color .16s ease,transform .16s ease}.chip:hover{transform:translateY(-1px)}.chip.current{background:#173126;border-color:#173126;color:#fff;box-shadow:0 5px 14px rgba(23,49,38,.12)}
.section-head h2{display:flex;align-items:center;gap:9px}.section-head h2:before{content:"";width:24px;height:24px;flex:0 0 24px;border-radius:9px;background:
radial-gradient(circle at 50% 65%,var(--theme) 0 5px,transparent 5.8px),
radial-gradient(circle at 24% 31%,var(--theme) 0 3px,transparent 3.8px),
radial-gradient(circle at 48% 20%,var(--theme) 0 3px,transparent 3.8px),
radial-gradient(circle at 73% 31%,var(--theme) 0 3px,transparent 3.8px),
var(--theme-soft);opacity:.95}
.visual-section .section-head h2:before{background:
radial-gradient(circle at 50% 65%,#197451 0 5px,transparent 5.8px),
radial-gradient(circle at 24% 31%,#197451 0 3px,transparent 3.8px),
radial-gradient(circle at 48% 20%,#197451 0 3px,transparent 3.8px),
radial-gradient(circle at 73% 31%,#197451 0 3px,transparent 3.8px),
#e8f5ed}
.section{position:relative}.section:not(.snapshot-section):not(.visual-section){overflow:hidden}.section:not(.snapshot-section):not(.visual-section):after{content:"";position:absolute;right:-38px;bottom:-44px;width:100px;height:100px;border-radius:50%;background:var(--theme-soft);opacity:.22;pointer-events:none}
.top3-strip{align-items:stretch}.top3-card:first-child{transform:translateY(-5px);border:2px solid #f0c75d;box-shadow:0 14px 28px rgba(0,0,0,.16)}.top3-card:first-child:hover{transform:translateY(-7px)}.top3-card:first-child .top3-rank:after{content:"♛";position:absolute;transform:translate(12px,-13px);font-size:13px;color:#ffca4b;text-shadow:0 1px 0 #6d5200}.top3-rank{position:relative}
.featured{border-left:5px solid var(--theme)}.featured:after{content:"";position:absolute;width:90px;height:90px;border-radius:50%;left:-42px;bottom:-48px;background:var(--theme-soft);opacity:.5}
.angle-card{border-top:4px solid transparent}.angle-card[data-angle-role="unit"]{border-top-color:#55ad83}.angle-card[data-angle-role="total"]{border-top-color:#e2b94f}.angle-card[data-angle-role="bulk"]{border-top-color:#69adba}
.footer{position:relative;padding-top:18px}.footer-brand{display:flex;align-items:center;gap:11px;margin-bottom:13px}.footer-brand .brand-mark{width:36px;height:36px;flex-basis:36px}.footer-brand strong{display:block;font-size:14px;color:var(--text)}.footer-brand span{font-size:11px;color:var(--muted)}
.mobile-dock{display:none}
@media(max-width:719px){
  body{padding-bottom:72px}.topnav .wrap{padding:8px 0}.chip{font-size:12px;padding:7px 9px}
  .mobile-dock{display:grid;grid-template-columns:repeat(4,1fr);position:fixed;z-index:30;left:10px;right:10px;bottom:max(8px,env(safe-area-inset-bottom));background:rgba(255,255,255,.94);border:1px solid rgba(205,222,212,.9);border-radius:18px;box-shadow:0 12px 34px rgba(23,49,38,.18);backdrop-filter:blur(14px);padding:6px}
  .dock-link{display:flex;flex-direction:column;align-items:center;justify-content:center;text-decoration:none;min-height:49px;border-radius:12px;font-size:9px;font-weight:850;color:#66776e;line-height:1.15;gap:2px}.dock-link .dock-icon{font-size:18px;line-height:1}.dock-link.current{background:var(--theme-soft);color:var(--theme-dark)}
  .top3-card:first-child{transform:none}.top3-card:first-child:hover{transform:none}
}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important;transition:none!important}}
'''

CSS += r'''
/* Product cards v8 */
.product-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:13px}
.shop-card{position:relative;display:grid;grid-template-columns:92px minmax(0,1fr);grid-template-areas:"image head" "image price" "meta meta" "action action";gap:8px 12px;background:#fff;border:1px solid var(--line);border-radius:19px;padding:13px;box-shadow:0 8px 24px rgba(28,68,49,.055);overflow:hidden;transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}
.shop-card:hover{transform:translateY(-2px);box-shadow:0 14px 30px rgba(28,68,49,.10);border-color:#bdd6c8}.shop-card[hidden]{display:none!important}
.shop-card.is-rank-1{border:2px solid #eac45a;background:linear-gradient(145deg,#fffdf5,#fff 48%)}.shop-card.is-rank-2{border-color:#cfd8d3}.shop-card.is-rank-3{border-color:#dfc6ae}
.shop-card.is-rank-1:before{content:"BEST";position:absolute;right:-23px;top:12px;transform:rotate(40deg);background:#ffd76f;color:#6b4d00;font-size:9px;font-weight:950;padding:4px 29px;letter-spacing:.08em}
.shop-card-image-wrap{grid-area:image;position:relative;align-self:start}.shop-card-image{width:92px;height:92px;object-fit:contain;border-radius:14px;background:#fff;border:1px solid var(--line)}
.shop-card-rank{position:absolute;left:-5px;top:-5px;min-width:31px;height:31px;padding:0 7px;border-radius:10px;display:grid;place-items:center;background:#173126;color:#fff;font-size:12px;font-weight:950;box-shadow:0 5px 12px rgba(23,49,38,.19)}.shop-card.is-rank-1 .shop-card-rank{background:#ffd76f;color:#684c00}
.shop-card-head{grid-area:head;min-width:0}.shop-card-tags{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:5px}.shop-card-title{font-size:13px;font-weight:850;line-height:1.38;display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}.shop-card-shop{font-size:10px;color:var(--muted);margin-top:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.shop-card-prices{grid-area:price;display:flex;align-items:end;justify-content:space-between;gap:9px}.shop-unit-wrap{min-width:0}.shop-unit-label{font-size:10px;font-weight:800;color:var(--muted)}.shop-unit{font-size:25px;font-weight:950;line-height:1;color:var(--theme-dark)}.shop-unit small{font-size:10px;font-weight:750;color:var(--muted)}.shop-total{text-align:right}.shop-total span{display:block;font-size:9px;color:var(--muted)}.shop-total b{font-size:14px}
.shop-card-meta{grid-area:meta;display:flex;justify-content:space-between;align-items:center;gap:8px;border-top:1px dashed var(--line);padding-top:8px}.shop-card-meta .price-diff{font-size:11px;color:var(--theme-dark);font-weight:850}.shop-card-meta .shipping{margin:0}
.shop-card-action{grid-area:action}.shop-card-action .btn{width:100%;padding:11px 13px;border-radius:12px}.shop-card-action .btn:after{content:"↗";margin-left:5px;font-size:12px}
.product-empty{grid-column:1/-1;padding:28px;text-align:center;color:var(--muted);background:#f8fbf9;border-radius:16px}
@media(max-width:759px){.product-grid{grid-template-columns:1fr}.shop-card{grid-template-columns:82px minmax(0,1fr);padding:12px}.shop-card-image{width:82px;height:82px}.shop-unit{font-size:23px}.shop-card-title{font-size:13px}}
'''

CSS += r'''
/* Visual polish v9 */
.brand-logo{display:block;width:214px;height:auto;max-width:44vw}.footer-logo{display:block;width:230px;height:auto;max-width:72vw}
.brand{padding:2px 0}.brand-name,.brand>.brand-mark{display:none}
.topnav{box-shadow:0 8px 26px rgba(23,49,38,.045)}
.category-visual{filter:drop-shadow(0 10px 16px rgba(37,70,53,.08))}
.category-card{isolation:isolate}.category-card:before{content:"";position:absolute;inset:0;background:linear-gradient(125deg,rgba(255,255,255,.38),transparent 43%);pointer-events:none;z-index:0}
.category-card:hover .category-visual{transform:translateY(-3px) scale(1.015)}.category-visual{transition:transform .22s ease}
.shop-card{box-shadow:0 9px 24px rgba(28,68,49,.06),0 1px 0 rgba(255,255,255,.9) inset}.shop-card:hover{box-shadow:0 18px 38px rgba(28,68,49,.12),0 1px 0 rgba(255,255,255,.9) inset}
.shop-card-image-wrap:after{content:"";position:absolute;inset:auto 9px -8px 9px;height:10px;border-radius:50%;background:rgba(23,49,38,.09);filter:blur(6px);z-index:-1}
.shop-card-action .btn{box-shadow:0 7px 18px color-mix(in srgb,var(--theme) 24%,transparent);transition:transform .16s ease,box-shadow .16s ease,background .16s ease}.shop-card-action .btn:hover{transform:translateY(-1px);box-shadow:0 10px 22px color-mix(in srgb,var(--theme) 31%,transparent)}
.hero-photo{transition:transform 8s ease}.hero:hover .hero-photo{transform:scale(1.025)}
.scene-label{font-size:9px;font-weight:900;letter-spacing:.08em}.scene-price{font-size:16px;font-weight:950}
.motion-ready .reveal-item{opacity:0;transform:translateY(14px);transition:opacity .5s ease,transform .5s cubic-bezier(.2,.7,.2,1)}.motion-ready .reveal-item.is-visible{opacity:1;transform:none}
.motion-ready .shop-card.reveal-item{transition:opacity .42s ease,transform .42s cubic-bezier(.2,.7,.2,1),box-shadow .18s ease,border-color .18s ease}
@media(max-width:719px){.topnav .brand{display:flex}.brand-logo{width:164px;max-width:none}.topnav .wrap{gap:6px}.topnav .chip{display:none}.category-visual{height:126px}.hero-photo{transition:none}}
@media(prefers-reduced-motion:reduce){.motion-ready .reveal-item{opacity:1!important;transform:none!important}.hero-photo{transition:none!important}.category-visual{transition:none!important}}
'''

CSS += r'''
/* Premium visual hierarchy v10 */
.home-hero-title{margin:15px 0 12px;display:flex;flex-direction:column;align-items:flex-start;gap:1px;line-height:.98;letter-spacing:-.045em}
.home-hero-title .hero-title-top{font-size:clamp(26px,5vw,38px);font-weight:800;color:#385348;letter-spacing:-.025em}
.home-hero-title .hero-title-main{position:relative;z-index:1;font-size:clamp(45px,8vw,68px);font-weight:950;color:#173126;padding:2px 2px 5px}
.home-hero-title .hero-title-main:after{content:"";position:absolute;z-index:-1;left:-3px;right:-5px;bottom:5px;height:.28em;border-radius:999px;background:linear-gradient(90deg,#ffd66e,#ffe9a9);transform:rotate(-1deg);opacity:.92}
.home-hero-title .hero-title-bottom{font-size:clamp(32px,6vw,48px);font-weight:900;color:#173126}
.hero-lead-mark{display:inline-block;font-weight:900;color:#173126;border-bottom:2px solid #ffd66e;padding-bottom:1px}
.hero-proof{display:flex;gap:8px;flex-wrap:wrap;margin-top:15px}.hero-proof-item{display:flex;align-items:center;gap:7px;background:rgba(255,255,255,.72);border:1px solid rgba(191,215,201,.9);border-radius:14px;padding:8px 10px;box-shadow:0 7px 20px rgba(28,68,49,.045)}.hero-proof-item b{font-size:15px;color:#173126}.hero-proof-item span{font-size:10px;color:#66776e;font-weight:750}
.category-hero-title{display:flex;flex-direction:column;align-items:flex-start;gap:2px}.category-hero-title .category-name{font-size:.62em;font-weight:800;color:var(--theme-dark);letter-spacing:.01em}.category-hero-title .category-question{position:relative;font-size:1.08em;font-weight:950;z-index:1}.category-hero-title .category-question:after{content:"";position:absolute;z-index:-1;left:0;right:-6px;bottom:4px;height:.22em;border-radius:999px;background:var(--theme-soft)}
.visual-section{padding-top:12px}.visual-section .section-head{margin-bottom:17px}.visual-section .section-head h2{font-size:clamp(24px,5vw,30px)}
.home-grid{gap:18px}.category-card{border-radius:24px;box-shadow:0 20px 45px rgba(31,65,49,.11),0 1px 0 rgba(255,255,255,.8) inset}.category-card:hover{transform:translateY(-6px) scale(1.006);box-shadow:0 28px 56px rgba(31,65,49,.16)}.category-card.theme-sheet{background:linear-gradient(150deg,#d9f5e5 0%,#f8fffb 68%)}.category-card.theme-litter{background:linear-gradient(150deg,#ffedbd 0%,#fffaf0 68%)}.category-card.theme-system{background:linear-gradient(150deg,#d8f1f5 0%,#f7fdfe 68%)}
.category-card-copy{padding:4px 18px 20px}.category-card-copy strong{font-size:21px;letter-spacing:-.02em}.category-price{font-size:31px;line-height:1.05}.category-meta{margin-top:7px}.price-ribbon{padding:6px 10px;background:rgba(255,255,255,.88);border:1px solid rgba(255,255,255,.72);box-shadow:0 7px 18px rgba(79,79,41,.08)}
.category-arrow{width:39px;height:39px;right:17px;bottom:17px;box-shadow:0 8px 17px rgba(23,49,38,.17);transition:transform .18s ease}.category-card:hover .category-arrow{transform:translateX(3px)}
.category-card-number{position:absolute;left:15px;top:13px;z-index:2;font-size:10px;font-weight:950;letter-spacing:.12em;color:rgba(23,49,38,.48);text-transform:uppercase}
.category-card-number b{font-size:21px;letter-spacing:-.05em;color:rgba(23,49,38,.78);margin-right:5px}
.snapshot-section{padding:22px 20px 19px;border-radius:24px;background:radial-gradient(circle at 83% 9%,rgba(255,215,111,.16),transparent 25%),linear-gradient(145deg,#142d23,#24513d 66%,#2e6e51);box-shadow:0 24px 55px rgba(20,45,35,.22)}
.snapshot-section .section-head h2:before{background:radial-gradient(circle at 50% 65%,#ffd66e 0 5px,transparent 5.8px),radial-gradient(circle at 24% 31%,#ffd66e 0 3px,transparent 3.8px),radial-gradient(circle at 48% 20%,#ffd66e 0 3px,transparent 3.8px),radial-gradient(circle at 73% 31%,#ffd66e 0 3px,transparent 3.8px),rgba(255,255,255,.12)}
.podium-title{display:flex;align-items:center;gap:8px}.podium-title span{display:inline-flex;background:#ffd66e;color:#654a00;border-radius:999px;padding:4px 8px;font-size:9px;font-weight:950;letter-spacing:.08em}
.top3-strip{grid-template-columns:repeat(3,minmax(0,1fr));grid-template-areas:"second first third";gap:12px;align-items:end;padding-top:12px}.top3-card:nth-child(1){grid-area:first;min-height:148px;transform:translateY(-13px);border:2px solid #ffd66e;background:linear-gradient(180deg,#fffdf2,#fff)}.top3-card:nth-child(2){grid-area:second;min-height:128px;border:1px solid #d8dedb}.top3-card:nth-child(3){grid-area:third;min-height:120px;border:1px solid #e4d4c7}
.top3-card{position:relative;flex-direction:column;align-items:flex-start;padding:13px;border-radius:18px}.top3-card:hover{transform:translateY(-3px)}.top3-card:nth-child(1):hover{transform:translateY(-16px)}
.top3-rank{position:absolute;top:-11px;left:12px;width:34px;height:34px;border-radius:12px;font-size:14px;box-shadow:0 7px 16px rgba(0,0,0,.18)}.top3-card:nth-child(1) .top3-rank{width:40px;height:40px;top:-16px;background:#ffd66e;color:#654a00;font-size:17px}.top3-card:nth-child(2) .top3-rank{background:#dce2df;color:#50615a}.top3-card:nth-child(3) .top3-rank{background:#d7b594;color:#68492f}
.top3-card:nth-child(1) .top3-rank:before{content:"♛";position:absolute;top:-15px;font-size:17px;color:#ffd66e;text-shadow:0 2px 0 #6b5100}.top3-card:first-child .top3-rank:after{display:none}
.top3-img{width:68px;height:68px;flex-basis:68px;margin:5px auto 2px}.top3-card:nth-child(1) .top3-img{width:78px;height:78px;flex-basis:78px}.top3-copy{width:100%;text-align:center}.top3-name{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;white-space:normal;min-height:30px}.top3-unit{display:block;margin-top:5px;font-size:21px}.top3-card:nth-child(1) .top3-unit{font-size:26px}.top3-total{display:block;margin-top:2px}
.podium-foot{height:7px;border-radius:999px;margin:4px 2px 0;background:linear-gradient(90deg,#ccd7d1 0 30%,#ffd66e 30% 68%,#c99a73 68% 100%);opacity:.85}
.featured{border-radius:22px}.featured-crown{transform:rotate(-6deg)}.featured-unit{letter-spacing:-.035em}
@media(max-width:759px){
  .home-hero-title{gap:0}.home-hero-title .hero-title-top{font-size:25px}.home-hero-title .hero-title-main{font-size:45px}.home-hero-title .hero-title-bottom{font-size:34px}.hero-proof{gap:6px}.hero-proof-item{padding:7px 9px}
  .category-card{border-radius:21px}.category-card-number{top:11px;left:12px}
  .snapshot-section{padding:18px 14px}.top3-strip{display:flex;grid-template-areas:none;padding:14px 2px 6px;align-items:stretch}.top3-card,.top3-card:nth-child(1),.top3-card:nth-child(2),.top3-card:nth-child(3){grid-area:auto;min-width:78%;min-height:0;transform:none;flex-direction:row;align-items:center}.top3-card:nth-child(1):hover{transform:none}.top3-img,.top3-card:nth-child(1) .top3-img{width:58px;height:58px;flex-basis:58px;margin:0}.top3-copy{text-align:left}.top3-rank,.top3-card:nth-child(1) .top3-rank{position:static;width:31px;height:31px;flex:0 0 31px;font-size:12px}.top3-card:nth-child(1) .top3-rank:before{display:none}.top3-unit,.top3-card:nth-child(1) .top3-unit{font-size:19px}.podium-foot{display:none}
}
'''

CSS += r'''
/* Daily price-gap spotlight v11 */
.daily-spotlight{position:relative;overflow:hidden;padding:0;border:0;background:linear-gradient(138deg,#142f24 0%,#214d39 55%,#2f7152 100%);color:#fff;border-radius:28px;box-shadow:0 26px 60px rgba(20,47,36,.22)}
.daily-spotlight:before{content:"";position:absolute;width:250px;height:250px;border-radius:50%;right:-90px;top:-115px;background:rgba(255,214,110,.13)}
.daily-spotlight:after{content:"";position:absolute;width:150px;height:150px;border-radius:50%;left:-80px;bottom:-90px;background:rgba(126,211,171,.12)}
.spotlight-inner{position:relative;z-index:1;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(250px,.72fr);gap:24px;align-items:center;padding:25px}
.spotlight-kicker{display:inline-flex;align-items:center;gap:7px;font-size:10px;font-weight:950;letter-spacing:.12em;color:#ffe08a}.spotlight-kicker:before{content:"";width:8px;height:8px;border-radius:50%;background:#ffd66e;box-shadow:0 0 0 5px rgba(255,214,110,.12)}
.daily-spotlight h2{margin:7px 0 4px;font-size:clamp(27px,5vw,38px);line-height:1.1;letter-spacing:-.035em}.daily-spotlight h2:before{display:none}
.spotlight-copy{margin:0;color:rgba(255,255,255,.78);font-size:13px;max-width:620px}.spotlight-copy strong{color:#fff}
.spotlight-gap{display:flex;align-items:baseline;gap:8px;margin:13px 0 4px}.spotlight-gap b{font-size:clamp(42px,7vw,58px);line-height:.95;color:#ffd66e;letter-spacing:-.055em}.spotlight-gap span{font-size:14px;font-weight:850;color:#fff}
.spotlight-price-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.spotlight-price{display:flex;flex-direction:column;background:rgba(255,255,255,.09);border:1px solid rgba(255,255,255,.12);border-radius:13px;padding:8px 10px}.spotlight-price span{font-size:9px;color:rgba(255,255,255,.62);font-weight:800}.spotlight-price b{font-size:17px;color:#fff;line-height:1.2}
.spotlight-action{display:inline-flex;margin-top:13px;background:#fff;color:#173126;text-decoration:none;border-radius:13px;padding:10px 14px;font-size:12px;font-weight:950;box-shadow:0 8px 20px rgba(0,0,0,.16);transition:transform .16s ease}.spotlight-action:hover{transform:translateY(-2px)}
.spotlight-product{position:relative;background:linear-gradient(145deg,#fff,#f7fbf8);color:#173126;border-radius:20px;padding:14px;box-shadow:0 16px 38px rgba(0,0,0,.17);min-width:0}.spotlight-product:before{content:"TODAY";position:absolute;right:-19px;top:14px;transform:rotate(38deg);background:#ffd66e;color:#654a00;font-size:8px;font-weight:950;letter-spacing:.12em;padding:4px 27px}
.spotlight-image{display:block;width:100%;height:135px;object-fit:contain;background:#fff;border-radius:14px}.spotlight-category-art{height:135px}.spotlight-category-art svg{width:100%;height:100%}
.spotlight-product-name{font-size:12px;font-weight:850;line-height:1.4;margin-top:9px;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}.spotlight-product-meta{font-size:10px;color:#66776e;margin-top:4px}
.gap-strip{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px;margin:10px 0 0}.gap-chip{display:flex;align-items:center;justify-content:space-between;gap:8px;text-decoration:none;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.11);border-radius:13px;padding:8px 10px;color:#fff}.gap-chip span{font-size:10px;color:rgba(255,255,255,.68);font-weight:800}.gap-chip b{font-size:15px;color:#ffe08a;white-space:nowrap}.gap-chip:hover{background:rgba(255,255,255,.12)}
.spotlight-note{font-size:9px;color:rgba(255,255,255,.53);margin-top:9px}
@media(max-width:759px){.daily-spotlight{border-radius:22px}.spotlight-inner{grid-template-columns:1fr;padding:18px;gap:15px}.spotlight-product{display:grid;grid-template-columns:78px minmax(0,1fr);gap:10px;align-items:center}.spotlight-image,.spotlight-category-art{width:78px;height:78px}.spotlight-product-name{margin-top:0}.gap-strip{display:flex;overflow-x:auto;scroll-snap-type:x mandatory}.gap-chip{min-width:66%;scroll-snap-align:start}.spotlight-gap b{font-size:44px}}
'''

CSS += r'''
/* Visual condition selector v12 */
.condition-panel{position:relative;overflow:hidden;background:linear-gradient(145deg,var(--theme-wash),#fff 58%);border-color:color-mix(in srgb,var(--theme) 18%,#dce7e0);padding:20px}.condition-panel:before{content:"SELECT";position:absolute;right:14px;top:11px;font-size:9px;font-weight:950;letter-spacing:.16em;color:color-mix(in srgb,var(--theme) 35%,transparent)}
.condition-current{display:inline-flex;align-items:center;gap:6px;margin-top:5px;padding:5px 9px;border-radius:999px;background:var(--theme-soft);color:var(--theme-dark);font-size:11px;font-weight:900}.condition-current:before{content:"●";font-size:7px}
.filter-wrap{margin:8px -4px 16px;padding:4px;overflow:auto}.filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:9px;min-width:0}
.filter-chip{position:relative;appearance:none;display:grid;grid-template-columns:38px minmax(0,1fr);grid-template-areas:"icon label" "icon meta";gap:0 9px;align-items:center;text-align:left;min-height:66px;padding:10px 11px;border:1px solid var(--line);border-radius:16px;background:#fff;color:var(--text);font:inherit;cursor:pointer;box-shadow:0 5px 15px rgba(28,68,49,.035);transition:transform .16s ease,box-shadow .16s ease,border-color .16s ease,background .16s ease}
.filter-chip:hover{transform:translateY(-2px);border-color:color-mix(in srgb,var(--theme) 42%,#dce7e0);box-shadow:0 10px 22px rgba(28,68,49,.075)}
.filter-chip.active,.filter-chip[aria-pressed="true"]{background:linear-gradient(145deg,var(--theme),var(--theme-dark));border-color:var(--theme);color:#fff;box-shadow:0 11px 25px color-mix(in srgb,var(--theme) 24%,transparent);transform:translateY(-2px)}
.filter-icon{grid-area:icon;width:38px;height:38px;border-radius:12px;display:grid;place-items:center;background:var(--theme-soft);color:var(--theme-dark);font-size:19px;font-weight:950;line-height:1}.filter-chip.active .filter-icon,.filter-chip[aria-pressed="true"] .filter-icon{background:rgba(255,255,255,.17);color:#fff}
.filter-label{grid-area:label;font-size:12px;font-weight:900;line-height:1.25;white-space:normal}.filter-meta{grid-area:meta;font-size:9px;font-weight:750;color:var(--muted);margin-top:3px}.filter-chip.active .filter-meta,.filter-chip[aria-pressed="true"] .filter-meta{color:rgba(255,255,255,.72)}
.filter-count{position:absolute;right:8px;top:7px;min-width:23px;height:20px;padding:0 6px;border-radius:999px;display:grid;place-items:center;background:#f1f5f2;color:#5d6f65;font-size:9px;font-weight:900}.filter-chip.active .filter-count,.filter-chip[aria-pressed="true"] .filter-count{background:#ffd76f;color:#664b00}
.filter-chip:focus-visible{outline:3px solid color-mix(in srgb,var(--theme) 26%,#fff);outline-offset:2px}
.filter-help{display:flex;align-items:center;gap:7px;margin:-4px 0 12px;font-size:10px;color:var(--muted)}.filter-help:before{content:"↔";display:grid;place-items:center;width:22px;height:22px;border-radius:8px;background:var(--theme-soft);color:var(--theme-dark);font-weight:950}
@media(max-width:759px){.condition-panel{padding:16px}.filter-wrap{margin-left:-16px;margin-right:-16px;padding:4px 16px 7px}.filters{display:flex;gap:9px;min-width:max-content}.filter-chip{width:150px;flex:0 0 150px;scroll-snap-align:start}.filter-wrap{scroll-snap-type:x proximity}.filter-help{margin-top:-5px}}
'''

CSS += r'''
/* Objective value badges v13 */
.value-badge-row{display:flex;flex-wrap:wrap;gap:5px;margin:6px 0 2px;min-height:24px}
.value-badge{display:inline-flex;align-items:center;gap:4px;border-radius:999px;padding:4px 7px;font-size:9px;font-weight:900;line-height:1;border:1px solid transparent}
.value-badge:before{font-size:11px;line-height:1}
.value-badge.is-discount{background:#e8f6ed;color:#176443;border-color:#cce9d8}.value-badge.is-discount:before{content:"↓"}
.value-badge.is-low-total{background:#fff2cc;color:#775800;border-color:#f2dda0}.value-badge.is-low-total:before{content:"¥"}
.value-badge.is-bulk{background:#e6f3f7;color:#286d78;border-color:#cbe4ea}.value-badge.is-bulk:before{content:"□"}
.value-badge.is-best-unit{background:#173126;color:#fff;border-color:#173126}.value-badge.is-best-unit:before{content:"♛";color:#ffd66e}
.shop-card.is-rank-1 .value-badge-row{padding-right:34px}
.value-badge-empty{font-size:9px;color:var(--muted);padding:4px 0}
.value-legend{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;font-size:9px;color:var(--muted)}.value-legend span{display:inline-flex;align-items:center;gap:4px}.value-legend i{width:7px;height:7px;border-radius:50%;display:inline-block}.value-legend .u{background:#173126}.value-legend .d{background:#55ad83}.value-legend .t{background:#e2b94f}.value-legend .b{background:#69adba}
@media(max-width:759px){.value-badge{font-size:9px;padding:4px 6px}.value-badge-row{margin-top:5px}.shop-card.is-rank-1 .value-badge-row{padding-right:22px}}
'''

CSS += r'''
/* Rank showcase v14 */
.product-grid{align-items:start}
.rank-showcase-label{display:none;position:absolute;z-index:3;left:13px;top:13px;border-radius:999px;padding:5px 8px;font-size:9px;font-weight:950;letter-spacing:.08em;box-shadow:0 6px 16px rgba(23,49,38,.12)}
.shop-card.is-rank-1{grid-column:1/-1;grid-template-columns:170px minmax(0,1fr) 190px;grid-template-areas:"image head price" "image meta price" "image action action";gap:10px 18px;min-height:205px;padding:18px;border:2px solid #e7bd49;background:radial-gradient(circle at 91% 10%,rgba(255,215,111,.24),transparent 25%),linear-gradient(145deg,#fffdf3,#fff 60%);box-shadow:0 22px 48px rgba(72,57,11,.14)}
.shop-card.is-rank-1:before{content:"CURRENT BEST";right:-31px;top:18px;padding:5px 39px;background:#ffd76f;color:#674c00;font-size:9px}
.shop-card.is-rank-1 .rank-showcase-label{display:inline-flex;background:#173126;color:#fff;left:183px;top:17px}
.shop-card.is-rank-1 .shop-card-image-wrap{align-self:center;padding-top:8px}.shop-card.is-rank-1 .shop-card-image{width:150px;height:150px;border-radius:18px;box-shadow:0 12px 28px rgba(23,49,38,.08)}
.shop-card.is-rank-1 .shop-card-rank{left:-8px;top:-7px;width:42px;height:42px;border-radius:14px;font-size:17px;background:#ffd76f;color:#654a00;box-shadow:0 8px 18px rgba(129,92,0,.22)}
.shop-card.is-rank-1 .shop-card-rank:before{content:"♛";position:absolute;top:-18px;font-size:18px;color:#e8b935;text-shadow:0 1px 0 #6a4d00}
.shop-card.is-rank-1 .shop-card-head{padding-top:30px}.shop-card.is-rank-1 .shop-card-title{font-size:17px;line-height:1.45;-webkit-line-clamp:2}.shop-card.is-rank-1 .shop-card-shop{font-size:11px}
.shop-card.is-rank-1 .shop-card-prices{align-self:center;display:block;text-align:right;padding-top:24px}.shop-card.is-rank-1 .shop-unit{font-size:36px}.shop-card.is-rank-1 .shop-unit-label{font-size:11px}.shop-card.is-rank-1 .shop-total{margin-top:10px}.shop-card.is-rank-1 .shop-total b{font-size:18px}
.shop-card.is-rank-1 .shop-card-meta{border-top:0;padding-top:0}.shop-card.is-rank-1 .shop-card-action{display:flex;justify-content:flex-end}.shop-card.is-rank-1 .shop-card-action .btn{width:auto;min-width:210px;padding:13px 18px;font-size:14px}
.shop-card.is-rank-2,.shop-card.is-rank-3{border-width:2px;border-top-width:5px}.shop-card.is-rank-2{border-color:#c9d1ce;background:linear-gradient(145deg,#fbfdfc,#fff)}.shop-card.is-rank-3{border-color:#d5b18d;background:linear-gradient(145deg,#fffaf6,#fff)}
.shop-card.is-rank-2 .rank-showcase-label,.shop-card.is-rank-3 .rank-showcase-label{display:inline-flex;left:48px;top:10px}.shop-card.is-rank-2 .rank-showcase-label{background:#e2e8e5;color:#50615a}.shop-card.is-rank-3 .rank-showcase-label{background:#e4c3a4;color:#68492f}
.shop-card.is-rank-2 .shop-card-rank{background:#dce3e0;color:#4f6058}.shop-card.is-rank-3 .shop-card-rank{background:#d8b18b;color:#68492f}
.shop-card.is-rank-2 .shop-card-image,.shop-card.is-rank-3 .shop-card-image{width:104px;height:104px}.shop-card.is-rank-2,.shop-card.is-rank-3{grid-template-columns:104px minmax(0,1fr)}.shop-card.is-rank-2 .shop-card-title,.shop-card.is-rank-3 .shop-card-title{font-size:14px}
@media(max-width:759px){
  .shop-card.is-rank-1{grid-column:auto;grid-template-columns:110px minmax(0,1fr);grid-template-areas:"image head" "image price" "meta meta" "action action";gap:8px 12px;min-height:0;padding:14px}
  .shop-card.is-rank-1 .shop-card-image{width:110px;height:110px}.shop-card.is-rank-1 .shop-card-head{padding-top:27px}.shop-card.is-rank-1 .shop-card-prices{display:flex;text-align:left;padding-top:0}.shop-card.is-rank-1 .shop-unit{font-size:27px}.shop-card.is-rank-1 .shop-total{margin-top:0}.shop-card.is-rank-1 .shop-card-action .btn{width:100%;min-width:0}
  .shop-card.is-rank-1 .rank-showcase-label{left:126px;top:12px}.shop-card.is-rank-2 .rank-showcase-label,.shop-card.is-rank-3 .rank-showcase-label{left:44px;top:8px}
  .shop-card.is-rank-2,.shop-card.is-rank-3{grid-template-columns:88px minmax(0,1fr)}.shop-card.is-rank-2 .shop-card-image,.shop-card.is-rank-3 .shop-card-image{width:88px;height:88px}
}
'''

CSS += r'''
/* Mobile-first product information hierarchy v15 */
.shop-unit-wrap{position:relative}.shop-unit-label{letter-spacing:.01em}.shop-unit{font-variant-numeric:tabular-nums}
.shop-card-meta{min-height:29px}.shipping{display:inline-flex;align-items:center;justify-content:center;border-radius:999px;padding:4px 7px;background:#f1f5f2;color:#607067;font-size:9px;font-weight:800}
.shop-card-head .shop-card-tags{margin:7px 0 0}.shop-card-title{letter-spacing:-.01em}
.price-diff:empty{display:none}
.mobile-price-caption{display:none}
@media(max-width:759px){
  .shop-card,.shop-card.is-rank-1,.shop-card.is-rank-2,.shop-card.is-rank-3{
    grid-template-columns:88px minmax(0,1fr);
    grid-template-areas:"image price" "image head" "meta meta" "action action";
    gap:7px 11px;
    padding:12px;
  }
  .shop-card.is-rank-1{grid-template-columns:104px minmax(0,1fr);padding:14px}
  .shop-card-image,.shop-card.is-rank-2 .shop-card-image,.shop-card.is-rank-3 .shop-card-image{width:88px;height:88px}
  .shop-card.is-rank-1 .shop-card-image{width:104px;height:104px}
  .shop-card-prices,.shop-card.is-rank-1 .shop-card-prices{
    align-self:start;display:block;text-align:left;padding:2px 0 0;
  }
  .shop-unit-label{font-size:9px;color:var(--theme-dark);font-weight:900}
  .shop-unit,.shop-card.is-rank-1 .shop-unit{font-size:29px;line-height:1.04;letter-spacing:-.045em}
  .shop-unit small{display:block;margin-top:3px;font-size:9px;letter-spacing:0}
  .shop-total{display:flex;align-items:baseline;gap:5px;text-align:left;margin-top:6px!important}
  .shop-total span{font-size:8px}.shop-total b,.shop-card.is-rank-1 .shop-total b{font-size:13px}
  .shop-card-head,.shop-card.is-rank-1 .shop-card-head{padding-top:0}
  .value-badge-row{order:0;margin:0 0 5px;min-height:0}.value-badge{font-size:8px;padding:4px 6px}
  .shop-card-title,.shop-card.is-rank-1 .shop-card-title,.shop-card.is-rank-2 .shop-card-title,.shop-card.is-rank-3 .shop-card-title{
    font-size:12px;line-height:1.4;-webkit-line-clamp:2;
  }
  .shop-card-shop{font-size:9px;margin-top:3px}
  .shop-card-tags{gap:3px!important;margin-top:6px!important}.condition-tag{font-size:8px;padding:3px 6px}
  .shop-card-meta{display:flex;justify-content:flex-start;gap:6px;border-top:1px dashed var(--line);padding-top:7px;min-height:0}
  .shop-card-meta .price-diff{font-size:9px;background:var(--theme-soft);color:var(--theme-dark);border-radius:999px;padding:4px 7px}
  .shipping{font-size:8px;padding:4px 7px}
  .shop-card-action .btn,.shop-card.is-rank-1 .shop-card-action .btn{min-height:43px;font-size:12px;padding:11px 13px}
  .shop-card.is-rank-1 .rank-showcase-label{left:119px;top:10px;font-size:8px}
  .shop-card.is-rank-2 .rank-showcase-label,.shop-card.is-rank-3 .rank-showcase-label{left:43px;top:7px;font-size:8px}
  .shop-card.is-rank-1 .shop-card-rank{width:36px;height:36px;font-size:14px}
  .shop-card.is-rank-1 .shop-card-rank:before{top:-15px;font-size:15px}
}
'''

CSS += r'''
/* Sticky comparison summary v16 */
.comparison-sticky{position:sticky;top:54px;z-index:9;margin:10px 0 14px;border:1px solid color-mix(in srgb,var(--theme) 18%,#dce7e0);border-radius:18px;background:rgba(255,255,255,.93);box-shadow:0 12px 30px rgba(23,49,38,.10);backdrop-filter:blur(14px);overflow:hidden}
.comparison-sticky-inner{display:grid;grid-template-columns:minmax(145px,1.1fr) minmax(110px,.8fr) minmax(150px,1fr) 76px auto;align-items:center;gap:0}
.sticky-cell{min-width:0;padding:10px 12px;border-right:1px solid var(--line)}.sticky-cell:last-of-type{border-right:0}
.sticky-label{display:block;font-size:8px;font-weight:900;letter-spacing:.06em;color:var(--muted);text-transform:uppercase}.sticky-value{display:block;margin-top:1px;font-size:13px;font-weight:950;color:#173126;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.sticky-price .sticky-value{font-size:19px;color:var(--theme-dark);letter-spacing:-.025em}.sticky-gap .sticky-value{color:var(--theme-dark)}
.sticky-count{text-align:center}.sticky-count .sticky-value{font-size:15px}
.sticky-jump{display:flex;align-items:center;justify-content:center;align-self:stretch;min-width:104px;padding:0 12px;text-decoration:none;background:var(--theme);color:#fff;font-size:11px;font-weight:950;transition:background .16s ease}.sticky-jump:hover{background:var(--theme-dark)}
.sticky-jump:after{content:"↓";margin-left:5px;font-size:12px}
@media(max-width:759px){
  .comparison-sticky{top:48px;margin:7px -4px 12px;border-radius:15px}
  .comparison-sticky-inner{grid-template-columns:1.15fr 1fr .82fr auto}
  .sticky-cell{padding:8px 8px}.sticky-label{font-size:7px}.sticky-value{font-size:10px}.sticky-price .sticky-value{font-size:17px}.sticky-gap{display:none}.sticky-count .sticky-value{font-size:12px}
  .sticky-jump{min-width:49px;padding:0 8px;font-size:0}.sticky-jump:after{content:"↓";margin:0;font-size:16px}
}
'''

CSS += r'''
/* Editorial homepage v17 */
.editorial-section{position:relative;overflow:hidden;padding:24px;border-radius:30px;background:#f7f3e9;border:1px solid #e9dfc9;box-shadow:0 20px 48px rgba(77,58,20,.08)}
.editorial-section:before{content:"PET COST JOURNAL";position:absolute;right:-8px;top:12px;font-size:10px;font-weight:950;letter-spacing:.18em;color:rgba(91,71,30,.22);transform:rotate(1deg)}
.editorial-head{display:flex;align-items:flex-end;justify-content:space-between;gap:14px;margin-bottom:18px;padding-bottom:13px;border-bottom:2px solid #173126}
.editorial-head h2{margin:0;font-size:clamp(28px,5vw,36px);letter-spacing:-.04em}.editorial-head h2:before{display:none}
.editorial-head-copy{max-width:610px}.editorial-eyebrow{display:block;margin-bottom:4px;font-size:9px;font-weight:950;letter-spacing:.16em;color:#8d6d2d}.editorial-date{flex:0 0 auto;text-align:right;font-size:9px;font-weight:850;color:#7d7464;line-height:1.5}
.editorial-grid{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(250px,.85fr);gap:14px}
.editorial-lead{position:relative;min-height:360px;display:grid;grid-template-columns:minmax(0,1fr) minmax(230px,.9fr);align-items:stretch;overflow:hidden;text-decoration:none;color:#173126;border-radius:24px;border:1px solid color-mix(in srgb,var(--theme) 20%,#e4ddd0);background:linear-gradient(145deg,#fff,var(--theme-wash));box-shadow:0 18px 42px rgba(23,49,38,.10)}
.editorial-lead-copy{position:relative;z-index:2;padding:28px 10px 26px 27px;display:flex;flex-direction:column;justify-content:center}
.editorial-index{display:inline-flex;width:max-content;border:1px solid currentColor;border-radius:999px;padding:5px 8px;font-size:8px;font-weight:950;letter-spacing:.12em;color:var(--theme-dark)}
.editorial-lead h3{margin:13px 0 5px;font-size:clamp(31px,5vw,45px);line-height:1.02;letter-spacing:-.055em}.editorial-lead-sub{font-size:12px;font-weight:800;color:#5f7168}
.editorial-price-block{margin-top:22px}.editorial-price-caption{display:block;font-size:9px;font-weight:900;color:#6f7b74}.editorial-price{display:block;margin-top:2px;font-size:clamp(38px,6vw,54px);font-weight:950;line-height:.95;letter-spacing:-.06em;color:var(--theme-dark)}.editorial-price small{font-size:12px;letter-spacing:0}
.editorial-gap{display:inline-flex;width:max-content;margin-top:10px;border-radius:999px;padding:6px 9px;background:#173126;color:#fff;font-size:10px;font-weight:900}.editorial-gap b{color:#ffd66e;margin-right:3px}
.editorial-lead-art{position:relative;display:grid;place-items:center;min-width:0;padding:22px;background:radial-gradient(circle at 52% 44%,rgba(255,255,255,.95),rgba(255,255,255,.3) 47%,transparent 68%)}.editorial-lead-art svg{width:100%;height:auto;max-height:260px}.editorial-lead-art:after{content:"TODAY'S FEATURE";position:absolute;right:12px;bottom:11px;font-size:8px;font-weight:950;letter-spacing:.14em;color:color-mix(in srgb,var(--theme-dark) 55%,transparent)}
.editorial-arrow{position:absolute;right:18px;top:18px;z-index:4;width:40px;height:40px;border-radius:50%;display:grid;place-items:center;background:#173126;color:#fff;font-size:19px;box-shadow:0 8px 18px rgba(23,49,38,.16);transition:transform .18s ease}.editorial-lead:hover .editorial-arrow{transform:translate(3px,-2px)}
.editorial-side{display:grid;grid-template-rows:repeat(2,minmax(0,1fr));gap:14px}.editorial-side-card{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 105px;align-items:center;overflow:hidden;text-decoration:none;color:#173126;border-radius:21px;border:1px solid color-mix(in srgb,var(--theme) 18%,#e7dfcf);background:linear-gradient(145deg,#fff,var(--theme-wash));padding:17px;box-shadow:0 12px 28px rgba(23,49,38,.07);transition:transform .18s ease,box-shadow .18s ease}.editorial-side-card:hover{transform:translateY(-3px);box-shadow:0 17px 34px rgba(23,49,38,.11)}
.editorial-side-card h3{margin:6px 0 5px;font-size:19px;line-height:1.1;letter-spacing:-.035em}.editorial-side-price{font-size:27px;font-weight:950;line-height:1;letter-spacing:-.045em;color:var(--theme-dark)}.editorial-side-price small{font-size:9px;letter-spacing:0}.editorial-side-meta{margin-top:7px;font-size:9px;font-weight:800;color:#6d796f}.editorial-side-art{height:105px;display:grid;place-items:center}.editorial-side-art svg{width:115px;max-width:100%;height:100%}
.editorial-folio{position:absolute;right:10px;top:8px;font-size:8px;font-weight:950;letter-spacing:.1em;color:rgba(23,49,38,.38)}
.editorial-footerline{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-top:15px;padding-top:11px;border-top:1px solid #dfd5c2;font-size:9px;color:#796f5f}.editorial-footerline strong{color:#173126}
@media(max-width:759px){
  .editorial-section{padding:16px;border-radius:22px}.editorial-section:before{font-size:7px;right:4px}.editorial-head{align-items:flex-start}.editorial-date{display:none}
  .editorial-grid{grid-template-columns:1fr}.editorial-lead{min-height:0;grid-template-columns:1fr 126px}.editorial-lead-copy{padding:20px 4px 19px 18px}.editorial-lead h3{font-size:29px}.editorial-lead-art{padding:8px}.editorial-lead-art svg{max-height:170px}.editorial-price{font-size:38px}.editorial-price-block{margin-top:16px}.editorial-arrow{width:34px;height:34px;right:9px;top:9px}
  .editorial-side{grid-template-rows:none;grid-template-columns:repeat(2,minmax(0,1fr));gap:9px}.editorial-side-card{display:block;padding:13px;min-height:190px}.editorial-side-card h3{font-size:15px;padding-right:14px}.editorial-side-price{font-size:24px}.editorial-side-art{height:83px;margin-top:4px}.editorial-side-art svg{width:100%;height:100%}.editorial-side-meta{font-size:8px}
  .editorial-footerline{display:block;line-height:1.6}
}
'''

CSS += r'''
/* Category cover feature v18 */
.featured.cover-feature{position:relative;overflow:hidden;display:grid;grid-template-columns:180px minmax(0,1fr) 210px;gap:22px;align-items:center;margin:14px 0 20px;padding:22px;border:1px solid color-mix(in srgb,var(--theme) 24%,#d9e4de);border-radius:26px;background:radial-gradient(circle at 84% 12%,color-mix(in srgb,var(--theme-soft) 76%,transparent),transparent 29%),linear-gradient(145deg,#fff,var(--theme-wash));box-shadow:0 20px 48px rgba(23,49,38,.11)}
.featured.cover-feature:before{content:"TODAY'S BEST PRICE";position:absolute;right:-31px;top:17px;transform:rotate(38deg);padding:5px 39px;background:#173126;color:#fff;font-size:8px;font-weight:950;letter-spacing:.12em;z-index:3}
.cover-media{position:relative;display:grid;place-items:center;min-height:180px;border-radius:21px;background:rgba(255,255,255,.74);border:1px solid rgba(255,255,255,.9);box-shadow:0 12px 30px rgba(23,49,38,.07)}
.cover-media:after{content:"";position:absolute;left:19%;right:19%;bottom:15px;height:11px;border-radius:50%;background:rgba(23,49,38,.10);filter:blur(7px)}
.cover-feature .featured-img{position:relative;z-index:1;width:156px;height:156px;border:0;border-radius:18px;background:#fff;object-fit:contain}
.cover-copy{min-width:0}.cover-kicker{display:flex;align-items:center;gap:7px;margin-bottom:8px;color:var(--theme-dark);font-size:9px;font-weight:950;letter-spacing:.12em}.cover-kicker:before{content:"♛";display:grid;place-items:center;width:25px;height:25px;border-radius:9px;background:#ffd66e;color:#674c00;font-size:13px}
.cover-feature .featured-badge{background:var(--theme);font-size:9px;padding:5px 8px;letter-spacing:.03em}.cover-feature .featured-crown{display:none}
.cover-feature .featured-title{margin:10px 0 3px;font-size:17px;line-height:1.45;-webkit-line-clamp:2}.cover-feature .featured-shop{font-size:10px}
.cover-reasons{display:flex;flex-wrap:wrap;gap:5px;margin-top:10px;min-height:25px}.cover-reason{display:inline-flex;align-items:center;border-radius:999px;padding:5px 8px;background:#fff;border:1px solid color-mix(in srgb,var(--theme) 18%,#dde7e1);color:#315546;font-size:9px;font-weight:900;box-shadow:0 4px 12px rgba(23,49,38,.04)}.cover-reason.is-primary{background:#173126;color:#fff;border-color:#173126}.cover-reason.is-warm{background:#fff2cb;color:#765600;border-color:#efd99b}.cover-reason.is-cool{background:#e5f3f6;color:#276d78;border-color:#c8e1e7}
.cover-price-panel{position:relative;padding:17px;border-radius:20px;background:#173126;color:#fff;box-shadow:0 14px 32px rgba(23,49,38,.18)}.cover-price-label{display:block;font-size:9px;font-weight:900;letter-spacing:.08em;color:rgba(255,255,255,.65)}.cover-unit-line{display:flex;align-items:baseline;gap:5px;margin-top:3px}.cover-feature .featured-unit{font-size:40px;line-height:.95;color:#ffd66e;letter-spacing:-.055em}.cover-metric{font-size:10px;font-weight:850;color:rgba(255,255,255,.76)}
.cover-feature .featured-diff{margin-top:8px;color:#fff;font-size:11px}.cover-feature .featured-total{display:block;margin-top:5px;color:rgba(255,255,255,.68);font-size:10px}.cover-feature .featured-action{margin-top:13px}.cover-feature .featured-action .btn{width:100%;margin:0;background:#fff;color:#173126;box-shadow:none}.cover-feature .featured-action .btn:hover{background:#f5f8f6}
@media(max-width:759px){
  .featured.cover-feature{grid-template-columns:104px minmax(0,1fr);grid-template-areas:"media copy" "price price";gap:12px;padding:14px;border-radius:21px}
  .cover-media{grid-area:media;min-height:112px;border-radius:16px}.cover-feature .featured-img{width:100px;height:100px}.cover-copy{grid-area:copy}.cover-price-panel{grid-area:price;display:grid;grid-template-columns:minmax(0,1fr) auto;grid-template-areas:"label total" "unit total" "diff action";gap:2px 10px;padding:13px 14px;border-radius:16px}
  .cover-price-label{grid-area:label}.cover-unit-line{grid-area:unit}.cover-feature .featured-diff{grid-area:diff;margin-top:5px}.cover-feature .featured-total{grid-area:total;align-self:center;margin:0;text-align:right}.cover-feature .featured-action{grid-area:action;align-self:end;margin:0}.cover-feature .featured-action .btn{width:auto;min-width:106px;padding:9px 10px;font-size:10px}
  .cover-feature .featured-title{font-size:12px;margin-top:7px}.cover-feature .featured-shop{font-size:8px}.cover-reasons{gap:4px;margin-top:7px}.cover-reason{font-size:7px;padding:4px 6px}.cover-feature .featured-unit{font-size:31px}.cover-metric{font-size:8px}.cover-feature:before{font-size:7px;right:-37px;top:12px}
}
'''


def schema_script(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def shell(title, description, body, category_id="", schema=None):
    page_url = f"{BASE_URL}{'categories/'+category_id+'/' if category_id else ''}"
    schema_html = schema_script(schema) if schema else ""
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#197451"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{esc(page_url)}"><link rel="icon" href="{BASE_URL}assets/favicon.svg" type="image/svg+xml"><link rel="manifest" href="{BASE_URL}assets/site.webmanifest"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(page_url)}"><meta property="og:image" content="{BASE_URL}assets/hero-pet-comparison.webp"><meta property="og:image:alt" content="犬と猫がペット用品を比較するビジュアル"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(title)}"><meta name="twitter:description" content="{esc(description)}"><meta name="twitter:image" content="{BASE_URL}assets/hero-pet-comparison.webp">{schema_html}{analytics_head()}<style>{CSS}</style></head><body data-category-id="{esc(category_id)}" class="page-{esc(category_id or 'home')}">{body}</body></html>'''


def nav(categories, current=""):
    links = ''.join(
        f'<a class="chip{" current" if c["id"] == current else ""}" href="{BASE_URL}categories/{esc(c["id"])}/">{esc(c["emoji"])} {esc(c["name"])}</a>'
        for c in categories
    )
    return f'''<div class="topnav"><div class="wrap">
      <a class="brand" href="{BASE_URL}" aria-label="ペット用品コスパ比較 トップ"><img class="brand-logo" src="{BASE_URL}assets/pet-cost-logo.svg" alt="ペット用品コスパ比較"></a>
      {links}
    </div></div>'''


def mobile_dock(categories, current=""):
    home_class = " current" if not current else ""
    links = [f'<a class="dock-link{home_class}" href="{BASE_URL}"><span class="dock-icon">⌂</span><span>トップ</span></a>']
    for c in categories:
        active = " current" if c["id"] == current else ""
        links.append(
            f'<a class="dock-link{active}" href="{BASE_URL}categories/{esc(c["id"])}/">'
            f'<span class="dock-icon">{esc(c["emoji"])}</span><span>{esc(c["name"]).replace("猫用","")}</span></a>'
        )
    return '<nav class="mobile-dock" aria-label="モバイルナビ">' + ''.join(links) + '</nav>'


def group_label(category, group):
    return category.get("groups", {}).get(group, group or "条件")


def shipping_label(flag):
    value = str(flag)
    if value == "0":
        return "送料込み"
    if value == "1":
        return "送料別"
    return "送料は商品ページで確認"


def product_rows(items, category):
    cards = []
    for idx, item in enumerate(items, 1):
        image = esc(item.get("image", ""))
        image_html = (
            f'<img class="shop-card-image" src="{image}" alt="{esc(item["name"])}" loading="lazy" width="92" height="92">'
            if image else
            f'<div class="shop-card-image category-icon" aria-hidden="true">{esc(category["emoji"])}</div>'
        )
        label = group_label(category, item.get("group"))
        cards.append(
            f'''<article class="shop-card" data-product-row
                data-group="{esc(item['group'])}"
                data-row-unit-price="{item['unit_price']}"
                data-total-price="{item['price']}"
                data-quantity="{item['quantity']}"
                data-quantity-evidence="{esc(item['quantity_evidence'])}"
                data-image="{image}"
                data-item-id="{esc(item['product_id'])}"
                data-item-name="{esc(item['name'])}"
                data-shop="{esc(item.get('shop', ''))}"
                data-url="{esc(item['url'])}">
              <div class="rank-showcase-label" data-rank-showcase-label hidden></div>
              <div class="shop-card-image-wrap">
                {image_html}
                <span class="shop-card-rank"><span data-rank-cell>{idx}</span><span data-rank-badge style="display:none">{idx}位</span></span>
              </div>
              <div class="shop-card-prices">
                <div class="shop-unit-wrap"><div class="shop-unit-label">{esc(category['metric_label'])}あたり</div><div class="shop-unit">{yen(item['unit_price'])}<small> / {esc(category['metric_label'])}</small></div></div>
                <div class="shop-total"><span>購入総額</span><b>¥{item['price']:,}</b></div>
              </div>
              <div class="shop-card-head">
                <div class="value-badge-row" data-value-badges aria-label="価格特徴"></div>
                <div class="shop-card-title">{esc(item['name'])}</div>
                <div class="shop-card-shop">{esc(item.get('shop', ''))}</div>
                <div class="shop-card-tags"><span class="condition-tag">{esc(label)}</span><span class="condition-tag">{esc(item['quantity_evidence'])}</span></div>
              </div>
              <div class="shop-card-meta"><div class="price-diff" data-price-diff></div><div class="shipping">{esc(shipping_label(item.get('postage_flag')))}</div></div>
              <div class="shop-card-action">
                <a class="btn" data-affiliate-link
                  data-merchant="rakuten"
                  data-category-id="{esc(category['id'])}"
                  data-item-id="{esc(item['product_id'])}"
                  data-item-name="{esc(item['name'])}"
                  data-metric="{esc(category['metric'])}"
                  data-unit-price="{item['unit_price']}"
                  data-position="{idx}"
                  data-conversion-source="comparison_card"
                  href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener">楽天で価格を見る</a>
              </div>
            </article>'''
        )
    return ''.join(cards)


def visible_default_items(category, items):
    default_group = category.get("default_group", "all")
    if default_group == "all":
        return items
    return [x for x in items if x.get("group") == default_group]


def group_counts(category, items):
    counts = {}
    for item in items:
        counts[item.get("group", "unknown")] = counts.get(item.get("group", "unknown"), 0) + 1
    if "all" in category.get("groups", {}):
        counts["all"] = len(items)
    return counts


def filter_visual(category_id, key):
    visuals = {
        "pet-sheets": {
            "regular": ("▭", "標準サイズ"),
            "wide": ("▰", "広めサイズ"),
            "super_wide": ("▣", "大判サイズ"),
            "unknown": ("?", "サイズ不明"),
            "all": ("◎", "すべて表示"),
        },
        "cat-litter": {
            "all": ("◎", "素材を問わず"),
            "paper": ("▤", "紙系"),
            "okara": ("♧", "おから系"),
            "wood": ("▥", "木・ひのき"),
            "mineral": ("◆", "鉱物系"),
            "silica": ("✦", "シリカ系"),
            "mixed": ("◐", "複合素材"),
            "system": ("▱", "システム用"),
            "unknown": ("?", "素材不明"),
        },
        "system-toilet-sheets": {
            "all": ("◎", "すべて表示"),
            "deotoilet": ("D", "デオトイレ系"),
            "nyantomo": ("N", "ニャンとも系"),
            "iris": ("I", "アイリス系"),
            "universal": ("↔", "各社共通"),
            "unknown": ("?", "対応不明"),
        },
    }
    return visuals.get(category_id, {}).get(key, ("•", "条件別"))


def filter_buttons(category, items):
    counts = group_counts(category, items)
    default_group = category.get("default_group", "all")
    parts = []
    for key, label in category.get("groups", {}).items():
        count = counts.get(key, 0)
        if key != "all" and count <= 0:
            continue
        active = key == default_group
        icon, hint = filter_visual(category["id"], key)
        parts.append(
            f'''<button type="button" class="filter-chip{" active" if active else ""}"
              data-group-button data-group="{esc(key)}" data-group-label="{esc(label)}"
              aria-pressed="{"true" if active else "false"}">
              <span class="filter-icon" aria-hidden="true">{esc(icon)}</span>
              <span class="filter-label">{esc(label)}</span>
              <span class="filter-meta">{esc(hint)}</span>
              <span class="filter-count">{count}件</span>
            </button>'''
        )
    return ''.join(parts)


def featured_box(category, item):
    if not item:
        return '<div class="featured cover-feature" data-featured-box hidden></div>'

    image = esc(item.get("image", ""))
    image_html = (
        f'<img class="featured-img" data-featured-image src="{image}" alt="{esc(item["name"])}" width="156" height="156">'
        if image else
        f'<img class="featured-img" data-featured-image alt="" width="156" height="156" hidden>'
    )
    return f'''<div class="featured cover-feature" data-featured-box>
      <div class="cover-media">{image_html}</div>
      <div class="cover-copy">
        <div class="cover-kicker">CURRENT LOWEST</div>
        <span class="featured-crown" aria-hidden="true">♛</span><span class="featured-badge" data-featured-badge>この条件の1位</span>
        <div class="featured-title" data-featured-title>{esc(item['name'])}</div>
        <div class="featured-shop" data-featured-shop>{esc(item.get('shop', ''))}</div>
        <div class="cover-reasons" data-featured-reasons aria-label="安さの理由"></div>
      </div>
      <div class="cover-price-panel">
        <span class="cover-price-label">{esc(category['metric_label'])}あたり</span>
        <div class="cover-unit-line"><span class="featured-unit" data-featured-unit>{yen(item['unit_price'])}</span><span class="cover-metric">/ {esc(category['metric_label'])}</span></div>
        <div class="featured-diff" data-featured-diff></div>
        <span class="featured-total" data-featured-total>総額 {yen(item['price'])}</span>
        <div class="featured-action">
          <a class="btn" data-affiliate-link
            data-merchant="rakuten"
            data-category-id="{esc(category['id'])}"
            data-item-id="{esc(item['product_id'])}"
            data-item-name="{esc(item['name'])}"
            data-metric="{esc(category['metric'])}"
            data-unit-price="{item['unit_price']}"
            data-position="1"
            data-conversion-source="featured_product"
            href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener">楽天で価格を見る →</a>
        </div>
      </div>
    </div>'''


def snapshot_cards(category, items):
    cards = []
    for idx, item in enumerate(items[:3], 1):
        image = esc(item.get("image", ""))
        image_html = (
            f'<img class="top3-img" src="{image}" alt="" loading="lazy" width="50" height="50">'
            if image else
            f'<div class="top3-img" aria-hidden="true"></div>'
        )
        cards.append(
            f'''<a class="top3-card" data-top3-card data-affiliate-link
              data-merchant="rakuten"
              data-category-id="{esc(category['id'])}"
              data-item-id="{esc(item['product_id'])}"
              data-item-name="{esc(item['name'])}"
              data-metric="{esc(category['metric'])}"
              data-unit-price="{item['unit_price']}"
              data-position="{idx}"
              data-conversion-source="top3_snapshot"
              href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener">
              <span class="top3-rank">{idx}</span>
              {image_html}
              <span class="top3-copy">
                <span class="top3-name">{esc(item['name'])}</span>
                <span class="top3-unit">{yen(item['unit_price'])}<small> / {esc(category['metric_label'])}</small></span>
                <span class="top3-total">総額 {yen(item['price'])}</span>
              </span>
            </a>'''
        )
    return ''.join(cards)


def angle_picks(items):
    if not items:
        return []
    return [
        ("unit", "💰", "単価最安", min(items, key=lambda x: (x["unit_price"], x["price"]))),
        ("total", "🧾", "支払総額が最小", min(items, key=lambda x: (x["price"], x["unit_price"]))),
        ("bulk", "📦", "最大容量", max(items, key=lambda x: (x["quantity"], -x["unit_price"]))),
    ]


def angle_cards(category, items):
    cards = []
    for role, icon, label, item in angle_picks(items):
        if role == "unit":
            value = f"{yen(item['unit_price'])} / {category['metric_label']}"
        elif role == "total":
            value = yen(item["price"])
        else:
            value = item["quantity_evidence"]
        cards.append(
            f'''<a class="angle-card" data-angle-card data-angle-role="{role}" data-affiliate-link
              data-merchant="rakuten"
              data-category-id="{esc(category['id'])}"
              data-item-id="{esc(item['product_id'])}"
              data-item-name="{esc(item['name'])}"
              data-metric="{esc(category['metric'])}"
              data-unit-price="{item['unit_price']}"
              data-position="0"
              data-conversion-source="comparison_angle_{role}"
              href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener">
              <span class="angle-icon">{icon}</span>
              <span class="angle-label">{label}</span>
              <span class="angle-value">{esc(value)}</span>
              <span class="angle-name">{esc(item['name'])}</span>
              <span class="angle-cta">楽天で確認 →</span>
            </a>'''
        )
    return ''.join(cards)


def guide_html(category):
    items = ''.join(
        f'<div class="guide-item"><span class="guide-check">✓</span><span>{esc(text)}</span></div>'
        for text in category.get("guide", [])
    )
    return f'<div class="guide-grid">{items}</div>'


def faq_html(category):
    items = ''.join(
        f'<details><summary>{esc(item["q"])}</summary><p>{esc(item["a"])}</p></details>'
        for item in category.get("faq", [])
    )
    return f'<div class="faq">{items}</div>'


def footer():
    return f'''<footer class="footer"><div class="wrap footer-box">
      <div class="footer-brand"><img class="footer-logo" src="{BASE_URL}assets/pet-cost-logo.svg" alt="ペット用品コスパ比較"></div>
      <div>当サイトはアフィリエイト広告を利用しています。価格・在庫・送料・商品仕様は取得後に変更される場合があるため、購入前に楽天市場の商品ページでご確認ください。</div>
      <div class="rakuten-credit">
        <!-- Rakuten Web Services Attribution Snippet FROM HERE -->
        <a href="https://developers.rakuten.com/" target="_blank">Supported by Rakuten Developers</a>
        <!-- Rakuten Web Services Attribution Snippet TO HERE -->
      </div>
    </div></footer>'''


def relative_price_label(value, median):
    if not value or not median or median <= 0:
        return "-"
    diff = (value - median) / median * 100
    if abs(diff) < 2:
        return "中央値付近"
    if diff < 0:
        return f"中央値より{abs(diff):.0f}%安い"
    return f"中央値より{diff:.0f}%高い"


def category_page(category, items, categories, updated):
    initial_items = visible_default_items(category, items)
    initial_prices = sorted(x["unit_price"] for x in initial_items)
    initial_median = initial_prices[len(initial_prices) // 2] if initial_prices else None
    initial_min = initial_prices[0] if initial_prices else None
    initial_gap = relative_price_label(initial_min, initial_median)
    default_label = group_label(category, category.get("default_group", "all"))
    featured = initial_items[0] if initial_items else None

    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "トップ", "item": BASE_URL},
            {
                "@type": "ListItem",
                "position": 2,
                "name": category["name"],
                "item": f"{BASE_URL}categories/{category['id']}/",
            },
        ],
    }

    body = f'''<header class="hero category-hero"><div class="wrap hero-inner">
      <div class="hero-copy">
        <span class="hero-kicker"><span class="dot"></span>条件が曖昧な商品は載せない</span>
        <h1 class="category-hero-title"><span class="category-name">{esc(category['name'])}</span><span class="category-question">いま安いのは？</span></h1>
        <p class="lead">{esc(category['intro'])}</p>
        <div class="trust-row"><span class="trust-pill">毎朝自動更新</span><span class="trust-pill">数量根拠つき</span><span class="trust-pill">公開前に自動監査</span></div>
        <p class="updated">最終更新 {esc(updated)}</p>
      </div>
      <div class="hero-art-shell"><div class="hero-art">{category_illustration(category['id'])}</div></div>
    </div></header>
    {nav(categories, category['id'])}
    <main class="main"><div class="wrap">
      <aside class="comparison-sticky" data-comparison-sticky aria-label="現在の比較条件">
        <div class="comparison-sticky-inner">
          <div class="sticky-cell"><span class="sticky-label">比較条件</span><strong class="sticky-value" data-sticky-condition>{esc(default_label)}</strong></div>
          <div class="sticky-cell sticky-price"><span class="sticky-label">現在最安</span><strong class="sticky-value" data-sticky-min>{yen(initial_min)} / {esc(category['metric_label'])}</strong></div>
          <div class="sticky-cell sticky-gap"><span class="sticky-label">中央値との差</span><strong class="sticky-value" data-sticky-gap>{esc(initial_gap)}</strong></div>
          <div class="sticky-cell sticky-count"><span class="sticky-label">表示</span><strong class="sticky-value" data-sticky-count>{len(initial_items)}件</strong></div>
          <a class="sticky-jump" href="#product-ranking" aria-label="商品ランキングへ移動">一覧へ</a>
        </div>
      </aside>
      <section class="section condition-panel">
        <div class="section-head"><div><h2>条件を選ぶ</h2><p class="section-sub">サイズ・素材・互換性をそろえると、比較がもっと正確になります。</p><span class="condition-current" data-current-condition>{esc(default_label)}</span></div><strong data-visible-count>{len(initial_items)}件</strong></div>
        <div class="filter-wrap"><div class="filters" data-group-filter data-rank-all="{1 if category.get('rank_all') else 0}">{filter_buttons(category, items)}</div></div>
        <div class="filter-help">横にスワイプして条件を変更できます。選ぶと最安・TOP3・商品一覧も同時に更新します。</div>
        {featured_box(category, featured)}

        <section class="section snapshot-section">
          <div class="section-head"><div><h2 class="podium-title">上位3商品をひと目で <span>TOP 3</span></h2><p class="section-sub">いま選んでいる条件の上位候補と、最安が中央値からどれくらい離れているかを表示します。</p></div></div>
          <div class="deal-meter">
            <div class="deal-meter-head"><span>この条件の最安ポジション</span><b data-deal-message>価格差を計算中</b></div>
            <div class="deal-track"><span class="deal-dot" data-deal-dot></span></div>
            <div class="deal-scale"><span>かなり安い</span><span>中央値</span><span>高め</span></div>
          </div>
          <div class="top3-strip" data-top3-strip>{snapshot_cards(category, initial_items)}</div>
          <div class="podium-foot" aria-hidden="true"></div>
          <div class="snapshot-note">※ 同じ条件内の現在掲載商品の単価を比較した目安です。過去価格との比較ではありません。</div>
        </section>

        <div class="angle-panel">
          <div class="angle-head"><div><h3>「安い」を3つの角度で見る</h3><p>単価・支払総額・容量を分けて表示します。</p></div></div>
          <div class="angle-grid" data-angle-grid>{angle_cards(category, initial_items)}</div>
          <div class="angle-note">※ 品質や性能のおすすめではなく、現在掲載データの数値だけで選んでいます。同じ商品が複数の条件に該当する場合があります。</div>
        </div>

        <div class="kpi">
          <div class="kpi-card"><span>全掲載商品</span><b>{len(items)}件</b></div>
          <div class="kpi-card"><span>この条件</span><b data-stat-count>{len(initial_items)}件</b></div>
          <div class="kpi-card"><span>最安単価</span><b data-stat-min>{yen(initial_prices[0]) if initial_prices else '-'}</b></div>
          <div class="kpi-card"><span>中央値</span><b data-stat-median>{yen(initial_median)}</b></div>
        </div>
      </section>

      <section class="section" id="product-ranking">
        <div class="section-head"><div><h2>安い順に比較</h2><p class="section-sub">{esc(default_label)}から表示。画像・総額・単価に加えて、安さの理由も自動表示します。</p></div></div>
        <div class="value-legend" aria-label="安さの理由"><span><i class="u"></i>単価最安</span><span><i class="d"></i>中央値より安い</span><span><i class="t"></i>支払総額が最小</span><span><i class="b"></i>最大容量</span></div>
        <div class="product-grid" data-product-grid>{product_rows(items, category) if items else '<div class="product-empty">安全に単価計算できる商品がまだありません。</div>'}</div>
      </section>

      <section class="section">
        <div class="section-head"><div><h2>比較するときのポイント</h2><p class="section-sub">安さだけで決めて失敗しないための最低限の確認です。</p></div></div>
        {guide_html(category)}
      </section>

      <section class="section">
        <div class="section-head"><div><h2>店頭価格も比べる</h2><p class="section-sub">ホームセンターやドラッグストアの価格を同じ単位に直します。</p></div></div>
        <div class="calculator">
          <div class="calc-inputs">
            <input class="input" data-calc-price inputmode="decimal" placeholder="総額（円）" aria-label="店頭商品の総額">
            <input class="input" data-calc-qty inputmode="decimal" placeholder="数量（{esc(category['metric_label'].replace('1',''))}）" aria-label="店頭商品の数量">
          </div>
          <button class="btn secondary" data-calc-button type="button">この価格を比較する</button>
          <div data-calc-result class="note" style="display:none"></div>
        </div>
      </section>

      <section class="section">
        <div class="section-head"><div><h2>このランキングの作り方</h2></div></div>
        <p class="method">楽天市場の商品情報から、商品名に明記された容量・枚数だけを使って「総額 ÷ 総容量（または総枚数）」を計算しています。</p>
        <ul class="method method-list">
          <li>複数サイズ・容量から選ぶ商品は、比較対象が一意に決まらなければ除外</li>
          <li>kgしかない猫砂はLへ推測換算しない</li>
          <li>中古・訳あり・定期便・ふるさと納税など通常比較に向かない商品は除外</li>
          <li>同じ商品が販売店違い・セット数違いで順位を占有しないよう整理</li>
        </ul>
        <div class="note">この順位は「価格の安さ」の比較です。吸収力、消臭力、原材料、ペットとの相性などの品質順位ではありません。</div>
      </section>

      <section class="section">
        <div class="section-head"><div><h2>よくある質問</h2></div></div>
        {faq_html(category)}
      </section>
    </div></main>
    {footer()}
    {mobile_dock(categories, category['id'])}'''

    title = f"{category['name']}はどれが安い？{category['metric_label']}あたりで比較 | {SITE_NAME}"
    desc = f"{category['name']}を{category['metric_label']}あたりに換算して安い順に比較。数量が曖昧な商品は除外し、条件別の最安値・総額・数量根拠まで確認できます。"
    return shell(title, desc, body, category['id'], breadcrumb_schema)


def deal_percent(min_price, median_price):
    if not min_price or not median_price or median_price <= 0:
        return 0
    return max(0, round((median_price - min_price) / median_price * 100))


def daily_spotlight(categories, summaries):
    candidates = []
    for category in categories:
        summary = summaries.get(category["id"], {})
        best = summary.get("best")
        if not best:
            continue
        gap = summary.get("deal_percent", 0)
        candidates.append((gap, category, summary))

    if not candidates:
        return ""

    candidates.sort(key=lambda x: (x[0], x[2].get("default_count", 0)), reverse=True)
    gap, category, summary = candidates[0]
    best = summary["best"]
    image = esc(best.get("image", ""))
    visual = (
        f'<img class="spotlight-image" src="{image}" alt="{esc(best["name"])}" loading="eager">'
        if image else
        f'<div class="spotlight-category-art">{category_illustration(category["id"])}</div>'
    )

    chips = []
    for item_gap, item_category, item_summary in candidates:
        chips.append(
            f'''<a class="gap-chip" href="{BASE_URL}categories/{esc(item_category['id'])}/">
              <span>{esc(item_category['name'])}<br>{esc(item_summary['default_label'])}</span>
              <b>{item_gap}%差</b>
            </a>'''
        )

    gap_text = f"{gap}%" if gap > 0 else "ほぼ同水準"
    return f'''<section class="section daily-spotlight" data-daily-spotlight>
      <div class="spotlight-inner">
        <div>
          <div class="spotlight-kicker">TODAY'S PRICE GAP</div>
          <h2>今日の価格差</h2>
          <p class="spotlight-copy"><strong>{esc(category['name'])}・{esc(summary['default_label'])}</strong>で、現在掲載中の商品を同じ単位にそろえて比較しました。</p>
          <div class="spotlight-gap"><b>{esc(gap_text)}</b><span>中央値より最安が低い</span></div>
          <div class="spotlight-price-row">
            <div class="spotlight-price"><span>現在の最安</span><b>{yen(summary['min'])} / {esc(category['metric_label'])}</b></div>
            <div class="spotlight-price"><span>掲載中央値</span><b>{yen(summary.get('median'))} / {esc(category['metric_label'])}</b></div>
          </div>
          <a class="spotlight-action" data-spotlight-link data-category-id="{esc(category['id'])}" data-gap-percent="{gap}" href="{BASE_URL}categories/{esc(category['id'])}/">この比較を見る →</a>
          <div class="gap-strip">{''.join(chips)}</div>
          <div class="spotlight-note">※ 過去価格との比較ではなく、本日取得した現在掲載商品の中での最安値と中央値の差です。</div>
        </div>
        <div class="spotlight-product">
          {visual}
          <div>
            <div class="spotlight-product-name">{esc(best['name'])}</div>
            <div class="spotlight-product-meta">{esc(best.get('shop', ''))} ・ 総額 {yen(best['price'])}</div>
          </div>
        </div>
      </div>
    </section>'''


def homepage(categories, summaries, updated):
    ranked_categories = sorted(
        categories,
        key=lambda category: (
            summaries.get(category["id"], {}).get("deal_percent", 0),
            summaries.get(category["id"], {}).get("total_count", 0),
        ),
        reverse=True,
    )
    lead = ranked_categories[0] if ranked_categories else None
    side_categories = ranked_categories[1:3]
    lead_html = ""
    side_html = []

    if lead:
        s = summaries[lead["id"]]
        gap = s.get("deal_percent", 0)
        lead_html = f'''<a class="editorial-lead {category_theme(lead['id'])}" data-editorial-category="{esc(lead['id'])}" data-editorial-position="1" href="{BASE_URL}categories/{esc(lead['id'])}/">
          <div class="editorial-lead-copy">
            <span class="editorial-index">01 / TODAY'S LEAD</span>
            <h3>{esc(lead['name'])}</h3>
            <div class="editorial-lead-sub">{esc(s['default_label'])}を同じ単位で比較 ・ 掲載 {s['total_count']}件</div>
            <div class="editorial-price-block">
              <span class="editorial-price-caption">{esc(s['default_label'])}の現在最安</span>
              <strong class="editorial-price">{yen(s['min'])}<small> / {esc(lead['metric_label'])}</small></strong>
              <span class="editorial-gap">{esc(relative_price_label(s.get('min'), s.get('median')))}</span>
            </div>
          </div>
          <div class="editorial-lead-art">{category_illustration(lead['id'])}</div>
          <span class="editorial-arrow" aria-hidden="true">→</span>
        </a>'''

    for index, category in enumerate(side_categories, 2):
        s = summaries[category["id"]]
        side_html.append(
            f'''<a class="editorial-side-card {category_theme(category['id'])}" data-editorial-category="{esc(category['id'])}" data-editorial-position="{index}" href="{BASE_URL}categories/{esc(category['id'])}/">
              <span class="editorial-folio">0{index}</span>
              <div>
                <span class="editorial-index">{esc(s['default_label'])}</span>
                <h3>{esc(category['name'])}</h3>
                <div class="editorial-side-price">{yen(s['min'])}<small> / {esc(category['metric_label'])}</small></div>
                <div class="editorial-side-meta">{esc(relative_price_label(s.get('min'), s.get('median')))} ・ 掲載{s['total_count']}件</div>
              </div>
              <div class="editorial-side-art">{category_illustration(category['id'])}</div>
            </a>'''
        )

    while len(side_html) < 2:
        side_html.append('<div class="editorial-side-card" aria-hidden="true"></div>')

    website_schema = {
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": BASE_URL,
        "description": "ペット用品を1枚・1Lなど同じ単位に揃えて比較するサイト",
    }

    body = f'''<header class="hero"><div class="wrap hero-inner">
      <div class="hero-copy">
        <span class="hero-kicker"><span class="dot"></span>毎日更新・登録不要</span>
        <h1 class="home-hero-title"><span class="hero-title-top">ペット用品の</span><span class="hero-title-main">ほんとの安さ</span><span class="hero-title-bottom">を、ひと目で。</span></h1>
        <p class="lead">袋の値段ではなく、<span class="hero-lead-mark">1枚・1Lなど同じ単位</span>にそろえて比較。犬と猫の毎日に、迷わない価格比較を。</p>
        <div class="hero-proof"><div class="hero-proof-item"><b>1枚</b><span>シーツを比較</span></div><div class="hero-proof-item"><b>1L</b><span>猫砂を比較</span></div><div class="hero-proof-item"><b>毎朝</b><span>価格を更新</span></div></div>
        <div class="trust-row"><span class="trust-pill">✓ サイズ別</span><span class="trust-pill">✓ 推測換算なし</span><span class="trust-pill">✓ 曖昧商品は除外</span></div>
        <p class="updated">最終更新 {esc(updated)}</p>
      </div>
      <div class="hero-art-shell photo-shell">{hero_illustration()}</div>
    </div></header>
    {nav(categories)}
    <main class="main"><div class="wrap">
      <section class="section editorial-section">
        <div class="editorial-head">
          <div class="editorial-head-copy"><span class="editorial-eyebrow">TODAY'S PET COST EDITION</span><h2>今日、まず見る3つ。</h2><p class="section-sub">現在掲載中の商品だけで比較し、平均との差が大きいカテゴリを主役にしています。</p></div>
          <div class="editorial-date">DAILY PRICE EDITION<br>{esc(updated)}</div>
        </div>
        <div class="editorial-grid">
          {lead_html}
          <div class="editorial-side">{''.join(side_html)}</div>
        </div>
        <div class="editorial-footerline"><span><strong>編集ルール：</strong>過去価格ではなく、同じ条件の現在掲載商品内で比較。</span><span>数量が曖昧な商品は掲載しません。</span></div>
      </section>

      {daily_spotlight(categories, summaries)}

      <section class="section story-section">
        <div class="section-head"><div><h2>使い方は3ステップ</h2></div></div>
        <div class="steps">
          <div class="step">{step_illustration(1)}<div class="step-num">1</div><div><b>用品を選ぶ</b><span>ペットシーツ・猫砂・システムトイレシートから選択。</span></div></div>
          <div class="step">{step_illustration(2)}<div class="step-num">2</div><div><b>条件をそろえる</b><span>サイズ・素材・互換性を選び、同じ条件だけを見る。</span></div></div>
          <div class="step">{step_illustration(3)}<div class="step-num">3</div><div><b>単価と総額を見る</b><span>最安単価だけでなく、実際に払う総額も一緒に確認。</span></div></div>
        </div>
      </section>

      <section class="section trust-section">
        <div class="section-head"><div><h2>「安い」を雑に作らない</h2><p class="section-sub">件数より、間違った1位を出さないことを優先します。</p></div></div>
        <div class="guide-grid">
          <div class="guide-item"><span class="guide-check">✓</span><span>選択式で数量が確定しない商品は除外します。</span></div>
          <div class="guide-item"><span class="guide-check">✓</span><span>別カテゴリ・中古・訳あり・定期便などはランキング対象外です。</span></div>
          <div class="guide-item"><span class="guide-check">✓</span><span>毎回の更新後に単価・分類・URL・重複を自動監査してから公開します。</span></div>
        </div>
      </section>

      <section class="section store-section">
        <div class="section-head"><div><h2>店頭でも使える</h2></div></div>
        <p class="method">各比較ページには単価計算機があります。ホームセンターで「これ安い？」と思ったとき、価格と枚数・容量を入れれば、現在の楽天候補と同じ単位で比べられます。</p>
      </section>
    </div></main>
    {footer()}
    {mobile_dock(categories)}'''

    return shell(
        f"{SITE_NAME} | 1枚・1Lあたりで安さを比較",
        "ペットシーツ、猫砂、猫用システムトイレシートを1枚・1Lあたりの単価に揃えて比較。数量が曖昧な商品は除外し、条件別に安い商品を確認できます。",
        body,
        schema=website_schema,
    )


def write_text(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def copy_static_verification_files():
    for source in ROOT.glob("google*.html"):
        shutil.copy2(source, SITE / source.name)
    assets = ROOT / "assets"
    if assets.exists():
        shutil.copytree(assets, SITE / "assets", dirs_exist_ok=True)


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
            raw = load_fixture(category["id"])
        else:
            raw = []
            for keyword in category.get("keywords", [category.get("keyword", "")]):
                if keyword:
                    raw.extend(fetch_items(keyword, pages=int(category.get("pages_per_keyword", 1))))

        ranked = choose_ranked(raw, category)
        out_dir = SITE / "categories" / category["id"]
        write_text(out_dir / "index.html", category_page(category, ranked, categories, updated))
        write_text(
            SITE / "data" / f"{category['id']}.json",
            json.dumps(
                {"updated": updated, "category": category, "items": ranked},
                ensure_ascii=False,
                indent=2,
            ),
        )

        initial_items = visible_default_items(category, ranked)
        initial_prices = sorted(x["unit_price"] for x in initial_items)
        min_price = initial_prices[0] if initial_prices else None
        median_price = initial_prices[len(initial_prices) // 2] if initial_prices else None
        summaries[category["id"]] = {
            "total_count": len(ranked),
            "default_count": len(initial_items),
            "min": min_price,
            "median": median_price,
            "deal_percent": deal_percent(min_price, median_price),
            "best": initial_items[0] if initial_items else None,
            "default_label": group_label(category, category.get("default_group", "all")),
        }

    write_text(SITE / "index.html", homepage(categories, summaries, updated))
    write_text(
        SITE / "robots.txt",
        f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}sitemap.xml\n",
    )

    urls = [BASE_URL] + [f"{BASE_URL}categories/{c['id']}/" for c in categories]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + ''.join(f"<url><loc>{u}</loc></url>" for u in urls)
        + "</urlset>"
    )
    write_text(SITE / "sitemap.xml", sitemap)
    copy_static_verification_files()
    print(f"Built {len(categories)} category pages in {SITE}")


if __name__ == "__main__":
    main()
