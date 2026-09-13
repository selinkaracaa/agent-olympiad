"""Regression checks for the explicit historical packet boundary migration."""
from pathlib import Path
import tempfile
import unittest

from scripts.repair_mystery_hunt_sources_20260913 import (
    BRUNCH, SELECTED, check_css, check_html, normalize_newlines, prompt_newlines, sanitize,
)


class MysteryHuntSourceRepairTests(unittest.TestCase):
    def legacy(self):
        return (b'<html><body><pre> a  b\n   c &7Z </pre><table><tr><td>1</td><td>2</td></tr></table>'
                b'<a href="solution.html">Solution</a></body>'
                b'<script type="module" src="/checkanswer.js"></script></html>')

    def test_legacy_layout_is_byte_preserved(self):
        original = self.legacy()
        cleaned, edits = sanitize(original, "mystery_hunt_00014")
        expected = original.replace(b'<a href="solution.html">Solution</a>', b'').replace(
            b'<script type="module" src="/checkanswer.js"></script>', b'')
        self.assertEqual(cleaned, expected)
        self.assertEqual(len(edits), 2)

    def test_source_drift_is_not_silently_sanitized(self):
        with self.assertRaises(ValueError):
            sanitize(self.legacy().replace(b'Solution</a>', b'Answers</a>'), "mystery_hunt_00014")

    def test_duplicate_solution_controls_are_rejected(self):
        with self.assertRaises(ValueError):
            sanitize(self.legacy() + b'<a href="solution.html">Solution</a>', "mystery_hunt_00014")

    def test_brunch_removes_specific_disclosure_not_every_answer_word(self):
        page = (b'<html><head><link href="../puzzle.css"></head><body>'
                b'<div id="nav"><a href="answer/">Check</a></div>'
                b'<p class="text"><b>This event has occured.  The answer is SNIFF.</b></p>'
                b'<p>clue words are retained</p><img src="line.gif"><img src="name.gif">'
                b'<img src="invitation.jpg"></body><script type="module" src="/checkanswer.js"></script></html>')
        cleaned, edits = sanitize(page, BRUNCH)
        self.assertNotIn(b'SNIFF', cleaned)
        self.assertNotIn(b'answer/', cleaned)
        self.assertIn(b'<p>clue words are retained</p>', cleaned)
        self.assertIn(b'src="media/invitation.jpg"', cleaned)
        self.assertEqual(len(edits), 7)

    def test_remote_html_dependency_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'puzzle.html'
            path.write_text('<html><body><img src="https://example.com/a.png"></body></html>')
            with self.assertRaises(ValueError):
                check_html(path, {path.resolve()})

    def test_solution_sibling_not_on_allowlist_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'puzzle.html'
            hidden = Path(folder) / 'solution.html'
            hidden.write_text('secret')
            path.write_text('<html><body><a href="solution.html">reference</a></body></html>')
            with self.assertRaises(ValueError):
                check_html(path, {path.resolve()})

    def test_css_dependencies_must_be_local_and_allowlisted(self):
        with tempfile.TemporaryDirectory() as folder:
            css = Path(folder) / 'puzzle.css'
            css.write_text('body {background: url(missing.png)}')
            with self.assertRaises(ValueError):
                check_css(css, {css.resolve()})

    def test_only_newline_bytes_are_normalized_for_source_comparison(self):
        self.assertEqual(normalize_newlines(b'A\r\r\nB\r\n'), b'A\nB\n')
        self.assertNotEqual(normalize_newlines(b'A  B'), b'A B')

    def test_staged_information_partitions_are_not_selected(self):
        self.assertEqual(len(SELECTED), 14)
        self.assertNotIn('mystery_hunt_00009', SELECTED)
        self.assertNotIn('mystery_hunt_00015', SELECTED)

    def test_auxiliary_prompt_roundtrips_windows_newlines(self):
        prompt = prompt_newlines('first\r\n  second\r\n\r\nthird')
        windows_bytes = prompt.replace('\n', '\r\n').encode()
        self.assertEqual(windows_bytes.decode().replace('\r\n', '\n'), prompt)
        self.assertEqual(prompt, 'first\n  second\n\nthird')


if __name__ == '__main__':
    unittest.main()
