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
        self.assertIn("ACTION: submit_final", systems[0])

    def test_open_table_coach_programming_can_submit_code(self):
        env = OlympiadEnvironment(
            "codeforces",
            "cf_4A",
            max_turns=4,
            rules_mode="enforced",
        )
        remote = {"status": "final", "verdict": "AC", "run_id": "1001"}
        calls = {"n": 0}

        def query(system: str, _user: str) -> str:
            calls["n"] += 1
            lower = system.lower()
            if "you are coach" in lower or "preparation advice" in lower:
                return "ACTION: speak | PAYLOAD: allocate time and verify samples"
            if "open-table single-action protocol" in lower:
                if "submit_code" in system and calls["n"] >= 4:
                    return f"ACTION: submit_code | PAYLOAD: {SOLUTION_4A}"
                return "ACTION: work | PAYLOAD: draft even-weight split check"
            return "ACTION: sleep | PAYLOAD: ready"

        with (
            patch.dict(
                "os.environ",
                {
                    "VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787",
                },
                clear=False,
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                return_value=remote,
            ),
        ):
            result = run_collaboration(
                "open_table_coach",
                env,
                query,
                CollabConfig(max_turns=4, synthesize=True),
            )

        self.assertTrue(result["submitted"])
        submit_actions = [
            item for item in env.action_log if item.get("action") == "submit_code"
        ]
        self.assertTrue(submit_actions)
        payload = json.loads(submit_actions[-1]["result"])
        self.assertEqual(payload["remote"]["verdict"], "AC")

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
