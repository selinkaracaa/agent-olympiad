"""Tests for AgentWorld-style causal collaboration effectiveness."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evaluation.cce import normalize_actions, score_cce
from llm import LLMRequest, LLMResponse


def _response(payload: dict) -> LLMResponse:
    return LLMResponse(
        text=json.dumps(payload),
        provider="mock",
        model="mock-cce",
    )


class CCETests(unittest.TestCase):
    def test_normalize_excludes_private_think_and_noncontestants(self):
        actions = normalize_actions(
            [
                {"turn": 1, "agent": "Coach", "action": "speak", "payload": "plan"},
                {"turn": 1, "agent": "Agent_1", "action": "think", "payload": "private"},
                {"turn": 2, "agent": "Agent_1", "action": "work", "payload": "lemma"},
            ],
            agents=["Agent_1"],
        )
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0].action_id, 0)
        self.assertEqual(actions[0].description, "lemma")

    def test_zero_utility_returns_zero_without_judge_calls(self):
        calls = {"count": 0}

        def request_fn(_: LLMRequest) -> LLMResponse:
            calls["count"] += 1
            return _response({})

        result = score_cce(
            request_fn=request_fn,
            task_text="Solve",
            action_log=[
                {"turn": 1, "agent": "Agent_1", "action": "work", "payload": "wrong"},
                {
                    "turn": 2,
                    "agent": "Agent_1",
                    "action": "submit_final",
                    "payload": "wrong",
                },
            ],
            task_utility=0.0,
            task_outcome="score=0/1",
            agents=["Agent_1"],
        )
        self.assertEqual(result.cce, 0.0)
        self.assertEqual(result.causal_efficiency, 0.0)
        self.assertEqual(calls["count"], 0)

    def test_backward_trace_computes_cce_and_per_agent_contribution(self):
        def request_fn(request: LLMRequest) -> LLMResponse:
            self.assertEqual(request.purpose, "cce_trace_round")
            if "TURN 2" in request.user_prompt.upper():
                return _response(
                    {
                        "links": [{"source_id": 1, "target_ids": [2]}],
                        "not_contributing_ids": [],
                    }
                )
            return _response(
                {
                    "links": [{"source_id": 0, "target_ids": [1, 2]}],
                    "not_contributing_ids": [],
                }
            )

        result = score_cce(
            request_fn=request_fn,
            task_text="Prove and submit the answer",
            action_log=[
                {"turn": 1, "agent": "Agent_1", "action": "speak", "payload": "lemma"},
                {"turn": 2, "agent": "Agent_2", "action": "work", "payload": "proof"},
                {
                    "turn": 3,
                    "agent": "Agent_1",
                    "action": "submit_final",
                    "payload": "answer",
                },
            ],
            task_utility=1.0,
            task_outcome="score=1/1",
            agents=["Agent_1", "Agent_2"],
        )
        self.assertEqual(result.cce, 1.0)
        self.assertEqual(result.causal_efficiency, 1.0)
        self.assertEqual(result.utility_weighted_cce, 1.0)
        self.assertEqual(result.contributing_action_ids, [0, 1, 2])
        self.assertEqual(result.per_agent_contribution["Agent_1"], 1.0)
        self.assertEqual(result.per_agent_contribution["Agent_2"], 1.0)

    def test_partial_credit_reports_weighted_metric_and_strict_zero(self):
        def request_fn(_: LLMRequest) -> LLMResponse:
            return _response(
                {
                    "links": [{"source_id": 0, "target_ids": [2]}],
                    "not_contributing_ids": [1],
                }
            )

        result = score_cce(
            request_fn=request_fn,
            task_text="Answer several parts",
            action_log=[
                {"turn": 1, "agent": "Agent_1", "action": "work", "payload": "correct part"},
                {"turn": 1, "agent": "Agent_2", "action": "rest", "payload": "idle"},
                {
                    "turn": 2,
                    "agent": "Agent_1",
                    "action": "submit_final",
                    "payload": "partial answer",
                },
            ],
            task_utility=0.5,
            task_outcome="score=5/10",
            agents=["Agent_1", "Agent_2"],
            trace_partial_credit=True,
        )
        self.assertEqual(result.cce, 0.0)
        self.assertAlmostEqual(result.causal_efficiency, 2 / 3)
        self.assertAlmostEqual(result.utility_weighted_cce, 1 / 3)
        self.assertIn("partial_success_strict_cce_zero", result.warnings)

    def test_partial_credit_is_zero_without_optional_tracing(self):
        calls = {"count": 0}

        def request_fn(_: LLMRequest) -> LLMResponse:
            calls["count"] += 1
            return _response({})

        result = score_cce(
            request_fn=request_fn,
            task_text="Answer several parts",
            action_log=[
                {"turn": 1, "agent": "Agent_1", "action": "work", "payload": "part"},
                {
                    "turn": 2,
                    "agent": "Agent_1",
                    "action": "submit_final",
                    "payload": "partial",
                },
            ],
            task_utility=0.5,
            task_outcome="score=5/10",
            agents=["Agent_1"],
        )
        self.assertEqual(result.cce, 0.0)
        self.assertEqual(result.causal_efficiency, 0.0)
        self.assertEqual(calls["count"], 0)
        self.assertIn("incomplete_task_strict_cce_zero", result.warnings)


if __name__ == "__main__":
    unittest.main()
