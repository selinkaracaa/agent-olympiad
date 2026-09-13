from __future__ import annotations

import dataclasses
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from tool_registry import (  # noqa: E402
    ACTION_REGISTRY,
    ACTION_SET_VERSION,
    COMMON_ACTION_NAMES,
    BASE_ACTION_NAMES,
    MODULE_ACTION_NAMES,
    DESK_ACTION_NAMES,
    DESK_READONLY_ACTION_NAMES,
    LEADER_ACTION_NAMES,
    MEMORY_ACTION_NAMES,
    ActionSpec,
    Resolution,
    actions_for_runtime,
    render_action_instructions,
    render_function_tools,
    render_action_schema,
    resolve_action_names,
    resolve_actions,
    resolve_actions_with_diagnostics,
    validate_action_payload,
    validate_registry,
)


class ActionRegistryTests(unittest.TestCase):
    def test_common_actions_are_exact_and_registry_is_source_of_truth(self) -> None:
        self.assertEqual(
            BASE_ACTION_NAMES,
            frozenset(
                {
                    "select_problem",
                    "speak",
                    "direct_message",
                    "work",
                    "request_review",
                    "review_answer",
                    "submit",
                    "skip_problem",
                    "finish_contest",
                    "rest",
                    "inspect_problem",
                    "triage_problem",
                    "remember",
                    "recall",
                    "share_note",
                    "assign_problem",
                    "check_budget",
                    "query_rules",
                }
            ),
        )
        self.assertEqual(
            {name for name, spec in ACTION_REGISTRY.items() if spec.pack == "common"},
            set(BASE_ACTION_NAMES),
        )
        self.assertEqual(COMMON_ACTION_NAMES, MODULE_ACTION_NAMES['common'])
        self.assertTrue(DESK_ACTION_NAMES <= BASE_ACTION_NAMES)
        self.assertEqual(
            MEMORY_ACTION_NAMES | DESK_READONLY_ACTION_NAMES, DESK_ACTION_NAMES
        )
        self.assertTrue(LEADER_ACTION_NAMES <= COMMON_ACTION_NAMES)
        # v4 added the rule-card ``deliberation`` pack; v5 unified the legacy
        # environment surface (aliases + runtime tags); v6 made every action
        # available in both runtimes. Deliberation is still not common.
        self.assertEqual(ACTION_SET_VERSION, 8)
        self.assertEqual(
            {name for name, spec in ACTION_REGISTRY.items() if spec.pack == "deliberation"},
            {"propose", "challenge", "provide_evidence", "revise", "decide"},
        )
        self.assertFalse(
            {"propose", "challenge", "provide_evidence", "revise", "decide"}
            & BASE_ACTION_NAMES
        )
        self.assertEqual(validate_registry(), ())

    def test_assign_problem_is_a_leader_reassignment_with_a_problem_list(self) -> None:
        spec = ACTION_REGISTRY["assign_problem"]
        self.assertEqual(LEADER_ACTION_NAMES, frozenset({"assign_problem"}))
        self.assertEqual([arg.name for arg in spec.arguments], ["agent", "problem_ids", "reason"])
        self.assertEqual(spec.arguments[1].type, "array")
        self.assertEqual(spec.arguments[1].items, "string")
        self.assertFalse(spec.submission)
        self.assertFalse(spec.budget.terminal)
        self.assertEqual(
            validate_action_payload(
                spec, {"agent": "Agent_2", "problem_ids": ["a", "b"]}
            ),
            (),
        )
        self.assertTrue(
            validate_action_payload(spec, {"agent": "Agent_2", "problem_ids": []})
        )

    def test_desk_actions_are_read_only_or_personal(self) -> None:
        for name in DESK_ACTION_NAMES:
            spec = ACTION_REGISTRY[name]
            self.assertFalse(spec.submission, name)
            self.assertFalse(spec.evaluator, name)
            self.assertFalse(spec.budget.terminal, name)
        self.assertEqual(
            ACTION_REGISTRY["triage_problem"].arguments[1].enum,
            ("high", "normal", "low", "hopeless"),
        )
        self.assertFalse(ACTION_REGISTRY["inspect_problem"].arguments[0].required)
        self.assertFalse(ACTION_REGISTRY["recall"].arguments[0].required)

    def test_direct_message_takes_a_recipient_list(self) -> None:
        spec = ACTION_REGISTRY["direct_message"]
        schema = dict(spec.argument_schema)
        self.assertEqual(schema["properties"]["recipients"]["type"], "array")
        self.assertEqual(schema["properties"]["recipients"]["items"], {"type": "string"})
        self.assertNotIn("minItems", schema["properties"]["recipients"])
        self.assertEqual(
            validate_action_payload(
                spec, {"recipients": ["Agent_2", "Agent_3"], "content": "hi"}
            ),
            (),
        )
        self.assertTrue(
            validate_action_payload(spec, {"recipients": [], "content": "hi"})
        )
        self.assertTrue(
            validate_action_payload(spec, {"recipients": "Agent_2", "content": "hi"})
        )
        restricted = dataclasses.replace(
            spec,
            arguments=(
                dataclasses.replace(spec.arguments[0], enum=("Agent_2",)),
                spec.arguments[1],
            ),
        )
        self.assertTrue(
            validate_action_payload(
                restricted, {"recipients": ["Agent_9"], "content": "hi"}
            )
        )
        self.assertEqual(
            dict(restricted.argument_schema)["properties"]["recipients"]["items"],
            {"type": "string", "enum": ["Agent_2"]},
        )

    def test_specs_and_registry_are_immutable(self) -> None:
        spec = ACTION_REGISTRY["submit"]
        self.assertIsInstance(spec, ActionSpec)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            spec.name = "changed"  # type: ignore[misc]
        with self.assertRaises(TypeError):
            ACTION_REGISTRY["changed"] = spec  # type: ignore[index]

    def test_specs_expose_execution_and_evaluation_semantics(self) -> None:
        submit = ACTION_REGISTRY["submit"]
        self.assertEqual(submit.visibility, "team")
        self.assertEqual(submit.budget.turns, 1)
        self.assertTrue(submit.submission)
        self.assertTrue(submit.evaluator)
        self.assertEqual(submit.handler_name, "submit")
        self.assertEqual(submit.handler_marker, "submit")
        self.assertTrue(submit.argument_schema)

    def test_pack_membership(self) -> None:
        self.assertEqual(ACTION_REGISTRY["use_calculator"].pack, "math")
        self.assertEqual(ACTION_REGISTRY["execute_code"].pack, "programming")
        self.assertEqual(ACTION_REGISTRY["submit_code"].pack, "programming")
        # v7: no legacy spellings exist anywhere in the registry.
        for legacy in (
            "verify",
            "verify_problem",
            "write_private_notes",
            "write_scratchpad",
            "sleep",
            "submit_final",
            "message_group",
        ):
            self.assertNotIn(legacy, ACTION_REGISTRY)
        self.assertEqual(ACTION_REGISTRY["check_budget"].pack, "common")
        self.assertEqual(ACTION_REGISTRY["query_rules"].pack, "common")
        self.assertEqual(ACTION_REGISTRY["web_search"].pack, "research")
        self.assertEqual(ACTION_REGISTRY["read_lab_equipment"].pack, "resources")
        self.assertEqual(ACTION_REGISTRY["read_star_chart"].pack, "resources")

    def test_programming_resolution_is_variant_independent(self) -> None:
        handlers = set(ACTION_REGISTRY)
        vanilla = resolve_actions(
            competition="icpc",
            task_type="algorithmic_programming",
            registered_handlers=handlers,
            system_variant="vanilla",
        )
        strategic = resolve_actions(
            competition="icpc",
            task_type="algorithmic_programming",
            registered_handlers=handlers,
            system_variant="strategic",
        )
        self.assertIsInstance(vanilla, frozenset)
        self.assertEqual(vanilla, strategic)
        self.assertEqual(
            {spec.name for spec in vanilla} - BASE_ACTION_NAMES,
            {"execute_code", "submit_code"},
        )
        self.assertEqual(
            vanilla,
            resolve_actions(
                competition_id="icpc",
                task_type="algorithmic_programming",
                registered_handlers=handlers,
            ),
        )

    def test_math_and_research_can_come_from_requirements(self) -> None:
        names = resolve_action_names(
            competition="unknown",
            task_type="proof",
            benchmark_requirements={
                "required_packs": ["math"],
                "required_tools": ["web_search"],
            },
            registered_handlers=set(ACTION_REGISTRY),
        )
        self.assertTrue(BASE_ACTION_NAMES <= names)
        self.assertTrue({"use_calculator", "web_search"} <= names)

    def test_resources_require_explicit_available_capability(self) -> None:
        handlers = set(ACTION_REGISTRY)
        demanded_only = resolve_action_names(
            competition="resource_fixture",
            benchmark_requirements={"required_tools": ["read_lab_equipment"]},
            registered_handlers=handlers,
        )
        declared = resolve_action_names(
            competition="resource_fixture",
            benchmark_requirements={"required_tools": ["read_lab_equipment"]},
            declared_capabilities={"read_lab_equipment"},
            registered_handlers=handlers,
        )
        self.assertNotIn("read_lab_equipment", demanded_only)
        self.assertIn("read_lab_equipment", declared)

    def test_unknown_capabilities_and_missing_handlers_are_diagnosable(self) -> None:
        result = resolve_actions_with_diagnostics(
            competition="custom",
            declared_capabilities={"teleport", "web_search"},
            registered_handlers=BASE_ACTION_NAMES,
        )
        self.assertIsInstance(result, Resolution)
        self.assertNotIn("teleport", result.names)
        self.assertNotIn("web_search", result.names)
        self.assertEqual(result.unknown_capabilities, frozenset({"teleport"}))
        self.assertEqual(result.missing_handlers, frozenset({"web_search"}))

    def test_handler_mapping_accepts_handler_markers(self) -> None:
        handlers = {
            spec.handler_marker: object()
            for spec in ACTION_REGISTRY.values()
        }
        names = resolve_action_names(
            competition="icpc",
            task_type="programming",
            registered_handlers=handlers,
        )
        self.assertIn("submit_code", names)

    def test_schema_rendering_and_payload_validation(self) -> None:
        schema = render_action_schema(
            resolve_actions(
                competition="icpc",
                task_type="programming",
                registered_handlers=set(ACTION_REGISTRY),
            )
        )
        encoded = json.dumps(schema)
        self.assertIn("submit_code", encoded)
        self.assertEqual(schema["type"], "object")

        tools = render_function_tools(
            resolve_actions(
                competition="icpc",
                task_type="programming",
                registered_handlers=set(ACTION_REGISTRY),
            )
        )
        speak = next(tool for tool in tools if tool["name"] == "speak")
        self.assertEqual(speak["type"], "function")
        self.assertTrue(speak["strict"])
        self.assertEqual(
            speak["parameters"]["required"],
            ["content"],
        )
        self.assertFalse(speak["parameters"]["additionalProperties"])
        direct_message = next(
            tool for tool in tools if tool["name"] == "direct_message"
        )
        self.assertEqual(
            direct_message["parameters"]["required"],
            ["recipients", "content"],
        )

        self.assertEqual(
            validate_action_payload("select_problem", {"problem_id": "A"}),
            (),
        )
        errors = validate_action_payload("select_problem", {})
        self.assertTrue(any("problem_id" in error for error in errors))
        self.assertTrue(
            any(
                "unexpected" in error
                for error in validate_action_payload(
                    "rest", {"reason": "done", "extra": True}
                )
            )
        )
        self.assertTrue(validate_action_payload("not_registered", {}))

    def test_instruction_rendering_uses_resolved_specs(self) -> None:
        text = render_action_instructions(
            resolve_actions(
                competition="purple_comet",
                task_type="mathematics",
                registered_handlers=set(ACTION_REGISTRY),
            )
        )
        self.assertIn("select_problem", text)
        self.assertIn("use_calculator", text)
        self.assertNotIn("web_search", text)

    def test_legacy_spellings_are_unknown_actions(self) -> None:
        from action_wire import normalize_invocation

        for legacy in (
            "submit_final",
            "sleep",
            "write_scratchpad",
            "write_private_notes",
            "publish_memory",
            "message_group",
            "set_priority",
            "mark_hopeless",
            "submit_problem",
            "verify",
            "verify_problem",
            "list_problems",
            "open_problem",
            "claim_problem",
            "release_problem",
        ):
            invocation = normalize_invocation(legacy, "anything")
            self.assertFalse(invocation.ok, legacy)
            self.assertEqual(invocation.errors, (f"unknown action: {legacy}",))

    def test_runtime_tags_split_the_surface_without_forking_common(self) -> None:
        env_names = actions_for_runtime("env")
        session_names = actions_for_runtime("session")
        # v6: one vocabulary, implemented on both paths.
        self.assertEqual(env_names, session_names)
        self.assertEqual(env_names, frozenset(ACTION_REGISTRY))
        self.assertEqual(len(env_names), 30)
        env_icpc = resolve_action_names("icpc", runtime="env")
        session_icpc = resolve_action_names("icpc", runtime="session")
        self.assertEqual(env_icpc, session_icpc)
        for name in ("check_budget", "query_rules", "assign_problem", "request_review", "finish_contest"):
            self.assertIn(name, env_icpc)
        self.assertEqual(resolve_action_names("icpc"), env_icpc)

    def test_text_payloads_split_by_declared_fields(self) -> None:
        from action_wire import normalize_invocation

        review = normalize_invocation("review_answer", "3 | reject | the sign looks off")
        self.assertEqual(review.errors, ())
        self.assertEqual(
            review.arguments,
            {"problem_id": "3", "decision": "reject", "content": "the sign looks off"},
        )
        self.assertEqual(
            normalize_invocation("remember", "keep 17 in mind").arguments,
            {"content": "keep 17 in mind"},
        )
        self.assertEqual(
            normalize_invocation("work", "3 | 268").arguments,
            {"problem_id": "3", "content": "268"},
        )
        # review_answer without a version pin is a valid typed call.
        typed = normalize_invocation(
            "review_answer", {"problem_id": "3", "decision": "approve", "content": "ok"}
        )
        self.assertEqual(typed.errors, ())


if __name__ == "__main__":
    unittest.main()
