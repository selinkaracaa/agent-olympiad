"""Delivery format is shared by all baselines without enabling Coach."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import run_competition_batch as cli
from contest_config import BASELINE_NAMES
from contest_manifest import ContestManifest, ManifestTask


def manifest(competition):
    return ContestManifest("fixture", competition, (
        ManifestTask("q", "q", None, "Question", "math", 1, False,
                     {"gold_label": {"expected_answer": "42"}}),))


class DeliveryRouteBaselineTests(unittest.TestCase):
    def prepare(self, competition, variant, output):
        args = cli._build_parser().parse_args([
            "--contest-manifest", "unused.json", "--system-variant", variant,
            "--max-turns", "1", "--output", str(output)])
        with patch.object(cli, "load_contest_manifest", return_value=manifest(competition)):
            return cli._prepare_contest_run(args)

    def test_all_five_baselines_reject_native_document_and_slide_routes(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "not-created"
            for competition, route in (("mcm", "document"), ("ieo_business_case", "slides")):
                for variant in BASELINE_NAMES:
                    with self.subTest(competition=competition, baseline=variant):
                        with self.assertRaisesRegex(ValueError, "requires the " + route):
                            self.prepare(competition, variant, output)
                        self.assertFalse(output.exists())

    def test_native_route_does_not_enable_rule_card_or_coach_for_plain_baselines(self):
        with tempfile.TemporaryDirectory() as directory:
            for variant in ("single_agent", "decentralized", "centralized"):
                with self.subTest(baseline=variant):
                    _, config, _, identity = self.prepare("arml_local", variant, directory)
                    self.assertIsNone(config.rule_card)
                    self.assertIsNone(config.otc_policy)
                    self.assertFalse(config.modules.coach)
                    self.assertFalse(config.modules.memory)
                    self.assertEqual(config.features.rule_card, "off")
                    self.assertIsNone(identity["settings"]["config"]["rule_card_hash"])

    def test_otc_native_presets_keep_existing_module_difference(self):
        with tempfile.TemporaryDirectory() as directory:
            for variant in ("vallina_otc", "otc"):
                _, config, _, _ = self.prepare("arml_local", variant, directory)
                self.assertIsNotNone(config.rule_card)
                self.assertTrue(config.modules.coach)
                self.assertEqual(config.modules.memory, variant == "otc")


if __name__ == "__main__":
    unittest.main()
