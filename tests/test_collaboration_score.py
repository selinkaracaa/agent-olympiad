"""Tests for MultiAgentBench-style coordination score."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from evaluation.collaboration_score import (
    format_communications,
    score_coordination,
)
from llm import LLMRequest, LLMResponse


class CollaborationScoreTests(unittest.TestCase):
    def test_no_communication_sets_cscore_zero(self):
        calls = {"n": 0}

        def mock_request(request: LLMRequest) -> LLMResponse:
            calls["n"] += 1
            return LLMResponse(
                text=json.dumps({"score": 4, "justification": "ok"}),
                provider="mock",
                model="mock",
            )

        result = score_coordination(
            request_fn=mock_request,
            task_text="Solve the team contest.",
            agents=["Group_Leader", "Agent_2"],
            schema="centralized",
            chat_history=[],
            action_log=[{"agent": "Group_Leader", "action": "sleep", "payload": "waiting"}],
        )
        self.assertEqual(result.communication_score, 0.0)
        self.assertEqual(result.planning_score, 4.0)
        self.assertEqual(result.coordination_score, 2.0)
        self.assertIn("no_communication", result.warnings)
        self.assertEqual(calls["n"], 1)  # planning only

    def test_cs_is_mean_of_communication_and_planning(self):
        def mock_request(request: LLMRequest) -> LLMResponse:
            if request.purpose == "collaboration_communication_score":
                score = 5
            else:
                score = 3
            return LLMResponse(
                text=json.dumps({"score": score, "justification": "fine"}),
                provider="mock",
                model="mock",
            )

        result = score_coordination(
            request_fn=mock_request,
            task_text="Write a team essay.",
            agents=["Agent_1", "Agent_2", "Agent_3"],
            schema="round_table",
            chat_history=[
                {"sender": "Agent_1", "message": "I will draft the thesis."},
                {"sender": "Agent_2", "message": "I will gather examples."},
            ],
            action_log=[],
        )
        self.assertEqual(result.communication_score, 5.0)
        self.assertEqual(result.planning_score, 3.0)
        self.assertEqual(result.coordination_score, 4.0)

    def test_format_uses_env_chat_fields(self):
        text = format_communications([{"sender": "A", "message": "hello"}])
        self.assertIn("A: hello", text)


if __name__ == "__main__":
    unittest.main()
