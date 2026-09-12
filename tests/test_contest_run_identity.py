from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(REPO_ROOT / "src"), str(REPO_ROOT / "scripts")]

import run_competition_batch as cli
import run_all_icpc_full_pairs as icpc_batch
import run_otc_gold_suite as gold_batch
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import ContestRunConfig
from contest_run_identity import (
    RunCompatibilityError, build_run_identity, inspect_contest_output,
)


def manifest() -> ContestManifest:
    return ContestManifest("example", "custom", (
        ManifestTask("q1", "q1", None, "What is 6 times 7?", "quiz", 1, False,
                     {"problem_id": "q1", "gold_label": {"expected_answer": "42"}}),
    ))


class IdentityTests(unittest.TestCase):
    def test_icpc_fresh_and_resumed_jobs_use_the_official_entry(self):
        benchmark = self.root / "benchmark.json"
        benchmark.write_text(json.dumps([{
            "year": 2012, "problem_id": "icpc-p1",
            "evaluation": {"status": "remote_judge_ready", "vjudge_prob_num": "p1"},
        }]), encoding="utf-8")
        for mode in ("new", "resume"):
            with (
                self.subTest(mode=mode),
                patch.object(sys, "argv", ["batch", "--output-root", str(self.root / mode)]),
                patch.object(icpc_batch, "BENCHMARK", benchmark),
                patch.object(icpc_batch, "inspect_contest_run", return_value=(mode, self.identity())),
                patch.object(icpc_batch, "gateway_ready", return_value=True),
                patch.object(icpc_batch, "completed", return_value=True),
                patch.object(icpc_batch.time, "sleep"),
                patch.object(icpc_batch.subprocess, "run") as process,
            ):
                process.return_value.returncode = 0
                self.assertEqual(icpc_batch.main(), 0)
                self.assertEqual(process.call_count, 2)
                for call in process.call_args_list:
                    command = call.args[0]
                    self.assertEqual(Path(command[2]), REPO_ROOT / "src" / "run_competition_batch.py")
                    self.assertEqual("--resume" in command, mode == "resume")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "src"
        self.source.mkdir()
        (self.source / "engine.py").write_text("VERSION = 1\n", encoding="utf-8")
        self.config = ContestRunConfig("vanilla", 2, 12, max_api_calls=24)
        self.execution = {"mode": "live", "provider": "perplexity", "model": "model-a",
                          "temperature": 0.2, "max_output_tokens": 8192,
                          "action_calling": "native"}

    def identity(self, *, config=None, tasks=None, execution=None):
        return build_run_identity(
            tasks or manifest(), config or self.config,
            execution=execution or self.execution,
            evaluation={"judge_collab": False}, source_root=self.source,
        )

    def write(self, name, payload):
        path = self.root / name
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def result(self, identity):
        settings = identity["settings"]
        return {
            **{k: settings[k] for k in ("session_id", "competition_id", "protocol_version", "action_set_version")},
            "system_variant": settings["config"]["system_variant"],
            "run_identity": identity,
            "grade": {"graded": False},
            "metrics": {"task_utility": None},
            "session_checkpoint": {"final_summary": {}},
        }

    def test_aliases_and_equivalent_review_defaults_share_identity(self):
        same = replace(self.config, system_variant="decentralized", require_review=False)
        self.assertEqual(self.identity(), self.identity(config=same))

    def test_effective_configuration_changes_invalidate_identity(self):
        baseline = self.identity()["fingerprint"]
        for updates in (
            {"team_size": 3}, {"max_turns": 13}, {"max_api_calls": 25},
            {"max_tokens": 1000}, {"max_simulated_minutes": 20},
            {"minutes_per_turn": 2}, {"start_seat": 1},
            {"require_review": True}, {"require_final_review": True},
            {"programming_deadline_submit": True},
            {"features": replace(self.config.features, memory_actions=True)},
        ):
            with self.subTest(updates=updates):
                self.assertNotEqual(baseline, self.identity(config=replace(self.config, **updates))["fingerprint"])
        for key, value in (("model", "model-b"), ("temperature", 0.7),
                           ("max_output_tokens", 4096), ("action_calling", "prompt_json")):
            self.assertNotEqual(baseline, self.identity(execution={**self.execution, key: value})["fingerprint"])

    def test_task_content_order_rule_card_and_source_changes_are_detected(self):
        original = manifest()
        second = replace(original.tasks[0], task_id="q2", parent_problem_id="q2")
        pair = replace(original, tasks=(*original.tasks, second))
        self.assertNotEqual(self.identity(tasks=pair), self.identity(tasks=replace(pair, tasks=pair.tasks[::-1])))
        self.assertNotEqual(self.identity(), self.identity(tasks=replace(original, tasks=(replace(original.tasks[0], prompt="Changed"),))))
        benchmark = copy.deepcopy(original.tasks[0].benchmark)
        benchmark["gold_label"]["expected_answer"] = "43"
        self.assertNotEqual(self.identity(), self.identity(tasks=replace(original, tasks=(replace(original.tasks[0], benchmark=benchmark),))))
        card = cli.load_rule_card("arml_local")
        config = ContestRunConfig("otc", card.team_size_default, 12, rule_card=card)
        changed = replace(config, rule_card=replace(card, rules_text=card.rules_text + " Revised."))
        self.assertNotEqual(self.identity(config=config), self.identity(config=changed))
        before = self.identity()
        (self.source / "engine.py").write_text("VERSION = 2\n", encoding="utf-8")
        self.assertNotEqual(before, self.identity())
        with patch("contest_run_identity.ACTION_SET_VERSION", 999):
            self.assertNotEqual(self.identity()["settings"]["action_set_version"], before["settings"]["action_set_version"])

    def test_legacy_outputs_fail_closed_and_are_untouched(self):
        path = self.write("contest_session.json", {"session_id": "example", "grade": {"graded": True}})
        before = path.read_bytes()
        with self.assertRaisesRegex(RunCompatibilityError, "missing resolved run identity"):
            gold_batch.case_complete(self.root, self.identity())
        with self.assertRaises(RunCompatibilityError):
            icpc_batch.completed(self.root, self.identity())
        self.assertEqual(path.read_bytes(), before)

    def test_same_identity_skips_even_when_grading_is_unavailable(self):
        identity = self.identity()
        self.write("contest_session.json", self.result(identity))
        self.assertTrue(gold_batch.case_complete(self.root, identity))
        self.assertTrue(icpc_batch.completed(self.root, identity))

    def test_wrong_identity_or_envelope_never_counts_as_completed(self):
        identity = self.identity()
        for key, value in (("session_id", "wrong"), ("system_variant", "otc"),
                           ("protocol_version", "contest_session_v3"), ("action_set_version", -1)):
            result = self.result(identity)
            result[key] = value
            self.write("contest_session.json", result)
            with self.subTest(key=key), self.assertRaises(RunCompatibilityError):
                inspect_contest_output(self.root, identity)
        self.write("contest_session.json", self.result(identity))
        changed = self.identity(execution={**self.execution, "model": "model-b"})
        with self.assertRaisesRegex(RunCompatibilityError, "execution.model"):
            inspect_contest_output(self.root, changed)

    def test_partial_checkpoint_requires_matching_identity_and_action_version(self):
        identity = self.identity()
        self.assertEqual(inspect_contest_output(self.root, identity), "new")
        checkpoint = {"run_identity": identity, "session": {}, "memory": "{}",
                      "protocol_version": identity["settings"]["protocol_version"],
                      "action_set_version": identity["settings"]["action_set_version"]}
        self.write("contest_checkpoint.json", checkpoint)
        self.assertEqual(inspect_contest_output(self.root, identity), "resume")
        checkpoint["action_set_version"] = -1
        self.write("contest_checkpoint.json", checkpoint)
        with self.assertRaises(RunCompatibilityError):
            inspect_contest_output(self.root, identity)


