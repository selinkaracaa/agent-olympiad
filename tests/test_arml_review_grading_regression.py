"""Regressions from the fresh ARML v11 paired run."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contest_config import ContestRunConfig
from contest_manifest import load_contest_manifest
from contest_memory import ContestMemory
from contest_policy import _actions_for_agent
from contest_prompts import _pending_review_queue, _user_prompt
from contest_session import ContestBudgetState, ContestSession, TaskUnit
from evaluation.final_answer import extract_final_answer
from evaluation.gold import GoldAnswerEvaluator, GoldPart
from rules.loader import load_rule_card
from tool_registry import ACTION_REGISTRY
from actions import validate_action_invocation

LIVE_SLOPE = (
    "Problem 2 draft confirmed: if f has slope -3, then composing multiplies "
    "slopes, so slopes are -3, 9, -27. The sum f(f(f(x)))+f(f(x))+f(x) "
    "therefore has slope -27+9-3=-21. No revision needed."
)


class ConclusionRegressionTests(unittest.TestCase):
    def score(self, expected, submission):
        return GoldAnswerEvaluator(
            [GoldPart("2", expected, 4)], submission
        ).evaluate().total_score

    def test_live_final_slope_is_not_lost_in_prose(self):
        self.assertEqual(self.score("-21", LIVE_SLOPE), 4)
        extracted = extract_final_answer(LIVE_SLOPE, part_id="2")
        self.assertEqual(extracted.final_answer, "-21")
        self.assertEqual(extracted.method, "answer_claim")

    def test_conclusion_equality_chain_uses_final_value(self):
        for word in ("therefore", "thus", "hence", "consequently"):
            with self.subTest(word=word):
                self.assertEqual(self.score(
                    "-21", "The sum " + word + " has slope -27+9-3=-21."
                ), 4)

    def test_explicit_final_answer_still_overrides_prose(self):
        self.assertEqual(self.score(
            "-21", LIVE_SLOPE + " Final answer: -20."
        ), 0)
        self.assertEqual(self.score(
            "-20", LIVE_SLOPE + " Final answer: -20."
        ), 4)

    def test_input_slope_is_not_selected_as_a_conclusion(self):
        self.assertEqual(self.score(
            "-3", "If f has slope -3, we still need to compute the final slope."
        ), 0)

    def test_denied_conclusion_is_not_accepted(self):
        self.assertEqual(self.score(
            "-21", "The sum therefore has slope -21. This is incorrect."
        ), 0)

    def test_symbolic_chain_is_not_sliced_for_a_matching_number(self):
        self.assertEqual(self.score(
            "-21", "The sum therefore has slope x=-21."
        ), 0)

    def test_expression_component_is_not_an_answer(self):
        self.assertEqual(self.score(
            "21", "The sum therefore has slope 1/21."
        ), 0)


class ReviewTargetRegressionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = load_contest_manifest(
            ROOT / "data/contest_manifests/arml_local_2009.json",
            benchmark_root=ROOT / "data/benchmarks",
        )
        self.card = load_rule_card("arml_local", required=True)
        ids = [task.task_id for task in self.manifest.tasks[:2]]
        self.session = ContestSession(
            [TaskUnit(task_id, kind="non_programming") for task_id in ids],
            ContestBudgetState(max_turns=10),
        )
        self.session.select_task(ids[0])
        self.own = self.session.create_answer("Final answer: 1", author="Agent_1")
        self.session.select_task(ids[1])
        self.peer = self.session.create_answer("Final answer: 2", author="Agent_2")
        self.session.select_task(ids[0])
        self.memory = ContestMemory(
            run_id="review-target-regression",
            session_id=self.manifest.session_id,
            competition_id=self.manifest.competition_id,
        )
        self.config = ContestRunConfig("vallina_otc", 6, 10, rule_card=self.card)

    def prompt(self, config=None):
        return _user_prompt(
            self.manifest, self.session, self.memory,
            config or self.config, "Agent_1",
        )

    def test_prompt_distinguishes_work_target_from_review_target(self):
        prompt = self.prompt()
        self.assertIn("not a review assignment", prompt)
        self.assertIn("CURRENT ANSWER IS YOUR OWN", prompt)
        self.assertIn("Copy problem_id and version_hash from the SAME row", prompt)

    def test_prompt_queue_excludes_own_answer_and_preserves_pair(self):
        prompt = self.prompt()
        rows, _ = json.JSONDecoder().raw_decode(
            prompt.split("YOUR ELIGIBLE PENDING REVIEWS\n", 1)[1]
        )
        self.assertEqual(
            [(row["problem_id"], row["version_hash"]) for row in rows],
            [(self.peer.task_id, self.peer.version_hash)],
        )
        actions = _actions_for_agent(
            frozenset({ACTION_REGISTRY["review_answer"]}),
            self.session, self.config, "Agent_1",
            answer_sheet_contest=True, memory=self.memory,
        )
        _, _, error = validate_action_invocation("review_answer", {
            "problem_id": self.peer.task_id,
            "version_hash": self.peer.version_hash,
            "decision": "approve", "content": "Independent check.",
        }, actions)
        self.assertIsNone(error)
        _, _, error = validate_action_invocation("review_answer", {
            "problem_id": self.own.task_id,
            "version_hash": self.own.version_hash,
            "decision": "approve", "content": "Self-check.",
        }, actions)
        self.assertIsNotNone(error)

    def test_runtime_still_rejects_self_review(self):
        with self.assertRaisesRegex(ValueError, "differ"):
            self.session.record_task_review(
                self.own.task_id, "Agent_1", "Self-check",
                version_hash=self.own.version_hash,
            )

    def test_runtime_still_rejects_stale_version(self):
        self.session.select_task(self.peer.task_id)
        self.session.create_answer("Final answer: 3", author="Agent_2")
        with self.assertRaisesRegex(ValueError, "current answer version"):
            self.session.record_task_review(
                self.peer.task_id, "Agent_1", "Review of old draft",
                version_hash=self.peer.version_hash,
            )

    def test_non_review_baselines_do_not_gain_review_guidance(self):
        for variant, size in (
            ("single_agent", 1), ("decentralized", 6), ("centralized", 6)
        ):
            with self.subTest(variant=variant):
                prompt = self.prompt(ContestRunConfig(variant, size, 10))
                self.assertNotIn("REVIEW TARGET RULE", prompt)
                self.assertNotIn("CURRENT ANSWER IS YOUR OWN", prompt)


if __name__ == "__main__":
    unittest.main()

