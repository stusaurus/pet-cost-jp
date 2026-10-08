import json
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_site


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def with_attr(self, attr):
        return [attrs for _, attrs in self.tags if attr in attrs]


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.categories = build_site.load_categories()
        self.category = self.categories[0]
        self.item = dict(name='ペットシーツ レギュラー 200枚', price=2000,
                         url='https://hb.afl.rakuten.co.jp/example', shop='テストショップ',
                         image='https://example.com/item.jpg', postage_flag=0,
                         product_id='abc123', metric='per_sheet', metric_label='1枚',
                         quantity=200.0, quantity_evidence='200枚', group='regular', unit_price=10.0)

    def render(self, items):
        return build_site.category_page(self.category, items, self.categories, '2026-09-30 07:00 JST')

    def test_first_visit_requires_own_condition_with_honest_noscript_example(self):
        wide = dict(self.item, product_id='wide', group='wide', unit_price=5.0, price=1000)
        page = Page(self.render([wide, self.item]))
        rows = page.with_attr('data-product-row')
        self.assertIn('hidden', rows[0])
        self.assertNotIn('hidden', rows[1])
        self.assertEqual(rows[1]['data-item-id'], 'abc123')
        buttons = page.with_attr('data-group-button')
        self.assertEqual([b['data-group'] for b in buttons if b['aria-pressed'] == 'true'], [])
        self.assertEqual([b['data-group'] for b in buttons], ['regular', 'wide'])
        featured = [x for x in page.with_attr('data-affiliate-link') if x.get('data-conversion-source') == 'featured_product'][0]
        self.assertEqual(featured['data-item-id'], 'abc123')
        self.assertEqual(featured['href'], self.item['url'])
        self.assertIn('hidden', page.with_attr('data-comparison-results')[0])
        self.assertIn('レギュラーの比較例', self.render([wide, self.item]))

    def test_crawlable_category_guidance_and_related_links_preserve_affiliate_links(self):
        text = self.render([self.item])
        self.assertIn("ペットシーツを選ぶときの確認ポイント", text)
        self.assertIn("実際に使うサイズを選んでから1枚単価を比較", text)
        self.assertIn(build_site.BASE_URL + "categories/cat-litter/", text)
        self.assertEqual(len(Page(text).with_attr('data-affiliate-link')), 4)

    def test_even_median_and_reasons_use_current_condition(self):
        rows = [dict(self.item, product_id=str(i), unit_price=u, price=u * 200) for i, u in enumerate([4, 6, 10, 20])]
        self.assertEqual(build_site.comparison_stats(rows), {'min': 4, 'median': 8})
        badges = dict(build_site.reason_badges(rows[0], rows, 8))
        self.assertEqual(badges['median'], '中央値より50%安い')
        self.assertIn('unit', badges)
        self.assertIn('total', badges)
        self.assertIn('bulk', badges)
        self.assertNotIn('median', dict(build_site.reason_badges(rows[2], rows, 8)))

    def test_empty_condition_has_no_product_advertisement(self):
        page = Page(self.render([]))
        self.assertIn('hidden', page.with_attr('data-featured-box')[0])
        self.assertEqual(page.with_attr('data-product-row'), [])
        self.assertNotIn('hidden', page.with_attr('data-empty-result')[0])

    def test_comparison_and_purchase_links_keep_tracking_and_seo(self):
        source = self.render([self.item])
        page = Page(source)
        links = [attrs for tag, attrs in page.tags if tag == 'a' and attrs.get('href', '').startswith('https://hb.afl.')]
        self.assertEqual(len(links), 4)  # Answer, TOP3, selected angle, list
        self.assertEqual({x['data-conversion-source'] for x in links}, {'featured_product', 'top3_snapshot', 'comparison_angle_unit', 'comparison_card'})
        for link in links:
            self.assertEqual(link['data-item-name'], self.item['name'])
            self.assertEqual(link['target'], '_blank')
            self.assertTrue({'nofollow', 'sponsored', 'noopener'} <= set(link['rel'].split()))
        canonicals = [a['href'] for tag, a in page.tags if tag == 'link' and a.get('rel') == 'canonical']
        self.assertEqual(canonicals, [build_site.BASE_URL + 'categories/pet-sheets/'])
        self.assertIn('BreadcrumbList', source)
        self.assertIn('Supported by Rakuten Developers', source)
        self.assertIn('prefers-reduced-motion', source)
        self.assertIn('aria-live="polite"', source)

    def test_promotions_trim_only_display_and_titles_are_escaped(self):
        item = dict(self.item, name='【ポイント10倍】<img src=x onerror=alert(1)> ペットシーツ 200枚')
        source = self.render([item])
        page = Page(source)
        row = page.with_attr('data-product-row')[0]
        self.assertEqual(row['data-item-name'], item['name'])
        self.assertNotIn('ポイント10倍', row['data-display-name'])
        self.assertIn('<img src=x', row['data-display-name'])
        self.assertNotIn('<img src=x onerror=', source)
        self.assertEqual(build_site.display_name('【厚型】ペットシーツ 200枚'), '【厚型】ペットシーツ 200枚')
        self.assertEqual(json.loads(build_site.schema_script({'name': '</script>'}).split('>', 1)[1].rsplit('<', 1)[0])['name'], '</script>')

    def test_home_price_difference_and_category_entry_are_one_link(self):
        summaries = {'pet-sheets': {'total_count': 23, 'default_count': 8, 'min': 5.5, 'median': 8.0,
                                   'deal_percent': 31, 'best': self.item, 'default_label': 'レギュラー'}}
        source = build_site.homepage([self.category], summaries, '2026-09-30 07:00 JST')
        page = Page(source)
        entries = page.with_attr('data-editorial-category')
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['href'], build_site.BASE_URL + 'categories/pet-sheets/')
        self.assertEqual(entries[0]['data-gap-percent'], '31')
        self.assertIn('data-spotlight-link', entries[0])
        self.assertIn('この条件 8件', source)
        self.assertIn('現在掲載商品の最安と中央値の差', source)
        self.assertIn('WebSite', source)
        self.assertLess(source.index('いつもの用品をすぐ比べる'), source.index('今日の価格差も見る'))
        self.assertIn('data-pet-category="pet-sheets"', source)
        self.assertNotIn('商品名から', source)

    def test_google_verification_file_and_assets_are_copied(self):
        original_site = build_site.SITE
        try:
            with tempfile.TemporaryDirectory() as tmp:
                build_site.SITE = Path(tmp)
                build_site.copy_static_verification_files()
                for source in ROOT.glob('google*.html'):
                    self.assertEqual((Path(tmp) / source.name).read_bytes(), source.read_bytes())
                for asset in ('pet-cost-logo.svg', 'favicon.svg', 'site.webmanifest', 'comparison.css', 'pet-home-morning.webp'):
                    self.assertTrue((Path(tmp) / 'assets' / asset).exists())
        finally:
            build_site.SITE = original_site

    def test_lifestyle_art_is_decorative_not_a_product_or_compatibility_claim(self):
        source = self.render([self.item])
        page = Page(source)
        self.assertIn('pet-living-1', source)
        self.assertEqual(page.with_attr('data-condition-progress')[0]['class'], 'condition-progress')
        self.assertEqual(len(page.with_attr('data-angle-card')), 3)
        svg = [a for tag, a in page.tags if tag == 'svg']
        self.assertTrue(svg)
        self.assertTrue(all(a.get('aria-hidden') == 'true' for a in svg))
        self.assertIn('数量・比較の根拠を見る', source)
        self.assertIn('品質やペットとの相性を保証するものではありません', source)
        self.assertIn('過去価格ではありません', source)
        self.assertLess((ROOT / 'assets/pet-home-morning.webp').stat().st_size, 300000)

    def test_empty_default_keeps_three_buying_choices_for_later_selection(self):
        page = Page(self.render([]))
        self.assertEqual([a['data-angle-role'] for a in page.with_attr('data-angle-card')], ['unit', 'total', 'bulk'])
        self.assertIn('hidden', page.with_attr('data-comparison-results')[0])

    def test_editorial_assets_are_real_files_with_reserved_geometry(self):
        manifest = json.loads((ROOT / 'assets/illustrations/manifest.json').read_text())
        self.assertEqual(len(manifest['assets']), 18)
        self.assertLess(sum(a['bytes'] for a in manifest['assets']), 400000)
        for asset in manifest['assets']:
            path = ROOT / 'assets/illustrations' / asset['file']
            data = path.read_bytes()
            self.assertEqual(data[:4], b'RIFF')
            self.assertEqual(data[8:12], b'WEBP')
            self.assertEqual(len(data), asset['bytes'])
            self.assertGreater(len(data), 1000)
            self.assertLess(len(data), 40000)
            self.assertEqual(asset['width'] / asset['height'], 4 / 3)
        for category in self.categories:
            for group in ('', *category['groups']):
                image = Page(build_site.care_art(category['id'], group)).tags[0]
                self.assertEqual(image[0], 'img')
                attrs = image[1]
                self.assertEqual(attrs['alt'], '')
                self.assertEqual(attrs['aria-hidden'], 'true')
                self.assertIn('width', attrs)
                self.assertIn('height', attrs)
                self.assertTrue((ROOT / attrs['src'].removeprefix(build_site.BASE_URL)).is_file())

    def test_home_and_category_use_distinct_editorial_compositions(self):
        for category in self.categories:
            home = build_site.care_art(category['id'])
            header = build_site.care_art(category['id'], role='category')
            self.assertIn('/assets/living/', home)
            self.assertIn('/header-', header)
            self.assertNotEqual(home, header)
            self.assertNotIn('<svg', home + header)
            self.assertIn('<svg', build_site.icon(category['id']))


if __name__ == '__main__':
    unittest.main()
