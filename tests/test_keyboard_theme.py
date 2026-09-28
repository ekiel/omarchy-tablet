import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from keyboard_theme import KeyboardTheme, palette, stylesheet, STYLES
from tablet import Backend


class KeyboardThemeTests(unittest.TestCase):
    def test_palette_changes_and_missing_or_invalid_theme(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            path = root / 'colors.toml'
            theme = KeyboardTheme(root, path)
            fallback = theme.prepare('omarchy')
            path.write_text('background = "#ffffff"\nforeground = "#123456"\naccent = "#224488"\n')
            light = theme.prepare('omarchy')
            self.assertNotEqual(fallback, light)
            self.assertIn('background: #ffffff', light)
            self.assertIn('color: #ffffff; border-color: #224488', light)
            path.write_text('accent = "bad; CSS injection"')
            self.assertEqual(theme.prepare('omarchy'), fallback)
            path.write_text('invalid = [')
            self.assertEqual(theme.prepare('omarchy'), fallback)

    def test_three_distinct_styles_and_reject_unknown(self):
        colors = {'background': '#ffffff', 'foreground': '#222222', 'accent': '#88aaff'}
        self.assertEqual(len({stylesheet(colors, s) for s in STYLES}), 3)
        contrast = stylesheet(colors, 'contrast')
        self.assertIn('2px solid #000000', contrast)
        with self.assertRaises(ValueError):
            stylesheet(colors, 'unknown')

    def test_preferences_persist_and_reload_waits_until_hidden(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ', {'XDG_RUNTIME_DIR': '/tmp'}):
            b = Backend(Path(folder))
            b.keyboard_theme = KeyboardTheme(Path(folder), Path(folder) / 'colors.toml')
            b.command({'action': 'keyboardStyle', 'value': 'rounded'})
            self.assertEqual(Backend(Path(folder)).preferences['keyboardStyle'], 'rounded')
            with self.assertRaises(ValueError):
                b.command({'action': 'keyboardStyle', 'value': []})
            b.manual_keyboard = True
            b.keyboard_started = True
            b.next_keyboard_check = b.next_style_check = float('inf')
            b.layout_dirty = False
            with patch.object(b, 'state', return_value={'tablet': True, 'keyboardAvailable': True}), \
                 patch.object(b, 'visible', return_value=True) as visible, patch('tablet.run') as run:
                b.reconcile()
                run.assert_not_called()
                visible.return_value = False
                b.reconcile()
                run.assert_called_once_with('systemctl', '--user', 'restart', 'omarchy-tablet-keyboard.service')
                b.reconcile()
                self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
