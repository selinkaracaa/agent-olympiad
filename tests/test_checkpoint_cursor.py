"""Checkpoint cursors preserve a seat's memory and ordinary action boundaries."""
from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from collections import Counter
from contextlib import redirect_stdout
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from contest_config import BASELINE_NAMES, ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_runner import run_contest
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card
import run_competition_batch as cli


class InterruptedCheckpoint(BaseException):
    pass


def manifest():
    return ContestManifest("cursor-fixture", "arml_local", (
        ManifestTask("q1", "q1", None, "What is 6 times 7?", "math", 1, False,
                     {"problem_id": "q1", "gold_label": {"expected_answer": "42"}}),
    ))


def config(variant="otc", *, max_turns=1, deadline_submit=True):
    card = load_rule_card("arml_local", required=True)
    return ContestRunConfig(
        variant, 1 if variant == "single_agent" else
        card.team_size_default if variant in {"otc", "vallina_otc"} else 3,
        max_turns, rule_card=card if variant in {"otc", "vallina_otc"} else None,
        max_api_calls=200, max_tokens=50000, minutes_per_turn=5,
        max_simulated_minutes=5 * max_turns, deadline_submit=deadline_submit,
    )


class Team:
    def __init__(self, side_calls=0, fail_memory=False):
        self.side_calls = side_calls
        self.fail_memory = fail_memory
        self.memory_calls = Counter()
        self.ordinary_calls = Counter()
        self.queries = []
        self.requests = []

    def query(self, system, user):
        self.queries.append((system, user))
        return "Divide the work, then verify."

    def request(self, request):
        agent = request.metadata["agent"]
        offered = {tool["name"] for tool in request.tools}
        count = self.memory_calls[agent]
        self.requests.append((agent, offered))
        if self.side_calls and count < self.side_calls and "remember" in offered:
            self.memory_calls[agent] += 1
            name, args = ("share_note", {"note_id": "missing-note"}) if self.fail_memory else (
                "remember", {"content": "Fact 42 for " + agent})
        else:
            if self.side_calls == 3 and count == 3:
                if offered & {"remember", "recall", "share_note"}:
                    raise AssertionError("Restoration reset the auxiliary-call allowance")
            self.ordinary_calls[agent] += 1
            name, args = ("work", {"content": "Final answer: 42"}) if (
                agent == "Agent_1" and "work" in offered
            ) else ("rest", {"reason": "Awaiting the draft"})
        return LLMResponse("", "mock", "cursor-test",
            tool_calls=(LLMToolCall(name, args),),
            usage={"api_calls": 1, "output_tokens": 1})


def run(team, cfg, *, saved=None, callback=None):
    return run_contest(
        manifest(), team.query, cfg, action_request_fn=team.request,
        action_transport="native", coach_query_fn=team.query,
        session_checkpoint=saved[0] if saved else None,
        memory_checkpoint=saved[1] if saved else None,
        checkpoint_callback=callback,
    )


def comparable(result):
    # Wall duration differs across real interruptions; execution must not.
    return {
        "submissions": result["submissions"],
        "tasks": result["tasks"],
        "events": result["memory"]["events"],
        "transport": result["action_transport_log"],
        "budget": {key: result["budget"][key] for key in
                   ("turns_used", "api_calls_used", "tokens_used", "simulated_minutes_used")},
        "diagnostics": {key: value for key, value in result["diagnostics"].items()
                        if key != "elapsed_seconds"},
    }


