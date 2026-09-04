from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import OlympiadEnvironment  # noqa: E402
from evaluation.gold import parse_numbered_answers  # noqa: E402
from workboard import Workboard  # noqa: E402


def _board(**problem_data) -> Workboard:
    board = Workboard.from_problem(problem_data)
    assert board is not None, "expected a board for this problem"
    return board


class BoardConstructionTests(unittest.TestCase):
    def test_gold_parts_become_items_without_leaking_answers(self):
        board = _board(
            gold_label={
                "parts": [
                    {"id": "1", "expected": "42", "points": 4, "reference": "sol"},
                    {"id": "2", "expected": "7", "points": 4, "reference": "sol"},
                ]
            }
        )
        self.assertEqual(board.source, "gold_parts")
        self.assertEqual(list(board.items), ["1", "2"])
        rendered = board.detail(board.items["1"], turn=1) + board.overview(turn=1)
        for leak in ("42", "sol"):
            self.assertNotIn(leak, rendered)

    def test_inline_answer_sheet_statements_attach_to_items(self):
        board = _board(
            problem_description=(
                "Team Problems 1. Compute the smallest integer whose digit "
                "product is 96. 2. Compute sin 2A. 3. Compute the surface area."
            ),
            gold_label={
                "parts": [
                    {"id": "1", "expected": "268", "points": 4},
                    {"id": "2", "expected": "6/25", "points": 4},
                    {"id": "3", "expected": "12", "points": 4},
                ]
            },
        )
        self.assertIn("digit product is 96", board.items["1"].statement)
        # "96." inside the prose must not become an item of its own.
        self.assertEqual(list(board.items), ["1", "2", "3"])

    def test_labeled_subquestions_form_a_board_without_gold_parts(self):
        board = _board(
            problem_description=(
                "(G01) Dark matter [150 marks]\n"
                "(G01.1) Measure the aperture.\n"
                "(G01.2) Point the telescope.\n"
            )
        )
        self.assertEqual(board.source, "statement_labels")
        self.assertEqual(list(board.items), ["G01", "G01.1", "G01.2"])

    def test_single_deliverable_task_gets_no_board(self):
        self.assertIsNone(
            Workboard.from_problem(
                {"topic": "Team Contest — Tocharian", "gold_label": {}}
            )
        )

    def test_reference_resolution_is_tolerant(self):
        board = _board(
            gold_label={"parts": [{"id": "3", "points": 1}, {"id": "4", "points": 1}]}
        )
        for ref in ("3", "P3", "p3", "Problem 3", "Q3", "(3)"):
            self.assertIsNotNone(board.resolve(ref), ref)
        self.assertIsNone(board.resolve("99"))


