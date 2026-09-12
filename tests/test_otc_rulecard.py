"""The ``otc`` baseline: the rule card drives the Open Table Coach session."""

from __future__ import annotations

import json
import re
import sys
import unittest
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

import otc_runtime  # noqa: E402
from contest_manifest import ContestManifest, ManifestTask  # noqa: E402
from contest_memory import ContestMemory  # noqa: E402
from contest_runner import (  # noqa: E402
    BASELINES,
    ContestRunConfig,
    _actions_for_agent,
    _resolved_actions,
    run_contest,
)
from contest_session import ContestBudgetState, ContestSession, TaskUnit  # noqa: E402
from rulecard_policy import (  # noqa: E402
    OpenTablePolicyError,
    clip_text,
    open_table_policy,
)
from rules.loader import load_rule_card  # noqa: E402
from rules.models import RuleCardError  # noqa: E402
from tool_registry import ACTION_SET_VERSION, DELIBERATION_ACTION_NAMES  # noqa: E402

ARML = load_rule_card("arml_local")
ICPC = load_rule_card("icpc")
assert ARML is not None and ICPC is not None


def task(task_id: str, *, programming: bool = False) -> ManifestTask:
    task_type = "algorithmic_programming" if programming else "team_contest"
    return ManifestTask(
        task_id=task_id,
        parent_problem_id=task_id,
        question_id=None,
        prompt=f"STATEMENT-{task_id}: solve it",
        task_type=task_type,
        max_score=1.0,
        programming=programming,
        benchmark={"problem_id": task_id, "task_type": task_type},
    )


def arml_manifest() -> ContestManifest:
    return ContestManifest("arml_local", "arml_test", (task("q1"), task("q2")))


def icpc_manifest() -> ContestManifest:
    return ContestManifest(
        "icpc",
        "icpc_test",
        (task("p1", programming=True), task("p2", programming=True)),
    )


def action(name: str, **arguments: Any) -> str:
    return json.dumps({"action": name, "arguments": arguments})


class ScriptedLLM:
    """Routes coach / think / action calls and records every prompt."""

    def __init__(
        self,
        scripts: dict[str, list[str]],
        *,
        opening_plan: dict[str, Any] | None = None,
    ) -> None:
        self.scripts = {agent: deque(items) for agent, items in scripts.items()}
        self.calls: list[dict[str, str]] = []
        self.opening_plan = opening_plan or {}

    def __call__(self, system: str, user: str) -> str:
        lowered = system.lower()
        match = re.search(r"You are (Agent_\d+)", system)
        agent = match.group(1) if match else "Coach"
        if "you are coach" in lowered and "pre-contest brief" in lowered:
            kind = "brief"
            response = "1. Read every problem. 2. Split by strength. 3. Check before writing."
        elif "you are coach" in lowered and "final participation" in lowered:
            kind = "opening"
            response = json.dumps(
                {"summary": "Opening summary: q1 first, q2 second.", **self.opening_plan}
            )
        elif "private deliberation" in lowered:
            kind = "think"
            response = f"{agent} thinking about the table. NEXT ACTION: rest"
        else:
            kind = "action"
            queue = self.scripts.get(agent)
            response = queue.popleft() if queue else action("rest", reason="idle")
        self.calls.append({"agent": agent, "kind": kind, "system": system, "user": user})
        return response