class CheckpointCursorTests(unittest.TestCase):
    def interrupted(self, team, cfg, predicate):
        saved = []
        def persist(session, memory):
            # Match the JSON serialization performed by both production CLIs.
            snapshot = json.loads(json.dumps(session))
            if predicate(snapshot, json.loads(memory)):
                saved[:] = [snapshot, memory]
                raise InterruptedCheckpoint()
        with self.assertRaises(InterruptedCheckpoint):
            run(team, cfg, callback=persist)
        self.assertTrue(saved)
        return saved

    def test_memory_interruption_keeps_last_round_ordinary_action(self):
        cfg = config()
        uninterrupted = run(Team(side_calls=1), cfg)
        team = Team(side_calls=1)
        saved = self.interrupted(team, cfg, lambda s, m:
            any(e["kind"] == "memory_auxiliary_call" for e in m["events"]))
        resumed = run(team, cfg, saved=saved)
        self.assertEqual(comparable(resumed), comparable(uninterrupted))
        self.assertEqual(resumed["submissions"]["q1"], "Final answer: 42")

    def test_three_side_call_cap_and_private_think_survive_resume(self):
        cfg = config()
        uninterrupted = run(Team(side_calls=3), cfg)
        team = Team(side_calls=3)
        saved = self.interrupted(team, cfg, lambda s, m:
            sum(e["kind"] == "memory_auxiliary_call" for e in m["events"]) == 2)
        resumed = run(team, cfg, saved=saved)
        self.assertEqual(comparable(resumed), comparable(uninterrupted))
        self.assertEqual(len(team.queries), cfg.team_size + 1)
        self.assertEqual(resumed["memory_action_policy"]["side_calls"], 3 * cfg.team_size)

    def test_failed_memory_receipt_and_allowance_survive_resume(self):
        cfg = config()
        uninterrupted = run(Team(side_calls=3, fail_memory=True), cfg)
        team = Team(side_calls=3, fail_memory=True)
        saved = self.interrupted(team, cfg, lambda s, m:
            any(e["kind"] == "memory_auxiliary_call" for e in m["events"]))
        resumed = run(team, cfg, saved=saved)
        self.assertEqual(comparable(resumed), comparable(uninterrupted))
        self.assertEqual(sum(e["kind"] == "action_error"
                             for e in resumed["memory"]["events"]), 3 * cfg.team_size)

    def test_completed_seat_is_not_repeated_and_later_seats_are_not_skipped(self):
        for variant in BASELINE_NAMES:
            with self.subTest(variant=variant):
                cfg = config(variant)
                expected = run(Team(), cfg)
                team = Team()
                saved = self.interrupted(team, cfg, lambda s, m:
                    bool(team.ordinary_calls["Agent_1"]))
                resumed = run(team, cfg, saved=saved)
                self.assertEqual(comparable(resumed), comparable(expected))
                self.assertEqual(dict(team.ordinary_calls),
                                 {"Agent_" + str(i): 1 for i in range(1, cfg.team_size + 1)})

    def test_every_otc_checkpoint_restores_identical_execution(self):
        cfg = config()
        checkpoints = []
        expected = run(Team(side_calls=3), cfg,
            callback=lambda s, m: checkpoints.append(json.loads(json.dumps(s))))
        for cutoff in range(1, len(checkpoints) + 1):
            with self.subTest(checkpoint=cutoff):
                team = Team(side_calls=3)
                seen = 0
                def predicate(s, m):
                    nonlocal seen
                    seen += 1
                    return seen == cutoff
                saved = self.interrupted(team, cfg, predicate)
                resumed = run(team, cfg, saved=saved)
                self.assertEqual(comparable(resumed), comparable(expected))

    def test_finalized_result_restores_without_model_or_executor_calls(self):
        for variant in BASELINE_NAMES:
            with self.subTest(variant=variant):
                cfg = config(variant)
                original = run(Team(), cfg)
                forbidden = Mock(side_effect=AssertionError("Finalized execution must not run again"))
                restored = run_contest(
                    manifest(), forbidden, cfg, action_request_fn=forbidden,
                    action_transport="native", coach_query_fn=forbidden,
                    task_action_executor=forbidden,
                    session_checkpoint=json.loads(json.dumps(original["session_checkpoint"])),
                    memory_checkpoint=json.dumps(original["memory"]),
                )
                self.assertEqual(comparable(restored), comparable(original))
                forbidden.assert_not_called()

    def test_changed_deadline_policy_cannot_rewrite_finalized_history(self):
        cfg = config("single_agent", deadline_submit=False)
        original = run(Team(), cfg)
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            run(Team(), replace(cfg, deadline_submit=True),
                saved=[original["session_checkpoint"], json.dumps(original["memory"])])

    def test_corrupt_cursor_fails_before_any_model_call(self):
        cfg = config()
        team = Team(side_calls=1)
        saved = self.interrupted(team, cfg, lambda s, m:
            any(e["kind"] == "memory_auxiliary_call" for e in m["events"]))
        saved[0]["engine_state"]["round"]["next_seat"] = cfg.team_size + 1
        forbidden = Mock(side_effect=AssertionError("Corrupt checkpoint must fail closed"))
        with self.assertRaisesRegex(ValueError, "checkpoint"):
            run_contest(manifest(), forbidden, cfg, action_request_fn=forbidden,
                        session_checkpoint=saved[0], memory_checkpoint=saved[1])
        forbidden.assert_not_called()

    def test_native_cli_recovers_final_checkpoint_before_result_write(self):
        with tempfile.TemporaryDirectory(prefix="cursor-cli-") as directory:
            out = Path(directory)
            argv = ["batch", "--contest-manifest", "fixture.json",
                    "--system-variant", "single_agent", "--max-turns", "1",
                    "--output", str(out)]
            query = Mock(return_value=json.dumps({
                "action": "work", "arguments": {
                    "problem_id": "q1", "content": "Final answer: 42"}}))
            original_write = cli._write_json_atomic
            def interrupted_write(path, payload):
                if path.name == "contest_session.json":
                    raise InterruptedCheckpoint()
                return original_write(path, payload)
            with patch.object(cli, "load_contest_manifest", return_value=manifest()), \
                 patch.object(cli, "resolve_query_fn", return_value=query), \
                 redirect_stdout(io.StringIO()):
                with patch.object(sys, "argv", argv), \
                     patch.object(cli, "_write_json_atomic", side_effect=interrupted_write):
                    with self.assertRaises(InterruptedCheckpoint):
                        cli.main()
                calls_before = query.call_count
                self.assertFalse((out / "contest_session.json").exists())
                checkpoint = json.loads((out / "contest_checkpoint.json").read_text(encoding="utf-8"))
                self.assertIsNotNone(checkpoint["session"]["final_summary"])
                self.assertEqual(
                    checkpoint["session"]["tasks"][0]["versions"][-1]["content"],
                    "Final answer: 42",
                )
                self.assertFalse(any(
                    event["kind"] == "action_error"
                    for event in json.loads(checkpoint["memory"])["events"]
                ))
                with patch.object(sys, "argv", argv + ["--resume"]):
                    cli.main()
            result = json.loads((out / "contest_session.json").read_text(encoding="utf-8"))
            self.assertEqual(query.call_count, calls_before)
            self.assertEqual(result["submissions"]["q1"], "Final answer: 42")
            self.assertTrue(result["grade"]["graded"])


if __name__ == "__main__":
    unittest.main()