class BoardBehaviourTests(unittest.TestCase):
    def setUp(self):
        self.board = _board(
            gold_label={
                "parts": [{"id": str(index), "points": 1} for index in range(1, 5)]
            }
        )

    def test_repeat_answer_is_rejected_and_counted(self):
        item = self.board.items["1"]
        first = self.board.record_answer("A", item, "42", turn=1)
        self.assertIn("Recorded", first)
        repeat = self.board.record_answer("A", item, " 42 ", turn=2)
        self.assertTrue(repeat.startswith("Board error:"))
        self.assertIn("turn 1", repeat)
        self.assertEqual(len(item.attempts), 1)
        self.assertEqual(item.repeat_attempts, 1)

    def test_a_different_answer_replaces_the_recorded_one(self):
        item = self.board.items["1"]
        self.board.record_answer("A", item, "42", turn=1)
        self.board.record_answer("B", item, "43", turn=2)
        self.assertEqual(item.answer, "43")
        self.assertEqual(len(item.attempts), 2)
        # Reverting to a superseded answer is still a no-op on the sheet.
        self.assertTrue(
            self.board.record_answer("A", item, "42", turn=3).startswith("Board error:")
        )

    def test_claim_blocks_other_agents_until_released(self):
        item = self.board.items["1"]
        self.board.claim("A", item, turn=1)
        self.assertIn("claimed by A", self.board.claim("B", item, turn=1))
        self.assertTrue(
            self.board.record_answer("B", item, "42", turn=1).startswith("Board error:")
        )
        self.board.release("A", item, turn=1)
        self.assertIn("Recorded", self.board.record_answer("B", item, "42", turn=2))

    def test_claiming_a_second_item_releases_the_first(self):
        self.board.claim("A", self.board.items["1"], turn=1)
        message = self.board.claim("A", self.board.items["2"], turn=1)
        self.assertIn("released 1", message)
        self.assertIsNone(self.board.items["1"].holder(1, self.board.claim_ttl_turns))

    def test_stale_claims_expire_so_the_board_cannot_deadlock(self):
        item = self.board.items["1"]
        self.board.claim("A", item, turn=1)
        ttl = self.board.claim_ttl_turns
        self.assertEqual(item.holder(1 + ttl, ttl), "A")
        self.assertIsNone(item.holder(2 + ttl, ttl))
        self.assertIn("Recorded", self.board.record_answer("B", item, "9", turn=2 + ttl))

    def test_review_requires_someone_elses_answer(self):
        item = self.board.items["1"]
        self.assertIn("no recorded answer", self.board.review("A", item, "agree", "", turn=1))
        self.board.record_answer("A", item, "42", turn=1)
        self.assertTrue(
            self.board.review("A", item, "agree", "", turn=2).startswith("Board error:")
        )
        result = self.board.review("B", item, "disagree", "sign flipped", turn=2)
        self.assertIn("disagree", result)
        self.assertEqual(item.answer, "42", "a review must not change the answer")

    def test_free_text_review_is_kept_as_an_unsure_comment(self):
        item = self.board.items["1"]
        self.board.record_answer("A", item, "42", turn=1)
        self.board.review("B", item, "looks", "wrong to me", turn=2)
        review = item.reviews[-1]
        self.assertEqual(review.verdict, "unsure")
        self.assertEqual(review.comment, "looks wrong to me")

    def test_metrics_report_the_repeat_rate(self):
        item = self.board.items["1"]
        self.board.record_answer("A", item, "42", turn=1)
        self.board.record_answer("A", item, "42", turn=2)
        self.board.record_answer("A", item, "42", turn=3)
        metrics = self.board.metrics()
        self.assertEqual(metrics["attempts_recorded"], 1)
        self.assertEqual(metrics["repeat_attempts_rejected"], 2)
        self.assertAlmostEqual(metrics["repeat_rate"], 2 / 3, places=3)
        self.assertEqual(metrics["items_unanswered"], 3)

    def test_answer_sheet_parses_back_through_the_grader(self):
        self.board.record_answer("A", self.board.items["1"], "268", turn=1)
        self.board.record_answer("A", self.board.items["3"], "6/25", turn=1)
        self.assertEqual(
            parse_numbered_answers(self.board.answer_sheet()),
            {"1": "268", "3": "6/25"},
        )


