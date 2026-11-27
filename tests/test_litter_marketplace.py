import json
import sys
import unittest
from pathlib import Path
from urllib.parse import urlencode
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from common.litter_marketplace import PRODUCTS, identity, verified_rakuten, inspect

CATEGORY = next(c for c in json.loads((ROOT/"config/categories.json").read_text()) if c["id"] == "cat-litter")


def row(name, target):
    return {"name": name, "price": 700, "url": "https://hb.afl.rakuten.co.jp/hgc/test/?" + urlencode({"pc": "https://item.rakuten.co.jp"+target+"/"})}


class LitterMarketplaceTests(unittest.TestCase):
    def test_single_bag_and_exact_evidence(self):
        p = PRODUCTS[0]
        r = row("アイリスオーヤマ 紙の猫砂 KMN-70N 7L", p[7][0])
        self.assertTrue(verified_rakuten(r,p,CATEGORY))
        self.assertFalse(verified_rakuten(row(r["name"],"/unknown/123"),p,CATEGORY))
        for suffix in ("×6袋", " 6袋", " 6個", " x2", " 14L", " 選べる", " おから", " 4905009714346", " システムトイレ", " ケース"):
            self.assertFalse(identity({"name":r["name"]+suffix},p,CATEGORY),suffix)
        self.assertFalse(identity({"name":r["name"].replace("KMN-70N","PKMN-70N")},p,CATEGORY))
        self.assertFalse(identity({"name":r["name"].replace("7L","7kg")},p,CATEGORY))

    def test_capacity_change_and_variant(self):
        p = PRODUCTS[4]
        r = row("クリーンミュウ 固まる流せる白い紙製の砂 12.5L",p[7][0])
        self.assertTrue(verified_rakuten(r,p,CATEGORY))
        self.assertFalse(verified_rakuten({**r,"name":r["name"].replace("12.5L","13.5L")},p,CATEGORY))
        self.assertFalse(verified_rakuten({**r,"name":r["name"]+" 4袋"},p,CATEGORY))
        p = PRODUCTS[1]
        self.assertFalse(identity({"name":"お茶の猫砂 OCN-70 7L"},p,CATEGORY))
        self.assertTrue(identity({"name":"お茶の猫砂 OCN-70N 7L"},p,CATEGORY))

    def test_probe_requires_both_malls_and_exact_yahoo_jan(self):
        p = PRODUCTS[0]
        r = row("アイリスオーヤマ 紙の猫砂 KMN-70N 7L",p[7][0])
        good = {"code":"s_a","name":r["name"],"janCode":p[0],"price":650,"condition":"new","inStock":True}
        class Client:
            def search(self,jan,results):
                return [good,good,{**good,"code":"s_b","name":r["name"]+" 6袋"},{**good,"code":"s_c","janCode":"4905009714346"},{**good,"code":"s_d","inStock":False}]
            def affiliate_link(self,hit):
                return "https://example.invalid/qa"
        def fetch(keyword,pages,shop_code=""):
            return [r,r]
        result=inspect(Client(),CATEGORY,fetch)
        self.assertEqual(result[p[0]]["rakuten_verified"],1)
        self.assertEqual(result[p[0]]["yahoo_verified"],1)
        self.assertTrue(result[p[0]]["matched"])
        self.assertFalse(result[PRODUCTS[1][0]]["matched"])
