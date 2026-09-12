from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_manifest import ContestManifest, ManifestTask  # noqa: E402
from contest_memory import ContestMemory  # noqa: E402
from contest_runner import (  # noqa: E402
    ContestRunConfig,
    _apply_action,
    _actions_for_agent,
    _scheduled_agent_task,
    _task_rows,
    run_contest,
)
from contest_session import (  # noqa: E402
    ContestBudgetState,
    ContestSession,
    TaskState,
    TaskUnit,
)
from llm import LLMResponse, LLMToolCall  # noqa: E402
from strategy import StrategicPolicy  # noqa: E402
from tool_registry import ACTION_REGISTRY  # noqa: E402


def task(
    task_id: str,
    *,
    programming: bool = False,
    max_score: float = 1.0,
    task_type: str | None = None,
) -> ManifestTask:
    resolved_task_type = task_type or (
        "algorithmic_programming" if programming else "quiz"
    )
    return ManifestTask(
        task_id=task_id,
        parent_problem_id=task_id,
        question_id=None,
        prompt=f"Solve {task_id}",
        task_type=resolved_task_type,
        max_score=max_score,
        programming=programming,
        benchmark={
            "problem_id": task_id,
            "task_type": resolved_task_type,
        },
    )


def answer_hash(task_id: str, content: str, parent_hash: str = "") -> str:
    value = "\0".join((task_id, "", parent_hash, content))
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


from contest_feature_fixtures import review_ablation_config, run_with_test_plan

