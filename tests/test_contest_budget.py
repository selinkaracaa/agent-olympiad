"""Tests for contest budget registry and token caps."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_budget import (
    MAX_TURNS_CAP,
    COMPETITION_BUDGET_REGISTRY,
    estimate_tokens,
    resolve_contest_budget,
    truncate_to_token_budget,
    turns_for_duration,
)
from env import OlympiadEnvironment
from collaboration import CollabConfig, run_round_table


class ContestBudgetTests(unittest.TestCase):
    def test_arml_turns_follow_the_45_minute_card(self):
        budget = resolve_contest_budget("arml_local")
        self.assertEqual(budget.duration_minutes, 45)
        self.assertEqual(budget.minutes_per_turn, 5.0)
        self.assertEqual(budget.max_turns, 9)
        self.assertEqual(resolve_contest_budget("arml_national_team").max_turns, 4)
        self.assertEqual(resolve_contest_budget("purple_comet").max_turns, 18)

    def test_icpc_has_output_cap_and_five_hour_clock(self):
        budget = resolve_contest_budget("icpc")
        self.assertEqual(budget.duration_minutes, 300)
        self.assertEqual(budget.max_turns, 60)
        self.assertEqual(budget.max_output_tokens_per_call, 4096)

    def test_turns_are_capped_at_ninety(self):
        self.assertEqual(MAX_TURNS_CAP, 90)
        self.assertEqual(turns_for_duration(60), 12)
        self.assertEqual(turns_for_duration(99 * 60, 60), 90)
        self.assertEqual(turns_for_duration(2), 1)
        self.assertEqual(turns_for_duration(None), 90)
        self.assertEqual(resolve_contest_budget("mcm").max_turns, 90)
        self.assertEqual(resolve_contest_budget("jessup").max_turns, 90)
        for competition, budget in COMPETITION_BUDGET_REGISTRY.items():
            with self.subTest(competition=competition):
                self.assertEqual(
                    budget.max_turns,
                    turns_for_duration(budget.duration_minutes, budget.minutes_per_turn),
                )
                self.assertTrue(1 <= budget.max_turns <= MAX_TURNS_CAP)

    def test_unknown_competition_defaults_to_one_hour(self):
        budget = resolve_contest_budget("science_bowl")
        self.assertEqual(budget.duration_minutes, 60)
        self.assertEqual(budget.max_turns, 12)

    def test_runtime_override(self):
        budget = resolve_contest_budget("icpc", max_turns=10, max_total_tokens=100_000)
        self.assertEqual(budget.max_turns, 10)
        self.assertEqual(budget.max_total_tokens, 100_000)
        self.assertEqual(resolve_contest_budget("icpc", max_turns=500).max_turns, 90)

    def test_truncate_to_token_budget(self):
        text = "word " * 500
        clipped = truncate_to_token_budget(text, max_tokens=10)
        self.assertLessEqual(estimate_tokens(clipped), 10)
        self.assertIn("truncated", clipped)

    def test_env_applies_per_call_token_cap(self):
        env = OlympiadEnvironment("icpc", "icpc_wf_2012_bottles")
        long_text = "x " * 20_000
        capped = env.apply_output_token_budget(long_text)
        self.assertLessEqual(estimate_tokens(capped), env.max_output_tokens_per_call or 0)
        self.assertGreater(env.tokens_used, 0)

    def test_env_advances_simulated_clock(self):
        env = OlympiadEnvironment("arml_local", "arml_local_2009", max_turns=3)
        env.begin_turn()
        self.assertEqual(env.simulated_minutes, 5.0)
        env.begin_turn()
        self.assertEqual(env.simulated_minutes, 10.0)

    def test_token_budget_stops_collaboration(self):
        def huge(_s, _u):
            return "token " * 10_000

        env = OlympiadEnvironment(
            "arml_local",
            "arml_local_2009",
            max_turns=1,
            max_total_tokens=50,
        )
        result = run_round_table(
            env,
            huge,
            CollabConfig(rounds=1, max_total_tokens=50, synthesize=False),
        )
        self.assertLessEqual(result["tokens_used"], 50)
        self.assertFalse(result["submitted"])

    def test_tokens_tracked_per_turn(self):
        def short(_s, _u):
            return "ACTION: sleep | PAYLOAD: done"

        env = OlympiadEnvironment(
            "arml_local",
            "arml_local_2009",
            max_turns=2,
        )
        result = run_round_table(
            env,
            short,
            CollabConfig(rounds=2, synthesize=False),
        )
        by_turn = result["tokens_by_turn"]
        self.assertEqual(len(by_turn), 2)
        self.assertEqual([row["turn"] for row in by_turn], [1, 2])
        self.assertEqual(sum(row["tokens"] for row in by_turn), result["tokens_used"])
        self.assertEqual(sum(row["api_calls"] for row in by_turn), result["api_calls"])
        self.assertGreater(by_turn[0]["tokens"], 0)

if __name__ == "__main__":
    unittest.main()
