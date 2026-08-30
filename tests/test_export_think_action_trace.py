from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from export_think_action_trace import build_markdown  # noqa: E402


class ThinkActionTraceTests(unittest.TestCase):
    def test_pairs_private_think_with_scoped_action(self) -> None:
        transcript = {
            "metadata": {
                "competition_id": "arml_local",
                "problem_id": "arml_local_2009",
            },
            "private_thoughts": {
                "Agent_1": [
                    {"turn": 3, "content": "privately derive Q5"},
                ]
            },
            "action_log": [
                {
                    "turn": 3,
                    "agent": "Agent_1",
                    "action": "speak",
                    "payload": "Please check Q5.",
                    "recipients": ["Agent_2"],
                    "visibility": "group",
                }
            ],
        }

        rendered = build_markdown(transcript, Path("transcript.json"))

        self.assertIn("## Turn 3", rendered)
        self.assertIn("privately derive Q5", rendered)
        self.assertIn("`speak` → `Agent_2`", rendered)
        self.assertIn("Please check Q5.", rendered)


if __name__ == "__main__":
    unittest.main()
