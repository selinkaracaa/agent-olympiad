from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from actions import parse_typed_action  # noqa: E402
from tool_registry import resolve_actions  # noqa: E402


class TypedActionParserTests(unittest.TestCase):
    def setUp(self) -> None:
        self.actions = resolve_actions(
            competition="icpc",
            task_type="algorithmic_programming",
        )

    def test_accepts_one_strict_json_action(self) -> None:
        action, arguments, error = parse_typed_action(
            '{"action":"select_problem","arguments":{"problem_id":"A"}}',
            self.actions,
        )
        self.assertEqual((action, arguments, error), ("select_problem", {"problem_id": "A"}, None))

    def test_rejects_unknown_or_bad_arguments(self) -> None:
        self.assertIn(
            "not available",
            parse_typed_action(
                '{"action":"web_search","arguments":{"query":"x"}}',
                self.actions,
            )[2],
        )
        self.assertIn(
            "unexpected argument",
            parse_typed_action(
                '{"action":"rest","arguments":{"extra":true}}',
                self.actions,
            )[2],
        )

    def test_rejects_wrappers_and_multiple_json_objects(self) -> None:
        self.assertIsNotNone(
            parse_typed_action(
                'text {"action":"rest","arguments":{}}',
                self.actions,
            )[2]
        )
        self.assertIsNotNone(
            parse_typed_action(
                '{"action":"rest","arguments":{}} {"action":"rest","arguments":{}}',
                self.actions,
            )[2]
        )


if __name__ == "__main__":
    unittest.main()
