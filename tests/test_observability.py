from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import _agent_user_prompt
from env import OlympiadEnvironment
from contest_budget import MIN_RECOMMENDED_TURNS, resolve_contest_budget
from run_competition_batch import run_one


class AgentObservationTests(unittest.TestCase):
    def test_tool_result_returns_only_to_calling_agent_next_turn(self):
        env = OlympiadEnvironment("icpc", "icpc_wf_2012_bottles", max_turns=2)
        env.begin_turn()
        result = env.execute_action(
            "Agent_1", "use_calculator", "987654321 * 1234567"
        )

        other_prompt = _agent_user_prompt(env, "Agent_2", "test")
        caller_prompt = _agent_user_prompt(env, "Agent_1", "test")
        caller_prompt_after_consumption = _agent_user_prompt(env, "Agent_1", "test")

        self.assertIn(result, caller_prompt)
        self.assertIn("=== YOUR LAST TOOL RESULT ===", caller_prompt)
        self.assertNotIn(result, other_prompt)
        self.assertNotIn(result, caller_prompt_after_consumption)
        self.assertNotIn(result, str(env.chat_history))

        action = env.to_transcript()["action_log"][-1]
        self.assertEqual(action["agent"], "Agent_1")
        self.assertEqual(action["sender"], "Agent_1")
        self.assertEqual(action["action"], "use_calculator")
        self.assertEqual(action["result"], result)
        self.assertEqual(action["turn"], 1)
        self.assertEqual(action["visibility"], "private")

    def test_shawn_common_action_aliases_use_existing_handlers(self):
        env = OlympiadEnvironment("arml_local", "arml_local_2009")
        env.register_agents(["Agent_1", "Agent_2"])
        env.begin_turn()

        self.assertIn("claimed", env.execute_action("Agent_1", "select_problem", "1"))
        self.assertIn("Message sent", env.execute_action(
            "Agent_1", "direct_message", "Agent_2 | check item 1"
        ))
        self.assertIn("sleeps", env.execute_action("Agent_2", "rest", "break"))
        self.assertEqual(env.to_transcript()["action_log"][-1]["action"], "rest")

    def test_public_work_and_inspect_actions_have_board_semantics(self):
        env = OlympiadEnvironment("arml_local", "arml_local_2009")
        env.register_agents(["Agent_1"])
        env.begin_turn()

        self.assertIn("Recorded", env.execute_action("Agent_1", "work", "1 | 268"))
        overview = env.execute_action("Agent_1", "inspect_problem", "")
        self.assertIn("answered 1/10", overview)
        self.assertEqual(env.to_transcript()["action_log"][0]["action"], "work")

    def test_shared_computer_capacity_is_k_per_turn_without_release(self):
        env = OlympiadEnvironment(
            "icpc",
            "icpc_wf_2012_bottles",
            rules_mode="enforced",
        )
        env.register_agents(["Agent_1", "Agent_2"])
        env.begin_turn()

        self.assertEqual(env.k, 1)
        self.assertIn("Code output", env.execute_action("Agent_1", "execute_code", "print(1)"))
        blocked = env.execute_action("Agent_2", "execute_code", "print(2)")
        self.assertIn("all 1 computer(s) are occupied", blocked)
        self.assertEqual(env.get_state()["computers_available_this_turn"], 0)

        env.begin_turn()
        self.assertIn("Code output", env.execute_action("Agent_2", "execute_code", "print(2)"))

    def test_standard_budget_has_at_least_ten_turns(self):
        self.assertGreaterEqual(resolve_contest_budget("icpc").max_turns, MIN_RECOMMENDED_TURNS)


class TranscriptPersistenceTests(unittest.TestCase):
    def test_batch_saves_complete_serializable_transcript(self):
        call_count = 0

        def query(_system: str, _user: str) -> str:
            nonlocal call_count
            call_count += 1
            return f"public observation {call_count}"

        with tempfile.TemporaryDirectory() as temp_dir:
            out_dir = Path(temp_dir)
            row = run_one(
                "icpc",
                "icpc_wf_2012_bottles",
                schema="round_table",
                query_fn=query,
                request_fn=None,
                rounds=30,
                synthesize=False,
                judge_task=False,
                judge_collab=False,
                out_dir=out_dir,
            )
            transcript_path = Path(row["transcript_path"])
            transcript = json.loads(transcript_path.read_text(encoding="utf-8"))

        self.assertGreater(len(transcript["chat_history"]), 80)
        self.assertGreater(len(transcript["action_log"]), 40)
        self.assertEqual(len(row["chat_history"]), 80)
        self.assertEqual(len(row["action_log_tail"]), 40)
        self.assertIn("budget_snapshots", transcript)
        self.assertIn("submission", transcript)
        json.dumps(transcript)


if __name__ == "__main__":
    unittest.main()
