"""OTC naming, protocol migration, and module-boundary regression checks."""
from __future__ import annotations

import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

import collaboration
import contest_actions
import contest_runner
import run_competition_batch as cli
from contest_config import BASELINES, ContestRunConfig, PROTOCOL_VERSION
from contest_manifest import ContestManifest, ManifestTask
from contest_run_identity import (
    RunCompatibilityError, build_run_identity, content_hash, validate_run_identity,
)
from rules.loader import load_rule_card
from run_otc_gold_suite import budget_for, team_size_for

OTC_NAMES = ("otc", "OTC", "open_table_coach", "open_table_coach_memory",
             "strategic", "strategic_team")


class OtcMigrationTests(unittest.TestCase):
    def setUp(self):
        self.card = load_rule_card("icpc")
        self.manifest = ContestManifest("migration", "icpc", (
            ManifestTask("a", "a", None, "Print 42", "algorithmic_programming",
                         1, True, {}),
        ))

    def config(self, name):
        return ContestRunConfig(name, 3, 2, rule_card=self.card)

    def test_five_canonical_presets_remain(self):
        self.assertEqual(set(BASELINES), {"single_agent", "decentralized", "centralized", "otc", "vallina_otc"})
        self.assertEqual(PROTOCOL_VERSION, "contest_session_v6")
        self.assertFalse(hasattr(collaboration, "run_open_table_coach"))
        self.assertFalse(hasattr(contest_runner, "_precontest_coach_prompts"))

    def test_aliases_have_identical_effective_configuration_and_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            identities = [build_run_identity(
                self.manifest, self.config(name), execution={}, evaluation={},
                source_root=Path(directory),
            ) for name in OTC_NAMES]
        self.assertTrue(all(item == identities[0] for item in identities))
        for name in OTC_NAMES:
            self.assertEqual(self.config(name).system_variant, "otc")
            self.assertEqual(self.config(name).features, BASELINES["otc"])

    def test_default_and_alias_cli_resolve_card_roster_and_budget(self):
        for name in (None, *OTC_NAMES):
            flags = [] if name is None else ["--system-variant", name]
            args = cli._build_parser().parse_args(["--contest-manifest", "fixture.json", *flags])
            with patch.object(cli, "load_contest_manifest", return_value=self.manifest):
                _, config, _, _ = cli._prepare_contest_run(args)
            self.assertEqual(config.system_variant, "otc")
            self.assertEqual(config.team_size, self.card.team_size_default)
            self.assertEqual(config.max_api_calls, config.max_turns * config.team_size * 2 + 1)

    def test_batch_helpers_normalize_before_roster_and_budget_resolution(self):
        for name in OTC_NAMES:
            self.assertEqual(team_size_for("arml_local", None, name), 6)
            self.assertEqual(budget_for("arml_local", 6, name), budget_for("arml_local", 6, "otc"))
        with self.assertRaises(SystemExit):
            team_size_for("arml_local", 3, "open_table_coach")

    def test_old_per_problem_entry_fails_before_any_model_call(self):
        query = Mock()
        for name in OTC_NAMES:
            with self.assertRaisesRegex(ValueError, "--contest-manifest"):
                collaboration.run_collaboration(name, object(), query)
        query.assert_not_called()

    def test_otc_cannot_reenable_the_removed_protocol_or_skip_its_card(self):
        for name in OTC_NAMES:
            with self.assertRaises(ValueError):
                ContestRunConfig(name, 3, 2)
        with self.assertRaisesRegex(ValueError, "unsupported coach mode"):
            replace(self.config("otc"), features=replace(BASELINES["otc"], coach="precontest"))
        with self.assertRaisesRegex(ValueError, "requires independent review"):
            replace(self.config("otc"), require_review=False)

    def test_v4_identity_is_rejected_without_relabeling_it(self):
        identity = build_run_identity(self.manifest, self.config("otc"), execution={}, evaluation={})
        old_settings = dict(identity["settings"], protocol_version="contest_session_v4")
        old = {"settings": old_settings, "fingerprint": content_hash(old_settings)}
        with self.assertRaisesRegex(RunCompatibilityError, "protocol_version"):
            validate_run_identity(old, identity, artifact=Path("historical/contest_session.json"))
        self.assertEqual(old["settings"]["protocol_version"], "contest_session_v4")

    def test_extracted_modules_have_one_implementation_and_no_runner_dependency(self):
        self.assertIs(contest_runner.ContestRunConfig, ContestRunConfig)
        self.assertIs(contest_runner._apply_action, contest_actions._apply_action)
        for module in ("contest_actions.py", "contest_config.py"):
            self.assertNotIn("import contest_runner", (ROOT / "src" / module).read_text())
            self.assertNotIn("from contest_runner", (ROOT / "src" / module).read_text())


if __name__ == "__main__":
    unittest.main()
