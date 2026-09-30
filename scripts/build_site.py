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
        return '''<svg viewBox="0 0 300 150" role="img" aria-label="ペットシーツのイラスト"><ellipse cx="151" cy="131" rx="112" ry="10" fill="#bddfca" opacity=".45"/><rect x="66" y="72" width="170" height="58" rx="16" fill="#fff" stroke="#93c9ac" stroke-width="3"/><path d="M88 91h126M88 106h98" stroke="#d7ebe0" stroke-width="7" stroke-linecap="round"/><g transform="translate(104 16)"><circle cx="47" cy="42" r="35" fill="#e9b17f"/><path d="M18 22 6 2l31 13M76 22 89 2 59 14" fill="#b8754a"/><circle cx="35" cy="38" r="4" fill="#173126"/><circle cx="59" cy="38" r="4" fill="#173126"/><ellipse cx="47" cy="49" rx="5" ry="4" fill="#173126"/></g><circle cx="236" cy="54" r="27" fill="#ffcf62"/><path d="m236 35 5 10 11 2-8 8 2 11-10-5-10 5 2-11-8-8 11-2z" fill="#fff5d6"/></svg>'''
    if category_id == "cat-litter":
        return '''<svg viewBox="0 0 300 150" role="img" aria-label="猫砂のイラスト"><ellipse cx="151" cy="132" rx="105" ry="10" fill="#e8d7ad" opacity=".55"/><path d="M68 79q0-22 22-22h123q22 0 22 22v38H68z" fill="#fff" stroke="#d8bd78" stroke-width="3"/><path d="M83 84h137l-10 31H93z" fill="#ead7aa"/><g fill="#c6a85d"><circle cx="107" cy="96" r="4"/><circle cx="128" cy="105" r="4"/><circle cx="153" cy="94" r="4"/><circle cx="180" cy="105" r="4"/><circle cx="201" cy="96" r="4"/></g><g transform="translate(112 12)"><circle cx="40" cy="40" r="34" fill="#9eb8be"/><path d="M13 20 17 0l20 15M67 20 64 0 44 15" fill="#708e97"/><circle cx="29" cy="37" r="4" fill="#173126"/><circle cx="52" cy="37" r="4" fill="#173126"/><path d="m40 46-5 4h10z" fill="#e59a95"/></g><rect x="218" y="37" width="48" height="28" rx="8" fill="#ffce62"/><text x="232" y="56" font-size="15" font-family="sans-serif" font-weight="900" fill="#6d5200">1L</text></svg>'''
    return '''<svg viewBox="0 0 300 150" role="img" aria-label="システムトイレシートのイラスト"><ellipse cx="150" cy="132" rx="106" ry="10" fill="#bcdde3" opacity=".55"/><rect x="65" y="66" width="170" height="62" rx="18" fill="#fff" stroke="#8cc7d0" stroke-width="3"/><rect x="78" y="83" width="144" height="29" rx="9" fill="#dff3f6"/><path d="M93 97h113" stroke="#9ed5dc" stroke-width="5" stroke-linecap="round"/><g transform="translate(112 9)"><circle cx="40" cy="40" r="34" fill="#98b6bd"/><path d="M13 20 17 0l20 15M67 20 64 0 44 15" fill="#6e8e96"/><circle cx="29" cy="37" r="4" fill="#173126"/><circle cx="52" cy="37" r="4" fill="#173126"/><path d="m40 46-5 4h10z" fill="#e59a95"/></g><circle cx="238" cy="52" r="27" fill="#5db7c4"/><path d="m226 53 8 8 16-19" fill="none" stroke="#fff" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'''


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


def schema_script(data):
    return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'


def shell(title, description, body, category_id="", schema=None):
    page_url = f"{BASE_URL}{'categories/'+category_id+'/' if category_id else ''}"
    schema_html = schema_script(schema) if schema else ""
    return f'''<!doctype html><html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#197451"><title>{esc(title)}</title><meta name="description" content="{esc(description)}"><meta name="robots" content="index,follow"><link rel="canonical" href="{esc(page_url)}"><meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(page_url)}">{schema_html}{analytics_head()}<style>{CSS}</style></head><body data-category-id="{esc(category_id)}">{body}</body></html>'''


