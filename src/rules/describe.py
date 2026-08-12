"""Human-readable phrasing for rule-card resource policies.

Both the agent system prompt (`src/collaboration.py`) and the card generator
(`collectors/rewrite_rules_text.py`) render the same `resources` object, so the
wording lives here instead of being duplicated on either side.
"""

from __future__ import annotations

from typing import Any, Mapping

RESOURCE_LABELS = {
    "internet": "internet access",
    "calculator": "calculators",
    "electronic_devices": "personal electronics",
    "books_notes": "books and notes",
    "code_execution": "running code",
    "reference_materials": "reference materials",
    "electronic_reference": "electronic references",
    "lab_equipment": "lab equipment",
    "physical_lab": "physical lab equipment",
    "external_help": "outside help",
    "external_teams": "help from other teams",
    "ai_assistance": "AI assistance",
    "ai_tools": "AI tools",
    "generative_ai": "generative AI",
    "computer_algebra": "computer algebra systems",
    "solution_method_search": "searching for published solution methods",
    "sandbox": "the provided sandbox",
    "paper_pencil": "paper and pencil",
}

VALUE_PHRASES = {
    "proxy_unavailable": "not available in this simulation",
    "judge_only_or_forbidden": "limited to the judge system",
    "forbidden_for_solution_search": "never usable for looking up solutions",
    "allowed_for_calculation_only": "allowed for calculation only",
    "task_dependent": "task dependent",
    "required": "required",
}

# Resource keys that read better as their own sentence than inside a list.
FLAG_RESOURCES = {
    "provided_materials_only": "Work only from the materials provided with the problem.",
    "shared_workstation": "The whole team shares a single workstation.",
}

SENTENCE_RESOURCES = {
    ("paper_pencil", "allowed"): "Paper and pencil are always available.",
    ("paper_pencil", "forbidden"): "Even paper and pencil are unavailable.",
}


def label_for(key: str) -> str:
    return RESOURCE_LABELS.get(key, key.replace("_", " "))


def join_clause(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def describe_resources(
    resources: Mapping[str, Any], *, skip_keys: frozenset[str] = frozenset()
) -> str:
    """Render a resources object as contestant-facing sentences."""
    banned: list[str] = []
    allowed: list[str] = []
    qualified: list[str] = []
    flags: list[str] = []

    for key, value in resources.items():
        if key in skip_keys:
            continue
        if key in FLAG_RESOURCES:
            if value:
                flags.append(FLAG_RESOURCES[key])
            continue
        sentence = SENTENCE_RESOURCES.get((key, value))
        if sentence:
            flags.append(sentence)
        elif value == "forbidden":
            banned.append(label_for(key))
        elif value == "allowed":
            allowed.append(label_for(key))
        elif isinstance(value, str) and value:
            phrase = VALUE_PHRASES.get(value, value.replace("_", " "))
            qualified.append(f"{label_for(key)} is {phrase}")

    parts: list[str] = []
    if banned:
        parts.append(f"Banned during the contest: {join_clause(banned)}.")
    if allowed:
        parts.append(f"Permitted: {join_clause(allowed)}.")
    if qualified:
        parts.append(f"Conditional: {join_clause(qualified)}.")
    parts.extend(flags)
    return " ".join(parts)
