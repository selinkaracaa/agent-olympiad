"""Fixed-clock v11 replay, with earlier protocol snapshots preserved."""
from __future__ import annotations

import hashlib
import ast
import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]
import contest_runner as runner
from contest_config import BASELINE_NAMES, ContestRunConfig
from test_otc_rulecard import ARML, ICPC, ScriptedLLM, action, arml_manifest, icpc_manifest


class FixedClock:
    @staticmethod
    def now(tz=None):
        return datetime(2026, 9, 10, 12, tzinfo=timezone.utc)


def replay(variant, programming=False, interrupted=False, *, return_payload=False):
    manifest = icpc_manifest() if programming else arml_manifest()
    tasks = [task.task_id for task in manifest.tasks]
    card = ICPC if programming else ARML
    has_coach = variant in {"otc", "vallina_otc"}
    team_size = 1 if variant == "single_agent" else card.team_size_default if has_coach else 3
    plan = {"summary": "Divide then verify.",
            "work_assignments": {f"Agent_{i}": tasks for i in range(1, team_size + 1)},
            "review_assignments": {}, "task_order": tasks}
    scripts = {f"Agent_{i}": [
        action("select_problem", problem_id=tasks[(i - 1) % 2]),
        action("execute_code", code="print(42)") if programming else action("work", content="42"),
        action("speak", content="Please verify."),
        action("submit_code", code="print(42)") if programming else action("submit"),
        action("rest", reason="wait"),
    ] for i in range(1, team_size + 1)}
    scripted = ScriptedLLM(scripts, opening_plan=plan)
    calls = []
    checkpoints = []
    def query(system, user):
        calls.append([system, user])
        if user.startswith("OPENING LEADER PLAN"):
            return json.dumps(plan)
        return scripted(system, user)
    def checkpoint(session, memory):
        checkpoints.append([session, memory])
        if interrupted and len(checkpoints) == 3:
            raise RuntimeError("replay interruption")
    config = ContestRunConfig(
        variant, team_size, 5, max_api_calls=70, max_tokens=12000,
        rule_card=card if has_coach else None,
    )
    kwargs = dict(coach_query_fn=query, checkpoint_callback=checkpoint,
                  task_action_executor=lambda *_: {"valid": True, "sample_verdict": "AC", "verdict": "AC"})
    with patch(f"{runner._run_contest_engine.__module__}.datetime", FixedClock), patch("time.perf_counter", return_value=100.0):
        try:
            result = runner.run_contest(manifest, query, config, **kwargs)
        except RuntimeError as exc:
            if str(exc) != "replay interruption":
                raise
            session, memory = checkpoints[-1]
            result = runner.run_contest(
                manifest, query, config, session_checkpoint=session,
                memory_checkpoint=memory, **kwargs,
            )
    if return_payload:
        return [result, calls, checkpoints]
    encoded = json.dumps([result, calls, checkpoints], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


# Recaptured for action set v7: the legacy alias layer is gone, so
# ``action_set_version`` is 7 in the result envelope and the rule cards spell
# ``rest`` / ``work`` (not ``sleep`` / ``write_scratchpad``), which the OTC
# Coach brief renders. Pinning the version back to 6 reproduces the v6
# non-OTC fingerprints exactly; the OTC ones differ only by the card text.
# v6 had made ``review_answer.version_hash`` optional; v5 unified the
# ``work``/desk descriptions with the env.
EXPECTED = {
    "decentralized/math/fresh": "e91a4af86f88d8a7bd8fbde5ceebd3ccd4f672e713cfd75df788b7ac3afb8931",
    "decentralized/math/resume": "0a2e73552aff59b78d9be6ca2b56a59407af5948d38d286cc2805892292f9d36",
    "decentralized/code/fresh": "d4d3b223c0236f79acbfb729f46c2d9b4c9258cf1b349bde02a27b5bec6f4b9e",
    "decentralized/code/resume": "1304fffb2772a10a88a5e5403d2c7c41ad099107b925030f4d45483113304042",
    "centralized/math/fresh": "b3f569d14c8b80955808c38821ee47bdb8caa9793606955d332148a3548cb432",
    "centralized/math/resume": "261bb59566db3a8b1b3848a3814d98e6ea514dadd3a937cc845ce02de91b1b83",
    "centralized/code/fresh": "7597e6a15a4e915f38d1588288b7ff1387d04c82265cdf8f7836676028fbe3ec",
    "centralized/code/resume": "3155f50384c2a1040fe5734d16b502f05900fdfcdc81a4f494fd6de8cd10c234",
    "otc/math/fresh": "3908c10f487c94a783fee74bc676eb1229a19a5b50be038b793cefe018aed7fa",
    "otc/math/resume": "592ff67a6176342d22fba100e3551f1dc58e5871a6431094a23526249c155adc",
    "otc/code/fresh": "c5e88e80d63066f0eb13274d3022e1fbcb3df8b733444c479b25fe6b7f154ffd",
    "otc/code/resume": "27588f1834213f751ac8736403a4e87a27542074ade41c2cd5cd12267edc61af",
}


# Keep the preceding hashes as historical evidence, not expected v7 behavior.
V8_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_modules_v8.json"
V9_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_deadline_v9.json"
V10_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_memory_v10.json"
V11_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_auxiliary_v11.json"
V11_REVIEW_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_review_guidance_v11.json"
V11_CURSOR_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_checkpoint_cursor_v11.json"
V11_MEMORY_ACTIVATION_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_memory_activation_v11.json"
V11_PLAIN_BOUNDARY_SNAPSHOT = ROOT / "tests" / "fixtures" / "contest_engine_replay_plain_boundary_v11.json"


class EngineReplayTests(unittest.TestCase):
    def test_lifecycle_phases_stay_small_and_do_not_import_the_facade(self):
        path = ROOT / "src" / "contest_engine.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        engine = next(node for node in tree.body
                      if isinstance(node, ast.ClassDef) and node.name == "_ContestEngine")
        methods = {node.name: node for node in engine.body if isinstance(node, ast.FunctionDef)}
        self.assertLessEqual(methods["run"].end_lineno - methods["run"].lineno, 25)
        for name, method in methods.items():
            with self.subTest(method=name):
                self.assertLessEqual(method.end_lineno - method.lineno, 260)
        for name in ("contest_engine", "contest_prompts", "contest_policy", "contest_lifecycle",
                     "vanilla_contest_runner", "strategic_contest_runner"):
            tree = ast.parse((ROOT / "src" / f"{name}.py").read_text(encoding="utf-8"))
            imports = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
            self.assertNotIn("contest_runner", imports)

    def test_v11_behavior_matches_versioned_snapshot(self):
        from action_modules.common import CORE_ACTION_NAMES
        # Plain baselines lose inactive review guidance. Neither OTC variant
        # changes; retain its historical prompts and complete execution payloads.
        expected = json.loads(V11_PLAIN_BOUNDARY_SNAPSHOT.read_text(encoding="utf-8"))
        previous = json.loads(V11_MEMORY_ACTIVATION_SNAPSHOT.read_text(encoding="utf-8"))
        for key, fingerprint in previous["cases"].items():
            if key.split("/")[0] in {"otc", "vallina_otc"}:
                self.assertEqual(expected["cases"][key], fingerprint)
        self.assertEqual(expected["protocol_version"], "contest_session_v11")
        self.assertEqual(set(expected["cases"]), {
            f"{variant}/{family}/{mode}" for variant in BASELINE_NAMES
            for family in ("math", "code") for mode in ("fresh", "resume")})
        for key, fingerprint in expected["cases"].items():
            variant, family, mode = key.split("/")
            with self.subTest(case=key):
                payload = replay(variant, family == "code", mode == "resume", return_payload=True)
                result = payload[0]
                self.assertEqual(result["protocol_version"], "contest_session_v11")
                memory_policy = result["memory_action_policy"]
                self.assertEqual(memory_policy["enabled"], variant == "otc")
                self.assertEqual(memory_policy["turn_cost"], 0)
                self.assertTrue(memory_policy["api_and_tokens_charged"])
                self.assertEqual(memory_policy["max_side_calls_per_agent_turn"],
                                 3 if variant == "otc" else 0)
                self.assertIn("answer_extractions", result)
                self.assertEqual(result['deadline_policy'], 'attempt_available_candidates_v1')
                self.assertEqual(result["action_set_version"], 8)
                self.assertEqual(result["module_version"], 3)
                self.assertTrue(CORE_ACTION_NAMES <= set(result["action_names"]))
                self.assertEqual(result["modules"], {
                    "common": True, "task_specific": True,
                    "memory": variant == "otc", "coach": variant in {"otc", "vallina_otc"},
                })
                self.assertLessEqual(result["budget"]["api_calls_used"], 70)
                self.assertLessEqual(result["budget"]["tokens_used"], 12000)
                for task in result["session_checkpoint"]["tasks"]:
                    if task["versions"]:
                        self.assertTrue(result["submissions"].get(task["task_id"]))
                coach_events = [event for event in result["memory"]["events"]
                                if event["kind"] == "precontest_coach_guidance"
                                and event["actor"] == "Coach"]
                self.assertEqual(len(coach_events), int(variant in {"otc", "vallina_otc"}))
                if variant != "otc":
                    self.assertFalse({"remember", "recall", "share_note"} & set(result["action_names"]))
                encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
                self.assertEqual(hashlib.sha256(encoded.encode()).hexdigest(), fingerprint)


if __name__ == "__main__":
    unittest.main()
