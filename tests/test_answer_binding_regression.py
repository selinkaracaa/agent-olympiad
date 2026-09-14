"""Saved cross-question writes must not replace another task's answer."""
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from contest_actions import _apply_action
from contest_config import ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_runner import run_contest
from contest_session import ContestSession, ContestBudgetState, TaskUnit
from evaluation.final_answer import extract_final_answer
from evaluation.gold import GoldAnswerEvaluator, GoldPart
from rules.loader import load_rule_card
from llm import LLMResponse, LLMToolCall

FIXTURE = json.loads((ROOT / "tests/fixtures/arml2009_answer_binding.json").read_text(encoding="utf-8"))
BASELINES = ("single_agent", "decentralized", "centralized", "vallina_otc", "otc")


def state(baseline, target="arml_local_2009:7", initial="Existing public draft"):
    ids = ("arml_local_2009:5", "arml_local_2009:6", target)
    manifest = ContestManifest("binding", "arml_local", tuple(
        ManifestTask(task_id, task_id, None, "Public problem", "team_contest", 4, False,
                     {"problem_id": task_id, "task_type": "team_contest"})
        for task_id in ids))
    session = ContestSession([TaskUnit(task_id) for task_id in ids], ContestBudgetState(max_turns=10))
    session.select_task(target)
    session.create_answer(initial, author="Agent_1")
    session.select_task(ids[0])
    memory = ContestMemory(run_id="binding", session_id="binding", competition_id="arml_local")
    card = load_rule_card("arml_local") if baseline in {"otc", "vallina_otc"} else None
    return manifest, session, memory, ContestRunConfig(
        baseline, 1 if baseline == "single_agent" else 6, 10, rule_card=card)


class AnswerBindingTests(unittest.TestCase):
    def apply(self, manifest, session, memory, config, content, target=None):
        args = {"content": content}
        if target is not None:
            args["problem_id"] = target
        return _apply_action(action="work", arguments=args, agent="Agent_1",
                             manifest=manifest, session=session, memory=memory, config=config,
                             strategic_policy=None, task_action_executor=Mock())

    def test_saved_wrong_task_writes_are_atomic_for_all_baselines(self):
        for baseline in BASELINES:
            for case in FIXTURE["overwrites"]:
                with self.subTest(baseline=baseline, event=case["overwriting_event"]):
                    manifest, session, memory, config = state(baseline, case["task_id"], case["initial_content"])
                    before = (session.checkpoint(), memory.to_checkpoint_json())
                    with self.assertRaisesRegex(ValueError, "task.*mismatch|different task"):
                        self.apply(manifest, session, memory, config, case["overwriting_content"], case["task_id"])
                    self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)

    def test_implicit_target_and_restored_state_get_the_same_guard(self):
        for restored in (False, True):
            with self.subTest(restored=restored):
                manifest, session, memory, config = state("decentralized")
                session.select_task("arml_local_2009:7")
                if restored:
                    session = ContestSession.from_checkpoint(session.checkpoint())
                before = (session.checkpoint(), memory.to_checkpoint_json())
                with self.assertRaisesRegex(ValueError, "task.*mismatch|different task"):
                    self.apply(manifest, session, memory, config, "Problem 6 final: 8")
                self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)

    def test_structured_and_decorated_task_mismatch_is_rejected(self):
        for content in (
            '{"problem_id":"arml_local_2009:6","final_answer":"8"}',
            '{"task_id":"other_contest:7","final_answer":"8"}',
            "**Task 6:** Final answer: 8.",
            "### Problem 6\nFinal answer: 8.",
            "Calculation complete. Final answer for problem 6: 8.",
            "Q99: Answer: 8.",
        ):
            with self.subTest(content=content):
                manifest, session, memory, config = state("decentralized")
                before = (session.checkpoint(), memory.to_checkpoint_json())
                with self.assertRaisesRegex(ValueError, "task.*mismatch|different task"):
                    self.apply(manifest, session, memory, config, content, "arml_local_2009:7")
                self.assertEqual((session.checkpoint(), memory.to_checkpoint_json()), before)

    def test_legitimate_revisions_steps_and_cross_references_remain_writable(self):
        for content in (
            "Problem 7 revised: Answer: 1/2.",
            "Task 7 correction: Final answer: 99.",
            "1) Find the sample space.\n2) Count outcomes.\nFinal answer: 1/2.",
            "Using the technique from Problem 6, the answer is 1/2.",
            '{"problem_id":"arml_local_2009:7","final_answer":"1/2"}',
            "A revised unlabelled draft with a different result: 99.",
        ):
            with self.subTest(content=content):
                manifest, session, memory, config = state("decentralized")
                self.apply(manifest, session, memory, config, content, "arml_local_2009:7")
                self.assertEqual(session.active_task.task_id, "arml_local_2009:7")
                self.assertEqual(session.active_task.versions[-1].content, content)
                self.assertEqual(len(session.active_task.versions), 2)

    def test_runner_reports_rejection_and_deadline_keeps_the_existing_draft(self):
        for baseline in BASELINES:
            for case in FIXTURE["overwrites"]:
                with self.subTest(baseline=baseline, event=case["overwriting_event"]):
                    manifest, _, _, config = state(baseline, case["task_id"])
                    requests = []
                    plan = {"work_assignments": {f"Agent_{i}": [t.task_id for t in manifest.tasks]
                                                for i in range(1, config.team_size + 1)}}

                    def query(system, user):
                        return json.dumps(plan) if user.startswith("OPENING LEADER PLAN") else "NEXT ACTION: rest"

                    def request(req):
                        actor = re.search(r"You are (Agent_\d+)", req.system_prompt).group(1)
                        name, args = "rest", {"reason": "waiting"}
                        if actor == "Agent_1":
                            requests.append(req.user_prompt)
                            if len(requests) in (1, 3):
                                name, args = "work", {"problem_id": case["task_id"], "content":
                                    case["initial_content"] if len(requests) == 1 else case["overwriting_content"]}
                            elif len(requests) == 2:
                                name, args = "speak", {"content": "Draft recorded; available for the team."}
                        return LLMResponse("", "mock", "binding", tool_calls=(LLMToolCall(name, args),),
                                           usage={"api_calls": 1, "output_tokens": 1})

                    result = run_contest(manifest, query, config, action_request_fn=request,
                                         coach_query_fn=query)
                    errors = [e for e in result["memory"]["events"] if e["kind"] == "action_error"]
                    self.assertEqual(len(errors), 1, errors)
                    self.assertIn("answer task mismatch", json.dumps(errors[0]))
                    self.assertTrue(any("answer task mismatch" in text for text in requests[3:]))
                    self.assertEqual(result["submissions"][case["task_id"]], case["initial_content"])
                    task = next(t for t in result["session_checkpoint"]["tasks"] if t["task_id"] == case["task_id"])
                    self.assertEqual(len(task["versions"]), 1)


