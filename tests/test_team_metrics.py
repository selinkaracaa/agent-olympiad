"""Focused tests for deterministic transcript metrics and taxonomy."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evaluation.error_taxonomy import classify_errors
from evaluation.team_metrics import (
    METRIC_DEFINITIONS,
    Action,
    Message,
    TeamTranscript,
    adapt_transcript,
    compute_team_metrics,
)


class TeamMetricTests(unittest.TestCase):
    def test_exact_gini_silence_and_redundancy_formulas(self):
        transcript = TeamTranscript(
            agents=["A", "B", "C"],
            messages=[
                Message("A", "one two three", 1),
                Message("B", "one", 2),
            ],
        )
        metrics = compute_team_metrics(transcript)
        self.assertAlmostEqual(metrics["communication"]["talk_share_gini"], 0.5)
        self.assertAlmostEqual(metrics["communication"]["silence_rate"], 1 / 3)
        self.assertEqual(metrics["communication"]["redundancy"], 0.0)

        duplicate = TeamTranscript(
            agents=["A", "B"],
            messages=[
                Message("A", "alpha beta gamma", 1),
                Message("B", "alpha beta gamma", 2),
            ],
        )
        duplicate_metrics = compute_team_metrics(duplicate)
        self.assertEqual(duplicate_metrics["communication"]["redundancy"], 1.0)
        self.assertEqual(duplicate_metrics["strategy"]["duplicated_effort"], 1.0)

    def test_question_observation_budget_and_parts(self):
        transcript = TeamTranscript(
            agents=["A", "B"],
            messages=[
                Message("A", "B, does Part 1 use radius seven?", 1),
                Message("B", "A, Part 1 uses radius seven.", 2),
                Message("B", "Part 2 checked with output forty two.", 4),
            ],
            actions=[
                Action("B", "execute_code", "print(42)", "output forty two", 3),
                Action("A", "submit_final", "Part 1 x. Part 2 y.", "ok", 5),
            ],
            required_parts=["1", "2"],
            final_answer="Part 1 uses radius seven. Part 2 output forty two.",
            budget_used={"turns": 5, "tokens": 50},
            budget_limits={"turns": 10, "tokens": 100},
        )
        metrics = compute_team_metrics(transcript)
        self.assertEqual(metrics["communication"]["question_answered_rate"], 1.0)
        self.assertEqual(metrics["communication"]["observation_use_rate"], 1.0)
        self.assertEqual(metrics["strategy"]["numbered_part_coverage"], 1.0)
        self.assertEqual(metrics["strategy"]["budget_utilization"], 0.5)
        self.assertEqual(metrics["strategy"]["premature_submit"], 0.0)
        self.assertGreater(metrics["communication"]["addressed_rate"], 0.0)

    def test_empty_inputs_are_safe_and_all_metrics_stay_in_range(self):
        metrics = compute_team_metrics(TeamTranscript())
        for section in ("communication", "strategy"):
            for name, value in metrics[section].items():
                self.assertGreaterEqual(value, 0.0, name)
                self.assertLessEqual(value, 1.0, name)
        self.assertEqual(metrics["strategy"]["numbered_part_coverage"], 1.0)
        self.assertEqual(classify_errors(TeamTranscript()), [])
        self.assertTrue(all("formula" in definition for definition in METRIC_DEFINITIONS.values()))

    def test_legacy_science_bowl_and_icpc_adapters(self):
        legacy = adapt_transcript(
            {
                "chat_history": [{"sender": "Captain", "message": "check answer"}],
                "action_log": [{"agent": "Captain", "action": "sleep", "payload": "wait"}],
            }
        )
        self.assertEqual(legacy.source_schema, "legacy_arml")
        self.assertEqual(legacy.messages[0].agent, "Captain")

        science = adapt_transcript(
            {"discussion": {"Player": "The answer is oxygen."}}
        )
        self.assertEqual(science.source_schema, "science_bowl.discussion")
        self.assertEqual(science.messages[0].text, "The answer is oxygen.")

        icpc = adapt_transcript(
            {
                "schema_version": "icpcrun.v1",
                "final_answer": "print(1)",
                "session": {
                    "focus": {"Agent_1": "algorithm"},
                    "team_events": [
                        {"turn": 1, "agent": "Agent_1", "kind": "done", "content": "checked"}
                    ],
                    "action_events": [
                        {
                            "turn": 1,
                            "agent": "Agent_1",
                            "action": "execute_code",
                            "command": {"code": "print(1)"},
                            "result": "Code output: 1",
                        }
                    ],
                    "scoreboard": {"penalized_rejections": 1, "penalty": 20},
                },
            }
        )
        self.assertEqual(icpc.source_schema, "icpcrun.v1")
        self.assertEqual(icpc.actions[0].action, "execute_code")
        self.assertEqual(icpc.wrong_submissions, 1)

    def test_taxonomy_triggers_machine_readable_occurrences(self):
        transcript = TeamTranscript(
            agents=["Leader", "Worker"],
            messages=[
                Message("Leader", "Can you solve Part 1?", 1),
                Message("Leader", "Can you solve Part 1?", 2),
                Message("Worker", "pass", 3),
            ],
            actions=[
                Action("Leader", "", "", "ACTION ERROR: invalid JSON", 4),
                Action("Leader", "submit_final", "Part 1 answer", "ok", 5),
            ],
            required_parts=["1", "2"],
            final_answer="unrelated final",
            allowed_tools=["execute_code"],
            budget_used={"turns": 1},
            budget_limits={"turns": 10},
        )
        occurrences = classify_errors(transcript)
        codes = {item["code"] for item in occurrences}
        self.assertTrue(
            {
                "COMM-1",
                "COMM-3",
                "COMM-5",
                "STRAT-1",
                "STRAT-2",
                "STRAT-3",
                "STRAT-5",
                "STRAT-6",
                "STRAT-8",
            }.issubset(codes)
        )
        for occurrence in occurrences:
            self.assertIn(occurrence["severity"], {"info", "warning", "error"})
            self.assertIn("evidence", occurrence)
            self.assertIn("turn", occurrence)
            self.assertIn("agent", occurrence)

    def test_remaining_aggregate_taxonomy_triggers(self):
        transcript = TeamTranscript(
            agents=["Leader", "Worker"],
            messages=[
                Message("Leader", "identical repeated effort text", 1),
                Message("Worker", "identical repeated effort text", 2),
            ],
            actions=[
                Action("Leader", "execute_code", "", "unique observation discarded", 3)
            ],
            final_answer="identical",
        )
        codes = {item["code"] for item in classify_errors(transcript)}
        self.assertTrue({"COMM-2", "COMM-4", "STRAT-4", "STRAT-6"}.issubset(codes))

        bottleneck = TeamTranscript(
            agents=["Group_Leader", "Worker"],
            messages=[
                Message("Group_Leader", "one two three four five six seven eight", 1),
                Message("Worker", "one", 2),
            ],
        )
        self.assertIn("STRAT-7", {item["code"] for item in classify_errors(bottleneck)})


if __name__ == "__main__":
    unittest.main()
