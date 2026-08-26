from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from env import COMPETITION_TOOL_REGISTRY, OlympiadEnvironment


class CompetitionToolPolicyTests(unittest.TestCase):
    def test_science_olympiad_has_bounded_reference_tools(self):
        self.assertEqual(
            COMPETITION_TOOL_REGISTRY["science_olympiad"],
            ["use_calculator", "read_official_materials"],
        )
        self.assertNotIn("web_search", COMPETITION_TOOL_REGISTRY["science_olympiad"])

    def test_pumac_has_rules_permitted_research_and_computation(self):
        self.assertEqual(
            set(COMPETITION_TOOL_REGISTRY["pumac_power"]),
            {"use_calculator", "execute_code", "web_search"},
        )

    def test_unavailable_physical_runtime_is_reported_without_fake_readings(self):
        env = OlympiadEnvironment(
            "ijso_practical",
            "ijso_practical_2004_team_practical_2004",
        )
        status = json.loads(env.execute_action("Agent_1", "inspect_environment", ""))
        self.assertEqual(status["status"], "unavailable")
        self.assertNotIn("read_lab_equipment", env.get_available_tools())

    def test_cybench_runtime_resolves_promoted_task_assets(self):
        env = OlympiadEnvironment(
            "cybench",
            "cybench_hkcert-ctf_CTF-Challenges_CTF-2022_05-motp",
        )
        status = json.loads(env.execute_action("Agent_1", "inspect_environment", ""))
        self.assertEqual(status["status"], "runnable")
        self.assertTrue(Path(status["task_root"]).is_dir())
        self.assertTrue(Path(status["compose_file"]).is_file())
        self.assertNotIn("execute_code", env.get_available_tools())
        self.assertNotIn("web_search", env.get_available_tools())

    def test_cybench_internet_is_granted_only_when_task_metadata_allows_it(self):
        env = OlympiadEnvironment(
            "cybench",
            "cybench_hackthebox_cyber-apocalypse-2024_web_Medium_LockTalk",
        )
        self.assertIn("web_search", env.get_available_tools())

    def test_official_material_lookup_does_not_cross_answer_key_boundary(self):
        env = OlympiadEnvironment(
            "science_olympiad",
            "science_olympiad_ss1718_annotated_example",
        )
        result = env.execute_action("Agent_1", "read_official_materials", "Kepler")
        self.assertIn("Kepler", result)
        self.assertNotIn("ANSWER KEY", result)


if __name__ == "__main__":
    unittest.main()
