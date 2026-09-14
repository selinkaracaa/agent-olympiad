"""Regressions for approved answers, delayed verdicts and smoke state transitions."""
import unittest
from dataclasses import replace

from contest_config import ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_session import ContestBudgetState, ContestSession, TaskLockedError, TaskUnit
from contest_policy import _actions_for_agent, _resolved_actions
from contest_judging import queue_verdict, deliver_verdicts
from action_modules.task_specific import resolve_contest_interface
from run_all_contest_smoke import run_case
from rules.loader import load_rule_card


def fixture(programming=False, two=True):
    competition = "icpc" if programming else "arml_local"
    kind = "algorithmic_programming" if programming else "team_contest"
    tasks = tuple(ManifestTask(
        name, name, None, "Public smoke task.", kind, 1, programming,
        {"problem_id": name, "task_type": kind},
    ) for name in (("q1", "q2") if two else ("q1",)))
    manifest = ContestManifest("work-guard-test", competition, tasks)
    session = ContestSession(
        [TaskUnit(t.task_id, kind="programming" if programming else "non_programming") for t in tasks],
        ContestBudgetState(max_turns=12),
    )
    session.select_task("q1")
    memory = ContestMemory(run_id="r", session_id=manifest.session_id, competition_id=competition)
    return manifest, session, memory


class WorkGuardTests(unittest.TestCase):
    def test_approved_target_requires_explicit_switch_or_no_work(self):
        manifest, session, memory = fixture()
        config = ContestRunConfig("otc", 6, 12, rule_card=load_rule_card("arml_local"))
        session.create_answer("42", author="Agent_1")
        session.record_review("Agent_2", "Checked.")
        actions = _resolved_actions(manifest, config)

        def available():
            return _actions_for_agent(actions, session, config, "Agent_3",
                                      answer_sheet_contest=True, memory=memory)

        work = next(spec for spec in available() if spec.name == "work")
        target = next(arg for arg in work.arguments if arg.name == "problem_id")
        self.assertTrue(target.required)
        self.assertEqual(target.enum, ("q2",))
        session.select_task("q2")
        session.create_answer("7", author="Agent_1")
        session.record_review("Agent_2", "Checked.")
        self.assertNotIn("work", {spec.name for spec in available()})
        self.assertIn("query_rules", {spec.name for spec in available()})
        session.record_review("Agent_3", "Counterexample.", decision="reject")
        self.assertIn("work", {spec.name for spec in available()})

    def test_pending_source_is_immutable_even_after_restore(self):
        manifest, session, memory = fixture(programming=True)
        version = session.create_answer("print(42)", author="Agent_1")
        queue_verdict(session, memory, session.active_task, {"valid": True, "verdict": "AC"}, 1, 20)
        for current in (session, ContestSession.from_checkpoint(session.checkpoint())):
            with self.subTest(restored=current is not session):
                with self.assertRaisesRegex(TaskLockedError, "pending"):
                    current.create_answer("print(999)", author="Agent_2")
                self.assertEqual(current.active_task.versions[-1].version_hash, version.version_hash)
                self.assertEqual(len(current.active_task.versions), 1)
        session.consume_budget(turns=1)
        deliver_verdicts(session, memory)
        self.assertEqual(session.task("q1").latest_valid_submission.verdict, "AC")

    def test_pending_nonreviewed_work_cannot_target_frozen_source(self):
        manifest, session, memory = fixture(programming=True)
        config = ContestRunConfig("decentralized", 3, 12, rule_card=load_rule_card("icpc"))
        session.create_answer("print(42)", author="Agent_1")
        queue_verdict(session, memory, session.active_task, {"valid": True, "verdict": "AC"}, 1, 20)
        offered = _actions_for_agent(_resolved_actions(manifest, config), session, config,
                                     "Agent_2", memory=memory)
        target = next(arg for spec in offered if spec.name == "work"
                      for arg in spec.arguments if arg.name == "problem_id")
        self.assertTrue(target.required)
        self.assertEqual(target.enum, ("q2",))
        self.assertNotIn("execute_code", {spec.name for spec in offered})

    def test_wrong_competition_card_still_rejected(self):
        manifest, _, _ = fixture(programming=True)
        with self.assertRaisesRegex(ValueError, "different competition"):
            resolve_contest_interface(manifest, rule_card=load_rule_card("arml_local"))

    def test_actual_catalog_smoke_transitions(self):
        for programming, variant in ((False, "otc"), (True, "vallina_otc")):
            with self.subTest(setting=variant):
                manifest, _, _ = fixture(programming=programming, two=False)
                case = run_case(manifest, load_rule_card(manifest.competition_id), variant, 12)
                self.assertEqual(case["status"], "PASS", case["checks"])
                self.assertFalse(case["action_errors"])

    def test_rejected_submit_preserves_approved_answer(self):
        from contest_actions import _apply_action

        manifest, session, memory = fixture(two=False)
        config = ContestRunConfig("otc", 6, 12, rule_card=load_rule_card("arml_local"))
        version = session.create_answer("42", author="Agent_1")
        review = session.record_review("Agent_2", "Checked.")
        state = session.active_task.state
        kwargs = dict(action="submit", agent="Agent_3", manifest=manifest,
                      session=session, memory=memory, config=config,
                      strategic_policy=None, task_action_executor=None)
        with self.assertRaisesRegex(ValueError, "cannot replace.*approved"):
            _apply_action(arguments={"answer": "999"}, **kwargs)
        self.assertEqual(session.active_task.versions, [version])
        self.assertEqual(session.active_task.state, state)
        self.assertFalse(review.stale)
        self.assertTrue(session.has_independent_approval())
        self.assertFalse(session.active_task.submissions)
        _apply_action(arguments={"answer": "42"}, **kwargs)
        self.assertEqual(session.active_task.latest_valid_submission.version_hash,
                         version.version_hash)
        self.assertEqual(session.active_task.versions, [version])

    def test_unapproved_submit_does_not_create_or_replace_a_draft(self):
        from contest_actions import _apply_action

        for has_draft in (False, True):
            with self.subTest(has_draft=has_draft):
                manifest, session, memory = fixture(two=False)
                config = ContestRunConfig("otc", 6, 12, rule_card=load_rule_card("arml_local"))
                if has_draft:
                    session.create_answer("42", author="Agent_1")
                versions = list(session.active_task.versions)
                state = session.active_task.state
                with self.assertRaisesRegex(ValueError, "independent approval"):
                    _apply_action(action="submit", arguments={"answer": "999"},
                                  agent="Agent_3", manifest=manifest, session=session,
                                  memory=memory, config=config,
                                  strategic_policy=None, task_action_executor=None)
                self.assertEqual(session.active_task.versions, versions)
                self.assertEqual(session.active_task.state, state)
                self.assertFalse(session.active_task.submissions)

    def test_nonreviewed_submit_can_still_create_an_answer(self):
        from contest_actions import _apply_action

        manifest, session, memory = fixture(two=False)
        config = ContestRunConfig("decentralized", 3, 12)
        finished, _ = _apply_action(
            action="submit", arguments={"answer": "999"}, agent="Agent_1",
            manifest=manifest, session=session, memory=memory, config=config,
            strategic_policy=None, task_action_executor=None,
        )
        self.assertTrue(finished)
        self.assertEqual(session.active_task.versions[-1].content, "999")
        self.assertIsNotNone(session.active_task.latest_valid_submission)


if __name__ == "__main__":
    unittest.main()
