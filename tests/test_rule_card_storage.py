from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from rules import (  # noqa: E402
    COMPONENT_FILES,
    RuleCard,
    RuleCardError,
    RuleCardStorageError,
    agent_view,
    grader_view,
    iter_rule_card_ids,
    load_rule_card,
    load_rule_card_payload,
    write_rule_card_payload,
)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


class RuleCardStorageTests(unittest.TestCase):
    def test_flat_card_remains_loadable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "sample.json", {"competition_id": "sample"})

            self.assertEqual(
                load_rule_card_payload(
                    "sample", rules_root=root, required=True
                ),
                {"competition_id": "sample"},
            )
            self.assertEqual(iter_rule_card_ids(root), ["sample"])

    def test_bundle_composes_three_owned_components(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "sample"
            write_json(
                bundle / "competition.json",
                {
                    "competition_id": "sample",
                    "rules_text": "Rules",
                    "deliverable": {"answer_format": "Answer"},
                },
            )
            write_json(
                bundle / "collaboration.json",
                {
                    "agent_roles": [],
                    "communication": {},
                    "simulation": {"max_turns": 12},
                },
            )
            write_json(
                bundle / "evaluation.json",
                {"evaluation_guidance": "Hidden", "scoring": {}},
            )

            payload = load_rule_card_payload(
                "sample", rules_root=root, required=True
            )
            self.assertEqual(payload["competition_id"], "sample")
            self.assertEqual(payload["agent_roles"], [])
            self.assertEqual(payload["deliverable"]["answer_format"], "Answer")
            self.assertEqual(payload["simulation"]["max_turns"], 12)
            self.assertEqual(iter_rule_card_ids(root), ["sample"])

    def test_bundle_requires_all_three_components(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(
                root / "sample" / "competition.json",
                {"competition_id": "sample"},
            )

            with self.assertRaisesRegex(
                RuleCardStorageError, "collaboration.json, evaluation.json"
            ):
                load_rule_card_payload(
                    "sample", rules_root=root, required=True
                )

    def test_bundle_rejects_misplaced_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "sample"
            write_json(
                bundle / "competition.json",
                {"competition_id": "sample"},
            )
            write_json(
                bundle / "collaboration.json",
                {"deliverable": {"answer_format": "wrong component"}},
            )
            write_json(bundle / "evaluation.json", {})

            with self.assertRaisesRegex(
                RuleCardStorageError, "owned by another component"
            ):
                load_rule_card_payload(
                    "sample", rules_root=root, required=True
                )

    def test_flat_and_bundle_is_ambiguous(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            write_json(root / "sample.json", {"competition_id": "sample"})
            for filename in COMPONENT_FILES.values():
                write_json(root / "sample" / filename, {})

            with self.assertRaisesRegex(
                RuleCardStorageError, "both flat and bundled"
            ):
                load_rule_card_payload(
                    "sample", rules_root=root, required=True
                )

    def test_bundle_rejects_non_object_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "sample"
            write_json(bundle / "competition.json", [])
            write_json(bundle / "collaboration.json", {})
            write_json(bundle / "evaluation.json", {})

            with self.assertRaisesRegex(
                RuleCardStorageError, "must be an object"
            ):
                load_rule_card_payload(
                    "sample", rules_root=root, required=True
                )

    def test_bundle_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "sample"
            bundle.mkdir(parents=True)
            (bundle / "competition.json").write_text(
                "{not-json}\n", encoding="utf-8"
            )
            write_json(bundle / "collaboration.json", {})
            write_json(bundle / "evaluation.json", {})

            with self.assertRaisesRegex(
                RuleCardStorageError, "Invalid JSON"
            ):
                load_rule_card_payload(
                    "sample", rules_root=root, required=True
                )

    def test_bundle_writer_updates_only_owning_component(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "sample"
            write_json(
                bundle / "competition.json",
                {
                    "competition_id": "sample",
                    "rules_text": "Before",
                    "deliverable": {"answer_format": "Before"},
                },
            )
            write_json(
                bundle / "collaboration.json",
                {"agent_roles": []},
            )
            write_json(
                bundle / "evaluation.json",
                {"evaluation_guidance": "Before"},
            )
            collaboration_before = (
                bundle / "collaboration.json"
            ).read_bytes()

            payload = load_rule_card_payload(
                "sample", rules_root=root, required=True
            )
            payload["evaluation_guidance"] = "After"
            write_rule_card_payload("sample", payload, rules_root=root)

            self.assertEqual(
                json.loads(
                    (bundle / "evaluation.json").read_text(encoding="utf-8")
                )["evaluation_guidance"],
                "After",
            )
            self.assertEqual(
                (bundle / "collaboration.json").read_bytes(),
                collaboration_before,
            )

    def test_wsc_bundle_loads_as_a_complete_rule_card(self):
        rules_root = REPO_ROOT / "data" / "rules"
        self.assertFalse((rules_root / "wsc_writing.json").exists())
        self.assertEqual(
            set(path.name for path in (rules_root / "wsc_writing").iterdir()),
            set(COMPONENT_FILES.values()),
        )
        card = load_rule_card("wsc_writing", required=True)
        self.assertEqual(card.competition_id, "wsc_writing")
        self.assertEqual(card.information_policy["mode"], "role_specialized")
        self.assertEqual(card.deliberation["mode"], "structured")
        self.assertEqual(card.communication["team_message_budget"], 8)
        self.assertGreaterEqual(len(card.agent_constraints), 6)
        self.assertTrue(
            any(
                "do not import rules from another contest" in item.lower()
                for item in card.agent_constraints
            )
        )
        self.assertNotIn(
            "Do not look up answer keys or hidden solutions.",
            card.human_constraints,
        )
        self.assertFalse(
            any("75 minutes" in item for item in card.human_constraints)
        )
        official_rubric = card.scoring["official_rubric_path"]
        self.assertEqual(
            official_rubric,
            "data/raw/wsc_writing/rubric/wsc_writing_rubric.pdf",
        )
        self.assertTrue((REPO_ROOT / official_rubric).is_file())
        self.assertNotIn("sources", card.provenance)
        self.assertNotIn("crawled_excerpts", card.provenance)
        self.assertNotIn("enriched_at", card.provenance)
        manifest = REPO_ROOT / card.provenance["manifest"]
        self.assertTrue(manifest.is_file())
        self.assertIn(
            "official_evaluation_rubric",
            manifest.read_text(encoding="utf-8"),
        )

    def test_icpc_bundle_models_dynamic_contestants_and_shared_workstation(self):
        rules_root = REPO_ROOT / "data" / "rules"
        self.assertFalse((rules_root / "icpc.json").exists())
        self.assertEqual(
            set(path.name for path in (rules_root / "icpc").iterdir()),
            set(COMPONENT_FILES.values()),
        )

        card = load_rule_card("icpc", required=True)

        self.assertEqual(card.team_size_default, 3)
        self.assertEqual(card.resources["shared_workstation_count"], 1)
        self.assertEqual(card.information_policy["mode"], "shared")
        self.assertEqual(card.deliberation["mode"], "unstructured")
        self.assertEqual(card.communication["mode"], "unlimited")
        self.assertEqual(
            {role.title for role in card.agent_roles},
            {"contestant"},
        )
        self.assertTrue(all(role.may_submit for role in card.agent_roles))
        self.assertEqual(card.simulation["max_turns"], card.max_turns)
        self.assertNotIn("max_turns", card.raw.get("execution") or {})
        self.assertEqual(card.simulation["exclusive_workstation_lease"], "enforced")
        visible = agent_view(card)
        self.assertNotIn("evaluation_guidance", visible)
        self.assertNotIn("scoring", visible)
        hidden = grader_view(card)
        self.assertIn("evaluation_guidance", hidden)
        self.assertEqual(hidden["scoring"]["official_performance"]["penalty_minutes_per_rejection"], 20)
        self.assertEqual(
            card.scoring["official_performance"]["penalty_minutes_per_rejection"],
            20,
        )
        self.assertFalse(
            card.scoring["official_performance"]["compilation_error_penalized"]
        )

    def test_assembled_competition_id_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bundle = root / "sample"
            for filename in COMPONENT_FILES.values():
                write_json(bundle / filename, {})
            payload = load_rule_card_payload(
                "wsc_writing",
                rules_root=REPO_ROOT / "data" / "rules",
                required=True,
            )
            payload["competition_id"] = "wrong"
            write_rule_card_payload("sample", payload, rules_root=root)

            with self.assertRaisesRegex(
                RuleCardError, "does not match"
            ):
                load_rule_card(
                    "sample",
                    rules_root=root,
                    required=True,
                )

    def test_conflicting_turn_budgets_are_rejected(self):
        payload = load_rule_card_payload(
            "icpc",
            rules_root=REPO_ROOT / "data" / "rules",
            required=True,
        )
        payload["execution"] = dict(payload.get("execution") or {}, max_turns=12)
        payload["simulation"] = dict(payload.get("simulation") or {}, max_turns=60)
        with self.assertRaisesRegex(RuleCardError, "simulation fields still present"):
            RuleCard.from_dict(payload, competition_id="icpc")

    def test_legacy_execution_max_turns_still_loads(self):
        payload = load_rule_card_payload(
            "icpc",
            rules_root=REPO_ROOT / "data" / "rules",
            required=True,
        )
        payload["execution"] = dict(payload.get("execution") or {}, max_turns=42)
        payload["simulation"] = {}
        card = RuleCard.from_dict(payload, competition_id="icpc")
        self.assertEqual(card.max_turns, 42)


if __name__ == "__main__":
    unittest.main()
