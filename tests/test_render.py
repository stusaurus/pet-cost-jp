import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_site


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.category = {
            "id": "pet-sheets",
            "name": "ペットシーツ",
            "emoji": "🐶",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "default_group": "regular",
            "rank_all": False,
            "groups": {"regular": "レギュラー", "wide": "ワイド"},
            "intro": "同じサイズで比較します。",
            "guide": ["サイズをそろえる"],
            "faq": [{"q": "なぜ？", "a": "条件をそろえるためです。"}],
        }
        self.item = {
            "name": "ペットシーツ レギュラー 200枚",
            "price": 2000,
            "url": "https://hb.afl.rakuten.co.jp/example",
            "shop": "テストショップ",
            "image": "https://example.com/item.jpg",
            "postage_flag": 0,
            "product_id": "abc123",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "quantity": 200.0,
            "quantity_evidence": "200枚",
            "group": "regular",
            "unit_price": 10.0,
        }

    def test_category_page_contains_mobile_ui_and_credit(self):
        page = build_site.category_page(
            self.category,
            [self.item],
            [self.category],
            "2026-09-30 07:00 JST",
        )
        self.assertIn('data-featured-box', page)
        self.assertIn('data-featured-diff', page)
        self.assertIn('data-price-diff', page)
        self.assertIn('data-group-button', page)
        self.assertIn('class="product-image"', page)
        self.assertIn('楽天で価格を見る', page)
        self.assertIn('Supported by Rakuten Developers', page)
        self.assertIn('送料込み', page)
        self.assertIn('application/ld+json', page)

    def test_homepage_uses_total_count_and_best_image(self):
        summaries = {
            "pet-sheets": {
                "total_count": 23,
                "default_count": 8,
                "min": 5.5,
                "best": self.item,
                "default_label": "レギュラー",
            }
        }
        page = build_site.homepage(
            [self.category],
            summaries,
            "2026-09-30 07:00 JST",
        )
        self.assertIn("掲載 23件", page)
        self.assertIn("レギュラーの現在最安", page)
        self.assertIn("https://example.com/item.jpg", page)
        self.assertIn("使い方は3ステップ", page)

    def test_google_verification_file_is_copied_to_site(self):
        verification_files = list(ROOT.glob("google*.html"))
        if not verification_files:
            self.skipTest("No Google verification file in repository")
        original_site = build_site.SITE
        try:
            with tempfile.TemporaryDirectory() as tmp:
                build_site.SITE = Path(tmp)
                build_site.copy_static_verification_files()
                for source in verification_files:
                    self.assertTrue((Path(tmp) / source.name).exists())
        finally:
            build_site.SITE = original_site


if __name__ == "__main__":
    unittest.main()
