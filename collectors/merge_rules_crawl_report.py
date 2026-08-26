"""Merge a rules research report's hard constraints into the rule-card store.

The report is a markdown file containing one fenced ```json block shaped like:

    {"competitions": {"<competition_id>": {
        "best_source_urls": [...], "hard_constraints": [...],
        "confidence": "high|medium|low", "proxy_limitations": [...],
        "notes": [...]}}}

Usage:
    python collectors/merge_rules_crawl_report.py
    python collectors/merge_rules_crawl_report.py --report docs/rules_lowconf_2026-08-12.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from constraint_hygiene import clean_constraints
from lint_rule_cards import dedupe_constraints, strip_meta_sentences

REPO = Path(__file__).resolve().parents[1]
DEFAULT_REPORT = REPO / "docs" / "rules_crawl_2026-08-11.md"
RULES = REPO / "data" / "rules"
sys.path.insert(0, str(REPO / "src"))

from rules import load_rule_card_payload, write_rule_card_payload  # noqa: E402


def load_report(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    if not match:
        raise SystemExit(f"Could not find a JSON block in {path}")
    return json.loads(match.group(1))


def merge_constraints(existing: list[str], incoming: list[str]) -> tuple[list[str], list[str]]:
    """Split maintainer notes off first: a bullet only collapses onto its stored
    twin once both have been reduced to their contestant-binding clause."""
    candidates = [str(item).strip() for item in existing + incoming if str(item).strip()]
    contestant, notes = clean_constraints(candidates)
    kept, _ = dedupe_constraints(contestant)
    return kept, notes


def contest_rules_text(current: str, official_time_note: str | None) -> str:
    """Keep rules_text contest-facing: official prose plus the official timing note."""
    base = strip_meta_sentences(current)
    note = str(official_time_note or "").strip().rstrip(".")
    if note and "Official timing note:" not in base:
        base = f"{base} Official timing note: {note}."
    return re.sub(r"\s{2,}", " ", base).strip()


def append_unique(existing: list, incoming: list) -> list:
    out = list(existing)
    for item in incoming:
        if item and item not in out:
            out.append(item)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = REPO / report_path
    report_ref = str(report_path.relative_to(REPO)).replace("\\", "/")

    report = load_report(report_path)
    report_date = str(report.get("report_date") or report.get("crawl_date") or "")
    competitions = report.get("competitions") or {}
    updated = 0
    for cid, payload in competitions.items():
        card = load_rule_card_payload(cid, rules_root=RULES)
        if card is None:
            print(f"skip missing card: {cid}")
            continue

        # An entry a later report retracted must not come back when the older
        # report is replayed.
        superseded_by = payload.get("superseded_by")
        if superseded_by and (REPO / superseded_by).exists():
            print(f"skip {cid}: superseded by {superseded_by}")
            continue

        original = json.dumps(card, ensure_ascii=False, sort_keys=True)

        hard = [str(x).strip() for x in (payload.get("hard_constraints") or []) if str(x).strip()]
        contestant_rules, research_notes = merge_constraints(
            list(card.get("human_constraints") or []), hard
        )
        card["human_constraints"] = contestant_rules

        provenance = dict(card.get("provenance") or {})
        external_manifest = bool(provenance.get("manifest"))
        sources = list(provenance.get("sources") or [])
        seen = {s.get("url") for s in sources if s.get("url")}
        if not external_manifest:
            for url in payload.get("best_source_urls") or []:
                if url and url not in seen:
                    sources.append(
                        {
                            "title": url,
                            "url": url,
                            "retrieved_at": datetime.now(timezone.utc).date().isoformat(),
                            "from_report": report_ref,
                        }
                    )
                    seen.add(url)
            provenance["sources"] = sources
            provenance["research_reports"] = append_unique(
                provenance.get("research_reports") or [], [report_ref]
            )
            provenance.pop("research_report", None)
        # Constraints accumulate across reports, but confidence is a verdict: replaying
        # an older report must not undo a newer pass's upgrade.
        if not external_manifest and report_date >= str(
            provenance.get("research_graded_at") or ""
        ):
            provenance["research_confidence"] = payload.get("confidence")
            provenance["proxy_limitations"] = payload.get("proxy_limitations") or []
            provenance["research_graded_at"] = report_date
        # Notes accumulate like constraints: a note this report did not restate was
        # still earned by an earlier one, and dropping it makes the two merges
        # oscillate against each other.
        notes = append_unique(list(provenance.get("research_notes") or []), research_notes)
        notes = append_unique(notes, payload.get("notes") or [])
        if not external_manifest:
            if notes:
                provenance["research_notes"] = notes
            else:
                provenance.pop("research_notes", None)
        card["provenance"] = provenance

        card["rules_text"] = contest_rules_text(
            str(card.get("rules_text") or ""), provenance.get("official_time_note")
        )

        # A replay that changes nothing should leave the file alone, so a real diff
        # stays visible in review.
        previous_merge = provenance.get("research_merged_at")
        if not external_manifest:
            provenance["research_merged_at"] = previous_merge
        if json.dumps(card, ensure_ascii=False, sort_keys=True) == original:
            continue
        if not external_manifest:
            provenance["research_merged_at"] = datetime.now(timezone.utc).isoformat()

        write_rule_card_payload(cid, card, rules_root=RULES)
        updated += 1
        print(
            f"{cid}: constraints={len(card['human_constraints'])} "
            f"notes={len(notes)} confidence={payload.get('confidence')}"
        )
    print(f"updated {updated} cards from {report_ref}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
