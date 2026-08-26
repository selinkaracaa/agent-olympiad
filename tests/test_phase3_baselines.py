from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from collaboration import (  # noqa: E402
    CollabConfig,
    SCHEMAS,
    aggregate_numbered_answers,
    run_collaboration,
)
from env import OlympiadEnvironment  # noqa: E402
from run_handicap_sweep import (  # noqa: E402
    analyze_crossovers,
    build_handicap_cells,
    write_json_atomic,
)
from run_phase_b_matrix import agent_roster  # noqa: E402


def environment(turns: int = 4) -> OlympiadEnvironment:
    return OlympiadEnvironment("arml_local", "arml_local_2009", max_turns=turns)


def rule_environment(turns: int = 4) -> OlympiadEnvironment:
    return OlympiadEnvironment(
        "arml_local",
        "arml_local_2009",
        max_turns=turns,
        rules_mode="enforced",
    )


class Phase3BaselineTests(unittest.TestCase):
    def test_schemas_registered_and_rosters(self) -> None:
        required = {
            "open_table_coach",
            "debate",
            "self_consistency",
            "memory_solo",
            "subagent",
            "liveoi_best_of_8",
        }
        self.assertTrue(required <= set(SCHEMAS))
        self.assertEqual(agent_roster("self_consistency", 6), ["Solo"])
        self.assertEqual(agent_roster("subagent", 2), ["Orchestrator", "Worker_1", "Worker_2"])

    def test_self_consistency_isolation_aggregation_and_accounting(self) -> None:
        prompts: list[str] = []
        answers = iter(
            [
                "1. Answer alpha\n2. Answer xray",
                "1. Answer beta\n2. Answer xray",
                "1. Answer alpha\n2. Answer yankee",
            ]
        )

        def query(_system: str, user: str) -> str:
            prompts.append(user)
            return next(answers)

        result = run_collaboration(
            "self_consistency",
            environment(),
            query,
            CollabConfig(sample_count=3, max_api_calls=3),
        )
        self.assertEqual(result["api_calls"], 3)
        self.assertEqual(result["final_answer"], "1. Answer alpha\n2. Answer xray")
        self.assertTrue(
            all("Answer alpha" not in prompt and "Answer beta" not in prompt for prompt in prompts)
        )
        self.assertEqual(
            aggregate_numbered_answers(["1. Z", "1. A"], tie_behavior="lexicographic"),
            "1. A",
        )

    def test_open_table_coach_is_problem_blind_then_exits_after_opening(self) -> None:
        env = rule_environment(3)
        calls: list[tuple[str, str]] = []

        def query(system: str, user: str) -> str:
            calls.append((system, user))
            return "ACTION: speak | PAYLOAD: phase contribution"

        result = run_collaboration(
            "open_table_coach",
            env,
            query,
            CollabConfig(max_turns=3, synthesize=False),
        )

        self.assertNotIn(env._problem_statement(), calls[0][1])
        self.assertNotIn("evaluation_guidance", calls[0][1])
        self.assertIn("pre-contest brief", calls[0][0].lower())
        opening_coach_call = 1 + env.team_size
        self.assertIn("opening discussion", calls[opening_coach_call][0].lower())
        self.assertIn(env._problem_statement(), calls[opening_coach_call][1])
        self.assertTrue(
            all(
                "you are coach" not in system.lower()
                for system, _ in calls[opening_coach_call + 1 :]
            )
        )
        coach_actions = [
            item for item in env.action_log if item["agent"] == "Coach"
        ]
        self.assertEqual([item["turn"] for item in coach_actions], [1, 2])
        self.assertEqual([item["action"] for item in coach_actions], ["speak", "speak"])
        self.assertEqual(result["turns_used"], 3)
        self.assertEqual(result["schema"], "open_table_coach")
        self.assertEqual(result["coach_exit_after_turn"], 2)

    def test_open_table_coach_output_cannot_execute_actions(self) -> None:
        env = rule_environment(1)

        result = run_collaboration(
            "open_table_coach",
            env,
            lambda system, _user: (
                "ACTION: submit_final | PAYLOAD: forbidden"
                if "you are coach" in system.lower()
                else "ACTION: sleep | PAYLOAD: test"
            ),
            CollabConfig(max_turns=1, synthesize=False),
        )

        self.assertFalse(result["submitted"])
        coach_actions = [
            item for item in env.action_log if item["agent"] == "Coach"
        ]
        self.assertEqual([item["action"] for item in coach_actions], ["sleep"])
        self.assertIn("blocked prohibited action", coach_actions[0]["payload"])

    def test_open_table_coach_requires_explicit_rule_card_policy(self) -> None:
        env = OlympiadEnvironment(
            "icpc",
            "icpc_wf_2012_bottles",
            max_turns=1,
            rules_mode="enforced",
        )
        with self.assertRaisesRegex(ValueError, "does not enable open-table coaching"):
            run_collaboration(
                "open_table_coach",
                env,
                lambda _system, _user: "unused",
                CollabConfig(max_turns=1, synthesize=False),
            )

    def test_memory_solo_shares_only_bounded_self_state(self) -> None:
        prompts: list[str] = []

        def query(_system: str, user: str) -> str:
            prompts.append(user)
            return f"1. private-{len(prompts)}"

        result = run_collaboration(
            "memory_solo",
            environment(3),
            query,
            CollabConfig(max_turns=3, memory_bound=2, max_api_calls=3),
        )
        self.assertNotIn("private-1", prompts[0])
        self.assertIn("private-1", prompts[1])
        self.assertEqual(len(result["memory"]["private"]["Solo"]), 2)
        self.assertEqual(result["roster"][0]["name"], "Agent_1")  # rule roster remains authoritative

    def test_subagent_workers_have_no_cross_talk(self) -> None:
        worker_prompts: list[str] = []

        def query(system: str, user: str) -> str:
            if "Orchestrator" in system and "Decompose" in user:
                return "1. alpha\n2. beta\n3. gamma\n4. delta\n5. epsilon\n6. zeta"
            if "Worker_" in system:
                worker_prompts.append(user)
                return f"SECRET-{len(worker_prompts)}"
            return "1. combined"

        result = run_collaboration(
            "subagent",
            environment(),
            query,
            CollabConfig(max_api_calls=8),
        )
        self.assertEqual(result["api_calls"], 8)
        self.assertTrue(result["worker_isolation"])
        for index, prompt in enumerate(worker_prompts):
            self.assertFalse(any(f"SECRET-{prior}" in prompt for prior in range(1, index + 1)))

    def test_debate_emits_structured_ledger_events(self) -> None:
        counter = 0

        def query(_system: str, _user: str) -> str:
            nonlocal counter
            counter += 1
            return f"claim-{counter}"

        result = run_collaboration(
            "debate",
            environment(3),
            query,
            CollabConfig(debate_rounds=1, max_api_calls=30),
        )
        counts = result["debate"]["counts"]
        self.assertEqual(counts["propose"], 6)
        self.assertEqual(counts["challenge"], 6)
        self.assertEqual(counts["revise"], 6)
        self.assertEqual(counts["decide"], 6)
        self.assertTrue(result["structured_events"])

    def test_best_of_8_requires_judge_for_selection(self) -> None:
        result = run_collaboration(
            "liveoi_best_of_8",
            environment(),
            lambda _system, user: user.rsplit(" ", 1)[-1],
            CollabConfig(max_api_calls=8),
        )
        self.assertEqual(len(result["candidates"]), 8)
        self.assertFalse(result["selection_available"])
        self.assertFalse(result["submitted"])

        judged = run_collaboration(
            "liveoi_best_of_8",
            environment(),
            lambda _system, user: user,
            CollabConfig(max_api_calls=8, deterministic_judge=len),
        )
        self.assertTrue(judged["selection_available"])
        self.assertTrue(judged["submitted"])

    def test_handicap_cells_crossover_and_atomic_output(self) -> None:
        cells = build_handicap_cells(
            {"turns": 1, "calls_per_turn": 1},
            {"turns": [1, 2], "calls_per_turn": [1, 3]},
        )
        self.assertEqual(len(cells), 4)
        self.assertEqual(cells[0]["solo_config"]["calls_per_turn"], 1)
        scored = [{**cell, "score": index / 3} for index, cell in enumerate(cells)]
        analysis = analyze_crossovers(scored, [{"score": 0.5}])
        self.assertEqual(analysis["team_target"], 0.5)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "result.json"
            write_json_atomic(path, {"cells": scored})
            self.assertEqual(len(json.loads(path.read_text())["cells"]), 4)


if __name__ == "__main__":
    unittest.main()
