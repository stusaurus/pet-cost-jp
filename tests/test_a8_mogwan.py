"""Mogwan A8 cost calculator + official creative quality gates."""
import sys
import unittest
from pathlib import Path
from html.parser import HTMLParser

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from a8_mogwan import AD_CREATIVE, MARKER, inject_mogwan_ad, check_mogwan_ad_integrity
from a8_dog_food import inject_dog_food_ad, AD_CREATIVE as SMALL_CREATIVE, check_ad_integrity


class Tags(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.anchors, self.pixels, self.sections = [], [], []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "a" and "px.a8.net" in data.get("href", ""):
            self.anchors.append(data)
        if tag == "img" and "a8.net/0.gif" in data.get("src", ""):
            self.pixels.append(data)
        if tag == "section":
            self.sections.append(data)


class MogwanTests(unittest.TestCase):
    def setUp(self):
        self.page = (
            '<main><section class="food-discovery"><h2>犬のごはん</h2>'
            '<p>楽天に掲載された製品を費用比較</p></section>'
            '<section class="discovery-return"><h2>商品をもっと見る</h2></section></main>'
        )

    def test_official_a8_creative_exactly_preserved_and_visible(self):
        content = inject_mogwan_ad(self.page)
        check_mogwan_ad_integrity(content)
        self.assertEqual(content.count(AD_CREATIVE), 1)
        self.assertEqual(content.count(MARKER), 1)
        parsed = Tags(content)
        self.assertEqual(parsed.anchors, [{
            'href':'https://px.a8.net/svt/ejp?a8mat=4BGCF1+8M6WHU+3J8+1BMW42',
            'rel':'nofollow',
        }])
        self.assertEqual(parsed.pixels, [{
            'border':'0', 'width':'1', 'height':'1',
            'src':'https://www13.a8.net/0.gif?a8mat=4BGCF1+8M6WHU+3J8+1BMW42',
            'alt':'',
        }])
        self.assertIn('広告｜A8.netアフィリエイト', content)
        self.assertIn('楽天の掲載商品ランキング・価格比較結果には含めていません', content)
        self.assertIn('1注文の送料', content)

    def test_existing_rakuten_and_small_dog_a8_are_preserved(self):
        before = inject_dog_food_ad(self.page)
        after = inject_mogwan_ad(before)
        check_ad_integrity(after)
        check_mogwan_ad_integrity(after)
        self.assertEqual(after.count(SMALL_CREATIVE), 1)
        self.assertEqual(after.count(AD_CREATIVE), 1)
        self.assertIn('<section class="food-discovery"><h2>犬のごはん</h2>', after)
        self.assertLess(after.index('id="a8-small-dog-food"'), after.index('id="a8-mogwan"'))
        self.assertLess(after.index('id="a8-mogwan"'), after.index('class="discovery-return"'))
        self.assertIn('program:"mogwan"', after)
        self.assertIn('conversion_source:"mogwan_sponsored_cost_planner"', after)
        self.assertIn('window.petCostTrack?.("affiliate_click"', after)
        self.assertIn('window.petCostTrack?.("mogwan_cost_planner_use"', after)
        self.assertNotIn('最安値', after)

    def test_duplicate_or_changed_pixel_fails_closed(self):
        first = inject_mogwan_ad(self.page)
        self.assertEqual(inject_mogwan_ad(first), first)
        with self.assertRaises(ValueError):
            inject_mogwan_ad('<main>No catalog</main>')
        with self.assertRaises(ValueError):
            check_mogwan_ad_integrity(first.replace('www13.a8.net','www14.a8.net'))
        with self.assertRaises(ValueError):
            check_mogwan_ad_integrity(first + AD_CREATIVE)


if __name__ == '__main__':
    unittest.main()
