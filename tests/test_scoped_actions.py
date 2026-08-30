from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from actions import parse_scoped_single_action  # noqa: E402


class ScopedActionParserTests(unittest.TestCase):
    def parse(self, text: str):
        return parse_scoped_single_action(
            text,
            allowed_actions={"speak", "work", "rest"},
        )

    def test_accepts_exact_scoped_action(self) -> None:
        self.assertEqual(
            self.parse(
                "ACTION: speak | TARGET: Agent_2,Agent_3 | PAYLOAD: check Q5"
            ),
            ("speak", "Agent_2,Agent_3", "check Q5", None),
        )

    def test_accepts_markdown_and_leading_explanation(self) -> None:
        wrapped = """I will report the result briefly.
```text
ACTION: work | TARGET: public | PAYLOAD: Q5 = 47sqrt(3)/4
```"""
        self.assertEqual(
            self.parse(wrapped),
            ("work", "public", "Q5 = 47sqrt(3)/4", None),
        )

    def test_accepts_newline_fields(self) -> None:
        text = """ACTION: speak
TARGET: Agent_2
PAYLOAD: Please compare the two Q5 derivations."""
        self.assertEqual(
            self.parse(text),
            (
                "speak",
                "Agent_2",
                "Please compare the two Q5 derivations.",
                None,
            ),
        )

    def test_accepts_json_action(self) -> None:
        self.assertEqual(
            self.parse(
                '{"action":"rest","target":"public","payload":"finished"}'
            ),
            ("rest", "public", "finished", None),
        )

    def test_accepts_bare_rest(self) -> None:
        self.assertEqual(
            self.parse("ACTION: rest"),
            ("rest", "public", "", None),
        )

    def test_rejects_multiple_actions(self) -> None:
        result = self.parse(
            "ACTION: speak | PAYLOAD: first\n"
            "ACTION: work | PAYLOAD: second"
        )
        self.assertIsNotNone(result[-1])


if __name__ == "__main__":
    unittest.main()
