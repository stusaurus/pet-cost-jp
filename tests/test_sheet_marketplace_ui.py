import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sheet_marketplace_ui import select_pairs, render, inject, build_pairs
from common.sheet_marketplace import PRODUCTS


class Client:
    def affiliate_link(self, row):
        return row.get("url")


class MarketplaceUITests(unittest.TestCase):
    def setUp(self):
        self.r = {"name": "同じ商品", "shop": "楽天店舗", "price": 1982,
                  "url": "https://hb.afl.rakuten.co.jp/hgc/test/", "postage_flag": 1}
        self.y = {"name": "同じ商品", "seller": {"name": "Yahoo店舗"}, "price": 1936,
                  "url": "https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=1&pid=2", "shipping": {"code": 2},
                  "description": "沖縄別途送料"}
        self.product = PRODUCTS[3]

    def test_price_and_shipping(self):
        pairs = select_pairs([(self.product, [self.r], [self.y])], Client())
        section = render(pairs, "2026-11-27 JST")
        for expected in ("1,982円", "1,936円", "46円低い", "55.1円", "53.8円", 'data-merchant="rakuten"',
                         'data-merchant="yahoo"', "送料未確定", "Webサービス by Yahoo! JAPAN"):
            self.assertIn(expected, section)
        self.assertNotIn("送料無料表示（地域条件は要確認）", section)
        self.assertEqual(render(pairs, "now", "wide"), "")
        page = '<section class="section" id="product-ranking"></section>'
        self.assertTrue(inject(page, section).endswith(page))
        self.assertEqual(inject(page, ""), page)

    def test_free_shipping_only_if_no_conditions(self):
        r = dict(self.r, postage_flag=0)
        y = dict(self.y, description="")
        section = render(select_pairs([(self.product, [r], [y])], Client()), "now")
        self.assertEqual(section.count("送料無料表示（地域条件は要確認）"), 2)

    def test_missing_mall_and_failure_preserve_ranking(self):
        self.assertEqual(select_pairs([(self.product, [self.r], [])], Client()), [])
        self.assertEqual(select_pairs([(self.product, [self.r], [dict(self.y, url=None)])], Client()), [])
        with patch("sheet_marketplace_ui.YahooShopping", side_effect=RuntimeError("secret")):
            self.assertEqual(build_pairs({}), [])

    def test_escape_external_strings(self):
        r = dict(self.r, shop='<script>alert(1)</script>')
        section = render(select_pairs([(self.product, [r], [self.y])], Client()), "now")
        self.assertNotIn("<script>", section)
        self.assertIn("&lt;script&gt;", section)
