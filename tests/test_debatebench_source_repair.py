"""Offline checks for round-local source extraction and historical role labels."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_debatebench_sources_20260913 import SPEAKING_ORDER, role_alignment, verify_motion_source


class DebateBenchSourceRepairTests(unittest.TestCase):
    def setUp(self):
        self.source = dict(source_url="https://example.test/motions/", round_heading="Round 1",
                           motion="Motion one", infoslide="First paragraph. Second paragraph.",
                           infoslide_status="published_present")
        self.html = b'''<div class="card"><h4 class="card-title">Round 1</h4>
          <li class="list-group-item"><div class="mr-auto lead">Motion one</div></li>
          <div class="modal-body lead"><p>First paragraph.</p><p>Second paragraph.</p></div></div>
          <div class="card"><h4 class="card-title">Round 2</h4>
          <li class="list-group-item"><div class="mr-auto lead">Motion two</div></li></div>'''

    def test_exact_motion_and_complete_slide_in_same_round(self):
        verify_motion_source(self.html, self.source)

    def test_another_round_motion_is_rejected(self):
        source = dict(self.source, motion="Motion two")
        with self.assertRaisesRegex(ValueError, "selected official round"):
            verify_motion_source(self.html, source)

    def test_incomplete_slide_is_rejected(self):
        source = dict(self.source, infoslide="First paragraph.")
        with self.assertRaisesRegex(ValueError, "Infoslide differs"):
            verify_motion_source(self.html, source)

    def test_absent_slide_is_verified_within_its_round(self):
        source = dict(self.source, round_heading="Round 2", motion="Motion two", infoslide="",
                      infoslide_status="published_blank_or_absent")
        verify_motion_source(self.html, source)
        source["infoslide_status"] = "published_present"
        with self.assertRaisesRegex(ValueError, "Infoslide status"):
            verify_motion_source(self.html, source)

    def test_duplicate_round_headings_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly one matching round"):
            verify_motion_source(self.html + self.html, self.source)

    def test_statistics_and_short_label_are_not_motion_text(self):
        source = dict(self.source, source_url="https://example.test/motions/statistics/", infoslide="",
                      infoslide_status="published_blank_or_absent")
        html = b'''<div class="list-group"><span class="badge badge-secondary">Round 1</span>
          <h4 class="mb-3 mt-1"><small>Short label</small>Motion one</h4>
          <table><tr><td>OG win rate 90%</td></tr></table></div>'''
        verify_motion_source(html, source)
        source["motion"] += " OG win rate 90%"
        with self.assertRaisesRegex(ValueError, "Motion differs"):
            verify_motion_source(html, source)

    def test_role_labels_use_speaking_order_not_workbook_order(self):
        transcript = "".join(f"<{role}>Speech</{role}>" for role in SPEAKING_ORDER)
        self.assertTrue(role_alignment(transcript)["valid_role_boundaries"])
        workbook_order = ("PM", "DPM", "LO", "DLO", "MG", "GW", "MO", "OW")
        wrong = "".join(f"<{role}>Speech</{role}>" for role in workbook_order)
        self.assertFalse(role_alignment(wrong)["valid_role_boundaries"])
        self.assertFalse(role_alignment(transcript.replace("</OW>", ""))["valid_role_boundaries"])


if __name__ == "__main__":
    unittest.main()
