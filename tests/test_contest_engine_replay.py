"""Behavior fingerprints captured before the engine phase refactor.

Cover prompts, events, checkpoints, budgets and result envelopes with a fixed
clock. Updating these hashes requires an intentional protocol change.
"""
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
from contest_config import ContestRunConfig
from test_otc_rulecard import ARML, ICPC, ScriptedLLM, action, arml_manifest, icpc_manifest


class FixedClock:
    @staticmethod
    def now(tz=None):
        return datetime(2026, 9, 10, 12, tzinfo=timezone.utc)


def replay(variant, programming=False, interrupted=False):
    manifest = icpc_manifest() if programming else arml_manifest()
    tasks = [task.task_id for task in manifest.tasks]
    card = ICPC if programming else ARML
    team_size = card.team_size_default if variant == "otc" else 3
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
        rule_card=card if variant == "otc" else None,
        programming_deadline_submit=programming,
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
    encoded = json.dumps([result, calls, checkpoints], sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(encoded.encode()).hexdigest()


# Recaptured for action set v5: ``work`` gained an optional ``problem_id`` and
# the desk action descriptions were unified with the environment runtime.
EXPECTED = {
    "decentralized/math/fresh": "b63acac146d79e0a2c6a5c5055a2eeb9f606d75d847aae017332818b26fbbc19",
    "decentralized/math/resume": "3834d4d2978ac48ccf7a253d85568a1071f91940baebf988252d56d93ebf1cde",
    "decentralized/code/fresh": "4ca04288977356e091514b4fd9fdd3fe988f1a1c869267ac456a7d41c9b744da",
    "decentralized/code/resume": "eda01330b3f7b948a41afa90b29f693d48bb968ae43df4a26d24d2f33d89d4f1",
    "centralized/math/fresh": "83854ea8c641559aea557f5675165570bf3a97e7a2bcb0928d9e677692bdf119",
    "centralized/math/resume": "5421eb72bae5b69bf0add35716fd16b053ed68ec11e53bac20dd99ca3a1825c2",
    "centralized/code/fresh": "a70ea105d63ffdccfcd7538cdaf720ec2c530cdf8b06b53ff458a5b6cf5cf7da",
    "centralized/code/resume": "eb12d3a299980ede6164ae0a414f92f9798a4c5642f27a0acbe8574358367b86",
    "otc/math/fresh": "bceff528c758db93aa355b01a029c31d8c8f498a36465b51b044756ebc2380c5",
    "otc/math/resume": "b6c3779fad0248bcc2ef905c9cd8168ae4386c3d6464c14cc5ddac52a2989fcb",
    "otc/code/fresh": "da6a82df6c1d8c60b565b00b3e9c1fb040e59c66b6d79bc69265a2c69b36bf3d",
    "otc/code/resume": "d67c2ac2de34f7257effb24920eda60fbe01147c34f0eacd86ad99a9d1a23172",
}


# Intentional v6 OTC migration: single turn-0 Coach and mandatory approval.
EXPECTED_V6_OTC = {
    "otc/math/fresh": "9d8cac6653d68a4be62592b9ac04ca4e5f7279764a99d3203d2c6657893f4172",
    "otc/math/resume": "52c4f84065fa0f446bab713334599c36f993c4aa82c6d2c706f4fcd2986fe1f2",
    "otc/code/fresh": "2088ac5dc21af416aa52a11d379528fc9be6433ba0986e825e73839d2a708489",
    "otc/code/resume": "fa7eb62ac2f49f7051b7462e30d5ce7ad45da7c69d4a08574ae08b029a21515b",
}


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

    def test_pre_refactor_behavior_is_preserved(self):
        self.assertTrue(EXPECTED, "Capture pre-refactor fingerprints before changing the engine")
        for key, expected in EXPECTED.items():
            variant, family, mode = key.split("/")
            with self.subTest(case=key):
                if variant == "otc":
                    self.assertEqual(replay(variant, family == "code", mode == "resume"),
                                     EXPECTED_V6_OTC[key])
                else:
                    # Preserve all original non-OTC fingerprints, normalizing only
                    # the top-level protocol label that intentionally became v6.
                    with patch("contest_engine.PROTOCOL_VERSION", "contest_session_v5"):
                        self.assertEqual(replay(variant, family == "code", mode == "resume"), expected)


if __name__ == "__main__":
    unittest.main()