class CliIdentityTests(unittest.TestCase):
    def setUp(self):
        # Batch CLI tests must not leak .env judge configuration to other suites.
        env_patch = patch.dict("os.environ")
        env_patch.start()
        self.addCleanup(env_patch.stop)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name) / "run"
        self.argv = ["--contest-manifest", "fixture.json", "--output", str(self.out),
                     "--system-variant", "vanilla", "--team-size", "1", "--max-turns", "3",
                     "--max-api-calls", "3", "--no-judge-collab", "--no-judge-task"]
        patcher = patch.object(cli, "load_contest_manifest", return_value=manifest())
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_cli(self, extra=()):
        with patch.object(sys, "argv", ["run_competition_batch.py", *self.argv, *extra]), redirect_stdout(io.StringIO()):
            cli.main()

    def test_mock_run_persists_identity_and_matching_resume_skips_without_provider(self):
        with patch.object(cli, "resolve_query_fn", return_value=lambda *_: '{"action":"work","arguments":{"content":"42"}}'):
            self.run_cli()
        state, identity = cli.inspect_contest_run(self.argv)
        self.assertEqual(state, "complete")
        for name in ("run_config.json", "contest_checkpoint.json", "contest_session.json"):
            payload = json.loads((self.out / name).read_text(encoding="utf-8"))
            self.assertEqual(payload if name == "run_config.json" else payload["run_identity"], identity)
        before = {p.name: p.read_bytes() for p in self.out.iterdir()}
        with patch.object(cli, "resolve_query_fn", side_effect=AssertionError("must not start provider")):
            self.run_cli(["--resume"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.out.iterdir()})
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_cli(["--resume", "--max-turns", "4"])
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.out.iterdir()})

    def test_interrupted_checkpoint_resumes_and_preserves_history(self):
        original_write = cli._write_json_atomic
        def interrupt_after_checkpoint(path, payload):
            original_write(path, payload)
            if path.name == "contest_checkpoint.json":
                raise InterruptedError("simulated interruption")
        with patch.object(cli, "resolve_query_fn", return_value=lambda *_: '{"action":"select_problem","arguments":{"problem_id":"q1"}}'), patch.object(cli, "_write_json_atomic", side_effect=interrupt_after_checkpoint):
            with self.assertRaises(InterruptedError):
                self.run_cli()
        self.assertEqual(cli.inspect_contest_run(self.argv)[0], "resume")
        checkpoint = json.loads((self.out / "contest_checkpoint.json").read_text(encoding="utf-8"))
        old_events = json.loads(checkpoint["memory"])["events"]
        with patch.object(cli, "resolve_query_fn", return_value=lambda *_: '{"action":"work","arguments":{"content":"42"}}'):
            self.run_cli(["--resume"])
        result = json.loads((self.out / "contest_session.json").read_text(encoding="utf-8"))
        self.assertEqual(result["memory"]["events"][:len(old_events)], old_events)
        self.assertEqual(cli.inspect_contest_run(self.argv)[0], "complete")

    def test_live_preflight_is_read_only_and_legacy_rejected_before_provider(self):
        state, _identity = cli.inspect_contest_run([*self.argv, "--live"])
        self.assertEqual(state, "new")
        self.assertFalse(self.out.exists())
        self.out.mkdir()
        result = self.out / "contest_session.json"
        result.write_text('{"protocol_version":"contest_session_v3"}', encoding="utf-8")
        before = result.read_bytes()
        with patch.object(cli, "_make_live_query", side_effect=AssertionError("must not start provider")), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            self.run_cli(["--live", "--resume"])
        self.assertEqual(result.read_bytes(), before)
        self.assertFalse((self.out / "run_config.json").exists())

    def test_gold_batch_rejects_legacy_before_launching_a_process(self):
        run_dir = self.out / "fixture"
        run_dir.mkdir(parents=True)
        result_path = run_dir / "contest_session.json"
        result_path.write_text('{"grade":{"graded":true},"metrics":{"task_utility":1}}', encoding="utf-8")
        before = result_path.read_bytes()
        with patch.object(gold_batch.subprocess, "run") as process:
            result = gold_batch.run_one(
                Path("fixture.json"), out_root=self.out, team_size=1,
                max_turns=3, max_api_calls=3, system_variant="vanilla",
            )
        self.assertEqual(result["status"], "blocked")
        process.assert_not_called()
        self.assertEqual(result_path.read_bytes(), before)
        self.assertFalse((run_dir / "run.log").exists())

    def test_gold_batch_adds_resume_and_does_not_trust_exit_zero(self):
        with patch.object(gold_batch, "inspect_contest_run", return_value=("resume", {})), patch.object(gold_batch, "case_complete", return_value=False), patch.object(gold_batch.subprocess, "run") as process:
            process.return_value.returncode = 0
            result = gold_batch.run_one(
                Path("fixture.json"), out_root=self.out, team_size=1,
                max_turns=3, max_api_calls=3, system_variant="vanilla",
            )
        self.assertIn("--resume", process.call_args.args[0])
        self.assertEqual(result["status"], "error")


if __name__ == "__main__":
    unittest.main()
