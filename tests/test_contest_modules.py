"""Module interfaces and isolation, independent of provider or remote judge."""
import json
import unittest
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

from action_modules import MODULE_SPECS
from action_modules.common import CORE_ACTION_NAMES
from action_modules.coach import prepare_brief
from action_modules.memory import agent_context, private_think_context, recall_notes, share_note
from action_modules.task_specific import resolve_contest_interface
from contest_actions import _apply_action
from contest_config import BASELINES, BASELINE_NAMES, ContestRunConfig
from contest_manifest import ContestManifest, ManifestTask
from contest_memory import ContestMemory
from contest_policy import _resolved_actions
from rules.loader import load_rule_card


def manifest(competition="arml_local", benchmark=None):
    return ContestManifest("module-test", competition, (
        ManifestTask("q1", "q1", None, "TASK_SECRET: compute an answer.", "math", 1, False, benchmark or {}),
    ))


def memory():
    return ContestMemory(run_id="r", session_id="module-test", competition_id="arml_local")


def note(store, actor="Agent_1", content="PRIVATE_CANARY", turn=0, kind="note"):
    return store.append(task_id="q1", question_id=None, actor=actor,
                        visibility="private", kind=kind,
                        payload={"content": content}, turn=turn)


class ContestModuleTests(unittest.TestCase):
    def test_four_modules_and_no_callable_coach(self):
        self.assertEqual(set(MODULE_SPECS), {"common", "memory", "coach", "task_specific"})
        self.assertEqual(MODULE_SPECS["coach"], ())

    def test_common_core_and_optional_selection_across_settings(self):
        card = load_rule_card("arml_local")
        for variant in BASELINE_NAMES:
            with self.subTest(variant=variant):
                config = ContestRunConfig(
                    variant, 1 if variant == "single_agent" else card.team_size_default, 3,
                    rule_card=card if variant in {"otc", "vallina_otc"} else None,
                )
                names = {spec.name for spec in _resolved_actions(manifest(), config)}
                self.assertTrue(CORE_ACTION_NAMES <= names)
                self.assertEqual("remember" in names, config.modules.memory)
                self.assertEqual(config.modules.coach, variant in {"otc", "vallina_otc"})
                self.assertTrue(config.modules.as_dict()["common"])

    def test_memory_enabled_without_coach(self):
        config = ContestRunConfig(
            "decentralized", 2, 3,
            features=replace(BASELINES["decentralized"], memory_actions=True),
        )
        self.assertTrue(config.modules.memory)
        self.assertFalse(config.modules.coach)
        self.assertIn("recall", {spec.name for spec in _resolved_actions(manifest(), config)})

    def test_disabled_memory_rejected_at_dispatch(self):
        with self.assertRaisesRegex(ValueError, "module.*disabled"):
            _apply_action(
                action="remember", arguments={"content": "no"}, agent="Agent_1",
                manifest=manifest(), session=None, memory=None,
                config=ContestRunConfig("decentralized", 2, 3),
                strategic_policy=None, task_action_executor=None,
            )

    def test_memory_off_filters_notes_and_retrieval_but_keeps_conversation(self):
        store = memory()
        note(store)
        recall_notes(store, agent="Agent_1", query="CANARY", problem_id="q1", event_task_id="q1", turn=0)
        store.append(task_id="q1", question_id=None, actor="Agent_2", visibility="public",
                     kind="speak", payload={"content": "PUBLIC_MESSAGE"}, turn=0)
        value = json.dumps(agent_context(store, viewer="Agent_1", enabled=False, current_task_id="q1"))
        self.assertNotIn("CANARY", value)
        self.assertIn("PUBLIC_MESSAGE", value)
        self.assertIn("CANARY", json.dumps(store.archival_snapshot()))
        enabled = json.dumps(agent_context(store, viewer="Agent_1", enabled=True, current_task_id="q1"))
        self.assertIn("CANARY", enabled)

    def test_private_notes_require_explicit_sharing_and_survive_checkpoint(self):
        store = memory()
        saved = note(store)
        self.assertFalse(store.recall("Agent_2", query="CANARY"))
        session = SimpleNamespace(budget=SimpleNamespace(turns_used=0))
        with self.assertRaises(ValueError):
            share_note(memory=store, session=session, agent="Agent_2", note_id=saved.event_id)
        share_note(memory=store, session=session, agent="Agent_1", note_id=saved.event_id)
        restored = ContestMemory.from_checkpoint_json(store.to_checkpoint_json())
        self.assertTrue(restored.recall("Agent_2", query="CANARY"))
        with self.assertRaises(ValueError):
            share_note(memory=store, session=session, agent="Agent_1", note_id=saved.event_id)

    def test_memory_off_retains_only_current_private_thought(self):
        store = memory()
        note(store, content="OLD", kind="think", turn=0)
        note(store, content="CURRENT", kind="think", turn=1)
        args = dict(enabled=False, current_turn=1, limit=4)
        self.assertEqual(private_think_context(store, "Agent_1", include_current=False, **args), [])
        self.assertEqual([r["content"] for r in private_think_context(store, "Agent_1", **args)], ["CURRENT"])

    def test_coach_is_blind_once_and_cannot_start_late(self):
        card = load_rule_card("arml_local")
        config = ContestRunConfig("otc", card.team_size_default, 3, rule_card=card)
        store = memory()
        budget = SimpleNamespace(turns_used=0)
        session = SimpleNamespace(budget=budget, consume_budget=Mock())
        query = Mock(return_value="Prepare carefully.")
        args = dict(enabled=True, card=card, policy=config.otc_policy,
                    manifest=manifest(), session=session, memory=store,
                    team_size=card.team_size_default, max_turns=3, max_api_calls=20,
                    query=query, charge_tokens=lambda _: True)
        self.assertTrue(prepare_brief(**args).created)
        budget.turns_used = 1
        self.assertFalse(prepare_brief(**args).created)
        query.assert_called_once()
        self.assertNotIn("TASK_SECRET", " ".join(query.call_args.args))
        self.assertFalse(prepare_brief(**{**args, "enabled": False}).created)
        with self.assertRaisesRegex(ValueError, "after the contest"):
            prepare_brief(**{**args, "memory": memory()})

    def test_missing_resource_and_unknown_card_tool_are_not_advertised(self):
        card = replace(load_rule_card("arml_local"), competition_id="fixture",
                       allowed_tools=("read_lab_equipment", "start_environment"))
        interface = resolve_contest_interface(manifest("fixture"), rule_card=card)
        self.assertNotIn("read_lab_equipment", {s.name for s in interface.actions})
        self.assertIn("unimplemented_card_action:start_environment", interface.issues)
        self.assertTrue(any("missing_runtime_resource" in issue for issue in interface.issues))
        supplied = resolve_contest_interface(
            manifest("fixture", {"tool_fixtures": {"lab": {"reading": 42}}}), rule_card=card,
        )
        self.assertIn("read_lab_equipment", {s.name for s in supplied.actions})

    def test_answer_sheet_contract_is_task_owned(self):
        one = manifest()
        sheet = replace(one, tasks=(*one.tasks, replace(one.tasks[0], task_id="q2")))
        interface = resolve_contest_interface(sheet)
        self.assertEqual(interface.delivery, "answer_sheet")
        submit = next(spec for spec in interface.actions if spec.name == "submit")
        self.assertEqual(submit.arguments, ())
        self.assertNotIn("request_review", {spec.name for spec in interface.actions})


if __name__ == "__main__":
    unittest.main()
