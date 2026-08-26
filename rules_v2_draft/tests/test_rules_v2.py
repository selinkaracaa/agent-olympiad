from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


DRAFT_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = DRAFT_ROOT.parent
sys.path.insert(0, str(DRAFT_ROOT))

from rules_v2 import RuleRepository  # noqa: E402


class RulesV2DraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = RuleRepository.open(DRAFT_ROOT)

    def test_full_schema_semantic_and_provenance_validation(self):
        report = self.repository.validate(check_source_hashes=True)
        self.assertEqual([issue.as_dict() for issue in report.errors], [])

    def test_hmmt_resolves_season_specific_rosters(self):
        feb = self.repository.resolve(
            {"competition_id": "hmmt_guts", "season": "feb", "team_size": 8}
        )
        nov = self.repository.resolve(
            {"competition_id": "hmmt_guts", "season": "nov", "team_size": 6}
        )
        self.assertEqual(feb.ruleset_id, "hmmt_guts:feb:v2-draft")
        self.assertEqual(nov.ruleset_id, "hmmt_guts:nov:v2-draft")
        self.assertEqual(len(feb.roster), 8)
        self.assertEqual(len(nov.roster), 6)

    def test_all_current_hmmt_rows_resolve(self):
        path = PROJECT_ROOT / "data" / "benchmarks" / "hmmt_guts" / "benchmark.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else payload.get("problems") or []
        self.assertEqual(len(rows), 45)
        for row in rows:
            with self.subTest(problem_id=row.get("problem_id")):
                task = dict(row)
                task["competition_id"] = "hmmt_guts"
                resolved = self.repository.resolve(task)
                self.assertEqual(len(resolved.roster), int(row["team_size"]))

    def test_variable_rosters_work_at_every_declared_size(self):
        cases = {
            "wharton_investment": range(4, 7),
            "purple_comet": range(1, 7),
            "fyziklani": range(1, 6),
            "ichto": range(4, 7),
        }
        for competition_id, sizes in cases.items():
            for size in sizes:
                with self.subTest(competition_id=competition_id, size=size):
                    resolved = self.repository.resolve(
                        {"competition_id": competition_id}, team_size=size
                    )
                    self.assertEqual(len(resolved.roster), size)
                    self.assertTrue(any(role["may_submit"] for role in resolved.roster))

    def test_wsc_assigns_one_complete_response_to_each_writer(self):
        resolved = self.repository.resolve(
            {"competition_id": "wsc_writing", "team_size": 3}
        )
        self.assertEqual(len(resolved.roster), 3)
        for role in resolved.roster:
            duties = " ".join(role["duties"]).lower()
            self.assertIn("write one complete response", duties)

    def test_ichto_does_not_treat_round_opponents_as_teammates(self):
        resolved = self.repository.resolve({"competition_id": "ichto"}, team_size=4)
        self.assertEqual(resolved.payload["team"]["active_min"], 4)
        self.assertEqual(resolved.payload["team"]["active_max"], 6)
        self.assertEqual(
            resolved.payload["resource_policy"]["internet"]["access"],
            "forbidden",
        )
        self.assertEqual(
            resolved.payload["resource_policy"]["code_execution"]["access"],
            "forbidden",
        )
        titles = {role["title"] for role in resolved.roster}
        self.assertNotIn("opponent", titles)
        self.assertNotIn("reviewer", titles)

    def test_iiot_encodes_two_machine_slots(self):
        resolved = self.repository.resolve({"competition_id": "iiot", "team_size": 4})
        code = resolved.payload["resource_policy"]["code_execution"]
        self.assertEqual(code["access"], "shared_capacity")
        self.assertEqual(code["capacity"], 2)

    def test_debatebench_has_four_private_coalitions(self):
        resolved = self.repository.resolve(
            {"competition_id": "debatebench", "team_size": 8}
        )
        coalitions = resolved.payload["collaboration"]["coalitions"]
        self.assertEqual(len(coalitions), 4)
        self.assertTrue(all(coalition["private_channel"] for coalition in coalitions))
        self.assertEqual(
            sum(len(coalition["member_role_ids"]) for coalition in coalitions),
            8,
        )

    def test_migration_matrix_covers_current_37_tracks(self):
        tracks = self.repository.migration_matrix["tracks"]
        ids = {track["competition_id"] for track in tracks}
        index = json.loads(
            (PROJECT_ROOT / "data" / "benchmarks" / "index.json").read_text(
                encoding="utf-8"
            )
        )
        current = {item["id"] for item in index["olympiads"]}
        self.assertEqual(len(tracks), 37)
        self.assertEqual(ids, current)

    def test_semantic_validator_rejects_false_official_equivalence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "draft"
            shutil.copytree(DRAFT_ROOT, root)
            path = root / "rulesets" / "wsc_writing" / "collaborative.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["profile"] = "official_equivalent"
            payload["comparability"]["overall"] = "equivalent"
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report = RuleRepository.open(root).validate(check_source_hashes=False)
            self.assertIn("false_official_equivalence", {issue.code for issue in report.errors})

    def test_semantic_validator_rejects_prose_resource_conflict(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "draft"
            shutil.copytree(DRAFT_ROOT, root)
            path = root / "rulesets" / "ichto" / "team.json"
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["resource_policy"]["internet"]["access"] = "allowed"
            payload["constraints"].append(
                {
                    "id": "ichto.internet_test",
                    "authority": "official",
                    "statement": "Internet access is prohibited during the round.",
                    "source_refs": ["ichto-rulebook-2025"],
                    "enforcement": {"mode": "runtime", "status": "enforced"},
                }
            )
            path.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            report = RuleRepository.open(root).validate(check_source_hashes=False)
            self.assertIn("text_policy_conflict", {issue.code for issue in report.errors})


if __name__ == "__main__":
    unittest.main()
