"""Derive each rule card's turn budget from official duration and answer volume.

`max_turns` is the only clock the runner has, so a flat 60 turns gave a 45-minute
ARML round the same budget as a five-hour ICPC contest. This script derives the
budget from facts the card and the benchmark already carry:

    from_clock = official_minutes / MINUTES_PER_TURN
    floor      = team_size x 2 speaking turns + answer_parts + synthesis_headroom
    max_turns  = clamp(max(from_clock, floor), MIN_TURNS, MAX_TURNS)

The floor keeps every teammate able to speak twice even in short rounds, and the
clock term is what makes a five-hour contest cost more turns than a 20-minute one.
Every card records the inputs in `execution` so the number can be audited.

Usage:
    python collectors/derive_turn_budgets.py --dry-run
    python collectors/derive_turn_budgets.py
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
BENCHMARKS = REPO / "data" / "benchmarks"

# One agent action stands in for roughly five minutes of human contest work.
MINUTES_PER_TURN = 5
SPEAKING_TURNS_PER_TEAMMATE = 2
SYNTHESIS_HEADROOM = 4
MIN_TURNS = 24
MAX_TURNS = 96

HOURS_RANGE = re.compile(r"(\d+(?:\.\d+)?)\s*[–—-]\s*(\d+(?:\.\d+)?)\s*h(?:ours?|r)?", re.I)
HOURS = re.compile(r"(\d+(?:\.\d+)?)\s*h(?:ours?|r|\b)", re.I)
MINUTES = re.compile(r"(\d+(?:\.\d+)?)\s*min(?:utes?)?", re.I)
DAYS = re.compile(r"(\d+(?:\.\d+)?)\s*days?", re.I)


def official_minutes(note: str | None) -> int | None:
    """Read the longest duration mentioned in a free-text official timing note."""
    if not note:
        return None
    candidates: list[float] = []
    for match in HOURS_RANGE.finditer(note):
        candidates.append(max(float(match.group(1)), float(match.group(2))) * 60)
    if not candidates:
        candidates.extend(float(m.group(1)) * 60 for m in HOURS.finditer(note))
    candidates.extend(float(m.group(1)) for m in MINUTES.finditer(note))
    candidates.extend(float(m.group(1)) * 24 * 60 for m in DAYS.finditer(note))
    if not candidates:
        return None
    return int(round(max(candidates)))


def answer_parts(competition_id: str) -> int:
    path = BENCHMARKS / competition_id / "benchmark.json"
    if not path.is_file():
        return 1
    counts = []
    for row in json.loads(path.read_text(encoding="utf-8")):
        gold = row.get("gold_label") or {}
        parts = gold.get("parts") or gold.get("answers") or []
        counts.append(len(parts) if isinstance(parts, list) else 1)
    if not counts:
        return 1
    return max(1, int(statistics.median(counts)))


def turn_budget(team_size: int, minutes: int | None, parts: int) -> tuple[int, int, int]:
    from_clock = math.ceil(minutes / MINUTES_PER_TURN) if minutes else 0
    floor = team_size * SPEAKING_TURNS_PER_TEAMMATE + parts + SYNTHESIS_HEADROOM
    budget = max(MIN_TURNS, min(MAX_TURNS, max(from_clock, floor)))
    return budget, from_clock, floor


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    changed = 0
    for path in sorted(RULES.glob("*.json")):
        if path.name == "schema.json":
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        team_size = int(card["team"]["active_default"])
        note = (card.get("provenance") or {}).get("official_time_note")
        minutes = official_minutes(note)
        parts = answer_parts(card["competition_id"])
        budget, from_clock, floor = turn_budget(team_size, minutes, parts)

        execution = dict(card.get("execution") or {})
        previous = execution.get("max_turns")
        execution["max_turns"] = budget
        execution["official_minutes"] = minutes
        execution["turn_budget_basis"] = (
            f"official clock {from_clock or 'n/a'} turns vs floor {floor} "
            f"({team_size} teammates x {SPEAKING_TURNS_PER_TEAMMATE} turns "
            f"+ {parts} answer parts + {SYNTHESIS_HEADROOM} for synthesis)"
        )
        card["execution"] = execution

        if previous == budget and not args.dry_run:
            continue
        changed += 1
        print(
            f"{card['competition_id']}: {previous} -> {budget} "
            f"(minutes={minutes}, clock={from_clock}, floor={floor}, team={team_size})"
        )
        if not args.dry_run:
            path.write_text(
                json.dumps(card, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )

    print(f"\n{changed} budgets changed" + (" (dry run)" if args.dry_run else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
