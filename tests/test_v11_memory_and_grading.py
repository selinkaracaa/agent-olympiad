"""Explicit v11 invariants, independent of replay fingerprint recapture."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contest_config import ContestRunConfig
from contest_manifest import load_contest_manifest
from evaluation.gold import GoldAnswerEvaluator, GoldPart, answers_match
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card
from strategic_contest_runner import run_strategic_contest


class FinalAnswerBoundaryTests(unittest.TestCase):
    def score(self, reference, text, part="1"):
        return GoldAnswerEvaluator(
            [GoldPart(part, reference, 1)], text,
        ).evaluate().total_score

    def test_explicitly_rejected_answers_never_score(self):
        for text in (
            "Final answer: 8 is incorrect; use 7.",
            "Final answer: 8 was wrong.",
            "Final answer: 8; this is not correct.",
            "Final answer: 8. This is incorrect; use 7.",
            "Final answer: 8; however, the answer is wrong.",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.score("8", text), 0)

    def test_arbitrary_english_suffixes_are_not_units(self):
        for text in ("8incorrect", "8garbage", "8 is incorrect", "8 is wrong"):
            with self.subTest(text=text):
                self.assertFalse(answers_match("8", text))

    def test_known_physical_units_still_work(self):
        self.assertTrue(answers_match("52", "Final answer: 52 dollars."))
        self.assertTrue(answers_match("6.0 x 10^7", "Final answer: 6.0e7 m/s."))

    def test_percent_is_not_silently_removed(self):
        self.assertFalse(answers_match("8", "Final answer: 8%."))
        self.assertTrue(answers_match("8%", "Final answer: 8%."))

    def test_last_answer_overrides_earlier_candidate(self):
        self.assertEqual(self.score("8", "Candidate answer: 8. Final answer: 7."), 0)
        self.assertEqual(self.score("7", "Candidate answer: 8. Final answer: 7."), 1)

    def test_denial_of_a_previous_candidate_does_not_reject_final_value(self):
        self.assertEqual(self.score(
            "8", "Final answer: 8. The previous candidate was wrong."
        ), 1)

    def test_positive_negative_and_digit_boundaries(self):
        self.assertEqual(self.score("8", "Final answer: 8."), 1)
        self.assertEqual(self.score("-21", "Answer: -21."), 1)
        self.assertEqual(self.score("8", "Final answer: 80."), 0)

    def test_structured_field_is_authoritative(self):
        self.assertEqual(self.score("8", json.dumps({
            "reasoning": "An earlier candidate was 8", "final_answer": "7",
        })), 0)
        self.assertEqual(self.score("8", json.dumps({
            "reasoning": "Earlier work is not the final answer",
            "final_answer": "8; this is incorrect",
        })), 0)
        self.assertEqual(self.score("8", json.dumps({
            "reasoning": "The earlier candidate was incorrect", "final_answer": 8,
        })), 1)

    def test_mismatched_task_id_never_scores(self):
        self.assertEqual(self.score("8", "Q2 final: Answer: 8.", part="1"), 0)
        self.assertEqual(self.score("8", json.dumps({
            "problem_id": "arml_local_2009:2", "final_answer": "8",
        }), part="1"), 0)

    def test_numbered_proof_does_not_become_a_multipart_sheet(self):
        self.assertEqual(self.score(
            "1350", "Q8 draft: Intermediate cases:\n1) 52\n2) 8\nFinal answer: 1350.",
            part="8",
        ), 1)

    def test_ordered_pair_assignment_is_a_final_value(self):
        self.assertEqual(self.score(
            "(-6,13)", "1. (A,B)=(-6,13). Reason: the roots are conjugates.",
        ), 1)

    def test_expression_substring_is_not_an_answer(self):
        self.assertEqual(self.score("5sqrt(11)", r"Final answer: \log_3(125\sqrt{11})."), 0)


class MemoryAuxiliaryTests(unittest.TestCase):
    def run_round(self, *, fail_memory=False):
        manifest = load_contest_manifest(
            ROOT / "data/contest_manifests/arml_local_2009.json",
            benchmark_root=ROOT / "data/benchmarks",
        )
        card = copy.deepcopy(load_rule_card("arml_local", required=True))
        card.simulation["max_turns"] = 1
        card.simulation["open_table_coach"]["min_turns"] = 1
        stages = Counter()
        query_calls = []

        def query(system, user):
            query_calls.append((system, user))
            return "Keep notes private until shared. Continue with one ordinary action."

        def request(req):
            agent = req.metadata["agent"]
            stage = stages[agent]
            offered = {tool["name"] for tool in req.tools}
            if stage < 3 and fail_memory:
                name, args = "share_note", {"note_id": "missing-note"}
            elif stage == 0:
                name, args = "remember", {
                    "content": "probe_fact for " + agent,
                    "problem_id": manifest.tasks[0].task_id,
                }
            elif stage == 1:
                name, args = "recall", {
                    "query": "probe_fact", "problem_id": manifest.tasks[0].task_id,
                }
            elif stage == 2:
                receipt = json.loads(req.user_prompt.rsplit(
                    "MEMORY TOOL RESULTS (same turn, private to you)\n", 1,
                )[1])
                note = next(event for event in receipt if event["kind"] == "note")
                name, args = "share_note", {"note_id": note["event_id"]}
            else:
                self.assertFalse(offered & {"remember", "recall", "share_note"})
                name, args = "rest", {"reason": "ordinary action"}
            self.assertIn(name, offered)
            stages[agent] += 1
            return LLMResponse(
                "", "mock", "memory-side-call-test",
                tool_calls=(LLMToolCall(name, args),),
                usage={"api_calls": 1, "output_tokens": 1},
            )

        result = run_strategic_contest(
            manifest, query,
            ContestRunConfig(
                "otc", 6, 1, rule_card=card, max_api_calls=100,
                max_tokens=50000, max_simulated_minutes=5, deadline_submit=False,
            ),
            action_request_fn=request, action_transport="native", coach_query_fn=query,
        )
        counts = Counter(event["kind"] for event in result["memory"]["events"])
        self.assertEqual(result["budget"]["turns_used"], 1)
        self.assertEqual(result["budget"]["simulated_minutes_used"], 5)
        self.assertEqual(result["memory_action_policy"]["side_calls"], 18)
        self.assertEqual(counts["rest"], 6)
        self.assertEqual(counts["think"], 6)
        self.assertEqual(dict(stages), {"Agent_" + str(i): 4 for i in range(1, 7)})
        self.assertEqual(result["budget"]["api_calls_used"], len(query_calls) + sum(stages.values()))
        self.assertGreater(result["budget"]["tokens_used"], 0)
        return counts

    def test_three_memory_calls_leave_the_ordinary_action_available(self):
        counts = self.run_round()
        self.assertEqual(counts["action_error"], 0)
        for kind in ("note", "recall_result", "note_shared"):
            self.assertEqual(counts[kind], 6)

    def test_failed_memory_calls_are_bounded_without_eating_the_ordinary_action(self):
        counts = self.run_round(fail_memory=True)
        self.assertEqual(counts["action_error"], 18)
        self.assertEqual(counts["note_shared"], 0)


if __name__ == "__main__":
    unittest.main()
