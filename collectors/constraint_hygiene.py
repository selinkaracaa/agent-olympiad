"""Separate contestant-binding constraints from notes addressed to maintainers.

The research reports mix two audiences in one bullet, e.g.

    "Team size commonly up to 5 in community practice; confirm exact roster limits
     in the linked Rules PDF on the same page (not fully extracted in this crawl)."

The first clause binds a contestant; the rest is a to-do for us. Everything in
`human_constraints` is injected into the agent prompt as BINDING, so the to-do half
has to move to `provenance.research_notes`. Both the merge step and the linter use
this module so the split survives a pipeline re-run.
"""

from __future__ import annotations

import re

# Phrases that only make sense to whoever maintains the rule cards.
MAINTAINER_PHRASES = (
    "in this crawl",
    "not fully extracted",
    "not fully retrieved",
    "not extracted here",
    "not extracted from",
    "not confirmed",
    "fetch timed out",
    "did not return",
    "index lists",
    "index team_size",
    "provisional",
    "confirm on ",
    "confirm in ",
    "confirm against",
    "confirm exact",
    "confirm roster",
    "verify against",
    "when simulating",
    "before treating",
    "until that pdf",
    "open those pdfs",
    "take from the packet",
    # Pointers to where the real rules live, rather than the rules themselves.
    "index uses",
    "must be taken from",
    "rules documents",
    "competition guidelines",
    "registration pages",
    "coach packet",
    "portal root fetch",
    "redirects to",
    "official site moved",
    "portal hosts",
    "handbooks on",
)

CLAUSE_SPLIT = re.compile(r"\s+[—–-]{1,2}\s+|;\s+")


def is_maintainer_text(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in MAINTAINER_PHRASES)


def _tidy(text: str) -> str:
    text = re.sub(r"\s{2,}", " ", text).strip(" ;,")
    text = text.strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def split_constraint(text: str) -> tuple[str | None, list[str]]:
    """Return (contestant constraint, maintainer notes) for one bullet."""
    if not is_maintainer_text(text):
        return _tidy(text), []

    # Parenthetical asides are their own clause.
    flattened = re.sub(r"\s*\(([^)]*)\)", r" ; \1", text)
    clauses = [clause for clause in CLAUSE_SPLIT.split(flattened) if clause.strip()]

    kept: list[str] = []
    notes: list[str] = []
    for clause in clauses:
        clause = clause.strip(" .;,")
        # A clause starting lowercase is the tail of the maintainer clause we just
        # dropped ("...not extracted from the fetch — use the year packet"), not a
        # rule that can stand on its own.
        if is_maintainer_text(clause) or (clause[:1].islower() and notes):
            notes.append(clause)
        else:
            kept.append(clause)

    if not kept:
        return None, [_tidy(text)]
    if not notes:
        return _tidy(text), []
    return _tidy("; ".join(kept)), [_tidy(f"{text}")]


def clean_constraints(constraints: list[str]) -> tuple[list[str], list[str]]:
    """Split a whole constraint list into contestant rules and maintainer notes."""
    kept: list[str] = []
    notes: list[str] = []
    for item in constraints:
        constraint, item_notes = split_constraint(str(item))
        if constraint:
            kept.append(constraint)
        for note in item_notes:
            if note not in notes:
                notes.append(note)
    return kept, notes
