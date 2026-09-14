"""Match explicit answer labels to their destination, without reading answers or gold."""
from __future__ import annotations

import json
import re


def normalize_task_reference(value: object) -> str:
    value = str(value).strip().rsplit(":", 1)[-1]
    match = re.fullmatch(r"(?i)(?:q|part|problem|task|question|t|team)?-?(\d+)", value)
    return match.group(1) if match else value


def task_reference_matches(declared: object, expected: object) -> bool:
    declared, expected = str(declared).strip(), str(expected).strip()
    # Full identifiers retain their contest namespace. Short question labels
    # can identify the numbered part of a manifest task.
    if ":" in declared and ":" in expected:
        return declared == expected
    return normalize_task_reference(declared) == normalize_task_reference(expected)


_REFERENCE = r"(?:[A-Za-z_][\w.-]*:[\w.-]+|(?:q|part|problem|task|t|team)?-?\d+)"
_LABEL = r"(?:problem|question|task|part|team|q|t)\s*-?\s*"
_HEADER = re.compile(r"(?i)^\s*(?:\#{1,6}\s+)?(?:\*\*)?" + _LABEL + "(" + _REFERENCE + r")\b")
_ANSWER_FOR = re.compile(
    r"(?i)(?:^|[.;\n]\s*)(?:\*\*)?(?:final\s+)?answer\s+(?:for|to)\s+"
    + _LABEL + "(" + _REFERENCE + r")\b"
)


def conflicting_answer_task(text: str, expected: str) -> str | None:
    """Return an explicitly conflicting label; ordinary references/steps are not labels.

    This never guesses a task from the subject matter or correct answer and
    never redirects a write to another task.
    """
    text = str(text).strip()
    if text.startswith("```") and text.endswith("```"):
        text = "\n".join(text.splitlines()[1:-1]).strip()
    references = []
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            data = None
        if isinstance(data, dict):
            references.extend(data[key] for key in ("problem_id", "task_id", "part_id")
                              if data.get(key) is not None)
    header = _HEADER.match(text)
    if header:
        references.append(header.group(1))
    references.extend(match.group(1) for match in _ANSWER_FOR.finditer(text))
    return next((str(ref) for ref in references if not task_reference_matches(ref, expected)), None)
