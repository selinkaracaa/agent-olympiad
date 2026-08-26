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
from rules import (  # noqa: E402
    SIMULATION_OWNED_KEYS,
    RuleCard,
    RuleCardError,
    RuleCardStorageError,
    iter_rule_card_ids,
    load_rule_card_payload,
    write_rule_card_payload,
)

NEAR_DUPLICATE_RATIO = 0.86
MIN_CONSTRAINTS = 6
CONTENT_STANDARD_NAME = "icpc_three_component_content_standard"
CONTENT_STANDARD_SECTIONS = {
    "competition_format",
    "timeline",
    "resource_policy",
    "collaboration_protocol",
    "integrity_and_compliance",
    "deliverable_format",
    "evaluation_criteria",
    "runtime_limitations",
}
CONTENT_STANDARD_SCORING = {
    "official_performance",
    "rule_compliance",
    "collaboration_quality",
    "current_repository_availability",
}
SOURCE_COVERAGE_GRADES = {"A", "B", "C", "D"}
SOURCE_METADATA_FIELDS = {
    "title",
    "url",
    "authority",
    "edition",
    "sections",
    "archive_status",
}

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

    deliverable = card.deliverable
    submission = card.submission
    card_tasks = sorted(str(item) for item in deliverable.get("task_types") or [])
    benchmark_tasks = sorted(facts.get("task_types") or [])
    if card_tasks != benchmark_tasks:
        report.errors.append(
            f"deliverable.task_types {card_tasks} != benchmark task types "
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

    if not deliverable.get("official_deliverable"):
        report.errors.append("deliverable.official_deliverable is missing")

    official_mimes = set(deliverable.get("official_mime_types") or [])
    runner_mimes = set(deliverable.get("mime_types") or [])
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
    competition_id: str,
    allowed_keys: set[str],
    required_keys: set[str],
    *,
    fix: bool,
    near_ratio: float = NEAR_DUPLICATE_RATIO,
) -> CardReport:
    report = CardReport(competition_id=competition_id)

    try:
        payload = load_rule_card_payload(
            competition_id,
            rules_root=RULES_ROOT,
            required=True,
        )
    except (FileNotFoundError, RuleCardStorageError) as exc:
        report.errors.append(str(exc))
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

    if not card.agent_constraints:
        report.errors.append("agent_constraints is empty")
    if not card.evaluation_guidance:
        report.errors.append("evaluation_guidance is empty")
    execution_keys = set((payload.get("execution") or {}))
    leaked_simulation = sorted(execution_keys & SIMULATION_OWNED_KEYS)
    if leaked_simulation:
        report.errors.append(
            "competition.execution still owns simulation fields: "
            + ", ".join(leaked_simulation)
        )
    if "max_turns" not in (payload.get("simulation") or {}):
        report.errors.append("collaboration.simulation.max_turns is missing")
    visible_text = " ".join(
        [
            card.rules_text,
            *card.human_constraints,
            str((card.information_policy or {}).get("coordination_requirement") or ""),
        ]
    ).lower()
    for needle in (
        "evaluation_guidance",
        "rubric_path",
        "evaluator_id",
        "evaluator_status",
    ):
        if needle in visible_text:
            report.errors.append(
                f"agent-visible contest text mentions hidden eval field {needle}"
            )
    missing_scoring = sorted(CONTENT_STANDARD_SCORING - set(card.scoring))
    if missing_scoring:
        report.errors.append(
            "scoring is missing content-standard sections: "
            + ", ".join(missing_scoring)
        )
    if competition_id != "icpc":
        missing_sections = sorted(CONTENT_STANDARD_SECTIONS - set(card.rule_sections))
        if missing_sections:
            report.errors.append(
                "rule_sections is missing content-standard sections: "
                + ", ".join(missing_sections)
            )
        standard = card.provenance.get("content_standard") or {}
        if standard.get("name") != CONTENT_STANDARD_NAME:
            report.errors.append(
                "provenance.content_standard does not declare the ICPC-level contract"
            )
        source_review = card.provenance.get("source_review") or {}
        if source_review.get("coverage_grade") not in SOURCE_COVERAGE_GRADES:
            report.errors.append(
                "provenance.source_review is missing a valid A-D coverage grade"
            )
        if not source_review.get("completion_status"):
            report.errors.append(
                "provenance.source_review.completion_status is missing"
            )
        if not source_review.get("audit_report"):
            report.errors.append("provenance.source_review.audit_report is missing")

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
        incomplete_access = [
            role.name
            for role in card.agent_roles
            if set(role.information_access) != {"contest_rules"}
        ]
        if incomplete_access:
            report.errors.append(
                "roles lack the complete public contest view: "
                + ", ".join(incomplete_access)
            )
        boilerplate_roles = [
            role.name for role in card.agent_roles if tuple(role.duties) in BOILERPLATE_DUTIES
        ]
        if boilerplate_roles:
            report.warnings.append(
                f"{len(boilerplate_roles)} roles still carry generated boilerplate duties; "
                "run collectors/write_role_duties.py"
            )
        if card.information_policy.get("mode") == "role_scoped":
            access_sets = {role.information_access for role in card.agent_roles}
            if len(access_sets) < 2:
                report.errors.append(
                    "role-scoped information policy gives every role the same access"
                )
            if not any(
                "contest_rules" in role.information_access
                for role in card.agent_roles
            ):
                report.errors.append(
                    "role-scoped information policy has no contest-rules holder"
                )
            if not card.information_policy.get("coordination_requirement"):
                report.errors.append(
                    "role-scoped information policy needs a coordination_requirement"
                )
        if card.information_policy.get("mode") == "role_specialized":
            if any(
                "contest_rules" not in role.information_access
                for role in card.agent_roles
            ):
                report.errors.append(
                    "role-specialized policy must let every role consult contest rules"
                )
            expertise_sets = {role.rule_expertise for role in card.agent_roles}
            if len(expertise_sets) < 2:
                report.errors.append(
                    "role-specialized policy gives every role the same rule expertise"
                )
            section_names = set(card.rule_sections)
            unknown_expertise = sorted(
                {
                    category
                    for role in card.agent_roles
                    for category in role.rule_expertise
                    if category not in section_names
                }
            )
            if unknown_expertise:
                report.errors.append(
                    "rule expertise references missing sections: "
                    + ", ".join(unknown_expertise)
                )
            if not card.information_policy.get("coordination_requirement"):
                report.errors.append(
                    "role-specialized information policy needs a "
                    "coordination_requirement"
                )
        if card.deliberation.get("mode") == "structured":
            if len(card.agent_roles) < 2:
                report.errors.append(
                    "structured deliberation requires at least two roles"
                )
            if int(card.deliberation.get("min_challenges", 0)) < 1:
                report.errors.append(
                    "structured deliberation must require at least one challenge"
                )
            if card.deliberation.get("decision_maker") != "submitter":
                report.errors.append(
                    "structured deliberation decision_maker must be submitter"
                )
            dimensions = set(
                card.deliberation.get("evaluation_dimensions") or []
            )
            if not {
                "evidence_responsiveness",
                "decision_traceability",
            }.issubset(dimensions):
                report.errors.append(
                    "structured deliberation must evaluate evidence responsiveness "
                    "and decision traceability"
                )
        if card.communication.get("mode") == "limited":
            required_budget_fields = {
                "team_message_budget",
                "per_agent_message_budget",
                "max_message_chars",
                "counted_actions",
            }
            missing_budget_fields = sorted(
                required_budget_fields - set(card.communication)
            )
            if missing_budget_fields:
                report.errors.append(
                    "limited communication missing fields: "
                    + ", ".join(missing_budget_fields)
                )
            counted = set(card.communication.get("counted_actions") or [])
            if "speak" not in counted or "write_scratchpad" not in counted:
                report.errors.append(
                    "limited communication must count speak and write_scratchpad"
                )
            if card.deliberation.get("mode") == "structured" and not {
                "propose",
                "challenge",
                "provide_evidence",
                "revise",
                "decide",
            }.issubset(counted):
                report.errors.append(
                    "structured deliberation actions must consume communication budget"
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

    manifest_ref = str(card.provenance.get("manifest") or "").strip()
    manifest: dict = {}
    if manifest_ref:
        manifest_path = REPO_ROOT / manifest_ref
        if not manifest_path.is_file():
            report.errors.append(
                f"provenance.manifest does not exist: {manifest_ref}"
            )
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                report.errors.append(
                    f"provenance.manifest is invalid JSON: {exc}"
                )
    sources = (
        manifest.get("sources") or []
        if manifest_ref
        else card.provenance.get("sources") or []
    )
    if not sources:
        report.warnings.append("no provenance sources")
    else:
        without_url = [item for item in sources if not str(item.get("url") or "").startswith("http")]
        if without_url:
            report.warnings.append(f"{len(without_url)} provenance sources without an http url")
        incomplete_metadata = [
            (index, sorted(SOURCE_METADATA_FIELDS - set(item)))
            for index, item in enumerate(sources)
            if SOURCE_METADATA_FIELDS - set(item)
        ]
        if incomplete_metadata:
            details = "; ".join(
                f"source[{index}] missing {','.join(missing)}"
                for index, missing in incomplete_metadata[:3]
            )
            report.errors.append("incomplete source metadata: " + details)
        unresolved_authority = sum(
            1 for item in sources if item.get("authority") == "unclassified"
        )
        unresolved_editions = sum(
            1 for item in sources if item.get("edition") == "not_frozen"
        )
        without_sections = sum(
            1 for item in sources if not item.get("sections")
        )
        if unresolved_authority:
            report.warnings.append(
                f"{unresolved_authority} provenance source authorities remain unclassified"
            )
        if unresolved_editions:
            report.warnings.append(
                f"{unresolved_editions} provenance source editions remain unfrozen"
            )
        if without_sections:
            report.warnings.append(
                f"{without_sections} provenance sources still lack section/page locators"
            )

    confidence = card.provenance.get("research_confidence") or (
        manifest.get("research") or {}
    ).get("confidence")
    if confidence not in {"high", "medium", "low"}:
        report.warnings.append(f"research_confidence missing or invalid: {confidence!r}")

    if card.profile == "proxy" and not card.provenance.get("proxy_limitations"):
        report.warnings.append("profile is proxy but proxy_limitations is empty")

    if fix and report.fixes:
        write_rule_card_payload(
            competition_id,
            payload,
            rules_root=RULES_ROOT,
        )

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
        lint_card(
            competition_id,
            allowed_keys,
            required_keys,
            fix=args.fix,
            near_ratio=args.near_ratio,
        )
        for competition_id in iter_rule_card_ids(RULES_ROOT)
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