class ContestRunnerTests(unittest.TestCase):
    def test_direct_message_is_delivered_only_to_sender_and_recipient(self) -> None:
        manifest = ContestManifest("icpc", "session", (task("q1"),))
        session = ContestSession(
            [TaskUnit("q1")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("q1")
        memory = ContestMemory(
            run_id="run",
            session_id="session",
            competition_id="icpc",
        )
        config = review_ablation_config(
            team_size=3,
            max_turns=10,
        )

        _apply_action(
            action="direct_message",
            arguments={
                "recipients": ["Agent_2"],
                "content": "Please review the overflow case.",
            },
            agent="Agent_1",
            manifest=manifest,
            session=session,
            memory=memory,
            config=config,
            strategic_policy=StrategicPolicy(),
            task_action_executor=lambda _task, _action, _args: {},
        )

        sender = memory.view("Agent_1")
        recipient = memory.view("Agent_2")
        outsider = memory.view("Agent_3")
        self.assertEqual(sender[0].kind, "direct_message")
        self.assertEqual(recipient[0].kind, "direct_message")
        self.assertEqual(recipient[0].recipients, ("Agent_2",))
        self.assertEqual(outsider, [])

    def test_direct_message_reaches_every_named_recipient_only(self) -> None:
        manifest = ContestManifest("icpc", "session", (task("q1"),))
        session = ContestSession(
            [TaskUnit("q1")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("q1")
        memory = ContestMemory(run_id="run", session_id="session", competition_id="icpc")
        config = review_ablation_config(team_size=4, max_turns=10)
        apply = lambda arguments: _apply_action(  # noqa: E731
            action="direct_message",
            arguments=arguments,
            agent="Agent_1",
            manifest=manifest,
            session=session,
            memory=memory,
            config=config,
            strategic_policy=StrategicPolicy(),
            task_action_executor=lambda _task, _action, _args: {},
        )

        apply({"recipients": ["Agent_2", "Agent_4", "Agent_2"], "content": "sub-group"})

        for viewer in ("Agent_1", "Agent_2", "Agent_4"):
            inbox = memory.view(viewer)
            self.assertEqual([event.kind for event in inbox], ["direct_message"], viewer)
            self.assertEqual(inbox[0].recipients, ("Agent_2", "Agent_4"))
            self.assertEqual(inbox[0].payload["recipients"], ["Agent_2", "Agent_4"])
        self.assertEqual(memory.view("Agent_3"), [])
        projection = memory.strategic_projection(viewer="Agent_4", current_task_id="q1")
        self.assertEqual(projection["direct_messages"][0]["recipients"], ["Agent_2", "Agent_4"])

        with self.assertRaises(ValueError):
            apply({"recipients": ["Agent_1"], "content": "to myself"})
        with self.assertRaises(ValueError):
            apply({"recipients": ["Agent_9"], "content": "unknown"})
        with self.assertRaises(ValueError):
            apply({"recipients": [], "content": "nobody"})

    def test_direct_message_is_strategic_and_excludes_sender(self) -> None:
        session = ContestSession(
            [TaskUnit("q1")],
            ContestBudgetState(max_turns=10),
        )
        actions = frozenset(ACTION_REGISTRY.values())

        strategic = _actions_for_agent(
            actions,
            session,
            review_ablation_config(
                team_size=3,
                max_turns=10,
            ),
            "Agent_2",
        )
        direct = next(spec for spec in strategic if spec.name == "direct_message")
        recipients = next(
            argument for argument in direct.arguments if argument.name == "recipients"
        )
        self.assertEqual(recipients.type, "array")
        self.assertEqual(recipients.enum, ("Agent_1", "Agent_3"))
        self.assertEqual(
            dict(direct.argument_schema)["properties"]["recipients"]["items"]["enum"],
            ["Agent_1", "Agent_3"],
        )

        vanilla = _actions_for_agent(
            actions,
            session,
            ContestRunConfig(
                system_variant="vanilla",
                team_size=3,
                max_turns=10,
            ),
            "Agent_2",
        )
        self.assertNotIn("direct_message", {spec.name for spec in vanilla})

    def test_coach_scheduler_skips_tasks_still_in_cooldown(self) -> None:
        blocked = TaskUnit("blocked", kind="programming")
        blocked.state = TaskState.BLOCKED
        blocked.blocked_until_turn = 5
        ready = TaskUnit("ready", kind="programming")
        session = ContestSession(
            [blocked, ready],
            ContestBudgetState(max_turns=10),
        )
        session.budget.turns_used = 3

        scheduled = _scheduled_agent_task(
            session,
            agent="Agent_1",
            work_task_ids=["blocked", "ready"],
            review_task_ids=set(),
            reported_version_hashes=set(),
        )

        self.assertIsNotNone(scheduled)
        self.assertEqual(scheduled.task_id, "ready")

    def test_coach_scheduler_prioritizes_pending_review_over_unstarted_work(self) -> None:
        review_ready = TaskUnit("review-ready", kind="programming")
        unstarted = TaskUnit("unstarted", kind="programming")
        session = ContestSession(
            [review_ready, unstarted],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("review-ready")
        version = session.create_answer(
            "print(1)",
            author="Agent_1",
            evidence_refs=("sample-ac",),
        )

        scheduled = _scheduled_agent_task(
            session,
            agent="Agent_2",
            work_task_ids=["unstarted"],
            review_task_ids={"review-ready"},
            reported_version_hashes={version.version_hash},
        )

        self.assertIsNotNone(scheduled)
        self.assertEqual(scheduled.task_id, "review-ready")

    def test_coach_scheduler_prioritizes_approved_code_over_unstarted_work(self) -> None:
        submit_ready = TaskUnit("submit-ready", kind="programming")
        unstarted = TaskUnit("unstarted", kind="programming")
        session = ContestSession(
            [submit_ready, unstarted],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("submit-ready")
        session.create_answer(
            "print(1)",
            author="Agent_1",
            evidence_refs=("sample-ac",),
        )
        session.record_review(
            "Agent_2",
            "algorithm and complexity checked",
            decision="approve",
        )

        scheduled = _scheduled_agent_task(
            session,
            agent="Agent_1",
            work_task_ids=["submit-ready", "unstarted"],
            review_task_ids=set(),
            reported_version_hashes=set(),
        )

        self.assertIsNotNone(scheduled)
        self.assertEqual(scheduled.task_id, "submit-ready")

    def test_native_function_calls_bypass_prompt_json_parser(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        calls = iter(
            [
                LLMToolCall("select_problem", {"problem_id": "q1"}, "call-1"),
                LLMToolCall("work", {"content": "draft"}, "call-2"),
                LLMToolCall("submit", {"answer": "final"}, "call-3"),
            ]
        )
        requests = []

        def request_fn(request):
            requests.append(request)
            return LLMResponse(
                text="",
                provider="perplexity",
                model="test",
                usage={"output_tokens": 5},
                tool_calls=(next(calls),),
            )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: self.fail("prompt fallback was used"),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=2,
                max_turns=2,
                max_api_calls=3,
            ),
            action_request_fn=request_fn,
        )

        self.assertEqual(result["submissions"]["q1"], "final")
        self.assertEqual(result["action_calling"], "native")
        self.assertTrue(all(request.tool_choice == "required" for request in requests))
        self.assertTrue(all(request.tools for request in requests))
        self.assertNotIn("Return exactly one JSON", requests[0].system_prompt)
        self.assertEqual(
            [item["call_id"] for item in result["action_transport_log"]],
            ["call-1", "call-2", "call-3"],
        )
        self.assertEqual(
            result["action_transport_log"][0]["name"],
            "select_problem",
        )

    def test_emulated_transport_counts_repairs_and_underlying_api_calls(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        requests = []

        def request_fn(request):
            requests.append(request)
            return LLMResponse(
                text="",
                provider="tinker",
                model="test",
                usage={
                    "output_tokens": 30,
                    "api_calls": 3,
                    "tool_retries": 2,
                    "action_transport": "emulated",
                },
                tool_calls=(
                    LLMToolCall(
                        "select_problem",
                        {"problem_id": "q1"},
                        "tinker-emulated-3",
                    ),
                ),
            )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: self.fail("prompt fallback was used"),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=1,
                max_api_calls=3,
            ),
            action_request_fn=request_fn,
            action_transport="emulated",
        )

        self.assertEqual(result["action_calling"], "emulated")
        self.assertEqual(result["budget"]["api_calls_used"], 3)
        self.assertEqual(result["budget"]["tokens_used"], 30)
        self.assertEqual(result["diagnostics"]["transport_api_calls"], 3)
        self.assertEqual(result["diagnostics"]["transport_retries"], 2)
        self.assertEqual(result["diagnostics"]["transport_failures"], 0)
        self.assertEqual(requests[0].metadata["max_transport_attempts"], 3)

    def test_native_strategic_agent_keeps_full_action_choice(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        calls = iter(
            [
                LLMToolCall("select_problem", {"problem_id": "q1"}),
                LLMToolCall("work", {"content": "42"}),
                LLMToolCall("request_review", {"content": "APPROVE: checked"}),
                LLMToolCall("submit", {"answer": "42"}),
            ]
        )
        requests = []

        def request_fn(request):
            requests.append(request)
            return LLMResponse(
                text="",
                provider="perplexity",
                model="test",
                tool_calls=(next(calls),),
            )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: self.fail("prompt fallback was used"),
            review_ablation_config(
                team_size=2,
                max_turns=2,
                max_api_calls=4,
                require_final_review=False,
            ),
            action_request_fn=request_fn,
        )

        # finish_contest is the only gated common action: its handler rejects it
        # until every task holds a valid submission, so it stays hidden here.
        expected = set(result["action_names"]) - {"finish_contest"}
        self.assertTrue(
            all({tool["name"] for tool in request.tools} == expected for request in requests)
        )

    def test_vanilla_uses_latest_submission_without_review_gate(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"first"}}',
                '{"action":"submit","arguments":{"answer":"second"}}',
            ]
        )
        prompts: list[str] = []

        def query(system: str, user: str) -> str:
            prompts.append(system + "\n" + user)
            return next(responses)

        result = run_with_test_plan(
            manifest,
            query,
            ContestRunConfig(
                system_variant="vanilla",
                team_size=2,
                max_turns=2,
                max_api_calls=3,
            ),
        )

        self.assertEqual(result["submissions"]["q1"], "second")
        self.assertEqual(result["budget"]["api_calls_used"], 3)
        self.assertEqual(result["metrics"]["active_agent_rate"], 1.0)
        self.assertEqual(result["metrics"]["action_balance"], 1.0)
        rendered = "\n".join(prompts).lower()
        self.assertNotIn("mandatory review", rendered)
        self.assertNotIn("rule card", rendered)
        self.assertNotIn("coach", rendered)

    def test_math_packet_submits_the_entire_draft_sheet_once(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"select_problem","arguments":{"problem_id":"q2"}}',
                '{"action":"work","arguments":{"content":"22"}}',
                '{"action":"submit","arguments":{}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=5,
                max_api_calls=5,
            ),
        )

        self.assertEqual(result["submissions"], {"q1": "11", "q2": "22"})
        self.assertEqual(
            sum(len(task["submissions"]) for task in result["session_checkpoint"]["tasks"]),
            2,
        )

    def test_answer_sheet_prompt_uses_only_whole_sheet_submit_protocol(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        systems: list[str] = []

        def query(system: str, _user: str) -> str:
            systems.append(system)
            return '{"action":"rest","arguments":{"reason":"plan"}}'

        run_with_test_plan(
            manifest,
            query,
            review_ablation_config(
                team_size=1,
                max_turns=1,
                max_api_calls=1,
            ),
        )

        prompt = systems[0]
        self.assertIn("ANSWER-SHEET COACH PROTOCOL", prompt)
        self.assertIn("Never submit an individual problem", prompt)
        self.assertIn("call submit once with no arguments", prompt)
        self.assertNotIn("submit that same content unchanged", prompt)

    def test_single_math_packet_uses_math_not_programming_workflow(self) -> None:
        manifest = ContestManifest(
            "hmmt_guts_2024",
            "hmmt_guts",
            (task("hmmt_guts_2024", task_type="team_contest"),),
            {
                "competition_description": (
                    "HMMT Guts Round: a fast team mathematics contest with "
                    "a 36-question numbered packet."
                )
            },
        )
        systems: list[str] = []
        user_prompts: list[str] = []
        coach_prompts: list[str] = []

        def query(system: str, user: str) -> str:
            systems.append(system)
            user_prompts.append(user)
            return '{"action":"rest","arguments":{"reason":"plan"}}'

        def coach(system: str, user: str) -> str:
            coach_prompts.append(f"{system}\n{user}")
            return "{}"

        result = run_with_test_plan(
            manifest,
            query,
            review_ablation_config(
                team_size=2,
                max_turns=1,
                max_api_calls=2,
            ),
            coach_query_fn=coach,
        )

        self.assertEqual(manifest.task_family, "mathematics")
        self.assertIn("MATHEMATICS WORKFLOW", systems[0])
        self.assertIn("This is a mathematics contest, not a programming task", systems[0])
        self.assertNotIn("MANDATORY PROGRAMMING WORKFLOW", systems[0])
        self.assertIn("Task family: mathematics", coach_prompts[0])
        self.assertIn("36-question numbered packet", coach_prompts[0])
        self.assertIn("36-question numbered packet", user_prompts[0])
        self.assertNotIn("use_calculator", result["action_names"])
        self.assertNotIn("execute_code", result["action_names"])
        self.assertNotIn("submit_code", result["action_names"])

    def test_history_packet_uses_short_answer_workflow(self) -> None:
        manifest = ContestManifest(
            "history",
            "history_olympiad",
            (task("round", task_type="history_bowl_session"),),
        )
        systems: list[str] = []

        run_with_test_plan(
            manifest,
            lambda system, _user: (
                systems.append(system)
                or '{"action":"rest","arguments":{"reason":"plan"}}'
            ),
            review_ablation_config(
                team_size=1,
                max_turns=1,
                max_api_calls=1,
            ),
        )

        self.assertEqual(manifest.task_family, "short_answer")
        self.assertIn("SHORT-ANSWER WORKFLOW", systems[0])
        self.assertNotIn("MANDATORY PROGRAMMING WORKFLOW", systems[0])

    def test_leader_plan_is_shared_persisted_and_budgeted(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        coach_calls: list[str] = []
        agent_prompts: list[str] = []

        def coach(system: str, user: str) -> str:
            coach_calls.append(f"{system}\n{user}")
            return json.dumps(
                {
                    "summary": "Split drafting and cross-review.",
                    "work_assignments": {
                        "Agent_1": ["q1", "q2"],
                        "Agent_2": ["q2"],
                    },
                    "review_assignments": {
                        "Agent_1": ["q2"],
                        "Agent_2": ["q1", "q2"],
                    },
                    "task_order": ["q1", "q2"],
                    "switch_conditions": ["Switch after approval."],
                    "final_check": ["Audit both answers."],
                }
            )

        def query(system: str, user: str) -> str:
            agent_prompts.append(f"{system}\n{user}")
            return '{"action":"rest","arguments":{"reason":"follow coach"}}'

        result = run_with_test_plan(
            manifest,
            query,
            review_ablation_config(
                team_size=2,
                max_turns=1,
                max_api_calls=3,
            ),
            coach_query_fn=coach,
        )

        self.assertEqual(len(coach_calls), 1)
        self.assertIn('"problem_id": "q1"', coach_calls[0])
        self.assertIn('"work_tasks": ["q1", "q2"]', agent_prompts[0])
        self.assertEqual(
            result["precontest_coach_plan"]["work_assignments"]["Agent_1"],
            ["q1", "q2"],
        )
        self.assertEqual(result["budget"]["api_calls_used"], 3)
        self.assertTrue(
            any(
                event["kind"] == "coach_personal_assignment"
                and event["payload"]["agent"] == "Agent_1"
                and event["payload"]["work_tasks"] == ["q1", "q2"]
                for event in result["memory"]["events"]
            )
        )

    def test_coach_assignments_schedule_personal_work_and_cross_review(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        coach_plan = json.dumps(
            {
                "summary": "Parallel drafts with cross-review.",
                "work_assignments": {
                    "Agent_1": ["q1"],
                    "Agent_2": ["q2"],
                },
                "review_assignments": {
                    "Agent_1": ["q2"],
                    "Agent_2": ["q1"],
                },
                "task_order": ["q1", "q2"],
                "switch_conditions": ["Review after drafting."],
                "final_check": ["Audit both answers."],
            }
        )
        responses = iter(
            [
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"work","arguments":{"content":"22"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q2","version_hash":"'
                + answer_hash("q2", "22")
                + '","decision":"approve","content":"q2 checked"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "11")
                + '","decision":"approve","content":"q1 checked"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q2","version_hash":"'
                + answer_hash("q2", "22")
                + '","decision":"approve","content":"final q2 check"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "11")
                + '","decision":"approve","content":"final q1 check"}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=3,
                max_api_calls=7,
            ),
            coach_query_fn=lambda _system, _user: coach_plan,
        )

        history = result["shared_review_history"]
        self.assertEqual(history["q1"][0]["author"], "Agent_1")
        self.assertEqual(history["q2"][0]["author"], "Agent_2")
        self.assertEqual(history["q1"][0]["reviews"][0]["reviewer"], "Agent_2")
        self.assertEqual(history["q2"][0]["reviews"][0]["reviewer"], "Agent_1")
        self.assertEqual(result["submissions"], {"q1": "11", "q2": "22"})
        self.assertTrue(result["diagnostics"]["deadline_submission"])
        self.assertFalse(
            any(
                event["kind"] == "action_error"
                for event in result["memory"]["events"]
            )
        )

    def test_strategic_deadline_submits_latest_non_programming_draft(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        coach_plan = json.dumps(
            {
                "summary": "Draft and review q1.",
                "work_assignments": {"Agent_1": ["q1"]},
                "review_assignments": {"Agent_1": []},
                "task_order": ["q1"],
                "switch_conditions": [],
                "final_check": ["Submit the best available draft."],
            }
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: (
                '{"action":"work","arguments":{"content":"best available answer"}}'
            ),
            review_ablation_config(
                team_size=2,
                max_turns=1,
                max_api_calls=2,
            ),
            coach_query_fn=lambda _system, _user: coach_plan,
        )

        self.assertEqual(result["submissions"], {"q1": "best available answer"})
        self.assertTrue(result["diagnostics"]["deadline_submission"])
        self.assertTrue(
            any(
                event["kind"] == "deadline_drafts_submitted"
                and event["payload"]["submitted_task_ids"] == ["q1"]
                and event["payload"]["review_gate_waived"]
                for event in result["memory"]["events"]
            )
        )

    def test_coach_scheduled_active_task_is_not_offered_for_reselection(self) -> None:
        manifest = ContestManifest(
            "icpc",
            "icpc",
            (task("a", programming=True), task("b", programming=True)),
        )
        coach_plan = json.dumps(
            {
                "summary": "Agent_1 owns both problems.",
                "work_assignments": {"Agent_1": ["a", "b"], "Agent_2": []},
                "review_assignments": {"Agent_1": [], "Agent_2": ["a", "b"]},
                "task_order": ["a", "b"],
                "switch_conditions": [],
                "final_check": [],
            }
        )
        calls = iter(
            [
                LLMToolCall("rest", {"reason": "inspect tools"}),
                LLMToolCall("rest", {"reason": "inspect tools"}),
            ]
        )
        requests = []

        def request_fn(request):
            requests.append(request)
            return LLMResponse(
                text="",
                provider="perplexity",
                model="test",
                tool_calls=(next(calls),),
            )

        run_with_test_plan(
            manifest,
            lambda _system, _user: self.fail("prompt fallback was used"),
            review_ablation_config(
                team_size=2,
                max_turns=1,
                max_api_calls=3,
            ),
            action_request_fn=request_fn,
            coach_query_fn=lambda _system, _user: coach_plan,
        )

        first = requests[0]
        self.assertIn("ACTIVE TASK a\n", first.user_prompt)
        select_tool = next(
            tool for tool in first.tools if tool["name"] == "select_problem"
        )
        self.assertEqual(
            select_tool["parameters"]["properties"]["problem_id"]["enum"], ["b"]
        )

    def test_math_packet_rejects_submit_before_every_draft_exists(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"submit","arguments":{}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=3,
                max_api_calls=3,
            ),
        )

        # The premature model submission is rejected; the common deadline
        # collector later preserves the available partial answer sheet.
        self.assertEqual(result["submissions"], {"q1": "11", "q2": ""})
        self.assertTrue(result["diagnostics"]["deadline_submission"])
        errors = [
            event["payload"]["error"]
            for event in result["memory"]["events"]
            if event["kind"] == "action_error"
        ]
        self.assertIn("action 'submit' is not available", errors)

    def test_zero_score_answer_sheet_task_does_not_block_submission(self) -> None:
        manifest = ContestManifest(
            "math",
            "arml_local",
            (task("q1"), task("q2", max_score=0.0)),
        )
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"submit","arguments":{}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=3,
                max_api_calls=3,
            ),
        )

        self.assertEqual(result["submissions"], {"q1": "11", "q2": ""})

    def test_strategic_math_packet_reviews_full_sheet_then_submits_once(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "11")
                + '","decision":"approve","content":"q1 approved"}}',
                '{"action":"select_problem","arguments":{"problem_id":"q2"}}',
                '{"action":"work","arguments":{"content":"22"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q2","version_hash":"'
                + answer_hash("q2", "22")
                + '","decision":"approve","content":"q2 approved"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "11")
                + '","decision":"approve","content":"final q1"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q2","version_hash":"'
                + answer_hash("q2", "22")
                + '","decision":"approve","content":"final q2"}}',
                '{"action":"submit","arguments":{}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=5,
                max_api_calls=9,
            ),
        )

        self.assertEqual(result["submissions"], {"q1": "11", "q2": "22"})
        self.assertEqual(result["diagnostics"]["final_review_status"], "completed")
        self.assertEqual(result["diagnostics"]["final_review_coverage"], 1.0)
        events = [event["kind"] for event in result["memory"]["events"]]
        self.assertLess(
            events.index("final_review_completed"),
            max(index for index, kind in enumerate(events) if kind == "submit"),
        )

    def test_agents_share_one_active_problem(self) -> None:
        manifest = ContestManifest(
            "math",
            "arml_local",
            (task("q1"), task("q2")),
        )
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "11")
                + '","decision":"approve","content":"q1 checked"}}',
                '{"action":"select_problem","arguments":{"problem_id":"q2"}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=2,
                max_api_calls=4,
                require_final_review=False,
            ),
        )

        self.assertEqual(result["active_task_id"], "q2")
        self.assertEqual(result["shared_review_history"]["q1"][0]["answer"], "11")
        self.assertEqual(
            result["shared_review_history"]["q1"][0]["reviews"][0]["decision"],
            "approve",
        )

    def test_select_problem_changes_the_team_active_problem(self) -> None:
        manifest = ContestManifest("math", "arml_local", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"11"}}',
                '{"action":"select_problem","arguments":{"problem_id":"q2"}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=1,
                max_turns=3,
                max_api_calls=3,
            ),
        )

        self.assertEqual(result["active_task_id"], "q2")
        self.assertTrue(
            result["tasks"]["q1"]["terminal_verdict"] == "SUBMITTED"
        )
        self.assertTrue(result["diagnostics"]["deadline_submission"])

    def test_strategic_rejects_unreviewed_answer_then_accepts_independent_review(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                '{"action":"work","arguments":{"content":"42"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                '{"action":"submit","arguments":{"answer":"42"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "42")
                + '","decision":"approve","content":"independently checked"}}',
                '{"action":"submit","arguments":{"answer":"42"}}',
            ]
        )
        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=4,
                max_api_calls=7,
            ),
        )

        self.assertEqual(result["submissions"]["q1"], "42")
        errors = [
            event
            for event in result["memory"]["events"]
            if event["kind"] == "action_error"
        ]
        self.assertTrue(
            any(
                "independent approval" in event["payload"]["error"]
                for event in errors
            )
        )
        self.assertEqual(result["diagnostics"]["review_coverage"], 1.0)

    def test_answer_review_history_is_shared_and_version_bound(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"rest","arguments":{"reason":"hold"}}',
                '{"action":"work","arguments":{"content":"42"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "42")
                + '","decision":"approve","content":"APPROVE: verified"}}',
                '{"action":"rest","arguments":{"reason":"history seen"}}',
            ]
        )
        prompts: list[str] = []

        def query(_system: str, user: str) -> str:
            prompts.append(user)
            return next(responses)

        result = run_with_test_plan(
            manifest,
            query,
            review_ablation_config(
                team_size=2,
                max_turns=3,
                max_api_calls=5,
                require_final_review=False,
            ),
        )

        history = result["shared_review_history"]["q1"][0]
        self.assertEqual(history["answer"], "42")
        self.assertEqual(history["author"], "Agent_1")
        self.assertEqual(history["reviews"][0]["reviewer"], "Agent_2")
        self.assertEqual(history["reviews"][0]["decision"], "approve")
        self.assertIn("SHARED ANSWER REVIEW HISTORY", prompts[-1])
        self.assertIn("APPROVE: verified", prompts[-1])

    def test_strategic_runs_reserved_final_review_after_answer_sheet_completion(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"rest","arguments":{"reason":"hold"}}',
                '{"action":"work","arguments":{"content":"42"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "42")
                + '","decision":"approve","content":"checked"}}',
                '{"action":"submit","arguments":{"answer":"42"}}',
                '{"action":"review_answer","arguments":{"problem_id":"q1","version_hash":"'
                + answer_hash("q1", "42")
                + '","decision":"approve","content":"final audit"}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=4,
                max_api_calls=6,
            ),
        )

        event_kinds = [event["kind"] for event in result["memory"]["events"]]
        self.assertIn("final_review_started", event_kinds)
        self.assertIn("final_review_approved", event_kinds)
        self.assertIn("final_review_completed", event_kinds)
        self.assertEqual(result["diagnostics"]["final_review_coverage"], 1.0)
        self.assertEqual(result["diagnostics"]["final_review_status"], "completed")

    def test_strategic_three_non_ac_attempts_switch_to_another_problem(self) -> None:
        manifest = ContestManifest(
            "icpc-two",
            "icpc",
            (task("a", programming=True), task("b", programming=True)),
        )
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"work","arguments":{"content":"code-1"}}',
                '{"action":"submit_code","arguments":{"code":"code-1"}}',
                '{"action":"work","arguments":{"content":"code-2"}}',
                '{"action":"submit_code","arguments":{"code":"code-2"}}',
                '{"action":"work","arguments":{"content":"code-3"}}',
                '{"action":"submit_code","arguments":{"code":"code-3"}}',
            ]
        )

        def executor(_task, action: str, _arguments: dict) -> dict:
            self.assertEqual(action, "submit_code")
            return {"verdict": "WA", "valid": True}

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=1,
                max_turns=7,
                max_api_calls=7,
                require_review=False,
            ),
            task_action_executor=executor,
        )

        self.assertEqual(result["tasks"]["a"]["state"], "blocked")
        self.assertEqual(result["active_task_id"], "b")
        self.assertEqual(result["diagnostics"]["switch_count"], 1)
        self.assertEqual(result["tasks"]["a"]["score"], 0.0)

    def test_vanilla_does_not_receive_strategic_three_fail_switch(self) -> None:
        manifest = ContestManifest(
            "icpc-two",
            "icpc",
            (task("a", programming=True), task("b", programming=True)),
        )
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"work","arguments":{"content":"code-1"}}',
                '{"action":"submit_code","arguments":{"code":"code-1"}}',
                '{"action":"work","arguments":{"content":"code-2"}}',
                '{"action":"submit_code","arguments":{"code":"code-2"}}',
                '{"action":"work","arguments":{"content":"code-3"}}',
                '{"action":"submit_code","arguments":{"code":"code-3"}}',
            ]
        )
        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=7,
                max_api_calls=7,
            ),
            task_action_executor=lambda _task, _action, _arguments: {
                "verdict": "WA",
                "valid": True,
            },
        )
        self.assertEqual(result["active_task_id"], "a")
        self.assertEqual(result["tasks"]["a"]["state"], "submitted")
        self.assertEqual(result["diagnostics"]["switch_count"], 0)

    def test_baselines_share_the_core_action_set_and_differ_only_by_bundles(self) -> None:
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True),))
        core = {
            "select_problem", "speak", "work", "request_review", "review_answer",
            "submit", "skip_problem", "rest", "finish_contest", "execute_code",
            "submit_code",
        }
        surfaces = {
            name: set(
                run_with_test_plan(
                    manifest,
                    lambda _system, _user: '{"action":"rest","arguments":{}}',
                    ContestRunConfig(system_variant=name, team_size=size, max_turns=1),
                )["action_names"]
            )
            for name, size in (
                ("single_agent", 1),
                ("decentralized", 3),
                ("centralized", 3),
            )
        }
        for name, names in surfaces.items():
            self.assertTrue(core <= names, name)
        self.assertEqual(surfaces["single_agent"], core)
        self.assertEqual(surfaces["decentralized"], core)
        self.assertEqual(
            surfaces["centralized"] - core,
            {"inspect_problem", "triage_problem", "direct_message", "assign_problem"},
        )

    def test_legacy_variant_names_are_aliases_and_team_size_rules_hold(self) -> None:
        self.assertEqual(
            ContestRunConfig("vanilla", 3, 1).system_variant, "decentralized"
        )
        from contest_config import canonical_baseline
        from rules.loader import load_rule_card
        for name in ("otc", "OTC", "strategic", "strategic_team", "open_table_coach", "open_table_coach_memory"):
            self.assertEqual(canonical_baseline(name), "otc")
            config = ContestRunConfig(name, 3, 1, rule_card=load_rule_card("icpc"))
            self.assertEqual(config.system_variant, "otc")
            self.assertEqual(config.features.coach, "card")
            self.assertTrue(config.features.memory_actions)
            self.assertTrue(config.review_required)
        self.assertFalse(ContestRunConfig("centralized", 3, 1).review_required)
        with self.assertRaisesRegex(ValueError, "single_agent requires team_size=1"):
            ContestRunConfig("single_agent", 3, 1)
        with self.assertRaisesRegex(ValueError, "worker seat"):
            ContestRunConfig("centralized", 1, 1)
        with self.assertRaisesRegex(ValueError, "unknown system_variant"):
            ContestRunConfig("round_table", 3, 1)

    def test_finish_contest_is_rejected_while_tasks_remain(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"finish_contest","arguments":{"reason":"done"}}',
                '{"action":"select_problem","arguments":{"problem_id":"q2"}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=3,
                max_api_calls=3,
            ),
        )

        self.assertEqual(result["active_task_id"], "q2")
        errors = [
            event["payload"]["error"]
            for event in result["memory"]["events"]
            if event["kind"] == "action_error"
        ]
        # The action is hidden (not merely rejected) while tasks remain, for
        # both variants; the turn is still lost but no finish event is written.
        self.assertEqual(len(errors), 1)
        self.assertIn("finish_contest", errors[0])
        self.assertNotIn(
            "finish_contest",
            [event["kind"] for event in result["memory"]["events"]],
        )

    def test_strategic_code_review_binds_local_evidence_before_remote_submit(self) -> None:
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True),))
        # work is a programming note; execute_code creates the first source version.
        evidence_hash = answer_hash("a", "print(1)")
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                '{"action":"work","arguments":{"content":"print(1)"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                '{"action":"execute_code","arguments":{"code":"print(1)"}}',
                '{"action":"rest","arguments":{"reason":"wait for run report"}}',
                '{"action":"speak","arguments":{"content":"Local run output is 1; please review."}}',
                '{"action":"review_answer","arguments":{"problem_id":"a","version_hash":"'
                + evidence_hash
                + '","decision":"approve","content":"checked run evidence"}}',
                '{"action":"submit_code","arguments":{}}',
            ]
        )
        calls: list[str] = []

        def executor(_task, action: str, arguments: dict) -> dict:
            calls.append(action)
            if action == "submit_code":
                self.assertEqual(arguments["code"], "print(1)")
            return {"result": "1", "valid": True} if action == "execute_code" else {
                "verdict": "AC",
                "valid": True,
            }

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=5,
                max_api_calls=9,
            ),
            task_action_executor=executor,
        )

        self.assertEqual(calls, ["execute_code", "submit_code"])
        self.assertEqual(result["tasks"]["a"]["state"], "solved")
        self.assertEqual(result["diagnostics"]["attempts_to_ac"]["a"], 1)

    def test_strategic_code_actions_follow_evidence_review_submit_gate(self) -> None:
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True),))
        evidence_hash = answer_hash("a", "print(1)")
        calls = iter(
            [
                LLMToolCall("select_problem", {"problem_id": "a"}),
                LLMToolCall("rest", {"reason": "wait"}),
                LLMToolCall("work", {"content": "print(1)"}),
                LLMToolCall("rest", {"reason": "wait"}),
                LLMToolCall("execute_code", {"code": "print(1)"}),
                LLMToolCall("rest", {"reason": "wait for run report"}),
                LLMToolCall(
                    "speak",
                    {"content": "Local run succeeded with output 1; please review."},
                ),
                LLMToolCall(
                    "review_answer",
                    {
                        "problem_id": "a",
                        "version_hash": evidence_hash,
                        "decision": "approve",
                        "content": "local output is correct",
                    },
                ),
                LLMToolCall("submit_code", {}),
            ]
        )
        requests = []

        def request_fn(request):
            requests.append(request)
            return LLMResponse(
                text="",
                provider="perplexity",
                model="test",
                tool_calls=(next(calls),),
            )

        def executor(_task, action: str, _arguments: dict) -> dict:
            if action == "execute_code":
                return {"result": "1", "valid": True}
            return {"verdict": "AC", "valid": True}

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: self.fail("prompt fallback was used"),
            review_ablation_config(
                team_size=2,
                max_turns=5,
                max_api_calls=9,
            ),
            action_request_fn=request_fn,
            task_action_executor=executor,
        )

        action_names = [
            {tool["name"] for tool in request.tools}
            for request in requests
        ]
        self.assertNotIn("submit_code", action_names[2])
        self.assertIn("execute_code", action_names[4])
        self.assertNotIn("review_answer", action_names[5])
        self.assertNotIn("submit_code", action_names[5])
        self.assertIn("review_answer", action_names[7])
        self.assertNotIn("submit_code", action_names[7])
        self.assertIn("submit_code", action_names[8])
        submit_tool = next(
            tool for tool in requests[8].tools if tool["name"] == "submit_code"
        )
        self.assertEqual(submit_tool["parameters"]["properties"], {})
        self.assertIn(
            "work stores analysis notes only",
            requests[4].user_prompt,
        )
        self.assertIn(
            "Only after the samples pass, the author calls speak",
            requests[0].system_prompt,
        )
        self.assertIn(
            "Wait for the author to report the successful local run",
            requests[5].user_prompt,
        )
        self.assertIn(
            "Call speak to report",
            requests[6].user_prompt,
        )
        self.assertIn(
            "Read the full source and the sample report",
            requests[7].user_prompt,
        )
        self.assertEqual(result["tasks"]["a"]["state"], "solved")

    def test_first_ac_locks_only_that_problem_not_the_whole_contest(self) -> None:
        manifest = ContestManifest(
            "icpc-two",
            "icpc",
            (task("a", programming=True), task("b", programming=True)),
        )
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"work","arguments":{"content":"code"}}',
                '{"action":"submit_code","arguments":{"code":"code"}}',
                '{"action":"select_problem","arguments":{"problem_id":"b"}}',
                '{"action":"finish_contest","arguments":{}}',
            ]
        )
        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=1,
                max_turns=5,
                max_api_calls=5,
                require_review=False,
            ),
            task_action_executor=lambda _task, _action, _arguments: {
                "verdict": "AC",
                "valid": True,
            },
        )
        self.assertEqual(result["budget"]["api_calls_used"], 5)
        self.assertEqual(result["tasks"]["a"]["state"], "solved")
        self.assertEqual(result["tasks"]["b"]["state"], "active")

    def test_wrong_penalty_affects_score_without_consuming_contest_clock(self) -> None:
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True),))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"work","arguments":{"content":"bad"}}',
                '{"action":"submit_code","arguments":{"code":"bad"}}',
                '{"action":"speak","arguments":{"content":"continue working"}}',
            ]
        )
        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=2,
                max_turns=2,
                max_api_calls=4,
                max_simulated_minutes=10,
                minutes_per_turn=0,
                require_review=False,
            ),
            task_action_executor=lambda _task, _action, _arguments: {
                "verdict": "WA",
                "valid": True,
            },
        )
        self.assertEqual(result["budget"]["api_calls_used"], 4)
        self.assertEqual(result["budget"]["simulated_minutes_used"], 0)
        self.assertEqual(result["budget"]["penalty_minutes"], 20)

    def test_checkpoint_resume_keeps_history_and_continues_current_session(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"),))
        captured: dict[str, object] = {}

        def interrupt(session_state: dict, memory_state: str) -> None:
            captured["session"] = session_state
            captured["memory"] = memory_state
            raise InterruptedError("simulated process stop")

        with self.assertRaises(InterruptedError):
            run_with_test_plan(
                manifest,
                lambda _system, _user: (
                    '{"action":"select_problem","arguments":{"problem_id":"q1"}}'
                ),
                ContestRunConfig(
                    system_variant="vanilla",
                    team_size=1,
                    max_turns=3,
                    max_api_calls=3,
                ),
                checkpoint_callback=interrupt,
            )

        responses = iter(
            [
                '{"action":"work","arguments":{"content":"draft"}}',
                '{"action":"submit","arguments":{"answer":"final"}}',
            ]
        )
        resumed = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=3,
                max_api_calls=3,
            ),
            session_checkpoint=captured["session"],
            memory_checkpoint=captured["memory"],
        )
        self.assertEqual(resumed["submissions"]["q1"], "final")
        self.assertEqual(
            [event["event_id"] for event in resumed["memory"]["events"]],
            [
                f"event-{index:06d}"
                for index in range(1, len(resumed["memory"]["events"]) + 1)
            ],
        )

    def test_run_records_wall_clock_timing_and_resume_accumulates(self) -> None:
        manifest = ContestManifest(
            "arml-time",
            "arml_local",
            (task("q1"),),
        )
        captured: dict[str, object] = {}

        def interrupt(session_state: dict, memory_state: str) -> None:
            if "session" not in captured:
                captured["session"] = session_state
                captured["memory"] = memory_state
                raise RuntimeError("interrupt after first checkpoint")

        with self.assertRaises(RuntimeError):
            run_with_test_plan(
                manifest,
                lambda _system, _user: (
                    '{"action":"select_problem","arguments":{"problem_id":"q1"}}'
                ),
                ContestRunConfig(
                    system_variant="vanilla",
                    team_size=1,
                    max_turns=3,
                    max_api_calls=3,
                ),
                checkpoint_callback=interrupt,
            )

        first_wall = float(captured["session"]["budget"]["wall_seconds_used"])
        first_started = captured["session"]["budget"]["wall_started_at"]
        self.assertIsNotNone(first_started)
        self.assertGreaterEqual(first_wall, 0.0)

        responses = iter(
            [
                '{"action":"work","arguments":{"content":"draft"}}',
                '{"action":"submit","arguments":{"answer":"final"}}',
            ]
        )
        resumed = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            ContestRunConfig(
                system_variant="vanilla",
                team_size=1,
                max_turns=3,
                max_api_calls=3,
            ),
            session_checkpoint=captured["session"],
            memory_checkpoint=captured["memory"],
        )
        timing = resumed["timing"]
        self.assertEqual(timing["started_at"], first_started)
        self.assertGreaterEqual(timing["elapsed_seconds"], first_wall)
        self.assertGreaterEqual(timing["segment_seconds"], 0.0)
        self.assertEqual(
            resumed["budget"]["wall_seconds_used"],
            timing["elapsed_seconds"],
        )
        self.assertEqual(
            resumed["metrics"]["elapsed_seconds"],
            timing["elapsed_seconds"],
        )
        self.assertEqual(resumed["submissions"]["q1"], "final")

    def test_sample_ac_code_can_be_submitted_after_independent_reject(self) -> None:
        """The remote judge is the oracle: a reviewer's reject must not starve submissions."""
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True),))
        passing_hash = answer_hash("a", "print(2)")
        responses = iter(
            [
                # turn 1: author runs samples (AC), reviewer waits
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                # turn 2: local run passes, then report
                '{"action":"execute_code","arguments":{"code":"print(2)"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                # turn 3: author reports; reviewer rejects on theoretical grounds
                '{"action":"speak","arguments":{"content":"samples pass: 1/1 AC"}}',
                '{"action":"review_answer","arguments":{"problem_id":"a","version_hash":"'
                + passing_hash
                + '","decision":"reject","content":"not proven for all n"}}',
                # turn 4: author disagrees and submits anyway -> remote verdict
                '{"action":"submit_code","arguments":{}}',
                '{"action":"rest","arguments":{"reason":"done"}}',
            ]
        )
        prompts: list[str] = []
        remote_submits: list[str] = []

        def query(_system: str, user: str) -> str:
            prompts.append(user)
            return next(responses)

        def executor(_task, action: str, arguments: dict) -> dict:
            if action == "execute_code":
                return {
                    "result": "Code output:\n2",
                    "valid": True,
                    "sample_verdict": "AC",
                    "sample_summary": "Sample judge: AC (1/1 official sample cases passed).",
                    "sample_cases": [{"name": "s1", "verdict": "AC", "detail": ""}],
                }
            remote_submits.append(arguments["code"])
            return {"verdict": "AC", "valid": True}

        result = run_with_test_plan(
            manifest,
            query,
            review_ablation_config(
                team_size=2,
                max_turns=4,
                max_api_calls=8,
            ),
            task_action_executor=executor,
        )

        self.assertEqual(remote_submits, ["print(2)"])
        self.assertEqual(result["tasks"]["a"]["state"], "solved")
        self.assertFalse(
            any(
                event["kind"] == "action_error"
                for event in result["memory"]["events"]
            )
        )
        # Turn 4, Agent_1: guidance offers submission as a valid path after a reject.
        self.assertIn("submit_code", prompts[6])

    def test_inspect_problem_returns_history_without_approval_or_cursor_move(self) -> None:
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True), task("b", programming=True)))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"work","arguments":{"content":"print(1)"}}',
                '{"action":"inspect_problem","arguments":{"focus":"edge cases"}}',
                '{"action":"inspect_problem","arguments":{"problem_id":"b"}}',
            ]
        )

        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=1,
                max_turns=4,
                max_api_calls=4,
                require_review=False,
            ),
        )

        self.assertNotIn("verify", result["action_names"])
        self.assertIn("inspect_problem", result["action_names"])
        inspections = [
            event
            for event in result["memory"]["events"]
            if event["kind"] == "inspect_problem_result"
        ]
        self.assertEqual([event["task_id"] for event in inspections], ["a", "b"])
        own = inspections[0]["payload"]
        self.assertEqual(own["focus"], "edge cases")
        self.assertEqual(own["statement"], "Solve a")
        self.assertEqual([v["content"] for v in own["versions"]], ["print(1)"])
        self.assertFalse(own["independent_approval"])
        self.assertEqual(inspections[1]["payload"]["versions"], [])
        self.assertEqual(inspections[0]["visibility"], "private")
        # Inspecting b never moved the shared cursor away from a.
        self.assertEqual(result["active_task_id"], "a")
        self.assertEqual(result["diagnostics"]["switch_count"], 0)
        self.assertEqual(result["diagnostics"]["inspect_count"], 2)
        self.assertEqual(result["session_checkpoint"]["tasks"][0]["reviews"], [])
        self.assertEqual(result["protocol_version"], "contest_session_v6")
        self.assertEqual(result["action_set_version"], 5)
        self.assertEqual(result["baseline"]["coach"], "none")

    def test_remember_recall_and_share_note_round_trip(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"), task("q2")))
        session = ContestSession(
            [TaskUnit("q1", kind="non_programming"), TaskUnit("q2", kind="non_programming")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("q1")
        memory = ContestMemory(run_id="run", session_id="quiz", competition_id="quiz")
        config = review_ablation_config(memory=True,
            team_size=2, max_turns=10
        )

        def apply(agent: str, action: str, arguments: dict) -> None:
            _apply_action(
                action=action,
                arguments=arguments,
                agent=agent,
                manifest=manifest,
                session=session,
                memory=memory,
                config=config,
                strategic_policy=StrategicPolicy(),
                task_action_executor=lambda _task, _action, _args: {},
                work_task_ids={"q1"},
            )

        # Notes are desk actions: they ignore the coach's work assignment.
        apply("Agent_1", "remember", {"content": "q2 looks like a telescoping sum", "problem_id": "q2"})
        apply("Agent_1", "remember", {"content": "q1 parity argument fails at n=3"})
        note_events = [event for event in memory.view("Agent_1") if event.kind == "note"]
        self.assertEqual([event.task_id for event in note_events], ["q2", "q1"])
        self.assertEqual(note_events[0].visibility, "private")
        self.assertEqual(memory.view("Agent_2"), [])
        self.assertEqual(session.active_task.task_id, "q1")
        self.assertEqual(session.task("q1").versions, [])

        apply("Agent_1", "recall", {"problem_id": "q2"})
        recall_result = next(e for e in memory.view("Agent_1") if e.kind == "recall_result")
        self.assertEqual(recall_result.payload["notes"][0]["content"], "q2 looks like a telescoping sum")
        self.assertEqual(recall_result.payload["notes"][0]["note_id"], note_events[0].event_id)
        self.assertEqual(len(recall_result.payload["notes"]), 2)

        with self.assertRaises(ValueError):
            apply("Agent_2", "share_note", {"note_id": note_events[0].event_id})
        apply("Agent_1", "share_note", {"note_id": note_events[0].event_id})
        shared = next(e for e in memory.view("Agent_2") if e.kind == "note_shared")
        self.assertEqual(shared.visibility, "public")
        self.assertEqual(shared.task_id, "q2")
        self.assertEqual(shared.payload["source_event_id"], note_events[0].event_id)
        self.assertEqual(shared.payload["author"], "Agent_1")
        with self.assertRaises(ValueError):
            apply("Agent_1", "share_note", {"note_id": note_events[0].event_id})

        teammate = memory.recall("Agent_2", query="telescoping")
        self.assertEqual([row["shared"] for row in teammate], [True])
        projection = memory.strategic_projection(viewer="Agent_1", current_task_id="q1")
        self.assertEqual(
            {row["note_id"] for row in projection["recent_notes"]},
            {note_events[0].event_id, shared.event_id},
        )

    def test_triage_problem_reorders_scheduler_and_keeps_hopeless_on_sheet(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("a"), task("b"), task("c")))
        session = ContestSession(
            [TaskUnit(t, kind="non_programming") for t in ("a", "b", "c")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("a")
        memory = ContestMemory(run_id="run", session_id="quiz", competition_id="quiz")
        config = review_ablation_config(team_size=2, max_turns=10)

        def schedule() -> str | None:
            scheduled = _scheduled_agent_task(
                session,
                agent="Agent_1",
                work_task_ids=["a", "b", "c"],
                review_task_ids=set(),
                reported_version_hashes=set(),
            )
            return scheduled.task_id if scheduled else None

        self.assertEqual(schedule(), "a")
        _apply_action(
            action="triage_problem",
            arguments={"problem_id": "c", "priority": "high", "reason": "easy points"},
            agent="Agent_2",
            manifest=manifest,
            session=session,
            memory=memory,
            config=config,
            strategic_policy=StrategicPolicy(),
            task_action_executor=lambda _task, _action, _args: {},
            work_task_ids={"a"},  # triage is a desk action: assignment does not gate it
        )
        self.assertEqual(schedule(), "c")
        self.assertEqual(session.active_task.task_id, "a")  # cursor untouched
        triaged = next(e for e in memory.view("Agent_1") if e.kind == "task_triaged")
        self.assertEqual(triaged.visibility, "public")
        self.assertEqual(triaged.payload["previous_priority"], "normal")
        self.assertEqual(session.task("c").triaged_by, "Agent_2")

        _apply_action(
            action="triage_problem",
            arguments={"problem_id": "a", "priority": "hopeless"},
            agent="Agent_1",
            manifest=manifest,
            session=session,
            memory=memory,
            config=config,
            strategic_policy=StrategicPolicy(),
            task_action_executor=lambda _task, _action, _args: {},
        )
        self.assertEqual(schedule(), "c")
        for task_id in ("c", "b"):
            session.select_task(task_id)
            session.create_answer(f"draft {task_id}", author="Agent_2")
        # a is hopeless, but still the only remaining blank task -> scheduled last, not dropped.
        self.assertEqual(schedule(), "a")
        rows = {row["task_id"]: row for row in _task_rows(session)}
        self.assertTrue(rows["a"]["hopeless"])
        self.assertEqual(rows["c"]["priority"], "high")
        with self.assertRaises(ValueError):
            _apply_action(
                action="triage_problem",
                arguments={"problem_id": "zz", "priority": "low"},
                agent="Agent_1",
                manifest=manifest,
                session=session,
                memory=memory,
                config=config,
                strategic_policy=StrategicPolicy(),
                task_action_executor=lambda _task, _action, _args: {},
            )

        restored = ContestSession.from_checkpoint(session.checkpoint())
        self.assertEqual(restored.task("a").priority, "hopeless")
        self.assertEqual(restored.task("c").triage_reason, "easy points")

    def test_hopeless_draft_is_still_collected_at_deadline(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"guess 7"}}',
                '{"action":"triage_problem","arguments":{"problem_id":"q1","priority":"hopeless"}}',
            ]
        )
        result = run_with_test_plan(
            manifest,
            lambda _system, _user: next(responses),
            review_ablation_config(
                team_size=1,
                max_turns=3,
                max_api_calls=3,
                require_review=False,
            ),
        )
        self.assertEqual(result["submissions"]["q1"], "guess 7")
        self.assertEqual(result["diagnostics"]["items_hopeless"], 1)
        self.assertEqual(result["diagnostics"]["triage_changes"], 1)

    def test_repeated_work_draft_gets_private_feedback_instead_of_silence(self) -> None:
        manifest = ContestManifest("quiz", "quiz", (task("q1"), task("q2")))
        responses = iter(
            [
                '{"action":"select_problem","arguments":{"problem_id":"q1"}}',
                '{"action":"work","arguments":{"content":"first"}}',
                '{"action":"work","arguments":{"content":"second"}}',
                '{"action":"work","arguments":{"content":"first"}}',
                '{"action":"rest","arguments":{}}',
            ]
        )
        prompts: list[str] = []

        def query(system: str, user: str) -> str:
            prompts.append(user)
            return next(responses)

        result = run_with_test_plan(
            manifest,
            query,
            ContestRunConfig(system_variant="vanilla", team_size=1, max_turns=5, max_api_calls=5),
        )
        versions = result["session_checkpoint"]["tasks"][0]["versions"]
        self.assertEqual([v["content"] for v in versions], ["first", "second"])
        duplicate = next(e for e in result["memory"]["events"] if e["kind"] == "work_duplicate")
        self.assertEqual(duplicate["visibility"], "private")
        self.assertEqual(duplicate["recipients"], ["Agent_1"])
        self.assertEqual(duplicate["payload"]["version_hash"], versions[0]["version_hash"])
        self.assertFalse(duplicate["payload"]["is_latest"])
        self.assertEqual(duplicate["payload"]["blank_task_ids"], ["q2"])
        self.assertEqual(duplicate["payload"]["recorded_turn"], 2)
        self.assertEqual(result["diagnostics"]["repeat_draft_attempts"], 1)
        # The feedback reaches the author's next prompt.
        self.assertIn("work_duplicate", prompts[-1])
        self.assertIn('"blank_tasks": ["q2"]', prompts[-1])

    def test_desk_bundles_follow_the_baseline_and_vanish_in_submit_only_phase(self) -> None:
        session = ContestSession(
            [TaskUnit("a", kind="non_programming"), TaskUnit("b", kind="non_programming")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("a")
        actions = frozenset(
            spec for spec in ACTION_REGISTRY.values() if spec.pack == "common"
        )
        readonly = {"inspect_problem", "triage_problem"}
        notes = {"remember", "recall", "share_note"}

        decentralized = {
            spec.name
            for spec in _actions_for_agent(
                actions, session, ContestRunConfig("decentralized", 2, 10), "Agent_1"
            )
        }
        self.assertFalse((readonly | notes | {"direct_message"}) & decentralized)
        # Off-assignment coach agents keep the desk but lose work/skip.
        coach = _actions_for_agent(
            actions,
            session,
            review_ablation_config(2, 10),
            "Agent_1",
            work_task_ids={"b"},
            review_task_ids=set(),
        )
        names = {spec.name for spec in coach}
        self.assertTrue(readonly <= names)
        self.assertFalse(notes & names)
        self.assertIn("direct_message", names)
        self.assertNotIn("work", names)
        inspect = next(spec for spec in coach if spec.name == "inspect_problem")
        self.assertEqual(inspect.arguments[0].enum, ("a", "b"))
        with_memory = {
            spec.name
            for spec in _actions_for_agent(
                actions,
                session,
                review_ablation_config(2, 10, memory=True),
                "Agent_1",
            )
        }
        self.assertTrue((readonly | notes) <= with_memory)

        # Answer-sheet contests collapse to submit-only once the sheet is ready.
        for t in ("a", "b"):
            session.select_task(t)
            session.create_answer("draft", author="Agent_2")
        submit_only = _actions_for_agent(
            actions,
            session,
            ContestRunConfig("decentralized", 2, 10),
            "Agent_1",
            answer_sheet_contest=True,
            required_answer_task_ids={"a", "b"},
        )
        self.assertEqual({spec.name for spec in submit_only}, {"submit"})

    def test_centralized_workers_cannot_submit_and_leader_reassigns(self) -> None:
        session = ContestSession(
            [TaskUnit("a", kind="non_programming"), TaskUnit("b", kind="non_programming")],
            ContestBudgetState(max_turns=10),
        )
        session.select_task("a")
        actions = frozenset(
            spec for spec in ACTION_REGISTRY.values() if spec.pack == "common"
        )
        config = ContestRunConfig("centralized", 3, 10)
        leader = {spec.name: spec for spec in _actions_for_agent(actions, session, config, "Agent_1")}
        worker = {spec.name for spec in _actions_for_agent(actions, session, config, "Agent_2")}
        self.assertIn("assign_problem", leader)
        self.assertIn("submit", leader)
        self.assertEqual(leader["assign_problem"].arguments[0].enum, ("Agent_2", "Agent_3"))
        self.assertEqual(leader["assign_problem"].arguments[1].enum, ("a", "b"))
        self.assertFalse({"assign_problem", "submit", "submit_code", "finish_contest"} & worker)
        self.assertFalse({"request_review", "review_answer", "remember"} & (worker | set(leader)))
        self.assertIn("work", worker)

        # Sheet complete: the leader collapses to submit, workers keep their desk.
        for t in ("a", "b"):
            session.select_task(t)
            session.create_answer("draft", author="Agent_2")
        ready_leader = _actions_for_agent(
            actions, session, config, "Agent_1",
            answer_sheet_contest=True, required_answer_task_ids={"a", "b"},
        )
        ready_worker = _actions_for_agent(
            actions, session, config, "Agent_2",
            answer_sheet_contest=True, required_answer_task_ids={"a", "b"},
        )
        self.assertEqual({spec.name for spec in ready_leader}, {"submit"})
        self.assertIn("work", {spec.name for spec in ready_worker})
        self.assertNotIn("submit", {spec.name for spec in ready_worker})

        manifest = ContestManifest("quiz", "quiz", (task("a"), task("b")))
        memory = ContestMemory(run_id="run", session_id="quiz", competition_id="quiz")
        table = {"Agent_2": {"agent": "Agent_2", "work_tasks": ["a"], "review_tasks": []}}
        common = dict(
            manifest=manifest, session=session, memory=memory, config=config,
            strategic_policy=StrategicPolicy(),
            task_action_executor=lambda _task, _action, _args: {},
            personal_assignments=table,
        )
        with self.assertRaisesRegex(ValueError, "only the team leader"):
            _apply_action(action="assign_problem", agent="Agent_2",
                          arguments={"agent": "Agent_3", "problem_ids": ["b"]}, **common)
        with self.assertRaisesRegex(ValueError, "only Agent_1 may submit"):
            _apply_action(action="submit", agent="Agent_2",
                          arguments={"answer": "x"}, **common)
        _apply_action(action="assign_problem", agent="Agent_1",
                      arguments={"agent": "Agent_2", "problem_ids": ["b", "b", "a"]}, **common)
        self.assertEqual(table["Agent_2"]["work_tasks"], ["b", "a"])
        event = next(e for e in memory.view("Agent_3") if e.kind == "assign_problem")
        self.assertEqual(event.visibility, "public")
        self.assertEqual(event.payload["problem_ids"], ["b", "a"])

    def test_centralized_leader_plans_reassigns_and_submits_for_the_team(self) -> None:
        manifest = ContestManifest(
            "quiz", "quiz",
            (task("a", task_type="team_contest"), task("b", task_type="team_contest")),
        )
        plan = json.dumps({
            "summary": "split",
            "work_assignments": {"Agent_2": ["a"], "Agent_3": ["b"]},
            "task_order": ["a", "b"],
        })
        responses = iter([
            plan,
            # turn 1: leader (first seat) reassigns Agent_3 onto a; Agent_2 drafts a
            '{"action":"assign_problem","arguments":{"agent":"Agent_3","problem_ids":["a"]}}',
            '{"action":"work","arguments":{"content":"draft a"}}',
            '{"action":"rest","arguments":{}}',
            # turn 2: leader drafts b; the sheet is complete but only the leader may submit
            '{"action":"work","arguments":{"content":"draft b"}}',
            '{"action":"submit","arguments":{}}',
            '{"action":"rest","arguments":{}}',
            # turn 3: leader hands in the whole sheet
            '{"action":"submit","arguments":{}}',
        ])
        prompts: list[tuple[str, str]] = []

        def query(system: str, user: str) -> str:
            prompts.append((system, user))
            return next(responses)

        result = run_with_test_plan(
            manifest, query,
            ContestRunConfig("centralized", 3, 6, max_api_calls=20),
        )
        self.assertEqual(result["system_variant"], "centralized")
        self.assertEqual(result["plan_author"], "Agent_1")
        self.assertTrue(result["baseline"]["leader_submits"])
        self.assertIn("OPENING LEADER PLAN", prompts[0][1])
        plan_event = next(
            e for e in result["memory"]["events"] if e["kind"] == "precontest_coach_guidance"
        )
        self.assertEqual(plan_event["actor"], "Agent_1")
        self.assertEqual(plan_event["payload"]["plan"]["work_assignments"]["Agent_1"], ["a", "b"])
        # Leader acts first each round; workers see the leader protocol.
        self.assertIn("LEADER PROTOCOL: You are Agent_1", prompts[1][0])
        self.assertIn("LEADER PROTOCOL: Agent_1 is the team leader", prompts[2][0])
        # Agent_3's enforced memory reflects the live reassignment in the same round.
        self.assertIn('"work_tasks": ["a"]', prompts[3][1])
        # Agent_2's submit attempt on the complete sheet was rejected and logged.
        errors = [
            e for e in result["memory"]["events"]
            if e["kind"] == "action_error" and e["actor"] == "Agent_2"
        ]
        self.assertEqual(len(errors), 1)
        self.assertIn("submit", errors[0]["payload"]["error"])
        self.assertEqual(plan_event["payload"]["plan"]["review_assignments"]["Agent_2"], [])
        self.assertEqual(result["submissions"], {"a": "draft a", "b": "draft b"})
        self.assertEqual(result["budget"]["turns_used"], 3)

    def test_centralized_reassignment_survives_resume(self) -> None:
        manifest = ContestManifest(
            "quiz", "quiz",
            (task("a", task_type="team_contest"), task("b", task_type="team_contest")),
        )
        plan = json.dumps({"work_assignments": {"Agent_2": ["a"]}, "task_order": ["a", "b"]})
        first = iter([
            plan,
            '{"action":"assign_problem","arguments":{"agent":"Agent_2","problem_ids":["b"]}}',
        ])
        captured: dict[str, object] = {}

        def interrupt(session_state: dict, memory_state: str) -> None:
            captured["session"] = session_state
            captured["memory"] = memory_state
            if any(
                e["kind"] == "assign_problem" for e in json.loads(memory_state)["events"]
            ):
                raise InterruptedError("simulated process stop")

        config = ContestRunConfig("centralized", 2, 3, max_api_calls=8)
        with self.assertRaises(InterruptedError):
            run_with_test_plan(
                manifest, lambda _s, _u: next(first), config,
                checkpoint_callback=interrupt,
            )
        seen: list[str] = []

        def resumed_query(_system: str, user: str) -> str:
            seen.append(user)
            return '{"action":"rest","arguments":{}}'

        resumed = run_with_test_plan(
            manifest, resumed_query, config,
            session_checkpoint=captured["session"],
            memory_checkpoint=captured["memory"],
        )
        # No second plan was requested, and Agent_2's live list is still ["b"].
        self.assertEqual(
            sum(e["kind"] == "precontest_coach_guidance" for e in resumed["memory"]["events"]), 1
        )
        worker_prompt = next(u for u in seen if "You are Agent_2" not in u and '"agent": "Agent_2"' in u)
        self.assertIn('"work_tasks": ["b"]', worker_prompt)

    def test_sample_failure_blocks_evidence_and_reviewers_see_full_source(self) -> None:
        manifest = ContestManifest("icpc", "icpc", (task("a", programming=True),))
        failing_hash = answer_hash("a", "print(1)")
        passing_hash = answer_hash("a", "print(2)", failing_hash)
        responses = iter(
            [
                # turn 1
                '{"action":"select_problem","arguments":{"problem_id":"a"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                # turn 2: local run fails the official sample
                '{"action":"execute_code","arguments":{"code":"print(1)"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                # turn 3: author speaks anyway; nothing enters the review queue
                '{"action":"speak","arguments":{"content":"please review"}}',
                '{"action":"rest","arguments":{"reason":"nothing to review"}}',
                # turn 4: revised code passes the sample
                '{"action":"execute_code","arguments":{"code":"print(2)"}}',
                '{"action":"rest","arguments":{"reason":"wait"}}',
                # turn 5: report, then independent review with the full source
                '{"action":"speak","arguments":{"content":"samples pass: 1/1 AC"}}',
                '{"action":"review_answer","arguments":{"problem_id":"a","version_hash":"'
                + passing_hash
                + '","decision":"approve","content":"read full source"}}',
                # turn 6: remote WA, then the team sees verdict-specific guidance
                '{"action":"submit_code","arguments":{}}',
                '{"action":"rest","arguments":{"reason":"read the WA checklist"}}',
            ]
        )
        prompts: list[str] = []

        def query(_system: str, user: str) -> str:
            prompts.append(user)
            return next(responses)

        def executor(_task, action: str, arguments: dict) -> dict:
            if action == "execute_code":
                if arguments["code"] == "print(1)":
                    return {
                        "result": "Code output:\n1",
                        "valid": True,
                        "sample_verdict": "WA",
                        "sample_summary": "Sample judge: WA (0/1 official sample cases passed).",
                        "sample_cases": [
                            {
                                "name": "s1",
                                "verdict": "WA",
                                "detail": "token 0 mismatch",
                                "input": "",
                                "expected": "2",
                                "actual": "1",
                            }
                        ],
                    }
                return {
                    "result": "Code output:\n2",
                    "valid": True,
                    "sample_verdict": "AC",
                    "sample_summary": "Sample judge: AC (1/1 official sample cases passed).",
                    "sample_cases": [{"name": "s1", "verdict": "AC", "detail": ""}],
                }
            self.assertEqual(arguments["code"], "print(2)")
            return {"verdict": "WA", "valid": True}

        result = run_with_test_plan(
            manifest,
            query,
            review_ablation_config(
                team_size=2,
                max_turns=6,
                max_api_calls=12,
            ),
            task_action_executor=executor,
        )

        versions = result["session_checkpoint"]["tasks"][0]["versions"]
        self.assertEqual([version["version_hash"] for version in versions], [failing_hash, passing_hash])
        self.assertEqual(versions[0]["evidence_refs"], [])
        self.assertEqual(len(versions[1]["evidence_refs"]), 1)

        # Turn 3, Agent_1: the sample failure is spelled out with expected vs actual.
        self.assertIn("failed the official samples", prompts[4])
        self.assertIn('expected: "2"', prompts[4])
        self.assertIn('got: "1"', prompts[4])
        # Turn 3, Agent_2: a speak about a non-evidence version never reaches the queue.
        self.assertIn("YOUR ELIGIBLE PENDING REVIEWS\n[]", prompts[5])
        local_reports = [
            event
            for event in result["memory"]["events"]
            if event["kind"] == "local_run_report"
        ]
        self.assertEqual(
            [event["payload"]["version_hash"] for event in local_reports],
            [passing_hash],
        )
        # Turn 5, Agent_2: the reviewer sees the full source, sample report and author report.
        pending = json.loads(prompts[9].split("YOUR ELIGIBLE PENDING REVIEWS\n", 1)[1].split("\n\nVISIBLE MEMORY", 1)[0])
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["version_hash"], passing_hash)
        self.assertEqual(pending[0]["source"], "print(2)")
        self.assertEqual(pending[0]["sample_report"]["sample_verdict"], "AC")
        self.assertEqual(pending[0]["author_report"], "samples pass: 1/1 AC")
        self.assertIn("Read the full source and the sample report", prompts[9])
        # Turn 6, Agent_2: verdict-specific recovery guidance after the remote WA.
        self.assertIn("REMOTE VERDICT WA on attempt 1", prompts[11])
        self.assertIn("2 more non-AC attempt(s)", prompts[11])
        self.assertIn("WA checklist", prompts[11])
        self.assertIn("The same source hash cannot be resubmitted", prompts[11])
        self.assertEqual(result["budget"]["penalty_minutes"], 20)
        self.assertEqual(result["tasks"]["a"]["state"], "submitted")


if __name__ == "__main__":
    unittest.main()
