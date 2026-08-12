"""Lint every competition rule card in data/rules.

Usage:
    python collectors/lint_rule_cards.py            # report only
    python collectors/lint_rule_cards.py --fix      # apply safe auto-fixes
    python collectors/lint_rule_cards.py --json     # machine-readable report

Exit code is 1 when errors remain, so CI/tests can gate on it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_ROOT = REPO_ROOT / "data" / "rules"
SCHEMA_PATH = RULES_ROOT / "schema.json"

sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from align_deliverables import benchmark_facts  # noqa: E402
from constraint_hygiene import clean_constraints, is_maintainer_text  # noqa: E402
from write_role_duties import BOILERPLATE as BOILERPLATE_DUTIES  # noqa: E402
from env import TOOL_ACTIONS  # noqa: E402
from evaluation.registry import load_registry  # noqa: E402
from rules import RuleCard, RuleCardError  # noqa: E402

NEAR_DUPLICATE_RATIO = 0.86
MIN_CONSTRAINTS = 6

REGISTRY = {spec.id: spec for spec in load_registry()}

# Sentences that describe our own pipeline rather than the contest the agent is in.
META_PATTERNS = (
    re.compile(r"\s*Primary contestant constraints merged from \S+", re.IGNORECASE),
    re.compile(r"\s*Source confidence:\s*\w+\.?", re.IGNORECASE),
    re.compile(r"\s*See\s+docs/\S+", re.IGNORECASE),
    re.compile(r"\s*This is an initial machine-readable[^.]*\.", re.IGNORECASE),
    re.compile(r"\s*Grounded from crawled official source[^.]*\.", re.IGNORECASE),
    re.compile(r"\s*verify against the cited official source[^.]*\.", re.IGNORECASE),
    # Leftover file-extension fragment from an earlier metadata strip.
    re.compile(r"(?<=[a-z])\.md(?=[\s.]|$)"),
    # Bare pipeline field names glued onto the prose by an earlier strip.
    re.compile(
        r"\s*\b(crawled_excerpts|research_notes|proxy_limitations|best_source_urls"
        r"|hard_constraints|official_time_note|rules_text_source)\b\.?",
        re.IGNORECASE,
    ),
)

PLACEHOLDER_PATTERN = re.compile(
    r"Draft rule card for|Tools=\[|Protocol=|Team size default", re.IGNORECASE
)

TOOL_RESOURCE_CONFLICTS = {
    "web_search": ("internet", "forbidden"),
    "use_calculator": ("calculator", "forbidden"),
}


@dataclass
class CardReport:
    competition_id: str
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    fixes: list[str] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return not self.errors and not self.warnings


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower()).strip()


def collapse_spaces(text: str) -> str:
    return re.sub(r"\s{2,}", " ", text).strip()


def schema_keys() -> tuple[set[str], set[str]]:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    return set(schema["properties"]), set(schema["required"])


def dedupe_constraints(
    constraints: list[str], *, ratio_threshold: float = NEAR_DUPLICATE_RATIO
) -> tuple[list[str], list[str]]:
    """Drop exact duplicates and keep the longer of two near-duplicate constraints."""
    kept: list[str] = []
    dropped: list[str] = []
    for candidate in constraints:
        text = collapse_spaces(candidate)
        key = normalize(text)
        replaced = False
        for index, existing in enumerate(kept):
            ratio = SequenceMatcher(None, normalize(existing), key).ratio()
            if ratio < ratio_threshold:
                continue
            if len(text) > len(existing):
                dropped.append(existing)
                kept[index] = text
            else:
                dropped.append(text)
            replaced = True
            break
        if not replaced:
            kept.append(text)
    return kept, dropped


def strip_meta_sentences(text: str) -> str:
    cleaned = text
    for pattern in META_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    return collapse_spaces(cleaned)


def check_deliverable_contract(card: RuleCard, report: CardReport) -> None:
    """The card, the benchmark rows, and the evaluator registry must agree."""
    facts = benchmark_facts(card.competition_id)
    if not facts:
        report.warnings.append("no benchmark rows found for this competition")
        return

    submission = card.raw.get("submission") or {}
    card_tasks = sorted(str(item) for item in submission.get("task_types") or [])
    benchmark_tasks = sorted(facts.get("task_types") or [])
    if card_tasks != benchmark_tasks:
        report.errors.append(
            f"submission.task_types {card_tasks} != benchmark task types "
            f"{benchmark_tasks}; run collectors/align_deliverables.py"
        )

    scoring = card.scoring
    benchmark_evaluator = facts.get("evaluator_id")
    card_evaluator = scoring.get("evaluator_id")
    if benchmark_evaluator and card_evaluator != benchmark_evaluator:
        report.errors.append(
            f"scoring.evaluator_id={card_evaluator!r} but benchmark rows use "
            f"{benchmark_evaluator!r}"
        )
    if not benchmark_evaluator and card_evaluator:
        report.errors.append(
            f"scoring.evaluator_id={card_evaluator!r} but no benchmark row declares one"
        )
    if not card_evaluator:
        report.warnings.append(
            "no evaluator assigned; submissions for this track cannot be graded yet"
        )

    rubric_path = scoring.get("rubric_path")
    if rubric_path and not (REPO_ROOT / rubric_path).is_file():
        report.errors.append(f"scoring.rubric_path does not exist: {rubric_path}")

    if not submission.get("official_deliverable"):
        report.errors.append("submission.official_deliverable is missing")

    official_mimes = set(submission.get("official_mime_types") or [])
    runner_mimes = set(submission.get("mime_types") or [])
    if official_mimes - runner_mimes and not submission.get("adaptation"):
        report.warnings.append(
            "official deliverable is not plain text but no submission.adaptation is recorded"
        )

    spec = REGISTRY.get(str(card_evaluator))
    if spec is not None and official_mimes and not official_mimes & set(spec.submission_mime_types):
        report.warnings.append(
            f"evaluator {spec.id} accepts {list(spec.submission_mime_types)} but the "
            f"official deliverable is {sorted(official_mimes)}"
        )


def lint_card(
    path: Path,
    allowed_keys: set[str],
    required_keys: set[str],
    *,
    fix: bool,
    near_ratio: float = NEAR_DUPLICATE_RATIO,
) -> CardReport:
    competition_id = path.stem
    report = CardReport(competition_id=competition_id)

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.errors.append(f"invalid JSON: {exc}")
        return report

    unknown_keys = sorted(set(payload) - allowed_keys)
    if unknown_keys:
        report.errors.append(f"unknown top-level keys: {', '.join(unknown_keys)}")
    missing_keys = sorted(required_keys - set(payload))
    if missing_keys:
        report.errors.append(f"missing required keys: {', '.join(missing_keys)}")

    try:
        card = RuleCard.from_dict(payload, competition_id=competition_id)
    except RuleCardError as exc:
        report.errors.append(f"rejected by RuleCard.from_dict: {exc}")
        return report

    unknown_tools = sorted(set(card.allowed_tools) - TOOL_ACTIONS)
    if unknown_tools:
        report.errors.append(f"unknown tools: {', '.join(unknown_tools)}")
    if "query_rules" not in card.allowed_tools:
        report.warnings.append("query_rules is not allowed, so agents cannot consult the rule card")

    for tool, (resource, banned_value) in TOOL_RESOURCE_CONFLICTS.items():
        if tool in card.allowed_tools and card.resources.get(resource) == banned_value:
            report.errors.append(f"{tool} allowed but resources.{resource} is {banned_value!r}")

    if card.agent_roles:
        if len(card.agent_roles) != card.team_size_default:
            report.errors.append(
                f"{len(card.agent_roles)} roles but team.active_default="
                f"{card.team_size_default}; env.roster() will raise at default size"
            )
        names = [role.name for role in card.agent_roles]
        if len(names) != len(set(names)):
            report.errors.append("duplicate agent role names")
        if not any(role.may_submit for role in card.agent_roles):
            report.errors.append("no agent role may submit")
        if not any(role.duties for role in card.agent_roles):
            report.warnings.append("no role declares duties")
        boilerplate_roles = [
            role.name for role in card.agent_roles if tuple(role.duties) in BOILERPLATE_DUTIES
        ]
        if boilerplate_roles:
            report.warnings.append(
                f"{len(boilerplate_roles)} roles still carry generated boilerplate duties; "
                "run collectors/write_role_duties.py"
            )

    constraints = list(payload.get("human_constraints") or [])
    deduped, dropped = dedupe_constraints(constraints, ratio_threshold=near_ratio)
    if dropped:
        message = f"{len(dropped)} duplicate/near-duplicate constraints"
        if fix:
            payload["human_constraints"] = deduped
            report.fixes.append(f"removed {len(dropped)} duplicate constraints")
        else:
            report.warnings.append(message + ": " + " | ".join(dropped[:3]))
    if len(deduped) < MIN_CONSTRAINTS:
        report.warnings.append(f"only {len(deduped)} distinct constraints")

    maintainer_text = [item for item in deduped if is_maintainer_text(item)]
    if maintainer_text:
        if fix:
            cleaned, notes = clean_constraints(deduped)
            payload["human_constraints"] = cleaned
            provenance = dict(payload.get("provenance") or {})
            provenance["research_notes"] = notes
            payload["provenance"] = provenance
            report.fixes.append(
                f"moved {len(notes)} maintainer notes out of human_constraints"
            )
        else:
            report.errors.append(
                f"{len(maintainer_text)} binding constraints are maintainer notes: "
                + maintainer_text[0][:90]
            )

    cleaned_rules_text = strip_meta_sentences(card.rules_text)
    if cleaned_rules_text != card.rules_text:
        if fix:
            payload["rules_text"] = cleaned_rules_text
            report.fixes.append("removed pipeline metadata from rules_text")
        else:
            report.warnings.append("rules_text contains pipeline metadata, not contest rules")

    if PLACEHOLDER_PATTERN.search(cleaned_rules_text):
        report.warnings.append(
            "rules_text is a generated placeholder; run collectors/rewrite_rules_text.py"
        )

    if not card.answer_format:
        report.warnings.append("answer_format is empty")

    check_deliverable_contract(card, report)

    sources = card.provenance.get("sources") or []
    if not sources:
        report.warnings.append("no provenance sources")
    else:
        without_url = [item for item in sources if not str(item.get("url") or "").startswith("http")]
        if without_url:
            report.warnings.append(f"{len(without_url)} provenance sources without an http url")

    confidence = card.provenance.get("research_confidence")
    if confidence not in {"high", "medium", "low"}:
        report.warnings.append(f"research_confidence missing or invalid: {confidence!r}")

    if card.profile == "proxy" and not card.provenance.get("proxy_limitations"):
        report.warnings.append("profile is proxy but proxy_limitations is empty")

    if fix and report.fixes:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="apply safe auto-fixes in place")
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument("--strict", action="store_true", help="treat warnings as failures")
    parser.add_argument(
        "--near-ratio",
        type=float,
        default=NEAR_DUPLICATE_RATIO,
        help="similarity threshold for near-duplicate constraints",
    )
    args = parser.parse_args()

    allowed_keys, required_keys = schema_keys()
    reports = [
        lint_card(path, allowed_keys, required_keys, fix=args.fix, near_ratio=args.near_ratio)
        for path in sorted(RULES_ROOT.glob("*.json"))
        if path.name != "schema.json"
    ]

    if args.json:
        print(
            json.dumps(
                [
                    {
                        "competition_id": item.competition_id,
                        "errors": item.errors,
                        "warnings": item.warnings,
                        "fixes": item.fixes,
                    }
                    for item in reports
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for item in reports:
            if item.clean and not item.fixes:
                continue
            print(item.competition_id)
            for message in item.errors:
                print(f"  ERROR   {message}")
            for message in item.warnings:
                print(f"  WARN    {message}")
            for message in item.fixes:
                print(f"  FIXED   {message}")

    error_count = sum(len(item.errors) for item in reports)
    warning_count = sum(len(item.warnings) for item in reports)
    print(
        f"\n{len(reports)} cards checked: {error_count} errors, {warning_count} warnings"
    )
    if error_count:
        return 1
    return 1 if args.strict and warning_count else 0


if __name__ == "__main__":
    raise SystemExit(main())
