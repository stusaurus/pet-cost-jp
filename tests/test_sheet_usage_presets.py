"""Pet sheet 1-tap usage presets preserve size fit, purchase math and data safety."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_site import usage_panel


class SheetUsagePresetTests(unittest.TestCase):
    def test_only_pet_sheets_show_explicit_usage_shortcuts(self):
        sheet = usage_panel({"id": "pet-sheets"})
        self.assertIn('data-sheet-usage-presets', sheet)
        for n in (1, 3, 5, 10):
            self.assertIn(f'data-usage-preset="{n}"', sheet)
            self.assertIn(f'{n}枚/日', sheet)
        self.assertEqual(sheet.count('data-usage-preset="'), 4)
        self.assertIn('aria-pressed="false"', sheet)
        self.assertIn('type="button" class="sheet-usage-preset"', sheet)
        self.assertIn('おすすめの交換頻度ではありません', sheet)
        self.assertIn('data-sheet-stock-input', sheet)
        self.assertIn('data-usage-panel hidden', sheet)

    def test_no_presets_for_cat_litter_or_system_toilet(self):
        for category in ('cat-litter', 'system-toilet-sheets'):
            with self.subTest(category=category):
                html = usage_panel({"id": category})
                self.assertNotIn('data-usage-preset', html)
                self.assertIn('data-usage-form', html)

    def test_existing_math_is_invoked_and_presets_never_skip_fit_filter(self):
        code = (ROOT / "scripts" / "analytics_runtime.js").read_text(encoding="utf-8")
        self.assertIn("const usagePreset = event.target.closest('[data-usage-preset]')", code)
        self.assertIn("if (usagePreset && category === 'pet-sheets')", code)
        self.assertIn("[1, 3, 5, 10].includes(count) && input && activeGroup", code)
        self.assertIn("input.value = String(count);", code)
        self.assertIn("setUsage(true);", code)
        self.assertIn("Number(button.dataset.usagePreset) === usage", code)
        self.assertIn("setSheetStock()", code)
        self.assertIn("appendSheetPurchasePlan", code)
        self.assertIn("if (category === 'pet-sheets') usagePanel.open = true;", code)

    def test_mobile_44_pixel_keyboard_focus_and_selection_state(self):
        css = (ROOT / "assets" / "living.css").read_text(encoding="utf-8")
        self.assertIn(".sheet-usage-preset{min-height:44px", css)
        self.assertIn(".sheet-usage-preset:focus-visible", css)
        self.assertIn('.sheet-usage-preset[aria-pressed="true"]', css)


if __name__ == "__main__":
    unittest.main()
