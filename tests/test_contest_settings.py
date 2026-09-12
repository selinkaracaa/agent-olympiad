from __future__ import annotations

import io
import os
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import run_competition_batch as cli
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import ContestRunConfig, _system_prompt, _resolved_actions, run_contest
from llm import LLMResponse, LLMToolCall


def example(competition="icpc"):
    return ContestManifest("settings-test", competition, (
        ManifestTask("q1", "q1", None, "Compute 6*7", "quiz", 1, False,
                     {"problem_id": "q1", "gold_label": {"expected_answer": "42"}}),
    ))


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class ContestSettingsTests(unittest.TestCase):
    def setUp(self):
        # CLI main loads .env; do not leak remote judge settings into later tests.
        env_patch = patch.dict(os.environ)
        env_patch.start()
        self.addCleanup(env_patch.stop)

    def test_retired_cross_root_skip_fails_before_batch_writes_or_launches(self):
        import run_otc_gold_suite as gold
        for value in ("old-results", ""):
            with (
                self.subTest(value=value),
                patch.object(sys, "argv", ["batch", "--skip-existing-roots", value]),
                patch.object(gold, "write_manifests") as manifests,
                patch.object(gold, "run_one") as launch,
                redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                gold.main()
            self.assertEqual(error.exception.code, 2)
            manifests.assert_not_called()
            launch.assert_not_called()

    def prepare(self, *flags, competition="icpc"):
        args = cli._build_parser().parse_args([
            "--live", "--contest-manifest", "fixture.json", "--system-variant", "decentralized", *flags,
        ])
        with patch.object(cli, "load_contest_manifest", return_value=example(competition)):
            return cli._prepare_contest_run(args)

    def test_registry_token_default_reaches_resolved_execution(self):
        identity = self.prepare()[3]
        self.assertEqual(identity["settings"]["execution"]["max_output_tokens"], 4096)

    def test_explicit_token_limit_wins_and_other_contests_fall_back(self):
        self.assertEqual(self.prepare("--max-output-tokens", "1234")[3]["settings"]["execution"]["max_output_tokens"], 1234)
        self.assertEqual(self.prepare(competition="arml_local")[3]["settings"]["execution"]["max_output_tokens"], 8192)

    def test_review_override_controls_both_gates(self):
        config = review_ablation_config(3, 12, require_review=False)
        self.assertFalse(config.review_required)
        self.assertFalse(config.final_review_required)

    def test_rule_root_and_prompt_only_reach_contestant_prompt(self):
        card = cli.load_rule_card("arml_local")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = dict(card.raw, rules_text="CUSTOM RULE ROOT MARKER")
            (root / "arml_local.json").write_text(json.dumps(payload), encoding="utf-8")
            manifest, config, _, _ = self.prepare(
                "--system-variant", "decentralized", "--rules-mode", "prompt_only",
                "--rules-root", str(root), competition="arml_local",
            )
        prompt = _system_prompt(config, "Agent_1", _resolved_actions(manifest, config))
        self.assertIn("CUSTOM RULE ROOT MARKER", prompt)
        self.assertEqual(config.features.coach, "none")
        self.assertEqual(config.features.rule_card, "prompt_only")
        self.assertNotIn("evaluation_guidance", prompt)

    def test_unsupported_enforcement_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "enforced.*otc"):
            self.prepare("--system-variant", "decentralized", "--rules-mode", "enforced")

    def test_otc_uses_custom_root_and_rejects_conflicting_modes_and_reviews(self):
        card = cli.load_rule_card("arml_local")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "arml_local.json").write_text(json.dumps(dict(card.raw, rules_text="OTC CUSTOM ROOT")), encoding="utf-8")
            _, config, _, identity = self.prepare(
                "--system-variant", "otc", "--team-size", "6", "--rules-root", str(root),
                competition="arml_local",
            )
            self.assertEqual(config.rule_card.rules_text, "OTC CUSTOM ROOT")
            self.assertEqual(config.features.rule_card, "enforced")
            self.assertIsNotNone(identity["settings"]["config"]["rule_card_hash"])
        for flags in (("--rules-mode", "off"), ("--rules-mode", "prompt_only"), ("--no-require-review",)):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                self.prepare("--system-variant", "otc", "--team-size", "6", *flags, competition="arml_local")

    def test_rule_options_with_off_mode_are_not_silently_ignored(self):
        for flags in (("--rules-root", "custom"), ("--rules-strict",)):
            with self.subTest(flags=flags), self.assertRaises(ValueError):
                self.prepare(*flags)

    def test_final_review_can_be_independently_disabled_or_enabled(self):
        _, config, _, identity = self.prepare("--no-require-review", "--require-final-review")
        self.assertFalse(config.review_required)
        self.assertTrue(config.final_review_required)
        self.assertFalse(identity["settings"]["config"]["baseline"]["review_workflow"])
        _, config, _, _ = self.prepare("--require-review", "--no-require-final-review")
        self.assertTrue(config.review_required)
        self.assertFalse(config.final_review_required)

    def test_final_only_review_is_actually_executable(self):
        def request(req):
            functions = {item["name"]: item for item in req.tools}
            if req.metadata.get("task_id") is None and "select_problem" in functions:
                name, arguments = "select_problem", {"problem_id": "q1"}
            elif "review_answer" in functions:
                props = functions["review_answer"]["parameters"]["properties"]
                name, arguments = "review_answer", {
                    "problem_id": props["problem_id"]["enum"][0],
                    "version_hash": props["version_hash"]["enum"][0],
                    "decision": "approve", "content": "Verified 6 times 7 is 42",
                }
            elif "submit" in functions:
                props = functions["submit"]["parameters"]["properties"]
                name, arguments = "submit", ({"answer": "42"} if "answer" in props else {})
            elif "work" in functions:
                name, arguments = "work", {"content": "42"}
            else:
                name, arguments = "rest", {}
            return LLMResponse("", "perplexity", "mock", tool_calls=(LLMToolCall(name, arguments),))
        sheet = example("arml_local")
        sheet = replace(sheet, tasks=(*sheet.tasks, replace(sheet.tasks[0], task_id="q2", parent_problem_id="q2")))
        for variant in ("decentralized", "centralized"):
            with self.subTest(variant=variant):
                result = run_with_test_plan(
                    sheet, lambda *_: "{}", ContestRunConfig(
                        variant, 2, 5, require_review=False, require_final_review=True,
                    ), action_request_fn=request, action_transport="native",
                    coach_query_fn=(lambda *_: "{}") if variant == "centralized" else None,
                )
                kinds = [event["kind"] for event in result["memory"]["events"]]
                self.assertIn("final_review_approved", kinds)
                self.assertIn("final_review_completed", kinds)
                self.assertFalse(result["baseline"]["review_workflow"])
                self.assertTrue(result["final_review_required"])

    def test_missing_card_non_strict_records_unavailable_and_strict_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            out = root / "out"
            argv = ["run_competition_batch.py", "--live", "--contest-manifest", "fixture.json",
                    "--system-variant", "decentralized", "--rules-mode", "prompt_only", "--rules-root", str(root / "absent"),
                    "--output", str(out)]
            with patch.object(cli, "load_contest_manifest", return_value=example()), patch.object(cli, "_make_live_query") as provider, patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                cli.main()
                provider.assert_not_called()
            self.assertEqual(json.loads((out / "rules_status.json").read_text())["status"], "rules_baseline_unavailable")
            self.assertFalse((out / "contest_session.json").exists())
            before = (out / "rules_status.json").read_bytes()
            with patch.object(cli, "load_contest_manifest", return_value=example()), patch.object(cli, "_make_live_query") as provider, patch.object(sys, "argv", [*argv, "--rules-strict"]), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                cli.main()
            provider.assert_not_called()
            self.assertEqual((out / "rules_status.json").read_bytes(), before)

    def test_resolved_limit_reaches_both_live_factories_and_saved_result(self):
        with tempfile.TemporaryDirectory() as directory:
            argv = ["run_competition_batch.py", "--live", "--contest-manifest", "fixture.json",
                    "--system-variant", "decentralized", "--max-turns", "1",
                    "--no-judge-task", "--no-judge-collab", "--output", directory]
            request = lambda _: LLMResponse("", "perplexity", "mock", tool_calls=(LLMToolCall("rest", {}),))
            with patch.object(cli, "load_contest_manifest", return_value=example()), patch.object(cli, "_make_live_query", return_value=lambda *_: "") as query_factory, patch.object(cli, "resolve_request_fn", return_value=request) as action_factory, patch.object(sys, "argv", argv), redirect_stdout(io.StringIO()):
                cli.main()
            self.assertEqual(query_factory.call_args.kwargs["max_output_tokens"], 4096)
            self.assertEqual(action_factory.call_args.kwargs["max_output_tokens"], 4096)
            result = json.loads((Path(directory) / "contest_session.json").read_text(encoding="utf-8"))
            self.assertEqual(result["run"]["max_output_tokens"], 4096)
            self.assertEqual(result["run_identity"]["settings"]["execution"]["max_output_tokens"], 4096)


if __name__ == "__main__":
    unittest.main()
