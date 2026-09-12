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
    DESK_ACTION_NAMES,
    DESK_READONLY_ACTION_NAMES,
    LEADER_ACTION_NAMES,
    LEGACY_ACTION_ALIASES,
    MEMORY_ACTION_NAMES,
    ActionSpec,
    Resolution,
    action_matches,
    action_name_variants,
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
            COMMON_ACTION_NAMES,
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
                }
            ),
        )
        self.assertEqual(
            {name for name, spec in ACTION_REGISTRY.items() if spec.pack == "common"},
            set(COMMON_ACTION_NAMES),
        )
        self.assertTrue(DESK_ACTION_NAMES <= COMMON_ACTION_NAMES)
        self.assertEqual(
            MEMORY_ACTION_NAMES | DESK_READONLY_ACTION_NAMES, DESK_ACTION_NAMES
        )
        self.assertTrue(LEADER_ACTION_NAMES <= COMMON_ACTION_NAMES)
        # v4 added the rule-card ``deliberation`` pack; v5 unified the legacy
        # environment surface (aliases + runtime tags). Neither is common.
        self.assertEqual(ACTION_SET_VERSION, 5)
        self.assertEqual(
            {name for name, spec in ACTION_REGISTRY.items() if spec.pack == "deliberation"},
            {"propose", "challenge", "provide_evidence", "revise", "decide"},
        )
        self.assertFalse(
            {"propose", "challenge", "provide_evidence", "revise", "decide"}
            & COMMON_ACTION_NAMES
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
        # ``verify`` folded into the desk's ``inspect_problem``.
        self.assertNotIn("verify", ACTION_REGISTRY)
        self.assertEqual(LEGACY_ACTION_ALIASES["verify"], "inspect_problem")
        self.assertEqual(ACTION_REGISTRY["submit_code"].pack, "programming")
        self.assertEqual(ACTION_REGISTRY["verify_problem"].pack, "workboard")
        self.assertEqual(ACTION_REGISTRY["check_budget"].pack, "workspace")
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
            {spec.name for spec in vanilla} - COMMON_ACTION_NAMES,
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
        self.assertTrue(COMMON_ACTION_NAMES <= names)
        self.assertTrue({"use_calculator", "web_search"} <= names)

    def test_resources_require_explicit_available_capability(self) -> None:
        handlers = set(ACTION_REGISTRY)
        demanded_only = resolve_action_names(
            competition="ijso_practical",
            benchmark_requirements={"required_tools": ["read_lab_equipment"]},
            registered_handlers=handlers,
        )
        declared = resolve_action_names(
            competition="ijso_practical",
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
            registered_handlers=COMMON_ACTION_NAMES,
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

    def test_legacy_aliases_are_adapter_only(self) -> None:
        self.assertEqual(LEGACY_ACTION_ALIASES["submit_final"], "submit")
        self.assertEqual(LEGACY_ACTION_ALIASES["sleep"], "rest")
        self.assertEqual(LEGACY_ACTION_ALIASES["publish_memory"], "share_note")
        self.assertEqual(LEGACY_ACTION_ALIASES["message_group"], "direct_message")
        self.assertEqual(LEGACY_ACTION_ALIASES["set_priority"], "triage_problem")
        self.assertEqual(LEGACY_ACTION_ALIASES["mark_hopeless"], "triage_problem")
        self.assertEqual(LEGACY_ACTION_ALIASES["submit_problem"], "work")
        for alias in LEGACY_ACTION_ALIASES:
            self.assertNotIn(alias, ACTION_REGISTRY)

    def test_runtime_tags_split_the_surface_without_forking_common(self) -> None:
        env_names = actions_for_runtime("env")
        session_names = actions_for_runtime("session")
        # Both runtimes implement every common action except the session-only
        # coordination verbs the environment has no equivalent for.
        self.assertEqual(
            COMMON_ACTION_NAMES - env_names,
            {"assign_problem", "request_review", "finish_contest"},
        )
        self.assertTrue(COMMON_ACTION_NAMES <= session_names)
        self.assertEqual(
            env_names - session_names,
            {"verify_problem", "check_budget", "query_rules", "write_private_notes"},
        )
        env_icpc = resolve_action_names("icpc", runtime="env")
        session_icpc = resolve_action_names("icpc", runtime="session")
        self.assertIn("check_budget", env_icpc)
        self.assertNotIn("check_budget", session_icpc)
        self.assertNotIn("assign_problem", env_icpc)
        # Without a runtime the canonical (non-desk-legacy) surface is returned.
        self.assertNotIn("check_budget", resolve_action_names("icpc"))
        self.assertTrue(action_matches("write_scratchpad", {"work"}))
        self.assertTrue(action_matches("work", {"write_scratchpad"}))
        self.assertEqual(
            action_name_variants("inspect_problem"),
            {"inspect_problem", "verify", "list_problems", "open_problem"},
        )


if __name__ == "__main__":
    unittest.main()
