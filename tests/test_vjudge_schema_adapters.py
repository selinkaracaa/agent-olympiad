from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import CollabConfig, run_collaboration  # noqa: E402
from env import OlympiadEnvironment  # noqa: E402


SOLUTION_4A = (
    "w = int(input())\n"
    'print("YES" if w > 2 and w % 2 == 0 else "NO")\n'
)


class VJudgeSchemaAdapterTests(unittest.TestCase):
    def test_single_agent_programming_allows_submit_code(self):
        env = OlympiadEnvironment(
            "codeforces",
            "cf_4A",
            max_turns=2,
            rules_mode="enforced",
        )
        systems: list[str] = []

        def query(system: str, _user: str) -> str:
            systems.append(system)
            return "ACTION: sleep | PAYLOAD: ready"

        run_collaboration(
            "single_agent",
            env,
            query,
            CollabConfig(max_turns=2, synthesize=False),
        )

        self.assertTrue(systems)
        self.assertIn("ACTION: submit_code", systems[0])
        self.assertIn("ACTION: submit |", systems[0])


    def test_centralized_still_exposes_submit_code_for_programming(self):
        env = OlympiadEnvironment(
            "codeforces",
            "cf_4A",
            max_turns=1,
            rules_mode="enforced",
        )
        systems: list[str] = []

        def query(system: str, _user: str) -> str:
            systems.append(system)
            return "ACTION: sleep | PAYLOAD: ready"

        run_collaboration(
            "centralized",
            env,
            query,
            CollabConfig(max_turns=1, synthesize=False),
        )

        self.assertTrue(any("submit_code" in system for system in systems))


if __name__ == "__main__":
    unittest.main()