class ExplicitConclusionTests(unittest.TestCase):
    def score(self, text, answer, part):
        return GoldAnswerEvaluator([GoldPart(part, answer, 4)], text).evaluate().total_score

    def test_saved_area_and_pair_conclusions_are_extracted(self):
        for text, answer, part in ((FIXTURE["area_conclusion"], "3√3/10", "9"),
                                   (FIXTURE["pair_conclusion"], "(-6,13)", "1")):
            with self.subTest(part=part):
                self.assertEqual(self.score(text, answer, part), 4)
                self.assertEqual(extract_final_answer(text, part_id=part).raw_text, text)

    def test_wrong_task_and_later_explicit_answers_still_win(self):
        text = FIXTURE["area_conclusion"]
        self.assertEqual(self.score(text.replace("Problem 9", "Problem 8"), "3√3/10", "9"), 0)
        self.assertEqual(self.score(text + " Final answer: 2.", "3√3/10", "9"), 0)
        self.assertEqual(self.score(text + " Final answer: 2.", "2", "9"), 4)

    def test_new_conclusion_forms_never_mine_inputs_or_rejected_values(self):
        for text in (
            "Given area(ADF)=3√3/10, find the length of DF.",
            "Assume area(ADF)=3√3/10. We still need to check this.",
            "If area(ADF)=3√3/10, then the construction works.",
            "Given a triangle, and area(ADF)=3√3/10.",
            "Assume we get a triangle, and area(ADF)=3√3/10.",
            "We considered area(ADF)=3√3/10, but this is incorrect.",
            "Thus area(ADF)=3√3/10. This is wrong.",
            "Thus area(ADF)=3√3/10 or 2.",
            "Thus area(ADF)=3√3/10. Or possibly 2.",
            "Thus area(ADF)=3√3/10, perhaps.",
            "Thus area(ADF)=3√3/10 + x.",
            "Thus area(ADF)=1/(3√3/10).",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.score(text, "3√3/10", "9"), 0)
        for text in (
            "Given (A,B)=(-6,13), compute A+B.",
            "If (A,B)=(-6,13), the polynomial has a repeated root.",
            "Therefore (A,B)=(-6,13) or (6,-13).",
            "Therefore (A,B)=(-6,13). Alternatively (6,-13).",
            "Therefore (A,B)=(-6,13). This is incorrect.",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.score(text, "(-6,13)", "1"), 0)


if __name__ == "__main__":
    unittest.main()
