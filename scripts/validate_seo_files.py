from pathlib import Path
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import json

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.tags=[]; self.ids=set(); self.schemas=[]; self.schema=False; self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs=dict(attrs); self.tags.append((tag,attrs))
        if attrs.get('id'): self.ids.add(attrs['id'])
        if tag=='script' and attrs.get('type')=='application/ld+json': self.schema=True
    def handle_endtag(self, tag):
        if tag=='script': self.schema=False
    def handle_data(self, data):
        if self.schema: self.schemas.append(json.loads(data))

SITE = Path("site")
BASE_URL = "https://stusaurus.github.io/pet-cost-jp/"

html_files = sorted(p for p in SITE.rglob("*.html") if p.name != "404.html" and not (p.parent == SITE and p.name.startswith("google")))
expected = []
for p in html_files:
    rel = p.relative_to(SITE).as_posix()
    if rel == "index.html":
        expected.append(BASE_URL)
    elif rel.endswith("/index.html"):
        expected.append(BASE_URL + rel[:-10])
    else:
        expected.append(BASE_URL + rel)

sitemap = SITE / "sitemap.xml"
robots_path = SITE / "robots.txt"
if not sitemap.exists() or not robots_path.exists():
    raise SystemExit("SEO discovery files missing")

root = ET.parse(sitemap).getroot()
ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
actual = [n.text for n in root.findall(f"{ns}url/{ns}loc")]
if not actual or len(actual) != len(set(actual)):
    raise SystemExit("sitemap.xml is empty or contains duplicate URLs")
if set(actual) != set(expected):
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    raise SystemExit(f"sitemap URLs differ from generated HTML; missing={missing}; extra={extra}")
if any(not u.startswith(BASE_URL) for u in actual):
    raise SystemExit("sitemap contains URL outside the canonical site prefix")

robots = robots_path.read_text(encoding="utf-8").splitlines()
if "Allow: /" not in robots or f"Sitemap: {BASE_URL}sitemap.xml" not in robots:
    raise SystemExit("robots.txt does not expose the canonical sitemap")
pages={url:Page(p.read_text()) for url,p in zip(expected,html_files)}
for url,page in pages.items():
    canonical=[a.get('href') for t,a in page.tags if t=='link' and a.get('rel')=='canonical']
    if canonical != [url]: raise SystemExit(f'{url}: incorrect canonical {canonical}')
    if sum(t=='h1' for t,a in page.tags)!=1: raise SystemExit(f'{url}: expected exactly one H1')
    metas={a.get('name'):a.get('content','') for t,a in page.tags if t=='meta'}
    if 'noindex' in metas.get('robots','') or not metas.get('description'): raise SystemExit(f'{url}: index/description error')
    if not page.schemas: raise SystemExit(f'{url}: structured data missing')
    for tag,a in page.tags:
        if tag!='a' or not a.get('href'): continue
        href=urljoin(url,a['href']); u=urlparse(href)
        if href.startswith(BASE_URL):
            target=u._replace(query='',fragment='').geturl()
            if target not in pages: raise SystemExit(f'{url}: broken internal link {href}')
            if u.fragment and u.fragment not in pages[target].ids: raise SystemExit(f'{url}: broken anchor {href}')
        if u.hostname=='hb.afl.rakuten.co.jp' and (a.get('target')!='_blank' or not {'sponsored','nofollow','noopener'} <= set(a.get('rel','').split())):
            raise SystemExit(f'{url}: affiliate link attributes invalid')
if (SITE/'404.html').exists() and 'noindex' not in (SITE/'404.html').read_text(): raise SystemExit('404 must be noindex')
print(f"SEO discovery validation passed: {len(actual)} sitemap URLs")
