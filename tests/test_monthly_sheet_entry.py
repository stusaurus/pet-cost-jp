"""Homepage link targets the existing pet sheet purchase calculator."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_site import homepage, monthly_pet_sheet_guide


class MonthlySheetEntryTests(unittest.TestCase):
    def test_home_link_targets_existing_calculator(self):
        # Empty category list is sufficient to validate the static home entry.
        html = homepage([], {}, "2026-11-21")
        self.assertIn("categories/pet-sheets/#comparison-conditions", html)
        self.assertIn("手持ち在庫を引いて、30日分の購入セット数を計算する", html)
        self.assertIn("交換回数をおすすめするものではありません", html)
        self.assertIn('id="monthly-sheet-guide-heading"', monthly_pet_sheet_guide())


if __name__ == "__main__":
    unittest.main()
