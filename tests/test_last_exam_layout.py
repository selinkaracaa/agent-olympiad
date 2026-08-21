from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LAST_EXAM = REPO_ROOT / "data" / "last_exam"
RULES = REPO_ROOT / "data" / "rules"
sys.path.insert(0, str(REPO_ROOT / "src"))

from rules import iter_rule_card_ids  # noqa: E402


class LastExamLayoutTests(unittest.TestCase):
    def test_one_pack_per_rule_card(self):
        ids = iter_rule_card_ids(RULES)
        catalog = json.loads((LAST_EXAM / "competitions" / "index.json").read_text(encoding="utf-8"))
        self.assertEqual(catalog["n_competitions"], len(ids))
        for competition_id in ids:
            pack = LAST_EXAM / "competitions" / competition_id
            self.assertTrue((pack / "input" / "ground_rules.md").is_file(), competition_id)
            self.assertTrue((pack / "method" / "collaboration.md").is_file(), competition_id)
            self.assertTrue((pack / "eval" / "scoring.md").is_file(), competition_id)
            self.assertTrue((pack / "mapping.json").is_file(), competition_id)

    def test_tasks_inherit_and_do_not_copy_rule_json(self):
        cards = json.loads((LAST_EXAM / "task_cards.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(cards["n_tasks"], 1)
        for card in cards["tasks"]:
            self.assertTrue(card["inherits_competition_pack"].startswith("competitions/"))
            task_dir = LAST_EXAM / "tasks" / card["competition_id"] / card["problem_id"]
            self.assertFalse((task_dir / "base" / "method").exists())
            self.assertFalse((task_dir / "collaboration.json").exists())
            self.assertTrue((task_dir / "eval" / "reference.json").is_file())
            reference = json.loads(
                (task_dir / "eval" / "reference.json").read_text(encoding="utf-8")
            )
            self.assertNotIn("expected_answer", reference)
            self.assertIn("gold_pointer", reference)

    def test_solution_pdfs_are_not_staged_as_input(self):
        eoes = LAST_EXAM / "tasks" / "eoes"
        if not eoes.exists():
            self.skipTest("eoes tasks not generated")
        for task_dir in eoes.iterdir():
            input_dir = task_dir / "base" / "input"
            if not input_dir.exists():
                continue
            names = " ".join(path.name.lower() for path in input_dir.iterdir())
            self.assertNotIn("sol", names)


if __name__ == "__main__":
    unittest.main()
