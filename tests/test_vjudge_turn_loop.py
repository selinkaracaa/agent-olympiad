from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment


SOLUTION = (
    "w = int(input())\n"
    'print("YES" if w > 2 and w % 2 == 0 else "NO")\n'
)


class VJudgeTurnLoopTests(unittest.TestCase):
    def _submit(self, remote: dict) -> tuple[OlympiadEnvironment, dict]:
        env = OlympiadEnvironment("codeforces", "cf_4A", max_turns=8)
        with (
            patch.dict(
                "os.environ",
                {
                    "VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787",
                    "VJUDGE_CONTEST_ID": "845103",
                    "VJUDGE_PROBLEM": "A",
                },
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                return_value=remote,
            ),
        ):
            response = json.loads(
                env.execute_action("Agent_1", "submit_code", SOLUTION)
            )
        return env, response

    def test_remote_ac_finalizes_without_manual_copy(self):
        remote = {
            "status": "final",
            "verdict": "AC",
            "run_id": "72268062",
            "remote_run_id": "388609955",
        }
        env, response = self._submit(remote)

        self.assertEqual(response["verdict"], "AC")
        self.assertEqual(response["remote"]["verdict"], "AC")
        self.assertTrue(response["finalized"])
        self.assertFalse(response["continue_allowed"])
        self.assertTrue(env.submitted)
        self.assertEqual(env.submitted_by, "Agent_1")
        self.assertEqual(env.workspace["final_answer"], SOLUTION.strip())

        # Final grading reuses the remote verdict instead of submitting twice.
        with patch(
            "judge.vjudge_gateway_client.submit_via_gateway"
        ) as submit_again:
            grade = env.grade_submission()
        submit_again.assert_not_called()
        self.assertEqual(grade["remote"]["run_id"], "72268062")

    def test_remote_wa_is_returned_and_next_turn_remains_open(self):
        remote = {"status": "final", "verdict": "WA", "run_id": "42"}
        env, response = self._submit(remote)

        self.assertEqual(response["remote"]["verdict"], "WA")
        self.assertFalse(response["finalized"])
        self.assertTrue(response["continue_allowed"])
        self.assertFalse(env.submitted)
        self.assertEqual(env.wrong_submissions, 1)

    def test_challenge_pauses_with_candidate_preserved(self):
        remote = {
            "status": "needs_human",
            "verdict": "CHALLENGE",
            "run_id": "43",
        }
        env, response = self._submit(remote)

        self.assertTrue(response["finalized"])
        self.assertFalse(response["continue_allowed"])
        self.assertTrue(env.submitted)
        self.assertEqual(env.workspace["final_answer"], SOLUTION.strip())

    def test_submit_final_remote_wa_keeps_run_open(self):
        env = OlympiadEnvironment("codeforces", "cf_4A", max_turns=8)
        remote = {"status": "final", "verdict": "WA", "run_id": "44"}
        with (
            patch.dict(
                "os.environ",
                {
                    "VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787",
                    "VJUDGE_CONTEST_ID": "845103",
                    "VJUDGE_PROBLEM": "A",
                },
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                return_value=remote,
            ),
        ):
            response = json.loads(
                env.execute_action("Agent_1", "submit_final", SOLUTION)
            )

        self.assertEqual(response["remote"]["verdict"], "WA")
        self.assertFalse(env.submitted)
        self.assertTrue(response["continue_allowed"])

    def test_problem_metadata_uses_problem_mode_prob_num(self):
        env = OlympiadEnvironment("codeforces", "cf_231A", max_turns=4)
        captured = {}

        def fake_submit(**kwargs):
            captured.update(kwargs)
            return {"status": "final", "verdict": "AC", "run_id": "99"}

        with (
            patch.dict(
                "os.environ",
                {
                    "VJUDGE_GATEWAY_URL": "http://127.0.0.1:8787",
                    "VJUDGE_SUBMIT_MODE": "problem",
                    "VJUDGE_CONTEST_ID": "999999",
                    "VJUDGE_PROBLEM": "A",
                },
            ),
            patch(
                "judge.vjudge_gateway_client.submit_via_gateway",
                side_effect=fake_submit,
            ),
        ):
            response = json.loads(
                env.execute_action(
                    "Agent_1",
                    "submit_code",
                    (
                        "n=int(input())\n"
                        "ans=0\n"
                        "for _ in range(n):\n"
                        " a,b,c=map(int,input().split()); ans+=a+b+c>=2\n"
                        "print(ans)\n"
                    ),
                )
            )

        self.assertEqual(response["remote"]["verdict"], "AC")
        self.assertEqual(captured.get("contest_id"), "")
        self.assertEqual(captured.get("oj"), "CodeForces")
        self.assertEqual(captured.get("problem"), "231A")


if __name__ == "__main__":
    unittest.main()
