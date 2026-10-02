from pathlib import Path
import xml.etree.ElementTree as ET

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
print(f"SEO discovery validation passed: {len(actual)} sitemap URLs")
