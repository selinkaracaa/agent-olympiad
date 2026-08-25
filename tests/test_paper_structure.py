"""Static validation for the Phase 5 paper and research documents."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER = ROOT / "paper"
SECTIONS = (
    "abstract",
    "introduction",
    "related_work",
    "benchmark",
    "method",
    "metrics",
    "experiments",
    "findings",
    "limitations",
    "conclusion",
    "appendix",
)


def latex_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_comments(text: str) -> str:
    return "\n".join(re.sub(r"(?<!\\)%.*$", "", line) for line in text.splitlines())


def assert_balanced_braces(test: unittest.TestCase, path: Path) -> None:
    text = strip_comments(latex_text(path))
    depth = 0
    for index, char in enumerate(text):
        if char in "{}" and (index == 0 or text[index - 1] != "\\"):
            depth += 1 if char == "{" else -1
            test.assertGreaterEqual(depth, 0, f"extra closing brace in {path}")
    test.assertEqual(depth, 0, f"unbalanced braces in {path}")


class PaperStructureTests(unittest.TestCase):
    def test_expected_files_exist(self) -> None:
        expected = {
            PAPER / "main.tex",
            PAPER / "refs.bib",
            PAPER / "Makefile",
            PAPER / "README.md",
            PAPER / "agentolympiad_iclr_standin.sty",
            *(PAPER / "sections" / f"{name}.tex" for name in SECTIONS),
            ROOT / "docs" / "CAPABILITY_MATRIX.md",
            ROOT / "docs" / "HUMAN_VS_AGENT_SETTING.md",
            ROOT / "docs" / "TOOLING_GAPS.md",
        }
        missing = sorted(str(path.relative_to(ROOT)) for path in expected if not path.is_file())
        self.assertEqual(missing, [])

    def test_all_inputs_resolve_and_expected_sections_are_used(self) -> None:
        main = latex_text(PAPER / "main.tex")
        inputs = re.findall(r"\\input\{([^}]+)\}", main)
        self.assertEqual(inputs, [f"sections/{name}" for name in SECTIONS])
        for target in inputs:
            path = PAPER / f"{target}.tex"
            self.assertTrue(path.is_file(), f"missing input: {path}")

    def test_all_citation_keys_exist(self) -> None:
        tex = "\n".join(latex_text(path) for path in PAPER.rglob("*.tex"))
        cited = {
            key.strip()
            for group in re.findall(r"\\cite\{([^}]+)\}", tex)
            for key in group.split(",")
        }
        bib = latex_text(PAPER / "refs.bib")
        defined = set(re.findall(r"@\w+\{\s*([^,\s]+)\s*,", bib))
        self.assertEqual(sorted(cited - defined), [])

    def test_latex_braces_and_environments_are_balanced(self) -> None:
        for path in [PAPER / "main.tex", *sorted((PAPER / "sections").glob("*.tex"))]:
            assert_balanced_braces(self, path)
            text = strip_comments(latex_text(path))
            stack: list[str] = []
            for match in re.finditer(r"\\(begin|end)\{([^}]+)\}", text):
                kind, environment = match.groups()
                if kind == "begin":
                    stack.append(environment)
                else:
                    self.assertTrue(stack, f"orphan end{{{environment}}} in {path}")
                    self.assertEqual(stack.pop(), environment, f"environment mismatch in {path}")
            self.assertEqual(stack, [], f"unclosed environments in {path}")

    def test_style_and_build_paths_are_explicitly_safe(self) -> None:
        style = latex_text(PAPER / "agentolympiad_iclr_standin.sty").lower()
        readme = latex_text(PAPER / "README.md").lower()
        makefile = latex_text(PAPER / "Makefile")
        self.assertIn("not the official iclr template", style)
        self.assertIn("not the official iclr template", readme)
        self.assertIn("latexmk", makefile)
        self.assertIn("docker image inspect", makefile)
        self.assertNotIn("docker pull", makefile)

    def test_research_docs_have_required_headings(self) -> None:
        requirements = {
            "CAPABILITY_MATRIX.md": (
                "# Capability matrix",
                "## Status legend",
                "## Competition families × abilities × grader coverage",
                "## Baselines × capability isolated",
            ),
            "HUMAN_VS_AGENT_SETTING.md": (
                "# Human versus agent setting",
                "## Fidelity labels",
                "## Rule-by-rule transfer assessment",
                "## Threats to human comparison",
            ),
            "TOOLING_GAPS.md": (
                "# Tooling gaps",
                "## Priority principle: correct feedback and isolation first",
                "## Evidence-based priorities",
                "## “More tools” versus valid tools",
            ),
        }
        for filename, headings in requirements.items():
            text = latex_text(ROOT / "docs" / filename)
            for heading in headings:
                self.assertIn(heading, text, f"{filename} missing {heading}")


if __name__ == "__main__":
    unittest.main()
