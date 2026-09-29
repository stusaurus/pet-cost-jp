import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.engine import choose_ranked


def raw(name, price, url, shop="shop"):
    return {
        "name": name,
        "price": price,
        "url": url,
        "shop": shop,
        "review_count": 0,
        "review_average": 0,
    }


class QualityTests(unittest.TestCase):
    def test_lifelex_same_family_keeps_best_unit_and_lowest_total(self):
        category = {
            "id": "pet-sheets",
            "parser": "count",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "group_by": "sheet_size",
            "include_any": ["ペットシーツ"],
            "exclude_any": [],
        }
        rows = [
            raw("ペットシーツ レギュラー 中厚 800枚 200枚×4個 LIFELEX 中厚KNPS_R", 7490, "https://x/a"),
            raw("ペットシーツ レギュラー 中厚 400枚 200枚×2個 LIFELEX 中厚KNPS_R", 3900, "https://x/b"),
            raw("ペットシーツ レギュラー 中厚 200枚 LIFELEX 中厚KNPS_R", 1990, "https://x/c"),
        ]
        ranked = choose_ranked(rows, category)
        self.assertEqual(len(ranked), 2)
        self.assertEqual({x["price"] for x in ranked}, {7490, 1990})

    def test_same_rakuten_source_slug_across_shops_dedupes(self):
        category = {
            "id": "cat-litter",
            "parser": "volume_liter",
            "metric": "per_liter",
            "metric_label": "1L",
            "group_by": "litter_material",
            "include_any": ["猫砂"],
            "exclude_any": [],
        }
        rows = [
            raw(
                "猫砂 木質ペレット 33L システムトイレ用",
                2000,
                "https://hb.afl.rakuten.co.jp/x/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fcat-land%2F7066251%2F",
                "a",
            ),
            raw(
                "猫砂 木質ペレット 33L システムトイレ用",
                2100,
                "https://hb.afl.rakuten.co.jp/y/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fdog-kan%2F7066251%2F",
                "b",
            ),
        ]
        ranked = choose_ranked(rows, category)
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["price"], 2000)

    def test_short_system_sheet_source_slug_across_shops_dedupes(self):
        category = {
            "id": "system-toilet-sheets",
            "parser": "count",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "group_by": "compatibility",
            "include_any": ["システムトイレ"],
            "exclude_any": [],
        }
        rows = [
            raw(
                "ねこシステムトイレ用シーツ 800枚 (200枚×4袋)",
                5980,
                "https://hb.afl.rakuten.co.jp/x/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fdogandcat%2F31005%2F",
                "a",
            ),
            raw(
                "システムトイレ用 ペットシーツ 800枚 (200枚×4袋)",
                5980,
                "https://hb.afl.rakuten.co.jp/y/?pc=https%3A%2F%2Fitem.rakuten.co.jp%2Fpets%2F31005%2F",
                "b",
            ),
        ]
        ranked = choose_ranked(rows, category)
        self.assertEqual(len(ranked), 1)

    def test_unknown_compatibility_is_excluded_when_configured(self):
        category = {
            "id": "system-toilet-sheets",
            "parser": "count",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "group_by": "compatibility",
            "exclude_groups": ["unknown"],
            "include_any": ["システムトイレ"],
            "exclude_any": [],
        }
        rows = [
            raw("猫の時間 システムトイレ用吸収シート 31枚", 600, "https://x/a")
        ]
        self.assertEqual(choose_ranked(rows, category), [])

    def test_deotoilet_family_does_not_dominate(self):
        category = {
            "id": "system-toilet-sheets",
            "parser": "count",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "group_by": "compatibility",
            "include_any": ["デオトイレ"],
            "exclude_any": [],
        }
        rows = [
            raw("デオトイレ 消臭・抗菌シート 20枚", 1800, "https://x/a", "a"),
            raw("デオトイレ 消臭・抗菌シート 20枚×6袋", 10500, "https://x/b", "b"),
            raw("デオトイレ 消臭・抗菌シート 20枚×12袋", 20800, "https://x/c", "c"),
        ]
        ranked = choose_ranked(rows, category)
        self.assertLessEqual(len(ranked), 2)
        self.assertEqual(ranked[0]["unit_price"], 86.6667)

    def test_scent_variants_remain_separate(self):
        category = {
            "id": "system-toilet-sheets",
            "parser": "count",
            "metric": "per_sheet",
            "metric_label": "1枚",
            "group_by": "compatibility",
            "include_any": ["デオトイレ"],
            "exclude_any": [],
        }
        rows = [
            raw("デオトイレ 消臭・抗菌シート 20枚", 1800, "https://x/a", "a"),
            raw("デオトイレ ふんわり香る消臭・抗菌シート ナチュラルガーデンの香り 20枚", 1900, "https://x/b", "b"),
            raw("デオトイレ ふんわり香る消臭・抗菌シート ナチュラルソープの香り 20枚", 1950, "https://x/c", "c"),
        ]
        ranked = choose_ranked(rows, category)
        self.assertEqual(len(ranked), 3)


if __name__ == "__main__":
    unittest.main()