def events_of(result: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    return [event for event in result["memory"]["events"] if event["kind"] == kind]


class CoachSummaryParsingTests(unittest.TestCase):
    def test_tex_escapes_inside_json_strings_are_tolerated(self) -> None:
        raw = (
            '{"summary":"Verify 4 by simplifying \\(f(3)\\) and |\\sin\\theta|.",'
            '"work_assignments":{"Agent_1":["q1"],"Agent_2":["q2"]},'
            '"task_order":["q1","q2"],"watch_points":["signs"]}'
        )
        plan = otc_runtime.parse_coach_summary(raw, arml_manifest(), team_size=2)
        self.assertTrue(plan["summary"].startswith("Verify 4"))
        self.assertEqual(plan["work_assignments"], {"Agent_1": ["q1"], "Agent_2": ["q2"]})
        self.assertEqual(plan["task_order"], ["q1", "q2"])

    def test_truncated_object_salvages_summary_text(self) -> None:
        raw = '{"summary":"Lock in the quick algebra first.\\nThen geometry.","work_assign'
        plan = otc_runtime.parse_coach_summary(raw, arml_manifest(), team_size=2)
        self.assertEqual(plan["summary"], "Lock in the quick algebra first.\nThen geometry.")
        self.assertEqual(plan["work_assignments"], {"Agent_1": [], "Agent_2": []})


class PolicyParsingTests(unittest.TestCase):
    def test_arml_card_yields_structured_limited_policy(self) -> None:
        policy = open_table_policy(ARML, team_size=6, programming=False)
        self.assertEqual(policy.allowed_actions, frozenset({"work", "speak", "rest"}))
        self.assertEqual(policy.private_think_calls_per_turn, 1)
        self.assertEqual(policy.min_turns, 9)
        self.assertTrue(policy.structured_deliberation)
        self.assertEqual(policy.min_challenges, 1)
        self.assertTrue(policy.communication_limited)
        self.assertEqual(policy.char_limit("speak"), 320)
        self.assertEqual(policy.char_limit("direct_message"), 320)
        self.assertEqual(policy.char_limit("think"), 2400)
        self.assertEqual(policy.memory_entries.private_think_per_agent, 3)
        self.assertTrue(policy.discussion.report_after_work)
        self.assertEqual(
            policy.submitters, frozenset(f"Agent_{i}" for i in range(1, 7))
        )
        self.assertIn("speak", policy.counted_message_actions())
        self.assertIn("challenge", policy.counted_message_actions())
        self.assertFalse(policy.workstation_lease)

    def test_icpc_card_yields_lease_latency_and_submit_code(self) -> None:
        policy = open_table_policy(ICPC, team_size=3, programming=True)
        self.assertIn("submit_code", policy.allowed_actions)
        self.assertTrue(policy.workstation_lease)
        self.assertEqual(policy.run_judging_latency_turns, 1)
        self.assertEqual(policy.repair_budget_after_rejected_run, 2)
        self.assertFalse(policy.structured_deliberation)
        self.assertEqual(policy.counted_message_actions(), frozenset())

    def test_submit_code_requires_programming_contest(self) -> None:
        with self.assertRaises(OpenTablePolicyError):
            open_table_policy(ICPC, team_size=3, programming=False)

    def test_card_without_open_table_block_is_rejected(self) -> None:
        from dataclasses import replace
        card = load_rule_card("iiot")
        assert card is not None
        card = replace(card, simulation={k: v for k, v in card.simulation.items()
                                        if k != 'open_table_coach'})
        with self.assertRaises(OpenTablePolicyError):
            open_table_policy(card, team_size=card.team_size_default, programming=True)

    def test_team_size_outside_card_range_is_rejected(self) -> None:
        with self.assertRaises(RuleCardError):
            open_table_policy(ARML, team_size=3, programming=False)

    def test_clip_text_prefers_sentence_boundary(self) -> None:
        text = "First sentence. Second sentence. " + "x" * 400
        clipped, cut = clip_text(text, 60)
        self.assertTrue(cut)
        self.assertLessEqual(len(clipped), 60)
        self.assertTrue(clipped.startswith("First sentence."))
        self.assertEqual(clip_text("short", 60), ("short", False))


class ConfigAndActionSurfaceTests(unittest.TestCase):
    def test_otc_preset_and_config_require_enforced_card(self) -> None:
        features = BASELINES["otc"]
        self.assertEqual(features.coach, "card")
        self.assertEqual(features.rule_card, "enforced")
        self.assertTrue(features.review_workflow)
        for name, other in BASELINES.items():
            if name not in {"otc", "vallina_otc"}:
                self.assertEqual(other.rule_card, "off", name)
        with self.assertRaises(ValueError):
            ContestRunConfig(system_variant="otc", team_size=6, max_turns=12)
        config = ContestRunConfig(
            system_variant="otc", team_size=6, max_turns=12, rule_card=ARML
        )
        self.assertIsNotNone(config.otc_policy)
        self.assertEqual(ACTION_SET_VERSION, 5)

    def test_common_actions_plus_card_bundle(self) -> None:
        arml = ContestRunConfig(
            system_variant="otc", team_size=6, max_turns=12, rule_card=ARML
        )
        names = {spec.name for spec in _resolved_actions(arml_manifest(), arml)}
        self.assertTrue(DELIBERATION_ACTION_NAMES <= names)
        self.assertNotIn("request_review", names)
        self.assertIn("review_answer", names)
        self.assertNotIn("assign_problem", names)
        self.assertNotIn("submit_code", names)
        icpc = ContestRunConfig(
            system_variant="otc", team_size=3, max_turns=60, rule_card=ICPC
        )
        icpc_names = {spec.name for spec in _resolved_actions(icpc_manifest(), icpc)}
        self.assertFalse(DELIBERATION_ACTION_NAMES & icpc_names)
        self.assertIn("submit_code", icpc_names)
        self.assertIn("execute_code", icpc_names)
        # Existing baselines never see the deliberation bundle.
        legacy = ContestRunConfig(
            system_variant="centralized", team_size=3, max_turns=12
        )
        legacy_names = {spec.name for spec in _resolved_actions(arml_manifest(), legacy)}
        self.assertFalse(DELIBERATION_ACTION_NAMES & legacy_names)

    def _icpc_table(self) -> tuple[ContestRunConfig, ContestSession, ContestMemory, frozenset]:
        config = ContestRunConfig(
            system_variant="otc", team_size=3, max_turns=60, rule_card=ICPC
        )
        session = ContestSession(
            [TaskUnit("p1", kind="programming"), TaskUnit("p2", kind="programming")],
            ContestBudgetState(max_turns=60),
        )
        session.consume_budget(turns=3)
        session.select_task("p1")
        memory = ContestMemory(run_id="r", session_id="icpc_test", competition_id="icpc")
        actions = _resolved_actions(icpc_manifest(), config)
        return config, session, memory, actions

    def test_workstation_lease_hides_machine_actions_from_others(self) -> None:
        config, session, memory, actions = self._icpc_table()
        memory.append(
            task_id="p1", question_id=None, actor="Agent_1", visibility="private",
            recipients=("Agent_1",), kind="execute_code",
            payload={"code": "print(1)"}, turn=3,
        )
        names = lambda agent: {  # noqa: E731
            spec.name for spec in _actions_for_agent(actions, session, config, agent, memory=memory)
        }
        self.assertNotIn("execute_code", names("Agent_2"))
        self.assertNotIn("submit_code", names("Agent_2"))
        self.assertIn("execute_code", names("Agent_1"))
        # The lease lapses after LEASE_TURNS turns without a machine action.
        session.consume_budget(turns=otc_runtime.LEASE_TURNS)
        self.assertIn("execute_code", names("Agent_2"))

    def test_judging_latency_hides_resubmission(self) -> None:
        config, session, memory, actions = self._icpc_table()
        from contest_judging import queue_verdict, deliver_verdicts
        session.create_answer("print(1)", author="Agent_1", evidence_refs=("sample",))
        session.record_review("Agent_2", "Checked source and samples.")
        queue_verdict(session, memory, session.active_task,
                      {"verdict": "WA", "valid": True}, 1, 20)
        names = lambda: {spec.name for spec in _actions_for_agent(
            actions, session, config, "Agent_1", memory=memory)}
        self.assertNotIn("submit_code", names())
        self.assertNotIn("execute_code", names())
        session.consume_budget(turns=1)
        deliver_verdicts(session, memory)
        self.assertIn("execute_code", names())
        self.assertNotIn("submit_code", names())  # Do not resubmit rejected code unchanged.

    def test_min_turns_and_min_challenges_gate_answer_sheet_submit(self) -> None:
        config = ContestRunConfig(
            system_variant="otc", team_size=6, max_turns=12, rule_card=ARML
        )
        manifest = arml_manifest()
        session = ContestSession(
            [TaskUnit("q1"), TaskUnit("q2")], ContestBudgetState(max_turns=12)
        )
        memory = ContestMemory(run_id="r", session_id="arml_test", competition_id="arml_local")
        actions = _resolved_actions(manifest, config)
        for task_id in ("q1", "q2"):
            session.select_task(task_id)
            session.create_answer(f"answer {task_id}", author="Agent_1")
            session.record_review("Agent_2", "Checked the complete answer.")
        session.consume_budget(turns=5)

        def names() -> set[str]:
            return {
                spec.name
                for spec in _actions_for_agent(
                    actions, session, config, "Agent_1",
                    answer_sheet_contest=True, memory=memory,
                )
            }

        self.assertNotIn("submit", names())  # before min_turns, no challenge
        self.assertIn("work", names())  # the desk stays open instead of a lone submit
        session.consume_budget(turns=5)  # turn 10 == min_turns
        self.assertNotIn("submit", names())  # still waiting on min_challenges
        memory.append(
            task_id="q1", question_id=None, actor="Agent_2", visibility="public",
            kind="challenge", payload={"proposal_id": "P1", "content": "sign error"}, turn=9,
        )
        self.assertEqual(names(), {"submit"})

    def test_silent_work_streak_forces_discussion(self) -> None:
        config = ContestRunConfig(
            system_variant="otc", team_size=6, max_turns=12, rule_card=ARML
        )
        session = ContestSession([TaskUnit("q1"), TaskUnit("q2")], ContestBudgetState(max_turns=12))
        session.select_task("q1")
        memory = ContestMemory(run_id="r", session_id="arml_test", competition_id="arml_local")
        for turn in (3, 4):
            memory.append(
                task_id="q1", question_id=None, actor="Agent_1", visibility="public",
                kind="work", payload={"content": f"draft {turn}"}, turn=turn,
            )
        session.consume_budget(turns=5)
        self.assertEqual(otc_runtime.silent_work_streak(memory, "Agent_1"), 2)
        actions = _resolved_actions(arml_manifest(), config)
        names = {
            spec.name
            for spec in _actions_for_agent(
                actions, session, config, "Agent_1", answer_sheet_contest=True, memory=memory
            )
        }
        self.assertNotIn("work", names)
        self.assertIn("speak", names)
        self.assertIn("direct_message", names)
        memory.append(
            task_id="q1", question_id=None, actor="Agent_1", visibility="public",
            kind="speak", payload={"content": "reporting"}, turn=5,
        )
        self.assertEqual(otc_runtime.silent_work_streak(memory, "Agent_1"), 0)


class ArmlEndToEndTests(unittest.TestCase):
    def run_arml(self, scripts: dict[str, list[str]], **plan: Any) -> tuple[dict[str, Any], ScriptedLLM]:
        llm = ScriptedLLM(scripts, opening_plan=plan)
        config = ContestRunConfig(
            system_variant="otc",
            team_size=6,
            max_turns=12,
            max_api_calls=12 * 6 * 2 + 1,
            rule_card=ARML,
        )
        result = run_contest(arml_manifest(), llm, config, coach_query_fn=llm)
        return result, llm

    def test_single_turn0_coach_think_then_act_and_card_limits(self) -> None:
        long_speech = "Opening thoughts. " * 40  # > 320 chars
        result, llm = self.run_arml(
            {
                "Agent_1": [
                    action("speak", content="I open q1."),
                    action("work", content="q1 answer: 42 because 6*7."),
                    action("propose", content="q1 = 42"),
                ],
                "Agent_2": [
                    action("speak", content=long_speech),
                    action("select_problem", problem_id="q2"),
                    action("work", content="q2 answer: 7.", problem_id="q2"),
                    action("challenge", proposal_id="P1", content="check the sign"),
                ],
            },
            work_assignments={"Agent_1": ["q1"], "Agent_2": ["q2"]},
            task_order=["q1", "q2"],
        )
        kinds = [call["kind"] for call in llm.calls]
        # Stage 1: the blind brief is the very first call and sees no statement.
        # Card turn 0: it happens before the clock, so the contestants keep all
        # 12 turns and the brief event is stamped turn 0.
        self.assertEqual(kinds[0], "brief")
        self.assertNotIn("STATEMENT-q1", llm.calls[0]["user"])
        self.assertIn("before the clock starts (turn 0)", llm.calls[0]["user"])
        self.assertEqual(events_of(result, "precontest_coach_guidance")[0]["turn"], 0)
        self.assertEqual(result["budget"]["turns_used"], 12)
        self.assertEqual(min(e["turn"] for e in events_of(result, "speak")), 1)
        # Every contestant turn is think -> action for the same seat.
        for index, call in enumerate(llm.calls):
            if call["kind"] == "think":
                self.assertEqual(llm.calls[index + 1]["kind"], "action")
                self.assertEqual(llm.calls[index + 1]["agent"], call["agent"])
                self.assertIn("YOUR PRIVATE THINK LEDGER", llm.calls[index + 1]["user"])
        self.assertEqual(kinds.count("brief"), 1)
        self.assertNotIn("opening", kinds)
        self.assertFalse(events_of(result, "coach_opening_summary"))
        self.assertFalse(events_of(result, "coach_personal_assignment"))
        self.assertFalse(result["coach_opening_summary"])
        # The advisory assignment did not stop Agent_2 from switching to q2.
        self.assertFalse(
            [e for e in events_of(result, "action_error") if "coach assignment" in e["payload"]["error"]]
        )
        q2_drafts = [
            e for e in events_of(result, "work")
            if e["actor"] == "Agent_2" and e["task_id"] == "q2"
        ]
        self.assertEqual(len(q2_drafts), 1)
        # Card limits: the 320-char speak cap clipped Agent_2's opening speech.
        clipped = events_of(result, "card_content_clipped")
        self.assertEqual(len(clipped), 1)
        self.assertEqual(clipped[0]["payload"]["action"], "speak")
        self.assertEqual(clipped[0]["payload"]["limit"], 320)
        speak = [e for e in events_of(result, "speak") if e["actor"] == "Agent_2"][0]
        self.assertLessEqual(len(speak["payload"]["content"]), 320)
        # Deliberation actions came from the card and were recorded.
        self.assertEqual(len(events_of(result, "propose")), 1)
        self.assertEqual(events_of(result, "propose")[0]["payload"]["proposal_id"], "P1")
        self.assertEqual(len(events_of(result, "challenge")), 1)
        otc = result["diagnostics"]["otc"]
        self.assertEqual(otc["think_calls"], 12 * 6)
        self.assertEqual(otc["deliberation"]["counts"]["challenge"], 1)
        self.assertEqual(otc["communication"]["team_used"], 4)
        self.assertEqual(result["rule_card"]["rule_id"], ARML.rule_id)
        self.assertEqual(result["rule_card"]["mode"], "enforced")
        # 1 brief + 12 turns x 6 seats x (think + action).
        self.assertEqual(result["budget"]["api_calls_used"], 1 + 12 * 6 * 2)
        self.assertEqual(result["budget"]["api_calls_used"], result["budget"]["max_api_calls"])
        # Unreviewed drafts are never silently submitted at the deadline.
        self.assertFalse(events_of(result, "deadline_drafts_submitted"))

    def test_work_with_problem_id_switches_in_one_move_and_focus_advances(self) -> None:
        result, llm = self.run_arml(
            {
                # Assigned q1 then q2: after the q1 draft the focus must move to
                # q2 by itself, so the second plain work lands on q2.
                "Agent_1": [
                    action("speak", content="starting q1"),
                    action("work", content="q1 answer: 42."),
                    action("work", content="q2 answer: 7.", problem_id="q2"),
                ],
                # Assigned nothing, so the scheduler points it at q1 (still
                # blank at turn 2); it switches to q2 and drafts in one move.
                "Agent_2": [action("work", content="q2 alt: 8.", problem_id="q2")],
            },
            work_assignments={"Agent_1": ["q1", "q2"]},
        )
        # The card's work action exposes an optional problem_id.
        first_action = next(c for c in llm.calls if c["kind"] == "action" and c["agent"] == "Agent_2")
        self.assertIn("problem_id", first_action["system"])
        agent1 = [(e["turn"], e["task_id"]) for e in events_of(result, "work") if e["actor"] == "Agent_1"]
        self.assertEqual([task for _, task in agent1], ["q1", "q2"])
        agent2 = [e for e in events_of(result, "work") if e["actor"] == "Agent_2"]
        self.assertEqual(len(agent2), 1)
        self.assertEqual(agent2[0]["task_id"], "q2")
        self.assertNotIn("problem_id", agent2[0]["payload"])
        switch = [e for e in events_of(result, "select_problem") if e["actor"] == "Agent_2"]
        self.assertEqual(len(switch), 1)
        self.assertEqual(switch[0]["payload"], {"problem_id": "q2", "via": "work"})
        self.assertFalse(events_of(result, "action_error"))
        # Once every problem holds a draft, an assigned seat stays on its own
        # last suggestion for verification instead of following the cursor.
        agent1_rest = [e for e in events_of(result, "rest") if e["actor"] == "Agent_1"]
        self.assertTrue(agent1_rest and all(e["task_id"] == "q2" for e in agent1_rest))
        # The protocol tells seats which proposals are open (none here), and
        # the follow-up deliberation actions are not even offered until then.
        protocol = [c for c in llm.calls if c["kind"] == "action"][-1]["system"]
        self.assertIn("open proposals now: none (use propose first)", protocol)
        offered = protocol.split("OPEN TABLE COACH PROTOCOL")[0]
        self.assertIn("- propose(", offered)
        self.assertNotIn("- challenge(", offered)
        self.assertNotIn("- decide(", offered)

    def test_long_counted_message_is_clipped_not_rejected(self) -> None:
        # ARML communication.max_message_chars is 1200 < the 2400 work-class
        # cap that propose inherits; the card clips instead of burning the turn.
        result, _ = self.run_arml(
            {"Agent_1": [action("propose", content="claim " * 400)]}
        )
        proposals = events_of(result, "propose")
        self.assertEqual(len(proposals), 1)
        self.assertLessEqual(len(proposals[0]["payload"]["content"]), 1200)
        clipped = events_of(result, "card_content_clipped")
        self.assertEqual(clipped[0]["payload"]["limit"], 1200)
        self.assertFalse(
            [e for e in events_of(result, "action_error") if "communication budget" in e["payload"]["error"]]
        )

    def test_communication_budget_rejects_the_eleventh_message(self) -> None:
        result, _ = self.run_arml(
            {"Agent_1": [action("speak", content=f"note {i}") for i in range(11)]}
        )
        spoken = [e for e in events_of(result, "speak") if e["actor"] == "Agent_1"]
        self.assertEqual(len(spoken), 10)
        rejected = [
            e for e in events_of(result, "action_error")
            if "communication budget" in e["payload"]["error"]
        ]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(result["diagnostics"]["otc"]["communication"]["by_agent"]["Agent_1"], 10)

    def test_submit_before_min_turns_is_not_offered(self) -> None:
        result, llm = self.run_arml(
            {
                "Agent_1": [
                    action("work", content="q1: 42"),
                    action("select_problem", problem_id="q2"),
                    action("work", content="q2: 7"),
                    action("challenge", proposal_id="P1", content="x"),
                    action("submit"),
                ],
                "Agent_2": [action("propose", content="q1 = 42")],
            }
        )
        # Agent_1 tried submit at turn 6 (< min_turns 10): not available.
        errors = [e for e in events_of(result, "action_error") if e["actor"] == "Agent_1"]
        self.assertTrue(any("'submit' is not available" in e["payload"]["error"] for e in errors))
        self.assertEqual(result["budget"]["turns_used"], 12)


class IcpcEndToEndTests(unittest.TestCase):
    def test_repair_budget_lowers_priority_after_rejected_run(self) -> None:
        executions: list[str] = []

        def executor(_task: ManifestTask, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
            if name == "execute_code":
                executions.append(arguments["code"])
                return {"valid": True, "sample_verdict": "AC" if len(executions) == 1 else "WA", "sample_summary": "1/2"}
            if name == "submit_code":
                return {"verdict": "WA", "valid": True}
            return {"valid": False}

        llm = ScriptedLLM(
            {
                "Agent_1": [
                    action("speak", content="taking p1"),
                    action("execute_code", code="print(1)"),
                    action("speak", content="Samples pass; please review."),
                    action("submit_code"),
                    action("execute_code", code="print(2)"),
                    action("execute_code", code="print(3)"),
                    action("execute_code", code="print(4)"),
                ],
                "Agent_2": [action("speak", content="I watch p1")],
                "Agent_3": [action("select_problem", problem_id="p2")],
            },
            opening_plan={"work_assignments": {"Agent_1": ["p1"], "Agent_2": ["p1"], "Agent_3": ["p2"]}},
        )
        def reviewed_query(system, user):
            if "You are Agent_2" in system and "private deliberation" not in system.lower():
                marker = "YOUR ELIGIBLE PENDING REVIEWS" + chr(10)
                rows = json.JSONDecoder().raw_decode(user.split(marker)[1])[0]
                if rows:
                    row = rows[0]
                    llm.calls.append({"agent": "Agent_2", "kind": "action", "system": system, "user": user})
                    return action("review_answer", problem_id=row["problem_id"],
                                  version_hash=row["version_hash"], decision="approve",
                                  content="Read full source and checked samples.")
            return llm(system, user)
        config = ContestRunConfig(
            system_variant="otc", team_size=3, max_turns=10, max_api_calls=200, rule_card=ICPC
        )
        result = run_contest(
            icpc_manifest(), reviewed_query, config, coach_query_fn=llm, task_action_executor=executor
        )
        exhausted = events_of(result, "programming_repair_budget_exhausted")
        self.assertEqual(len(exhausted), 1)
        self.assertEqual(exhausted[0]["task_id"], "p1")
        p1 = next(row for row in result["session_checkpoint"]["tasks"] if row["task_id"] == "p1")
        self.assertEqual(p1["priority"], "low")
        self.assertEqual(result["diagnostics"]["otc"]["repair_budget_exhausted"], 1)
        # Lease: while Agent_1 held p1's keyboard, Agent_2's action prompt on p1
        # did not offer execute_code.
        agent2_actions = [
            c for c in llm.calls if c["agent"] == "Agent_2" and c["kind"] == "action"
        ]
        turn3 = agent2_actions[1]["system"]
        self.assertIn("Workstation lease", turn3)
        self.assertIn("currently held by Agent_1", turn3)
        self.assertNotIn('"execute_code"', turn3.split("OPEN TABLE COACH PROTOCOL")[0])
        # Latency: right after submit_code, the same seat's next prompt says a
        # verdict is pending and resubmission is withheld in that turn window.
        self.assertTrue(
            any("verdict is pending" in c["system"] for c in llm.calls if c["agent"] == "Agent_2")
        )
        self.assertEqual(result["diagnostics"]["otc"]["deliberation"], None)


if __name__ == "__main__":
    unittest.main()
