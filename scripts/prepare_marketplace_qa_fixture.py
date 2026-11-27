"""Offline QA fixture: never used by the production generator."""
from pathlib import Path
from common.sheet_marketplace import PRODUCTS
from sheet_marketplace_ui import render, inject, select_pairs

ROOT = Path(__file__).resolve().parents[1]


class FixtureClient:
    def affiliate_link(self, row):
        return row["url"]


def main():
    pairs = []
    for index, product in enumerate(PRODUCTS):
        if index not in (1, 3):
            continue
        jan, group, count, family, source = product
        name = "デオシート しっかり超吸収 無香消臭 ワイド 54枚" if index == 1 else "ネオシーツ FX 薄型 スーパーワイド 36枚"
        from urllib.parse import urlencode
        r = {"name": name, "shop": "検証専用・楽天店舗", "price": 1692 if index == 1 else 1982,
             "url": "https://hb.afl.rakuten.co.jp/hgc/fixture/?" + urlencode({"pc": "https://item.rakuten.co.jp/fixture/item"+str(index)+"/"}),
             "postage_flag": 1}
        y = {"name": name, "seller": {"name": "検証専用・Yahoo店舗"}, "price": 1692 if index == 1 else 1936,
             "url": "https://ck.jp.ap.valuecommerce.com/servlet/referral?" + urlencode({"sid": "1", "pid": "2", "vc_url": "https://store.shopping.yahoo.co.jp/fixture/item"+str(index)+".html"}),
             "shipping": {"code": 2}, "description": "沖縄別途送料"}
        pairs.append((product, [r], [y]))
    selected = select_pairs(pairs, FixtureClient())
    assert len(selected) == 2
    directory = ROOT / "site/categories/pet-sheets"
    for slug, group in (("", None), ("regular", "regular"), ("wide", "wide"), ("super-wide", "super_wide")):
        file = directory / slug / "index.html"
        file.write_text(inject(file.read_text(encoding="utf-8"), render(selected, "QA fixture (not live prices)", group)), encoding="utf-8")


if __name__ == "__main__":
    main()
