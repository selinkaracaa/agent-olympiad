"""Tests for contest budget registry and token caps."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_budget import estimate_tokens, resolve_contest_budget, truncate_to_token_budget
from env import OlympiadEnvironment
from collaboration import CollabConfig, run_round_table


class ContestBudgetTests(unittest.TestCase):
    def test_arml_uses_standardized_turn_budget(self):
        budget = resolve_contest_budget("arml_local")
        self.assertEqual(budget.duration_minutes, 60)
        self.assertEqual(budget.max_turns, 30)

    def test_icpc_has_output_cap_and_five_hour_clock(self):
        budget = resolve_contest_budget("icpc")
        self.assertEqual(budget.duration_minutes, 300)
        self.assertEqual(budget.max_turns, 30)
        self.assertEqual(budget.max_output_tokens_per_call, 4096)

    def test_runtime_override(self):
        budget = resolve_contest_budget("icpc", max_turns=10, max_total_tokens=100_000)
        self.assertEqual(budget.max_turns, 10)
        self.assertEqual(budget.max_total_tokens, 100_000)

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

if __name__ == "__main__":
    unittest.main()
