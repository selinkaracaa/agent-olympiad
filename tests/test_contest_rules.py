"""Tests for contest rules audit + env search / penalty hooks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_rules import CONTEST_RULES, get_contest_rules, rules_report
from env import OlympiadEnvironment


class ContestRulesTests(unittest.TestCase):
    def test_all_smoke_families_have_rules(self):
        from run_smoke_batch import SMOKE_CASES

        for competition, _ in SMOKE_CASES:
            self.assertIn(competition, CONTEST_RULES)
            self.assertIsNotNone(get_contest_rules(competition))

    def test_icpc_penalty_metadata(self):
        rules = get_contest_rules("icpc")
        self.assertEqual(rules.wrong_submission_penalty_minutes, 20)
        self.assertTrue(any(f.name == "wrong-submit penalty" for f in rules.gaps()))

    def test_report_counts_gaps(self):
        report = rules_report()
        self.assertEqual(report["contests"], 20)
        self.assertGreater(report["total_gaps"], 0)


class EnvRulesHookTests(unittest.TestCase):
    def test_answer_key_search_blocked_on_mcm(self):
        env = OlympiadEnvironment("mcm", "mcm_2024_A", max_turns=2)
        out = env.execute_action("Agent_1", "web_search", "official solution MCM 2024 A")
        self.assertIn("RULE VIOLATION", out)
        self.assertTrue(env.rule_violations)

    def test_wrong_submission_burns_remaining_clock(self):
        env = OlympiadEnvironment("icpc", "icpc_wf_2012_bottles", max_turns=60)
        env.begin_turn()  # ~5 simulated minutes
        before = env.simulated_minutes
        turn_before = env.current_turn
        env.record_wrong_submission()
        env.record_wrong_submission()
        self.assertEqual(env.penalty_minutes(), 40)
        self.assertEqual(env.simulated_minutes, before + 40)
        self.assertGreater(env.current_turn, turn_before)
        # Official clock metadata is tracked separately from the standardized
        # collaboration-turn budget.
        env.simulated_minutes = float(env.duration_minutes or 300)
        self.assertTrue(env.can_begin_turn())


if __name__ == "__main__":
    unittest.main()