def nav(categories):
    links = ''.join(
        f'<a class="chip" href="{BASE_URL}categories/{esc(c["id"])}/">{esc(c["emoji"])} {esc(c["name"])}</a>'
        for c in categories
    )
    return f'<div class="topnav"><div class="wrap"><a class="brand" href="{BASE_URL}">{SITE_NAME}</a>{links}</div></div>'


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
    rows = []
    for idx, item in enumerate(items, 1):
        image = esc(item.get("image", ""))
        image_html = (
            f'<img class="product-image" src="{image}" alt="{esc(item["name"])}" loading="lazy" width="64" height="64">'
            if image else
            f'<div class="category-icon" aria-hidden="true">{esc(category["emoji"])}</div>'
        )
        label = group_label(category, item.get("group"))
        rows.append(
            f'''<tr data-product-row
                data-group="{esc(item['group'])}"
                data-row-unit-price="{item['unit_price']}"
                data-total-price="{item['price']}"
                data-image="{image}"
                data-item-id="{esc(item['product_id'])}"
                data-item-name="{esc(item['name'])}"
                data-shop="{esc(item.get('shop', ''))}"
                data-url="{esc(item['url'])}">
              <td class="rank"><span class="rank-number" data-rank-cell>{idx}</span><span class="rank-badge" data-rank-badge>{idx}位</span></td>
              <td class="image-cell">{image_html}</td>
              <td class="product">
                <div><span class="condition-tag">{esc(label)}</span><span class="condition-tag">{esc(item['quantity_evidence'])}</span></div>
                <div class="product-title">{esc(item['name'])}</div>
                <div class="meta">{esc(item.get('shop', ''))}</div>
              </td>
              <td class="total">¥{item['price']:,}</td>
              <td class="unit">{yen(item['unit_price'])}<div class="meta">/{esc(category['metric_label'])}</div><div class="price-diff" data-price-diff></div></td>
              <td class="action">
                <a class="btn" data-affiliate-link
                  data-merchant="rakuten"
                  data-category-id="{esc(category['id'])}"
                  data-item-id="{esc(item['product_id'])}"
                  data-item-name="{esc(item['name'])}"
                  data-metric="{esc(category['metric'])}"
                  data-unit-price="{item['unit_price']}"
                  data-position="{idx}"
                  data-conversion-source="comparison_table"
                  href="{esc(item['url'])}" target="_blank" rel="nofollow sponsored noopener">楽天で価格を見る →</a>
                <div class="shipping">{esc(shipping_label(item.get('postage_flag')))}</div>
              </td>
            </tr>'''
        )
    return ''.join(rows)


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


def filter_buttons(category, items):
    counts = group_counts(category, items)
    default_group = category.get("default_group", "all")
    parts = []
    for key, label in category.get("groups", {}).items():
        count = counts.get(key, 0)
        if key != "all" and count <= 0:
            continue
        active = key == default_group
        parts.append(
            f'<button type="button" class="filter-chip{" active" if active else ""}" '
            f'data-group-button data-group="{esc(key)}" aria-pressed="{"true" if active else "false"}">'
            f'{esc(label)} <span>{count}</span></button>'
        )
    return ''.join(parts)


def featured_box(category, item):
    if not item:
        return '<div class="featured" data-featured-box hidden></div>'

    image = esc(item.get("image", ""))
    image_html = (
        f'<img class="featured-img" data-featured-image src="{image}" alt="{esc(item["name"])}" width="120" height="120">'
        if image else
        f'<img class="featured-img" data-featured-image alt="" width="120" height="120" hidden>'
    )
    return f'''<div class="featured" data-featured-box>
      <div>{image_html}</div>
      <div>
        <span class="featured-crown" aria-hidden="true">♛</span><span class="featured-badge" data-featured-badge>この条件の1位</span>
        <div class="featured-title" data-featured-title>{esc(item['name'])}</div>
        <div class="featured-shop" data-featured-shop>{esc(item.get('shop', ''))}</div>
        <div class="featured-price"><span class="featured-unit" data-featured-unit>{yen(item['unit_price'])}</span><span class="featured-total" data-featured-total>総額 {yen(item['price'])}</span></div><div class="featured-diff" data-featured-diff></div>
      </div>
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
      <div>当サイトはアフィリエイト広告を利用しています。価格・在庫・送料・商品仕様は取得後に変更される場合があるため、購入前に楽天市場の商品ページでご確認ください。</div>
      <div class="rakuten-credit">
        <!-- Rakuten Web Services Attribution Snippet FROM HERE -->
        <a href="https://developers.rakuten.com/" target="_blank">Supported by Rakuten Developers</a>
        <!-- Rakuten Web Services Attribution Snippet TO HERE -->
      </div>
    </div></footer>'''


