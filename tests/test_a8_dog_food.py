"""Regression tests for A8 creative placement and preservation."""
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from a8_dog_food import AD_CREATIVE, MARKER, inject_dog_food_ad, check_ad_integrity


class _Nodes(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.nodes = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.nodes.append((tag, dict(attrs)))


class A8DogFoodTests(unittest.TestCase):
    def setUp(self):
        self.body = '<main><section class="food-guide">既存の価格比較</section><section class="discovery-return"><h2>用品に戻る</h2></section></main>'

    def test_official_ad_creative_is_exactly_preserved_once(self):
        html = inject_dog_food_ad(self.body)
        self.assertEqual(html.count(AD_CREATIVE), 1)
        self.assertEqual(html.count(MARKER), 1)
        check_ad_integrity(html)
        nodes = _Nodes(html).nodes
        links = [a for tag, a in nodes if tag == "a" and "px.a8.net" in a.get("href", "")]
        pixels = [a for tag, a in nodes if tag == "img" and "a8.net/0.gif" in a.get("src", "")]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0], {
            "href": "https://px.a8.net/svt/ejp?a8mat=4BGCF1+8NZ7B6+4PA6+BWVTE",
            "rel": "nofollow",
        })
        self.assertEqual(len(pixels), 1)
        self.assertEqual(pixels[0], {
            "border": "0", "width": "1", "height": "1",
            "src": "https://www14.a8.net/0.gif?a8mat=4BGCF1+8NZ7B6+4PA6+BWVTE",
            "alt": "",
        })

    def test_ad_not_ranked_and_existing_comparison_not_modified(self):
        html = inject_dog_food_ad(self.body)
        self.assertIn('<section class="food-guide">既存の価格比較</section>', html)
        self.assertIn('楽天の掲載商品ランキングや価格・品質の比較結果には含めていません', html)
        self.assertIn('広告｜A8.netアフィリエイト', html)
        self.assertIn('対象年齢', html)
        self.assertLess(html.index('pet-sponsor'), html.index('discovery-return'))
        self.assertNotIn('最安値保証', html)

    def test_click_event_uses_current_site_tracker(self):
        html = inject_dog_food_ad(self.body)
        self.assertIn('window.petCostTrack?.("affiliate_click"', html)
        self.assertIn('category_id:"dog-food"', html)
        self.assertIn('affiliate:"a8"', html)
        self.assertIn('conversion_source:"small_dog_food_sponsored_card"', html)

    def test_idempotence_and_fail_closed(self):
        html = inject_dog_food_ad(self.body)
        self.assertEqual(inject_dog_food_ad(html), html)
        with self.assertRaises(ValueError):
            inject_dog_food_ad('<main>no known anchor</main>')
        with self.assertRaises(ValueError):
            check_ad_integrity(html.replace("www14.a8.net", "www20.a8.net"))
        with self.assertRaises(ValueError):
            check_ad_integrity(html + AD_CREATIVE)


if __name__ == "__main__":
    unittest.main()
