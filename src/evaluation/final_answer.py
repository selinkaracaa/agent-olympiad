"""Gold-independent extraction of a final answer from a single submission.

The original text stays available for audit. This module never sees the gold
answer and never chooses a substring because it happens to match the reference.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re

from answer_identity import conflicting_answer_task, normalize_task_reference


@dataclass(frozen=True)
class FinalAnswer:
    raw_text: str
    final_answer: str
    method: str


def _part_id(value: str | None) -> str | None:
    if value is None:
        return None
    return normalize_task_reference(value)


def _value(text: str) -> str:
    """Strip presentation wrappers, not arbitrary terms inside an expression."""
    text = re.split(r"[\r\n;]|\.(?=\s|$)", text.strip(), maxsplit=1)[0].strip()
    for left, right in (("**", "**"), (chr(96), chr(96)), ("$", "$"),
                        (r"\(", r"\)"), (r"\[", r"\]")):
        if text.startswith(left) and text.endswith(right) and len(text) > len(left) + len(right):
            text = text[len(left):-len(right)].strip()
    text = text.rstrip(" .;")
    text = re.sub(r"\s+(?:dollars?|values?|solutions?|terms?|points?)$", "", text, flags=re.I)
    return text.strip()


def _math_value(text: str) -> bool:
    probe = re.sub(r"\\[A-Za-z]+", "", text)
    probe = re.sub(r"sqrt|sin|cos|tan|log|ln|pi", "", probe, flags=re.I)
    return bool(probe.strip()) and bool(re.fullmatch(
        r"[0-9\s+\-*/^=().,{}\[\]_$%\u2212\u221a\u00b7\u00d7]+", probe
    ))


def _claim_is_rejected(text: str) -> bool:
    """Reject an explicit denial attached to the selected answer, not its proof."""
    clauses = re.split(r"[.;](?=\s|$)|[\r\n]+", text.strip(), maxsplit=1)
    denial = r"(?:incorrect|wrong|invalid|rejected|not\s+(?:the\s+)?(?:correct|right|valid)(?:\s+answer)?)"
    if re.search(r"\b" + denial + r"\b", clauses[0], flags=re.I):
        return True
    if len(clauses) == 1:
        return False
    return bool(re.match(
        r"(?i)^\s*(?:(?:but|however|actually)\s*[:,]?\s*)?"
        r"(?:(?:this|that|it|the\s+(?:answer|result|candidate))\s+(?:is|was)\s+)?"
        + denial + r"\b",
        clauses[1],
    ))


def _conclusion_value(text: str) -> str:
    if _claim_is_rejected(text):
        return ""
    value = _value(text)
    # A complete equality chain in an explicitly selected answer is allowed.
    # Never take the denominator or an arbitrary interior numerical substring.
    if "=" in value:
        sides = [part.strip() for part in value.split("=")]
        if all(_math_value(part) for part in sides):
            value = sides[-1]
    return value


_MARKER = re.compile(
    r"(?i)\b(?:(?:final|candidate)\s+)?answer\s*[:=]\s*(?:\*\*\s*)?"
)
_CLAIM = re.compile(
    r"(?i)\b(?:final\s+answer|answer|(?:win\s+)?probability|slope|area|"
    r"ordered\s+pair|expected\s+winnings|total\s+expected\s+winnings|"
    r"number\s+of\s+(?:values|solutions|terms))\s*(?:is|equals?|=|:)\s*"
)
_CONCLUSION_CLAIM = re.compile(
    # A conclusion cue is required: "if f has slope -3" is an input fact,
    # not an answer. Keep the entire selected expression for boundary checks.
    r"(?i)\b(?:therefore|thus|hence|consequently)\s+"
    r"(?:has|have)\s+(?:a\s+)?(?:slope|area|probability)\s+"
    r"(?:(?:of|is|equals?)\s+)?"
)
_NAMED_CONCLUSION = re.compile(
    r"(?i)\b(?P<cue>therefore|thus|hence|consequently|so|and)\s+(?:the\s+)?"
    r"(?:(?:area|slope|probability)\s*\([A-Za-z][A-Za-z0-9_,\s]*\)|"
    r"\(\s*[A-Za-z]\w*\s*,\s*[A-Za-z]\w*\s*\))\s*=\s*"
)


def _named_conclusion_value(text: str, match: re.Match) -> str:
    """Recognize a concluded quantity/pair assignment, never a premise."""
    prefix = re.split(r"[\r\n;]|\.(?=\s|$)", text[:match.start()])[-1]
    if re.search(r"(?i)\b(?:if|given|assum\w*|suppos\w*|consider\w*|perhaps|maybe)\b", prefix):
        return ""
    if match.group("cue").lower() == "and" and not re.search(
        r"(?i)\b(?:we\s+(?:get|obtain|find)|gives?|yields?)\b", prefix
    ):
        return ""
    selected = text[match.end():]
    if re.search(
        r"(?i)(?:[.;]\s*|\n\s*)(?:or\b|alternatively\b|perhaps\b|possibly\b|"
        r"(?:this|that|it)\s+(?:may|might|could)\b)", selected
    ):
        return ""
    return _conclusion_value(selected)


def extract_final_answer(submission: str, *, part_id: str | None = None) -> FinalAnswer:
    raw = str(submission or "")
    text = raw.strip()
    if not text:
        return FinalAnswer(raw, "", "missing")

    fence = chr(96) * 3
    if text.startswith(fence) and text.endswith(fence):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    if part_id is not None and conflicting_answer_task(text, part_id) is not None:
        return FinalAnswer(raw, "", "task_id_mismatch")
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            data = None
        if isinstance(data, dict) and "final_answer" in data:
            declared = data.get("problem_id", data.get("task_id", data.get("part_id")))
            if declared is not None and part_id is not None and _part_id(declared) != _part_id(part_id):
                return FinalAnswer(raw, "", "task_id_mismatch")
            answer = data["final_answer"]
            if isinstance(answer, list) and all(isinstance(v, (str, int, float)) and not isinstance(v, bool) for v in answer):
                answer = ", ".join(str(v) for v in answer)
            if answer is None or isinstance(answer, (bool, dict, list)):
                return FinalAnswer(raw, "", "invalid_final_answer")
            return FinalAnswer(raw, _conclusion_value(str(answer)), "final_answer_field")

    # A single question already has an ID. Do not split its proof into fake
    # questions using numbered steps, newlines, semicolons, or comma lists.
    header = re.match(
        r"(?i)^\s*(?:problem|q|part|t|team)\s*-?\s*(\d+)\b\s*[.):\-]?\s*", text
    )
    if header is None:
        header = re.match(r"^\s*(\d+)\s*(?:[):]|\.(?=\s))\s*", text)
    if header:
        if part_id is not None and _part_id(header.group(1)) != _part_id(part_id):
            return FinalAnswer(raw, "", "task_id_mismatch")
        text = text[header.end():].lstrip()
        text = re.sub(r"(?i)^(?:final|draft|verified|revised|confirmed)\s*:\s*", "", text)

    markers = list(_MARKER.finditer(text))
    if markers:
        # A later correction overrides earlier candidates, even when incorrect.
        chosen = markers[-1]
        return FinalAnswer(raw, _conclusion_value(text[chosen.end():]), "answer_marker")

    # Support common answer-only mathematical claims without using the gold.
    # Long unstructured reasoning without such a claim is deliberately not
    # searched for potentially matching numbers.
    claims = sorted(
        (*_CLAIM.finditer(text), *_CONCLUSION_CLAIM.finditer(text),
         *_NAMED_CONCLUSION.finditer(text)),
        key=lambda match: match.start(),
    )
    if claims:
        chosen = claims[-1]
        value = (_named_conclusion_value(text, chosen) if chosen.re is _NAMED_CONCLUSION
                 else _conclusion_value(text[chosen.end():]))
        if _math_value(value):
            return FinalAnswer(raw, value, "answer_claim")

    first = _value(text)
    pair = re.match(r"^\(\s*[A-Za-z]\w*\s*,\s*[A-Za-z]\w*\s*\)\s*=\s*(.+)$", first)
    if pair and _math_value(pair.group(1)):
        return FinalAnswer(raw, pair.group(1).strip(), "ordered_pair_assignment")
    label = re.match(r"(?i)^(?:slope|probability|area)\s+(.+)$", first)
    if label and _math_value(label.group(1)):
        return FinalAnswer(raw, label.group(1).strip(), "answer_label")
    if _math_value(first) and (first == text.rstrip(" .;") or not re.search(
        r"(?i)\b(?:incorrect|wrong|reject|instead|but|not)\b", text[len(first):]
    )):
        return FinalAnswer(raw, first, "bare_answer")
    # Exact textual answers still work. No substring acceptance is performed.
    return FinalAnswer(raw, text.strip(), "unstructured")
