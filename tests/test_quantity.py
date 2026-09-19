import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from common.quantity import parse_count, parse_liters, parse_100g
from common.classify import sheet_size, litter_material, compatibility


class QuantityTests(unittest.TestCase):
    def test_count_multiplier(self):
        self.assertEqual(parse_count("ペットシーツ 200枚×4袋")["quantity"], 800)

    def test_count_single(self):
        self.assertEqual(parse_count("デオトイレ シート 20枚入")["quantity"], 20)

    def test_count_ambiguous_rejected(self):
        self.assertIsNone(parse_count("シート 20枚 30枚 選べる"))

    def test_liter_multiplier(self):
        self.assertEqual(parse_liters("猫砂 紙 10L×6袋")["quantity"], 60)

    def test_liter_kg_only_rejected(self):
        self.assertIsNone(parse_liters("猫砂 5kg"))

    def test_food_future_parser(self):
        self.assertEqual(parse_100g("キャットフード 1.5kg×2袋")["quantity"], 30)

    def test_classifiers(self):
        self.assertEqual(sheet_size("ペットシーツ スーパーワイド 100枚"), "super_wide")
        self.assertEqual(litter_material("猫砂 おから 7L"), "okara")
        self.assertEqual(compatibility("デオトイレ 消臭シート 20枚"), "deotoilet")


if __name__ == "__main__":
    unittest.main()
