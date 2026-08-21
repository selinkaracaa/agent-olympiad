from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "collectors"))

from constraint_hygiene import is_maintainer_text, split_constraint  # noqa: E402
from apply_source_review_corrections import apply_source_corrections  # noqa: E402
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
from rules import (  # noqa: E402
    describe_resources,
    iter_rule_card_ids,
    load_rule_card,
    load_rule_card_payload,
)
from standardize_rule_card_content import (  # noqa: E402
    HAND_AUTHORED_ICPC_QUALITY,
    STANDARD_NAME,
    STANDARD_RULE_SECTIONS,
    apply_content_standard,
    display_names,
    protected_facts,
)
from write_role_duties import BOILERPLATE  # noqa: E402

CARD_IDS = iter_rule_card_ids(RULES_ROOT)


def card_payload(competition_id: str) -> dict:
    return load_rule_card_payload(
        competition_id,
        rules_root=RULES_ROOT,
        required=True,
    )


class RuleCardLintTests(unittest.TestCase):
    def test_cards_exist(self):
        self.assertGreaterEqual(len(CARD_IDS), 37)

    def test_no_lint_errors(self):
        allowed_keys, required_keys = schema_keys()
        failures = {}
        for competition_id in CARD_IDS:
            report = lint_card(
                competition_id, allowed_keys, required_keys, fix=False
            )
            if report.errors:
                failures[report.competition_id] = report.errors
        self.assertEqual(failures, {})

    def test_rules_text_is_contest_facing(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                text = card_payload(competition_id)["rules_text"]
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
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                card = load_rule_card(competition_id, required=True)
                roster = card.roster(card.team_size_default)
                self.assertEqual(len(roster), card.team_size_default)
                self.assertTrue(any(role.may_submit for role in roster))

    def test_roster_resolves_across_declared_team_range(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                card = load_rule_card(competition_id, required=True)
                for team_size in {
                    card.team_size_min,
                    card.team_size_default,
                    card.team_size_max,
                }:
                    roster = card.roster(team_size)
                    self.assertEqual(len(roster), team_size)
                    self.assertTrue(any(role.may_submit for role in roster))


class DeliverableContractTests(unittest.TestCase):
    def test_every_card_names_its_official_deliverable(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                deliverable = card_payload(competition_id)["deliverable"]
                self.assertTrue(deliverable.get("official_deliverable"))
                self.assertTrue(deliverable.get("official_mime_types"))

    def test_rubric_paths_exist(self):
        for competition_id in CARD_IDS:
            rubric = card_payload(competition_id)["scoring"].get("rubric_path")
            if rubric:
                with self.subTest(card=competition_id):
                    self.assertTrue((REPO_ROOT / rubric).is_file(), rubric)


class ContentStandardTests(unittest.TestCase):
    def test_every_bundle_matches_icpc_component_top_level_contract(self):
        filenames = (
            "competition.json",
            "collaboration.json",
            "evaluation.json",
        )
        reference = {
            filename: set(
                json.loads(
                    (RULES_ROOT / "icpc" / filename).read_text(encoding="utf-8")
                )
            )
            for filename in filenames
        }
        for competition_id in CARD_IDS:
            for filename in filenames:
                with self.subTest(card=competition_id, component=filename):
                    payload = json.loads(
                        (RULES_ROOT / competition_id / filename).read_text(
                            encoding="utf-8"
                        )
                    )
                    self.assertEqual(set(payload), reference[filename])

    def test_non_icpc_cards_declare_complete_content_standard(self):
        scoring_sections = {
            "official_performance",
            "rule_compliance",
            "collaboration_quality",
            "current_repository_availability",
        }
        for competition_id in CARD_IDS:
            card = card_payload(competition_id)
            with self.subTest(card=competition_id):
                self.assertTrue(card["agent_constraints"])
                self.assertTrue(card["evaluation_guidance"])
                self.assertTrue(scoring_sections.issubset(card["scoring"]))
                for role in card["agent_roles"]:
                    self.assertEqual(
                        set(role["information_access"]),
                        {"contest_rules"},
                    )
                if competition_id != "icpc":
                    self.assertEqual(
                        card["provenance"]["content_standard"]["name"],
                        STANDARD_NAME,
                    )
                    self.assertTrue(
                        set(STANDARD_RULE_SECTIONS).issubset(card["rule_sections"])
                    )

    def test_standardizer_is_idempotent_and_preserves_competition_facts(self):
        names = display_names()
        for competition_id in CARD_IDS:
            if competition_id in HAND_AUTHORED_ICPC_QUALITY:
                continue
            current = card_payload(competition_id)
            candidate = copy.deepcopy(current)
            facts = protected_facts(candidate)
            apply_content_standard(
                candidate,
                name=names.get(competition_id, competition_id),
            )
            with self.subTest(card=competition_id):
                self.assertEqual(candidate, current)
                self.assertEqual(protected_facts(candidate), facts)

    def test_source_corrections_are_idempotent(self):
        for competition_id in CARD_IDS:
            if competition_id == "icpc":
                continue
            current = card_payload(competition_id)
            candidate = copy.deepcopy(current)
            apply_source_corrections(candidate)
            with self.subTest(card=competition_id):
                self.assertEqual(candidate, current)

    def test_non_icpc_cards_record_source_review_status(self):
        for competition_id in CARD_IDS:
            if competition_id == "icpc":
                continue
            review = card_payload(competition_id)["provenance"]["source_review"]
            with self.subTest(card=competition_id):
                self.assertIn(review["coverage_grade"], {"A", "B", "C", "D"})
                self.assertTrue(review["completion_status"])
                self.assertEqual(
                    review["audit_report"],
                    "docs/rule_card_icpc_standard_gap_audit_2026-08-17.md",
                )

    def test_generated_sections_separate_rule_layers(self):
        expected_labels = {
            "competition_format": (
                "Competition model:",
                "The source-recorded",
                "Benchmark adaptation:",
                "Mixed or unresolved rulesets:",
            ),
            "timeline": ("Source-recorded timing:", "Benchmark adaptation:"),
            "resource_policy": (
                "Source-recorded resource policy:",
                "Benchmark safety rule:",
            ),
            "deliverable_format": (
                "Runner answer contract:",
                "Official deliverable:",
            ),
            "runtime_limitations": ("Runtime limitation:",),
        }
        for competition_id in CARD_IDS:
            if competition_id in HAND_AUTHORED_ICPC_QUALITY:
                continue
            sections = card_payload(competition_id)["rule_sections"]
            for section, labels in expected_labels.items():
                with self.subTest(card=competition_id, section=section):
                    self.assertTrue(
                        any(item.startswith(labels) for item in sections[section])
                    )

    def test_hand_authored_icpc_quality_cards_label_official_vs_simulation(self):
        required = (
            "competition_format",
            "timeline",
            "resource_policy",
            "collaboration_protocol",
            "integrity_and_compliance",
            "deliverable_format",
            "evaluation_criteria",
            "runtime_limitations",
        )
        for competition_id in sorted(HAND_AUTHORED_ICPC_QUALITY - {"icpc"}):
            sections = card_payload(competition_id)["rule_sections"]
            for section in required:
                with self.subTest(card=competition_id, section=section):
                    self.assertTrue(
                        any(
                            item.startswith(("Official:", "Simulation choice:"))
                            for item in sections[section]
                        )
                    )


class TurnBudgetTests(unittest.TestCase):
    def test_budgets_match_their_recorded_basis(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                card = card_payload(competition_id)
                expected, _, _ = turn_budget(
                    card["team"]["active_default"],
                    official_minutes(card["provenance"].get("official_time_note")),
                    answer_parts(card["competition_id"]),
                )
                self.assertEqual(card["simulation"]["max_turns"], expected)

    def test_longer_contests_get_more_turns(self):
        icpc = card_payload("icpc")
        arml = card_payload("arml_local")

        self.assertGreater(
            icpc["simulation"]["max_turns"], arml["simulation"]["max_turns"]
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
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                constraints = card_payload(competition_id)["human_constraints"]
                self.assertEqual(len(constraints), len(set(constraints)))

    def test_cards_have_no_maintainer_notes_in_binding_rules(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                card = card_payload(competition_id)
                dirty = [c for c in card["human_constraints"] if is_maintainer_text(c)]
                self.assertEqual(dirty, [])


class RoleDutyTests(unittest.TestCase):
    def test_no_role_carries_boilerplate_duties(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                card = card_payload(competition_id)
                for role in card["agent_roles"]:
                    self.assertNotIn(tuple(role["duties"]), BOILERPLATE)


class SourceReviewRegressionTests(unittest.TestCase):
    def test_reviewed_profiles_are_never_official_equivalent_or_draft(self):
        for competition_id in CARD_IDS:
            with self.subTest(card=competition_id):
                card = card_payload(competition_id)
                self.assertNotEqual(card["profile"], "official_equivalent")
                self.assertNotEqual(card["comparability"]["overall"], "draft")

    def test_hmmt_variants_and_variable_rosters(self):
        card = load_rule_card("hmmt_guts", required=True)
        variants = card.raw["execution"]["season_variants"]
        self.assertEqual(variants["feb"]["team_size"], 8)
        self.assertEqual(variants["nov"]["team_size"], 6)
        self.assertEqual(len(card.roster(8)), 8)
        self.assertEqual(len(card.roster(6)), 6)

    def test_ichto_models_one_four_to_six_person_team(self):
        card = card_payload("ichto")
        self.assertEqual(
            (card["team"]["active_min"], card["team"]["active_max"]),
            (4, 6),
        )
        self.assertEqual(card["resources"]["internet"], "forbidden")
        self.assertEqual(card["resources"]["code_execution"], "forbidden")
        titles = {role["title"] for role in card["agent_roles"]}
        self.assertNotIn("opponent", titles)
        self.assertNotIn("reviewer", titles)

    def test_iiot_declares_two_contest_machines(self):
        card = card_payload("iiot")
        self.assertEqual(card["resources"]["contest_machine_capacity"], 2)
        self.assertNotIn("single workstation", card["rules_text"].lower())

    def test_bp_has_four_private_coalitions(self):
        card = card_payload("debatebench")
        coalitions = card["execution"]["coalitions"]
        self.assertEqual(len(coalitions), 4)
        self.assertTrue(all(len(item["members"]) == 2 for item in coalitions))

    def test_wharton_pumac_and_wsc_corrections(self):
        wharton = card_payload("wharton_investment")
        self.assertEqual(
            (wharton["team"]["active_min"], wharton["team"]["active_max"]),
            (4, 6),
        )
        self.assertEqual(card_payload("pumac_power")["allowed_tools"], ["query_rules"])
        wsc = card_payload("wsc_writing")
        for role in wsc["agent_roles"]:
            self.assertIn(
                "complete response",
                " ".join(role["duties"]).lower(),
            )

    def test_appe_and_nhseb_use_official_active_rosters(self):
        appe = card_payload("ethics_bowl_appe")
        self.assertEqual(
            (appe["team"]["active_min"], appe["team"]["active_max"]),
            (1, 6),
        )
        self.assertEqual(appe["execution"]["rules_edition"], "2025_national")
        self.assertEqual(
            len(appe["scoring"]["official_performance"]["mechanics"]), 4
        )

        nhseb = card_payload("ethics_bowl_nhseb")
        self.assertEqual(
            (
                nhseb["team"]["active_min"],
                nhseb["team"]["active_max"],
                nhseb["team"]["roster_max"],
            ),
            (3, 5, 7),
        )
        presentation = nhseb["execution"]["official_phases"][1]
        self.assertEqual(
            presentation["minutes_by_scope"],
            {"regional": 5, "divisional_or_national": 6},
        )

    def test_history_bowl_uses_2025_four_quarter_rules_without_negs(self):
        card = card_payload("history_olympiad")
        self.assertEqual(card["profile"], "non_comparable")
        self.assertEqual(card["team"]["active_default"], 3)
        self.assertEqual(card["team"]["range_basis"], "mixed_or_unresolved")
        self.assertTrue(
            any(
                "never deduct points" in item
                for item in card["human_constraints"]
            )
        )
        self.assertEqual(len(card["execution"]["official_quarters"]), 4)

    def test_ioai_team_does_not_inherit_individual_web_access(self):
        card = card_payload("ioai_team")
        self.assertNotIn("web_search", card["allowed_tools"])
        self.assertEqual(
            card["resources"]["internet"],
            "translation_site_only_unless_team_task_guide_allows_more",
        )
        self.assertEqual(
            card["execution"]["team_challenge_environment"],
            "specified_by_separate_task_guide",
        )

    def test_mystery_science_olympiad_and_wro_scope_adaptations(self):
        mystery = card_payload("mystery_hunt")
        self.assertEqual(mystery["team"]["range_basis"], "benchmark_adaptation")
        self.assertIn("no official team-size", mystery["team"]["official_roster_note"])

        science = card_payload("science_olympiad")
        self.assertEqual(
            science["execution"]["required_selectors"],
            ["season", "division", "event"],
        )
        self.assertIn("tournament roster", science["team"]["official_roster_note"])

        wro = card_payload("wro")
        self.assertEqual(wro["execution"]["rules_edition"], "2026_robomission_general")
        self.assertEqual(wro["execution"]["robot_attempt_seconds"], 120)
        self.assertTrue(
            all("WRO-2025" not in item["url"] for item in wro["provenance"]["sources"])
        )

    def test_unsourced_exact_durations_are_null(self):
        for competition_id in (
            "arml_national_power",
            "arml_national_team",
            "arml_power",
            "ieo_business_case",
            "iiot",
            "ijso_practical",
            "ioaa_group",
        ):
            with self.subTest(card=competition_id):
                self.assertIsNone(
                    card_payload(competition_id)["execution"]["official_minutes"]
                )


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