class EnvironmentIntegrationTests(unittest.TestCase):
    """The board reaches the agents through real env actions, or not at all."""

    def _env(self) -> OlympiadEnvironment:
        env = OlympiadEnvironment("arml_local", "arml_local_2012")
        env.register_agents(["Agent_1", "Agent_2"])
        env.begin_turn()
        return env

    def test_board_actions_are_available_without_being_declared_tools(self):
        env = self._env()
        self.assertEqual(env.get_available_tools(), [])
        result = env.execute_action("Agent_1", "list_problems", "")
        self.assertIn("PROBLEM BOARD", result)
        self.assertEqual(env.rule_violations, [])

    def test_repeat_rejection_reaches_the_agent_that_made_it(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        env.consume_agent_observations("Agent_1")
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        observations = env.consume_agent_observations("Agent_1")
        self.assertTrue(
            any("already the recorded answer" in item["result"] for item in observations)
        )

    def test_board_changes_are_announced_to_the_team(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        announcements = [
            entry["message"]
            for entry in env.chat_history
            if entry["sender"] == "Contest_Control"
        ]
        self.assertTrue(any("[board]" in text for text in announcements))

    def test_refused_board_calls_are_not_rule_violations(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "99 | nonsense")
        env.execute_action("Agent_1", "open_problem", "")
        self.assertEqual(env.rule_violations, [])

    def test_bare_submit_final_falls_back_to_the_recorded_sheet(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        env.execute_action("Agent_1", "submit_problem", "2 | 144")
        env.execute_action("Agent_1", "submit_final", "submit")
        self.assertEqual(env.workspace["final_answer"], "1. 268\n2. 144")
        self.assertTrue(env.submitted)

    def test_written_submission_is_not_overwritten_by_the_board(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        env.execute_action("Agent_1", "submit_final", "1. 999\n2. 144\n3. 6/25")
        self.assertTrue(env.workspace["final_answer"].startswith("1. 999"))

    def test_items_dropped_by_the_submitter_are_recovered_from_the_board(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "4 | 21")
        env.execute_action("Agent_1", "submit_final", "1. 999\n2. 144\n3. 6/25")
        final = env.workspace["final_answer"]
        self.assertIn("1. 999", final)
        self.assertIn("4. 21", final)

    def test_a_submission_with_no_answers_falls_back_to_the_board(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        env.execute_action(
            "Agent_1", "submit_final", "The team agreed on its answers."
        )
        self.assertEqual(env.workspace["final_answer"], "1. 268")

    def test_board_free_contest_submissions_are_untouched(self):
        env = OlympiadEnvironment("iol_team", "iol_team_2003")
        env.register_agents(["Agent_1"])
        env.begin_turn()
        essay = "Tocharian B verbs mark the subjunctive with a palatalised stem."
        env.execute_action("Agent_1", "submit_final", essay)
        self.assertEqual(env.workspace["final_answer"], essay)

    def test_memory_round_trips_from_private_to_team(self):
        env = self._env()
        stored = env.execute_action("Agent_1", "remember", "1 | digit product is 96")
        self.assertIn("M1", stored)
        self.assertNotIn("96", env.execute_action("Agent_2", "recall", "digit"))
        env.execute_action("Agent_1", "publish_memory", "M1")
        self.assertIn("96", env.execute_action("Agent_2", "recall", "digit"))

    def test_message_group_reaches_only_named_teammates(self):
        env = self._env()
        env.register_agents(["Agent_1", "Agent_2", "Agent_3"])
        result = env.execute_action(
            "Agent_1", "message_group", "Agent_2 | you take items 5-10"
        )
        self.assertIn("Agent_2", result)
        self.assertIn("5-10", env.format_group_memory("Agent_2"))
        self.assertEqual(env.format_group_memory("Agent_3"), "")

    def test_message_group_rejects_unknown_recipients(self):
        env = self._env()
        result = env.execute_action("Agent_1", "message_group", "Agent_9 | hello")
        self.assertIn("unknown recipient", result)
        self.assertFalse(env.group_messages)

    def test_check_budget_reports_what_is_still_blank(self):
        env = self._env()
        report = env.execute_action("Agent_1", "check_budget", "")
        self.assertIn("Board: 0/10 answered", report)
        self.assertIn("10 blank", report)

    def test_single_deliverable_contest_reports_the_board_unavailable(self):
        env = OlympiadEnvironment("iol_team", "iol_team_2003")
        env.register_agents(["Agent_1"])
        env.begin_turn()
        self.assertIsNone(env.workboard)
        result = env.execute_action("Agent_1", "list_problems", "")
        self.assertIn("Board unavailable", result)
        self.assertEqual(env.rule_violations, [])

    def test_transcript_carries_board_and_memory_state(self):
        env = self._env()
        env.execute_action("Agent_1", "submit_problem", "1 | 268")
        transcript = env.to_transcript()
        self.assertEqual(transcript["workboard"]["metrics"]["items_answered"], 1)
        self.assertIn("private", transcript["memory"])


if __name__ == "__main__":
    unittest.main()


class PhaseGateTests(unittest.TestCase):
    """Phase allowlists predate these actions; bookkeeping must not be banned."""

    def _schedule(self):
        from rules.phases import PhaseSchedule

        return PhaseSchedule.from_simulation(
            {
                "phases": [
                    {
                        "id": "prep",
                        "label": "Prep day",
                        "turn_start": 1,
                        "turn_end": 5,
                        "allowed_actions": ["speak", "write_private_notes", "sleep"],
                    }
                ]
            }
        )

    def test_reads_and_notes_survive_an_allowlist(self):
        schedule = self._schedule()
        for action in ("check_budget", "recall", "remember", "list_problems"):
            self.assertIsNone(schedule.validate_action(1, action), action)

    def test_board_mutations_still_obey_the_allowlist(self):
        schedule = self._schedule()
        for action in ("submit_problem", "claim_problem", "message_group"):
            self.assertIsNotNone(schedule.validate_action(1, action), action)

    def test_banned_actions_beat_the_implicit_allowance(self):
        from rules.phases import PhaseSchedule

        schedule = PhaseSchedule.from_simulation(
            {
                "phases": [
                    {
                        "id": "quiet",
                        "label": "Quiet hour",
                        "turn_start": 1,
                        "turn_end": 5,
                        "banned_actions": ["recall"],
                    }
                ]
            }
        )
        self.assertIsNotNone(schedule.validate_action(1, "recall"))
