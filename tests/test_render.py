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
        self.assertIn('aria-label="ペットシーツのイラスト"', page)
        self.assertIn('class="featured-crown"', page)
        self.assertIn('data-featured-diff', page)
        self.assertIn('data-price-diff', page)
        self.assertIn('data-top3-strip', page)
        self.assertIn('data-deal-message', page)
        self.assertIn('data-deal-dot', page)
        self.assertIn('top3_snapshot', page)
        self.assertIn('class="podium-title"', page)
        self.assertIn('class="podium-foot"', page)
        self.assertIn('class="category-hero-title"', page)
        self.assertIn('data-angle-grid', page)
        self.assertIn('comparison_angle_unit', page)
        self.assertIn('comparison_angle_total', page)
        self.assertIn('comparison_angle_bulk', page)
        self.assertIn('data-group-button', page)
        self.assertIn('brand-mark', page)
        self.assertIn('mobile-dock', page)
        self.assertIn('chip current', page)
        self.assertIn('page-pet-sheets', page)
        self.assertIn('data-product-grid', page)
        self.assertIn('class="shop-card"', page)
        self.assertIn('class="shop-card-image"', page)
        self.assertIn('comparison_card', page)
        self.assertIn('楽天で価格を見る', page)
        self.assertIn('Supported by Rakuten Developers', page)
        self.assertIn('送料込み', page)
        self.assertIn('application/ld+json', page)
        self.assertIn('assets/favicon.svg', page)
        self.assertIn('assets/site.webmanifest', page)
        self.assertIn('assets/hero-pet-comparison.webp', page)
        self.assertIn('assets/pet-cost-logo.svg', page)

    def test_homepage_uses_total_count_and_best_image(self):
        summaries = {
            "pet-sheets": {
                "total_count": 23,
                "default_count": 8,
                "min": 5.5,
                "median": 8.0,
                "deal_percent": 31,
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
        self.assertIn('class="category-card theme-sheet"', page)
        self.assertIn('aria-label="ペットシーツのイラスト"', page)
        self.assertIn("ペット用品の", page)
        self.assertIn("ほんとの安さ", page)
        self.assertIn('class="home-hero-title"', page)
        self.assertIn('class="hero-proof"', page)
        self.assertIn('class="category-card-number"', page)
        self.assertIn("assets/hero-pet-comparison.webp", page)
        self.assertIn("同じ単位で比較", page)
        self.assertIn("使い方は3ステップ", page)
        self.assertIn("今日の価格差", page)
        self.assertIn('data-daily-spotlight', page)
        self.assertIn('data-spotlight-link', page)
        self.assertIn("31%", page)
        self.assertIn("story-section", page)
        self.assertIn("trust-section", page)
        self.assertIn("store-section", page)
        self.assertIn("mobile-dock", page)
        self.assertIn("page-home", page)
        self.assertIn("assets/pet-cost-logo.svg", page)
        self.assertIn("assets/favicon.svg", page)
        self.assertIn("twitter:card", page)

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
                if (ROOT / "assets" / "hero-pet-comparison.webp").exists():
                    self.assertTrue((Path(tmp) / "assets" / "hero-pet-comparison.webp").exists())
                for asset in ("pet-cost-logo.svg", "favicon.svg", "site.webmanifest"):
                    if (ROOT / "assets" / asset).exists():
                        self.assertTrue((Path(tmp) / "assets" / asset).exists())
        finally:
            build_site.SITE = original_site


if __name__ == "__main__":
    unittest.main()
