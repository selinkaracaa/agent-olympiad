from __future__ import annotations

import inspect
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from contest_manifest import ContestManifest  # noqa: E402
from rules.loader import load_rule_card
from contest_runner import ContestRunConfig  # noqa: E402
from strategic_contest_runner import run_strategic_contest  # noqa: E402
from vanilla_contest_runner import run_vanilla_contest  # noqa: E402


class ContestVariantRunnerTests(unittest.TestCase):
    def config(self, variant: str) -> ContestRunConfig:
        return ContestRunConfig(
            system_variant=variant,
            team_size=3,
            max_turns=10,
            rule_card=load_rule_card("icpc") if variant == "strategic" else None,
        )

    def manifest(self) -> ContestManifest:
        return ContestManifest("session", "icpc", ())

    def test_vanilla_interface_has_no_coach_dependency(self) -> None:
        self.assertNotIn(
            "coach_query_fn",
            inspect.signature(run_vanilla_contest).parameters,
        )
        with patch(
            "vanilla_contest_runner._run_contest_engine",
            return_value={"system_variant": "vanilla"},
        ) as engine:
            result = run_vanilla_contest(
                self.manifest(),
                lambda _system, _user: "",
                self.config("vanilla"),
            )

        self.assertEqual(result["system_variant"], "vanilla")
        self.assertIsNone(engine.call_args.kwargs["coach_query_fn"])

    def test_strategic_interface_owns_coach_dependency(self) -> None:
        coach = lambda _system, _user: "{}"
        with patch(
            "strategic_contest_runner._run_contest_engine",
            return_value={"system_variant": "strategic"},
        ) as engine:
            result = run_strategic_contest(
                self.manifest(),
                lambda _system, _user: "",
                self.config("strategic"),
                coach_query_fn=coach,
            )

        self.assertEqual(result["system_variant"], "strategic")
        self.assertIs(engine.call_args.kwargs["coach_query_fn"], coach)

    def test_variant_modules_reject_crossed_configuration(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires a no-coach baseline"):
            run_vanilla_contest(
                self.manifest(),
                lambda _system, _user: "",
                self.config("strategic"),
            )
        with self.assertRaisesRegex(ValueError, "requires a no-coach baseline"):
            run_vanilla_contest(
                self.manifest(),
                lambda _system, _user: "",
                self.config("centralized"),
            )
        with self.assertRaisesRegex(ValueError, "requires a coach or leader baseline"):
            run_strategic_contest(
                self.manifest(),
                lambda _system, _user: "",
                self.config("vanilla"),
            )


if __name__ == "__main__":
    unittest.main()
