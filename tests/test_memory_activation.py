"""Memory activation guidance and zero-turn tool-loop regressions."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import otc_runtime
from action_modules.memory import SPECS, decision_guidance
from contest_config import BASELINES, ContestRunConfig
from contest_budget import estimate_tokens
from contest_manifest import load_contest_manifest
from contest_policy import _resolved_actions
from contest_prompts import _system_prompt
from llm import LLMResponse, LLMToolCall
from rules.loader import load_rule_card
from strategic_contest_runner import run_strategic_contest


class MemoryActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load_contest_manifest(
            ROOT / "data/contest_manifests/arml_local_2009.json",
            benchmark_root=ROOT / "data/benchmarks",
        )
        cls.card = copy.deepcopy(load_rule_card("arml_local", required=True))
        cls.card.simulation["max_turns"] = 1
        cls.card.simulation["open_table_coach"]["min_turns"] = 1

    def config(self, baseline="otc"):
        return ContestRunConfig(
            baseline, 1 if baseline == "single_agent" else 6, 1,
            rule_card=self.card if baseline in {"otc", "vallina_otc"} else None,
            max_api_calls=100, max_tokens=50000,
            max_simulated_minutes=5, deadline_submit=False,
        )

    def test_memory_desk_prompt_does_not_charge_a_turn(self):
        config = self.config()
        prompt = _system_prompt(
            config, "Agent_1", _resolved_actions(self.manifest, config),
            native_actions=True, answer_sheet_contest=True,
        )
        self.assertNotIn("Desk tools consume a turn like any other action", prompt)
        self.assertIn("zero-turn", prompt)

    def test_write_read_share_and_empty_store_bootstrap_are_explicit(self):
        guidance = decision_guidance()
        for marker in ("MEMORY WRITE:", "MEMORY READ:", "MEMORY SHARE:",
                       "empty note store", "No call quota"):
            self.assertIn(marker, guidance)
        self.assertIn("Do not recall when", guidance)
        self.assertIn("already shown", guidance)
        self.assertIn("notes_changed_since_last_recall", guidance)

    def test_native_memory_descriptions_explain_zero_turn_cost(self):
        for spec in SPECS:
            with self.subTest(action=spec.name):
                self.assertIn("zero-turn", spec.description.lower())
                self.assertEqual(spec.budget.turns, 0)

    def test_think_prompt_includes_write_activation(self):
        config = self.config()
        text = otc_runtime.think_system_prompt(
            self.card, config.otc_policy, "Agent_1", team_size=6,
            action_names=[s.name for s in _resolved_actions(self.manifest, config)],
            retain_history=True,
        )
        self.assertIn("MEMORY WRITE:", text)

    def test_disabled_baselines_do_not_receive_memory_strategy(self):
        for baseline in ("single_agent", "decentralized", "centralized", "vallina_otc"):
            config = self.config(baseline)
            actions = _resolved_actions(self.manifest, config)
            with self.subTest(baseline=baseline), patch(
                "contest_prompts.decision_guidance",
                side_effect=AssertionError("memory strategy leaked"),
            ):
                prompt = _system_prompt(config, "Agent_1", actions, native_actions=True)
                self.assertFalse({s.name for s in actions} & {"remember", "recall", "share_note"})
                self.assertNotIn("MEMORY WRITE:", prompt)
                self.assertIn("OPTIONAL MEMORY MODULE: disabled", prompt)
                self.assertEqual(config.modules.coach, baseline == "vallina_otc")
        a, b = BASELINES["otc"], BASELINES["vallina_otc"]
        self.assertEqual(
            {key for key in a.__dataclass_fields__ if getattr(a, key) != getattr(b, key)},
            {"memory_actions"},
        )

    def test_real_engine_same_turn_write_share_recall_then_work(self):
        counts = Counter()
        captures = []

        def query(system, user):
            return "Preserve a useful unresolved branch, then continue. NEXT ACTION: work"

        def request(req):
            agent = req.metadata["agent"]
            stage = counts[agent]
            offered = {tool["name"] for tool in req.tools}
            captures.append(req)
            if stage < 3:
                self.assertTrue({"remember", "recall", "share_note"} <= offered)
                self.assertIn("ONE ordinary contest action", req.system_prompt)
                self.assertNotIn("take exactly ONE action.", req.system_prompt)
            if stage == 0:
                name, args = "remember", {
                    "content": "probe_fact: failed symmetry shortcut; verify conditional states.",
                    "problem_id": req.metadata["task_id"],
                }
            elif stage == 1:
                receipts = json.loads(req.user_prompt.rsplit(
                    "MEMORY TOOL RESULTS (same turn, private to you)\n", 1,
                )[1])
                note = next(e for e in receipts if e["kind"] == "note")
                name, args = "share_note", {"note_id": note["event_id"]}
            elif stage == 2:
                name, args = "recall", {
                    "query": "probe_fact", "problem_id": req.metadata["task_id"],
                }
            else:
                self.assertFalse(offered & {"remember", "recall", "share_note"})
                self.assertIn("recall_result", req.user_prompt)
                name, args = "work", {"content": "Partial derivation retained for verification."}
            counts[agent] += 1
            return LLMResponse("", "mock", "activation-test",
                tool_calls=(LLMToolCall(name, args),),
                usage={"api_calls": 1, "output_tokens": 1})

        result = run_strategic_contest(
            self.manifest, query, self.config(), action_request_fn=request,
            action_transport="native", coach_query_fn=query,
        )
        kinds = Counter(e["kind"] for e in result["memory"]["events"])
        self.assertEqual(kinds["action_error"], 0)
        self.assertEqual(result["budget"]["turns_used"], 1)
        self.assertEqual(result["budget"]["simulated_minutes_used"], 5)
        self.assertEqual(result["memory_action_policy"]["side_calls"], 18)
        self.assertEqual(kinds["think"], 6)
        self.assertEqual(kinds["work"], 6)
        self.assertEqual(kinds["note"], 6)
        self.assertEqual(kinds["note_shared"], 6)
        self.assertEqual(kinds["recall_result"], 6)
        self.assertEqual(dict(counts), {f"Agent_{i}": 4 for i in range(1, 7)})

    def test_mixed_batch_retry_then_note_receipt_and_work_in_same_turn(self):
        counts = Counter()
        queries = []

        def query(system, user):
            text = "Continue the derivation. NEXT ACTION: work"
            queries.append(text)
            return text

        def request(req):
            agent = req.metadata["agent"]
            stage = counts[agent]
            counts[agent] += 1
            note_text = f"{agent} private unfinished recurrence; check S2."
            note = LLMToolCall("remember", {"content": note_text,
                "problem_id": req.metadata["task_id"]}, f"{agent}-note-{stage}")
            if stage == 0:
                calls = (note, LLMToolCall("inspect_problem", {
                    "problem_id": req.metadata["task_id"], "focus": "Read statement."},
                    f"{agent}-inspect"))
            elif stage == 1:
                self.assertIn(note_text, req.user_prompt)
                self.assertIn("No action from that response executed", req.user_prompt)
                self.assertNotIn("MEMORY TOOL RESULTS", req.user_prompt)
                calls = (note,)
            else:
                self.assertEqual(stage, 2)
                receipts = json.loads(req.user_prompt.rsplit(
                    "MEMORY TOOL RESULTS (same turn, private to you)\n", 1)[1])
                self.assertEqual([e["kind"] for e in receipts], ["note"])
                self.assertIn(note_text, json.dumps(receipts))
                self.assertIn("remember", {tool["name"] for tool in req.tools})
                calls = (LLMToolCall("work", {"content": "Continue calculation."}),)
            for other in range(1, 7):
                if f"Agent_{other}" != agent:
                    self.assertNotIn(f"Agent_{other} private unfinished recurrence", req.user_prompt)
            return LLMResponse("", "mock", "batch-repair", tool_calls=calls,
                usage={"api_calls": 1, "output_tokens": 7})

        result = run_strategic_contest(self.manifest, query, self.config(),
            action_request_fn=request, action_transport="native", coach_query_fn=query)
        kinds = Counter(e["kind"] for e in result["memory"]["events"])
        self.assertEqual(kinds["note"], 6)
        self.assertEqual(kinds["work"], 6)
        self.assertEqual(kinds["action_error"], 0)
        self.assertEqual(result["memory_action_policy"]["side_calls"], 6)
        self.assertEqual(result["budget"]["turns_used"], 1)
        self.assertEqual(result["budget"]["simulated_minutes_used"], 5)
        self.assertEqual(result["budget"]["api_calls_used"], 18 + len(queries))
        self.assertEqual(result["budget"]["tokens_used"], 18 * 7 + sum(map(estimate_tokens, queries)))
        log = result["action_transport_log"]
        rejected = [c for c in log if c.get("rejection_reason")]
        self.assertEqual(len(rejected), 12)
        self.assertTrue(all(not c["executed"] for c in rejected))
        self.assertEqual(Counter(c["name"] for c in log if c["executed"]),
                         Counter(remember=6, work=6))


if __name__ == "__main__":
    unittest.main()
