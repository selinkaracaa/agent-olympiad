"""Rewrite generated placeholder rules_text into a contestant-facing briefing.

`rules_text` is injected verbatim into the agent system prompt by
`src/collaboration.py`, so it must read like a contest briefing, not like a dump
of our own pipeline fields. This script composes the briefing from the card's own
structured facts (protocol, roster, official timing, resource bans, submission
model) and leaves hand-written briefings untouched unless --all is passed.

Usage:
    python collectors/rewrite_rules_text.py --dry-run
    python collectors/rewrite_rules_text.py
    python collectors/rewrite_rules_text.py --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from lint_rule_cards import PLACEHOLDER_PATTERN, strip_meta_sentences

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
INDEX = REPO / "data" / "benchmarks" / "index.json"

sys.path.insert(0, str(REPO / "src"))

from rules import describe_resources  # noqa: E402

PROTOCOL_FORMAT = {
    "shared_answer": (
        "The active team of {team} works the problem set together and turns in one "
        "shared answer sheet."
    ),
    "progressive_release": (
        "The team of {team} works through problems that arrive in waves; you commit "
        "to the current batch before the next one is available."
    ),
    "single_workstation_programming": (
        "The team of {team} shares a single workstation and submits programs to an "
        "automated judge that only reports accept or reject."
    ),
    "research_artifact": (
        "The team of {team} prepares one research deliverable that expert judges "
        "score against a rubric."
    ),
    "presentation_and_cross_examination": (
        "The team of {team} builds a case, presents it, and defends it under "
        "questioning from judges or an opposing team."
    ),
    "buzzer_match_question_proxy": (
        "Four active team members face one match question at a time; toss-ups are "
        "answered individually and bonuses allow team consultation."
    ),
    "buzzer_match_session_proxy": (
        "The team of {team} plays a buzzer round packet: quick recall, no reference "
        "material, and one recognized answer per question."
    ),
    "lab_practical_proxy": (
        "The team of {team} runs a practical task and reports raw data, analysis, "
        "and conclusions on the official answer sheet."
    ),
    "ctf_sandbox": (
        "The team of {team} attacks a capture-the-flag challenge inside an isolated "
        "sandbox and reports the flag it recovers."
    ),
    "cyber_defense_proxy": (
        "The team of {team} defends an inherited production network while service "
        "availability is scored and injects arrive from management."
    ),
    "event_packet_proxy": (
        "The team of {team} splits into event pairs; this row is one event packet "
        "worked with the materials that event permits."
    ),
    "creative_performance_proxy": (
        "The team of {team} solves a long-term problem with its own work only; "
        "outside assistance is the one unforgivable violation."
    ),
    "robotics_rules_proxy": (
        "The team of {team} designs, builds, and debugs a robot solution against "
        "the season's game rules and scoring table."
    ),
    "staged_collaborative_writing": (
        "The team of {team} moves through fixed stages: plan together, write "
        "individually, then peer-edit before submission."
    ),
}

COMPOSED_MARKER = "composed_from_card_fields"

SUBMISSION_SENTENCE = {
    True: "The team files one shared submission",
    False: "Each contestant files a submission",
}


def display_names() -> dict[str, str]:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    return {item["id"]: item["name"] for item in index["olympiads"]}


def joined(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def format_sentence(card: dict) -> str:
    team = card["team"]["active_default"]
    template = PROTOCOL_FORMAT.get(card["protocol"])
    if template:
        return template.format(team=team)
    return f"The team of {team} works under the official format for this event."


def timing_sentence(card: dict) -> str:
    note = str((card.get("provenance") or {}).get("official_time_note") or "").strip()
    if note:
        return f"Official timing note: {note.rstrip('.')}."
    return (
        "Official wall-clock timing is not encoded for this track; treat the turn "
        "budget as your clock and submit before it runs out."
    )


def submission_sentence(card: dict) -> str:
    submission = card.get("submission") or {}
    shared = bool(submission.get("shared", True))
    sentence = SUBMISSION_SENTENCE[shared]
    max_count = submission.get("max_count")
    if isinstance(max_count, int) and max_count > 1:
        sentence += f", up to {max_count} times"
    if submission.get("finality") == "irrevocable":
        sentence += "; once filed it cannot be revised"
    return sentence + "."


def proxy_sentence(card: dict) -> str:
    if card.get("profile") != "proxy":
        return ""
    protocol = card.get("protocol") or ""
    if protocol.startswith("buzzer"):
        return (
            "Simulation note: there is no opposing team, lock-out buzzer, or moderator "
            "recognition here, so play the question as written."
        )
    if protocol in {"ctf_sandbox", "cyber_defense_proxy", "robotics_rules_proxy"}:
        return (
            "Simulation note: physical hardware and live adversaries are replaced by a "
            "scripted environment, so rely only on what the environment reports."
        )
    if protocol in {"lab_practical_proxy", "creative_performance_proxy", "event_packet_proxy"}:
        return (
            "Simulation note: the hands-on portion is represented in text, so state "
            "measurements, setup, and reasoning explicitly instead of demonstrating them."
        )
    if protocol == "presentation_and_cross_examination":
        return (
            "Simulation note: oral rounds are represented as written argument, so make "
            "the case and its rebuttals fully explicit in the text."
        )
    return (
        "Simulation note: this row is a partial view of the official event, so answer "
        "exactly what the problem asks."
    )


def compose(card: dict, name: str) -> str:
    """Describe format, roster, submission, and timing.

    Resource policy is rendered separately from `resources` in the agent prompt,
    so repeating it here would only duplicate the prompt.
    """
    pieces = [
        f"{name}.",
        format_sentence(card),
        card.get("team", {}).get("collaboration", "").strip(),
        submission_sentence(card),
        timing_sentence(card),
        proxy_sentence(card),
    ]
    text = " ".join(piece for piece in pieces if piece)
    return re.sub(r"\s{2,}", " ", text).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print without writing")
    parser.add_argument(
        "--all",
        action="store_true",
        help="also rewrite hand-written briefings, not just placeholders",
    )
    args = parser.parse_args()

    names = display_names()
    rewritten = 0
    for path in sorted(RULES.glob("*.json")):
        if path.name == "schema.json":
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        current = strip_meta_sentences(str(card.get("rules_text") or ""))
        previously_composed = str(
            (card.get("provenance") or {}).get("rules_text_source") or ""
        ).startswith(COMPOSED_MARKER)
        regenerate = bool(PLACEHOLDER_PATTERN.search(current)) or previously_composed
        if not regenerate and not args.all:
            if current != card.get("rules_text"):
                card["rules_text"] = current
                if not args.dry_run:
                    path.write_text(
                        json.dumps(card, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                rewritten += 1
                print(f"{path.stem}: cleaned metadata only")
            continue

        name = names.get(path.stem, path.stem)
        composed = compose(card, name)
        if composed == card.get("rules_text") and previously_composed:
            continue
        card["rules_text"] = composed
        provenance = dict(card.get("provenance") or {})
        provenance["rules_text_source"] = f"{COMPOSED_MARKER}_v2"
        card["provenance"] = provenance
        if not args.dry_run:
            path.write_text(
                json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        rewritten += 1
        print(f"{path.stem}: {card['rules_text']}")

    print(f"\nrewrote {rewritten} cards" + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
