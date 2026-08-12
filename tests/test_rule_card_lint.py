from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "collectors"))

from constraint_hygiene import is_maintainer_text, split_constraint  # noqa: E402
from derive_turn_budgets import (  # noqa: E402
    answer_parts,
    official_minutes,
    turn_budget,
)
from lint_rule_cards import (  # noqa: E402
    PLACEHOLDER_PATTERN,
    RULES_ROOT,
    lint_card,
    schema_keys,
    strip_meta_sentences,
)
from rules import describe_resources, load_rule_card  # noqa: E402
from write_role_duties import BOILERPLATE  # noqa: E402

CARD_PATHS = sorted(
    path for path in RULES_ROOT.glob("*.json") if path.name != "schema.json"
)


class RuleCardLintTests(unittest.TestCase):
    def test_cards_exist(self):
        self.assertGreaterEqual(len(CARD_PATHS), 37)

    def test_no_lint_errors(self):
        allowed_keys, required_keys = schema_keys()
        failures = {}
        for path in CARD_PATHS:
            report = lint_card(path, allowed_keys, required_keys, fix=False)
            if report.errors:
                failures[report.competition_id] = report.errors
        self.assertEqual(failures, {})

    def test_rules_text_is_contest_facing(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                text = json.loads(path.read_text(encoding="utf-8"))["rules_text"]
                self.assertIsNone(
                    PLACEHOLDER_PATTERN.search(text),
                    "rules_text still contains generated placeholder fields",
                )
                self.assertEqual(
                    text,
                    strip_meta_sentences(text),
                    "rules_text still contains pipeline metadata",
                )

    def test_roster_resolves_at_default_team_size(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                card = load_rule_card(path.stem, required=True)
                roster = card.roster(card.team_size_default)
                self.assertEqual(len(roster), card.team_size_default)
                self.assertTrue(any(role.may_submit for role in roster))


class DeliverableContractTests(unittest.TestCase):
    def test_every_card_names_its_official_deliverable(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                submission = json.loads(path.read_text(encoding="utf-8"))["submission"]
                self.assertTrue(submission.get("official_deliverable"))
                self.assertTrue(submission.get("official_mime_types"))

    def test_rubric_paths_exist(self):
        for path in CARD_PATHS:
            rubric = (json.loads(path.read_text(encoding="utf-8"))["scoring"]).get(
                "rubric_path"
            )
            if rubric:
                with self.subTest(card=path.stem):
                    self.assertTrue((REPO_ROOT / rubric).is_file(), rubric)


class TurnBudgetTests(unittest.TestCase):
    def test_budgets_match_their_recorded_basis(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                card = json.loads(path.read_text(encoding="utf-8"))
                expected, _, _ = turn_budget(
                    card["team"]["active_default"],
                    official_minutes(card["provenance"].get("official_time_note")),
                    answer_parts(card["competition_id"]),
                )
                self.assertEqual(card["execution"]["max_turns"], expected)

    def test_longer_contests_get_more_turns(self):
        icpc = json.loads((RULES_ROOT / "icpc.json").read_text(encoding="utf-8"))
        arml = json.loads((RULES_ROOT / "arml_local.json").read_text(encoding="utf-8"))

        self.assertGreater(
            icpc["execution"]["max_turns"], arml["execution"]["max_turns"]
        )

    def test_official_minutes_parsing(self):
        self.assertEqual(official_minutes("5 hours."), 300)
        self.assertEqual(official_minutes("About 3–4 hours."), 240)
        self.assertEqual(official_minutes("About 45 minutes."), 45)
        self.assertIsNone(official_minutes("Question-level proxy."))


class ConstraintHygieneTests(unittest.TestCase):
    def test_maintainer_clause_is_split_off(self):
        constraint, notes = split_constraint(
            "Team size commonly up to 5 in community practice; confirm exact roster "
            "limits in the linked Rules PDF (not fully extracted in this crawl)."
        )

        self.assertEqual(constraint, "Team size commonly up to 5 in community practice.")
        self.assertEqual(len(notes), 1)

    def test_plain_contest_rule_is_untouched(self):
        text = "No calculators, phones, or notes during the round."
        self.assertEqual(split_constraint(text), (text, []))

    def test_tail_of_a_maintainer_clause_is_not_kept_as_a_rule(self):
        constraint, notes = split_constraint(
            "Detailed roster constraints not extracted from the homepage fetch "
            "— use the year packet if present."
        )

        self.assertIsNone(constraint)
        self.assertEqual(len(notes), 1)

    def test_cards_carry_no_duplicate_constraints(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                constraints = json.loads(path.read_text(encoding="utf-8"))["human_constraints"]
                self.assertEqual(len(constraints), len(set(constraints)))

    def test_cards_have_no_maintainer_notes_in_binding_rules(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                card = json.loads(path.read_text(encoding="utf-8"))
                dirty = [c for c in card["human_constraints"] if is_maintainer_text(c)]
                self.assertEqual(dirty, [])


class RoleDutyTests(unittest.TestCase):
    def test_no_role_carries_boilerplate_duties(self):
        for path in CARD_PATHS:
            with self.subTest(card=path.stem):
                card = json.loads(path.read_text(encoding="utf-8"))
                for role in card["agent_roles"]:
                    self.assertNotIn(tuple(role["duties"]), BOILERPLATE)


class ResourceDescriptionTests(unittest.TestCase):
    def test_forbidden_allowed_and_conditional_are_rendered(self):
        prose = describe_resources(
            {
                "internet": "forbidden",
                "calculator": "allowed",
                "physical_lab": "proxy_unavailable",
                "provided_materials_only": True,
                "paper_pencil": "allowed",
            }
        )

        self.assertIn("Banned during the contest: internet access.", prose)
        self.assertIn("Permitted: calculators.", prose)
        self.assertIn("physical lab equipment is not available in this simulation", prose)
        self.assertIn("Work only from the materials provided", prose)
        self.assertIn("Paper and pencil are always available.", prose)

    def test_skip_keys_removes_a_resource(self):
        prose = describe_resources(
            {"internet": "forbidden", "calculator": "forbidden"},
            skip_keys=frozenset({"calculator"}),
        )

        self.assertEqual(prose, "Banned during the contest: internet access.")

    def test_empty_resources_render_empty(self):
        self.assertEqual(describe_resources({}), "")


if __name__ == "__main__":
    unittest.main()