def category_page(category, items, categories, updated):
    initial_items = visible_default_items(category, items)
    initial_prices = sorted(x["unit_price"] for x in initial_items)
    initial_median = initial_prices[len(initial_prices) // 2] if initial_prices else None
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
        <h1>{esc(category['name'])}<br>いま安いのは？</h1>
        <p class="lead">{esc(category['intro'])}</p>
        <div class="trust-row"><span class="trust-pill">毎朝自動更新</span><span class="trust-pill">数量根拠つき</span><span class="trust-pill">公開前に自動監査</span></div>
        <p class="updated">最終更新 {esc(updated)}</p>
      </div>
      <div class="hero-art-shell"><div class="hero-art">{category_illustration(category['id'])}</div></div>
    </div></header>
    {nav(categories)}
    <main class="main"><div class="wrap">
      <section class="section">
        <div class="section-head"><div><h2>条件を選ぶ</h2><p class="section-sub">いま選んでいる条件だけで順位・最安値を更新します。</p></div><strong data-visible-count>{len(initial_items)}件</strong></div>
        <div class="filter-wrap"><div class="filters" data-group-filter data-rank-all="{1 if category.get('rank_all') else 0}">{filter_buttons(category, items)}</div></div>
        {featured_box(category, featured)}

        <section class="section snapshot-section">
          <div class="section-head"><div><h2>上位3商品をひと目で</h2><p class="section-sub">いま選んでいる条件の上位候補と、最安が中央値からどれくらい離れているかを表示します。</p></div></div>
          <div class="deal-meter">
            <div class="deal-meter-head"><span>この条件の最安ポジション</span><b data-deal-message>価格差を計算中</b></div>
            <div class="deal-track"><span class="deal-dot" data-deal-dot></span></div>
            <div class="deal-scale"><span>かなり安い</span><span>中央値</span><span>高め</span></div>
          </div>
          <div class="top3-strip" data-top3-strip>{snapshot_cards(category, initial_items)}</div>
          <div class="snapshot-note">※ 同じ条件内の現在掲載商品の単価を比較した目安です。過去価格との比較ではありません。</div>
        </section>

        <div class="kpi">
          <div class="kpi-card"><span>全掲載商品</span><b>{len(items)}件</b></div>
          <div class="kpi-card"><span>この条件</span><b data-stat-count>{len(initial_items)}件</b></div>
          <div class="kpi-card"><span>最安単価</span><b data-stat-min>{yen(initial_prices[0]) if initial_prices else '-'}</b></div>
          <div class="kpi-card"><span>中央値</span><b data-stat-median>{yen(initial_median)}</b></div>
        </div>
      </section>

      <section class="section">
        <div class="section-head"><div><h2>安い順に比較</h2><p class="section-sub">{esc(default_label)}から表示。画像・総額・単価を一緒に確認できます。</p></div></div>
        <div class="table-wrap"><table class="compare">
          <thead><tr><th>順</th><th></th><th>商品</th><th>総額</th><th>単価</th><th>確認</th></tr></thead>
          <tbody>{product_rows(items, category) if items else '<tr><td colspan="6" class="empty">安全に単価計算できる商品がまだありません。</td></tr>'}</tbody>
        </table></div>
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
    {footer()}'''

    title = f"{category['name']}はどれが安い？{category['metric_label']}あたりで比較 | {SITE_NAME}"
    desc = f"{category['name']}を{category['metric_label']}あたりに換算して安い順に比較。数量が曖昧な商品は除外し、条件別の最安値・総額・数量根拠まで確認できます。"
    return shell(title, desc, body, category['id'], breadcrumb_schema)


def homepage(categories, summaries, updated):
    cards = []
    for c in categories:
        s = summaries[c["id"]]
        best = s.get("best")
        image = esc(best.get("image", "")) if best else ""
        visual = category_illustration(c["id"])
        cards.append(
            f'''<a class="category-card {category_theme(c['id'])}" href="{BASE_URL}categories/{esc(c['id'])}/">
              <div class="category-visual">{visual}</div>
              <div class="category-card-copy">
                <span class="price-ribbon">👑 {esc(s['default_label'])}の現在最安</span>
                <strong>{esc(c['name'])}</strong>
                <div class="category-price">{yen(s['min'])}<small> / {esc(c['metric_label'])}</small></div>
                <div class="category-meta">掲載 {s['total_count']}件・条件別に比較</div>
              </div>
              <span class="category-arrow" aria-hidden="true">→</span>
            </a>'''
        )

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
        <h1>ペット用品の<br>「ほんとの安さ」を、<br>ひと目で。</h1>
        <p class="lead">袋の値段ではなく、1枚・1Lなど同じ単位にそろえて比較。犬と猫の毎日に、迷わない価格比較を。</p>
        <div class="trust-row"><span class="trust-pill">✓ サイズ別</span><span class="trust-pill">✓ 推測換算なし</span><span class="trust-pill">✓ 曖昧商品は除外</span></div>
        <p class="updated">最終更新 {esc(updated)}</p>
      </div>
      <div class="hero-art-shell photo-shell">{hero_illustration()}</div>
    </div></header>
    {nav(categories)}
    <main class="main"><div class="wrap">
      <section class="section visual-section">
        <div class="section-head"><div><h2>いま比較できるもの</h2><p class="section-sub">最初は消耗品に絞って、比較精度を優先しています。</p></div></div>
        <div class="home-grid">{''.join(cards)}</div>
      </section>

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
    {footer()}'''

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
        summaries[category["id"]] = {
            "total_count": len(ranked),
            "default_count": len(initial_items),
            "min": min([x["unit_price"] for x in initial_items], default=None),
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
