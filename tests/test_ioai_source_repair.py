"""Offline regressions for historical IOAI statement and contract repair."""
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repair_ioai_sources_20260913 import fix_rubrics, fix_rules, nonspacing, task_contract, STALE_DEFAULTS


class IOAISourceRepairTests(unittest.TestCase):
    def setUp(self):
        self.evidence = dict(rules_2025_cover_version="2.4 (August 3, 2025)", upstream={"runtime_executed": False},
                            sources={"rules_2025": {"sha256": "rules-hash"}})
        self.rows = [dict(problem_id=f"ioai_team_{year}", year=year, source_file=f"{year}.pdf", source_url=f"https://example.test/{year}",
                          evaluation={"status": "not_ready", "evaluator_id": None}) for year in (2024, 2025)]

    def contracts(self):
        with patch("scripts.repair_ioai_sources_20260913.digest", return_value="original-pdf-hash"):
            return {r["problem_id"]: task_contract(r, self.evidence) for r in self.rows}

    def test_spacing_recovery_cannot_change_words_or_digits(self):
        self.assertEqual(nonspacing("Practical\u200b round\n40 to 60"), nonspacing("Practicalround40to60"))
        self.assertNotEqual(nonspacing("40 to 40"), nonspacing("40 to 60"))

    def test_2024_media_contract_and_tool_permissions(self):
        contract = self.contracts()["ioai_team_2024"]
        self.assertEqual(contract["official_minutes"], 240)
        self.assertIn("cover_image_and_music_video", contract["deliverable"])
        self.assertIn("non-AI", contract["tools"]["image"])
        self.assertIn("LLMs", contract["tools"]["supplementary"])

    def test_raw_maxima_are_not_final_ranking_weights(self):
        contract = self.contracts()["ioai_team_2024"]
        self.assertEqual(contract["raw_task_maxima"], {"image_cover": 40, "music_video": 40})
        self.assertEqual(contract["ranking_weight_ratio"], {"image_cover": 40, "music_video": 60})
        self.assertIsNone(contract["final_ranking_formula"])

    def test_2025_does_not_invent_duration_or_submission_schema(self):
        contract = self.contracts()["ioai_team_2025"]
        self.assertIsNone(contract["official_minutes"])
        self.assertIsNone(contract["exact_submission_schema"])
        self.assertIsNone(contract["numeric_scoring"])
        self.assertNotIn("code_and_predictions", contract["deliverable"])
        self.assertFalse(contract["historical_environment_verified"])

    def test_rules_version_follows_cover_not_url(self):
        contract = self.contracts()["ioai_team_2025"]
        self.assertEqual(contract["rules_cover_version"], "2.4 (August 3, 2025)")

    def test_rubric_fix_preserves_criteria_and_total(self):
        original = {2024: dict(total_points=80, criteria=[{"id": "untouched", "max_score": 5}],
                              limitations=["old"], provenance=[{}]),
                    2025: dict(provenance=[{}], limitations=[])}
        before = deepcopy(original)
        fixed = fix_rubrics(original, self.evidence)
        self.assertEqual(original, before)
        self.assertEqual(fixed[2024]["criteria"], original[2024]["criteria"])
        self.assertEqual(fixed[2024]["total_points"], 80)
        self.assertEqual(fixed[2024]["task_weights"]["music_video"], 60)

    def test_historical_rule_repair_preserves_collaboration_overlay(self):
        original = dict(competition={"provenance": {"sources": [{"edition": 2026}]}},
            collaboration={"agent_roles": [{"name": "Captain"}], "simulation": {"open_table_coach": {"enabled": True}},
                           "agent_constraints": ["Banned during old contest", "Do not generalize Individual permissions", "Keep hidden references private."]},
            evaluation={"scoring": {"current_repository_availability": {}}, "submission": {"max_count": 1}})
        before = deepcopy(original)
        with patch("scripts.repair_ioai_sources_20260913.digest", return_value="source-hash"):
            fixed = fix_rules(original, self.rows, self.contracts())
        self.assertEqual(original, before)
        self.assertEqual(fixed["collaboration"]["simulation"], original["collaboration"]["simulation"])
        self.assertEqual(fixed["collaboration"]["agent_roles"], original["collaboration"]["agent_roles"])
        self.assertEqual(fixed["competition"]["provenance"]["superseded_sources"], [{"edition": 2026}])
        visible = str(fixed["competition"]["execution"]) + str(fixed["competition"]["resources"]) + str(fixed["collaboration"])
        self.assertTrue(all(token not in visible for token in STALE_DEFAULTS))
        self.assertEqual(fixed["competition"]["execution"]["official_minutes_by_year"], {"2024": 240, "2025": None})


if __name__ == "__main__":
    unittest.main()
