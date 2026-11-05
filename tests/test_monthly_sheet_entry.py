"""Homepage link targets the existing monthly sheet guide."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from build_site import homepage, monthly_pet_sheet_guide


class MonthlySheetEntryTests(unittest.TestCase):
    def test_home_link_targets_existing_guide(self):
        # Empty category list is sufficient to validate the static home entry.
        html = homepage([], {}, "2026-11-05")
        self.assertIn("categories/pet-sheets/#monthly-sheet-guide-heading", html)
        self.assertIn("交換頻度をおすすめするものではありません", html)
        self.assertIn('id="monthly-sheet-guide-heading"', monthly_pet_sheet_guide())


if __name__ == "__main__":
    unittest.main()
