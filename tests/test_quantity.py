import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.quantity import parse_count, parse_liters, parse_100g
from common.classify import sheet_size, litter_material, compatibility
from common.engine import category_matches


class QuantityTests(unittest.TestCase):
    def test_count_multiplier(self):
        self.assertEqual(parse_count("ペットシーツ 200枚×4袋")["quantity"], 800)

    def test_count_total_and_pack_are_consistent(self):
        self.assertEqual(parse_count("ペットシーツ 800枚（200枚×4袋）")["quantity"], 800)

    def test_count_single(self):
        self.assertEqual(parse_count("デオトイレ シート 20枚入")["quantity"], 20)

    def test_count_ambiguous_rejected(self):
        self.assertIsNone(parse_count("シート 20枚 30枚 選べる"))

    def test_count_spaced_case_quantity_rejected(self):
        # Live listing: title alone does not prove whether 100枚 is per bag or case total.
        self.assertIsNone(parse_count("ペットシーツ ワイド 薄型 100枚 国産 4袋 ペットシート"))
        self.assertIsNone(parse_count("ペットシーツ スーパーワイド 薄型 40枚 国産 4袋"))

    def test_single_or_bundle_selector_rejected(self):
        self.assertIsNone(parse_count("システムトイレ用 20枚 単品 4個セット ラクリーン"))

    def test_multiple_sheet_variants_rejected(self):
        title = "レギュラー1200枚（300枚×4袋） ワイド600枚（150枚×4袋） スーパーワイド300枚（75枚×4袋）"
        self.assertIsNone(parse_count(title))
        self.assertEqual(sheet_size(title), "ambiguous")

    def test_liter_multiplier(self):
        self.assertEqual(parse_liters("猫砂 紙 10L×6袋")["quantity"], 60)

    def test_liter_total_and_pack_are_consistent(self):
        self.assertEqual(parse_liters("猫砂 40L (5L×8袋)")["quantity"], 40)

    def test_liter_multiple_pack_options_rejected(self):
        self.assertIsNone(parse_liters("猫砂 5L×4袋 5L×8袋"))
        self.assertIsNone(parse_liters("猫砂 5L 4袋 8袋"))

    def test_liter_free_choice_rejected(self):
        self.assertIsNone(parse_liters("自由に選べ 猫砂 おから 7L×6袋"))

    def test_liter_range_rejected(self):
        self.assertIsNone(parse_liters("猫砂 1袋 6袋 12袋 2.5〜63L"))

    def test_liter_kg_only_rejected(self):
        self.assertIsNone(parse_liters("猫砂 5kg"))

    def test_food_future_parser(self):
        self.assertEqual(parse_100g("キャットフード 1.5kg×2袋")["quantity"], 30)

    def test_classifiers(self):
        self.assertEqual(sheet_size("ペットシーツ スーパーワイド 100枚"), "super_wide")
        self.assertEqual(litter_material("猫砂 おから 7L"), "okara")
        self.assertEqual(litter_material("猫砂 クリーンサンド 7L 鉱物系 ベントナイト"), "mineral")
        self.assertEqual(
            litter_material("猫砂 木の猫砂 木 ベントナイト 鉱物系 7L"),
            "mixed",
        )
        self.assertEqual(compatibility("デオトイレ 消臭シート 20枚"), "deotoilet")
        self.assertEqual(
            compatibility("ラクリーン システムトイレ用消臭シート 30枚"),
            "universal",
        )

    def test_non_retail_listing_excluded(self):
        category = {"include_any": ["ペットシーツ"], "exclude_any": []}
        for title in (
            "【ふるさと納税】ペットシーツ 800枚",
            "ペットシーツ 定期便 800枚",
            "中古 ペットシーツ 800枚",
            "訳あり ペットシーツ 800枚",
            "アウトレット ペットシーツ 800枚",
        ):
            self.assertFalse(category_matches(title, category))


if __name__ == "__main__":
    unittest.main()
