"""Smoke parsing must not confuse ordinary prose with a state header."""
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from run_all_contest_smoke import CatalogSmokeAgent


class SmokePromptHeaderTests(unittest.TestCase):
    def make_request(self, body):
        task_id = "header-smoke:1"
        manifest = SimpleNamespace(
            tasks=(SimpleNamespace(task_id=task_id, programming=False),),
            metadata={},
        )
        config = SimpleNamespace(leader=None, otc_policy=None, review_required=False)
        agent = CatalogSmokeAgent(manifest, config, probe_task_tools=False)
        rows = [{"task_id": task_id, "state": "active", "has_draft": False,
                 "locked": False, "valid_submission": False}]
        request = SimpleNamespace(
            system_prompt="You are Agent_1",
            user_prompt="TASK STATUS " + json.dumps(rows) + "\nBUDGET {}\n" + body,
            tools=({"name": "work", "parameters": {
                "properties": {"content": {"type": "string"},
                               "problem_id": {"type": "string", "enum": [task_id]}},
                "required": ["content"],
            }},),
        )
        return agent, request

    def test_no_active_header_ignores_review_rule_mention(self):
        agent, request = self.make_request(
            "NO ACTIVE TASK. Select one unfinished problem.\n"
            "REVIEW TARGET RULE: use the queue, not ACTIVE TASK or shared history.\n"
        )
        call = agent(request).tool_calls[0]
        self.assertEqual(call.name, "work")
        self.assertEqual(call.arguments["problem_id"], "header-smoke:1")

    def test_inline_mention_before_real_header_is_not_a_task_id(self):
        agent, request = self.make_request(
            "The phrase ACTIVE TASK is only a label.\n"
            "ACTIVE TASK header-smoke:1\n"
        )
        call = agent(request).tool_calls[0]
        self.assertEqual(call.name, "work")
        self.assertNotIn("problem_id", call.arguments)

    def test_crlf_header_is_supported(self):
        agent, request = self.make_request("ACTIVE TASK header-smoke:1\r\n")
        self.assertEqual(agent(request).tool_calls[0].name, "work")

    def test_unknown_header_id_fails_explicitly(self):
        agent, request = self.make_request("ACTIVE TASK missing-task\n")
        with self.assertRaisesRegex(ValueError, "unknown active task"):
            agent(request)


if __name__ == "__main__":
    unittest.main()

