import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from yahoo_readiness import summarize
from common.yahoo_shopping import YahooShopping, YahooUnavailable


class StubClient:
    def affiliate_link(self, hit):
        return "https://example.invalid/verified" if hit.get("verified") else None


class ReadinessTests(unittest.TestCase):
    def test_size_quantity_and_validated_link_are_required(self):
        category = json.loads((ROOT / "config/categories.json").read_text())[0]
        good = {"code": "shop_a", "name": "ペットシーツ レギュラー 100枚",
                "price": 1000, "verified": True}
        hits = [good, dict(good), {**good, "code": "shop_b", "name": "ペットシーツ ワイド 100枚"},
                {**good, "code": "shop_c", "name": "ペットシーツ 100枚"},
                {**good, "code": "shop_d", "name": "ペットシーツ レギュラー 100枚 200枚 選べる"},
                {**good, "code": "shop_e", "verified": False},
                {**good, "code": "shop_f", "price": 0}]
        self.assertEqual(summarize(hits, StubClient(), category, "regular"),
                         {"returned": 7, "eligible_distinct_listings": 1})

    def test_missing_and_invalid_credentials_fail_without_values(self):
        for app, affiliate, reason in [("", "", "missing_app_id"),
                                       ("dummy", "", "missing_affiliate_id"),
                                       ("dummy", "invalid-private-value", "affiliate_config_format")]:
            with self.assertRaises(YahooUnavailable) as exc:
                YahooShopping(app, affiliate)
            self.assertEqual(str(exc.exception), reason)


class ManufacturerMatchTests(unittest.TestCase):
    def test_single_pack_and_variant(self):
        from common.sheet_marketplace import PRODUCTS, identity, totals_known
        category = json.loads((ROOT / "config/categories.json").read_text())[0]
        product = PRODUCTS[1]
        good = {"name": "デオシート しっかり超吸収 無香消臭タイプ ワイド 54枚 ペットシーツ", "price": 1800, "url": "https://example.invalid"}
        self.assertTrue(identity(good, product, category))
        for suffix in ("×4袋", " おまけ付き", " 選べる", " フローラル"):
            self.assertFalse(identity({**good, "name": good["name"] + suffix}, product, category))
        self.assertFalse(identity({**good, "name": good["name"].replace("ワイド", "スーパーワイド")}, product, category))
        self.assertFalse(identity({**good, "name": good["name"].replace("無香消臭", "香り消臭")}, product, category))
        self.assertTrue(totals_known({**good, "postage_flag": 0}, {"name": good["name"], "shipping": {"code": 2}}))
        self.assertFalse(totals_known({**good, "postage_flag": 0}, {"name": good["name"], "shipping": {"code": 2}, "description": "沖縄別途送料"}))
        self.assertFalse(totals_known({**good, "postage_flag": 1}, {"name": good["name"], "shipping": {"code": 2}}))


    def test_verified_rakuten_requires_explicit_jan_or_reviewed_target(self):
        from common.sheet_marketplace import PRODUCTS, verified_rakuten
        from urllib.parse import urlencode
        category = json.loads((ROOT / "config/categories.json").read_text())[0]
        product = PRODUCTS[1]
        good = {"name": "デオシート しっかり超吸収 無香消臭タイプ ワイド 54枚 ペットシーツ", "price": 1800}
        def url(path):
            return "https://hb.afl.rakuten.co.jp/hgc/test/?" + urlencode({"pc": "https://item.rakuten.co.jp" + path})
        reviewed = {**good, "url": url("/chanet/246764/")}
        unknown = {**good, "url": url("/other/sku/")}
        self.assertTrue(verified_rakuten(reviewed, product, category))
        self.assertFalse(verified_rakuten(unknown, product, category))
        self.assertTrue(verified_rakuten({**unknown, "name": good["name"] + " 4520699672143"}, product, category))
        self.assertFalse(verified_rakuten({**reviewed, "name": good["name"] + " 4520699676066"}, product, category))
        self.assertFalse(verified_rakuten({**reviewed, "name": good["name"] + " ×4袋"}, product, category))
        self.assertFalse(verified_rakuten({**reviewed, "url": "https://item.rakuten.co.jp/chanet/246764/"}, product, category))
