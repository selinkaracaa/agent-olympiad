"""Configure pressure-aware coordination rules for suitable team competitions.

Each mechanism has its own curated allow-list. Rule specialization, structured
deliberation, and communication scarcity are not interchangeable: a contest may
benefit from one while another would distort its official collaboration model.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
sys.path.insert(0, str(REPO / "src"))

from rules import describe_resources  # noqa: E402


FIRST_WAVE = {
    "cfa_research_challenge",
    "gcch_harvard",
    "ieo_business_case",
    "wharton_investment",
    "wsc_writing",
}
ROLE_SPECIALIZED = FIRST_WAVE | {
    "arml_local",
    "arml_national_power",
    "arml_national_team",
    "arml_power",
    "ccdc",
    "eoes",
    "ethics_bowl_appe",
    "ethics_bowl_nhseb",
    "fyziklani",
    "hmmt_guts",
    "ichto",
    "icpc",
    "iiot",
    "ijso_practical",
    "ioaa_group",
    "ioai_team",
    "iol_team",
    "jessup",
    "mystery_hunt",
    "odyssey_of_the_mind",
    "pumac_power",
    "purple_comet",
    "vis_moot",
    "wmtc",
    "wro",
}
STRUCTURED_DELIBERATION = FIRST_WAVE | {
    "arml_local",
    "arml_national_power",
    "arml_national_team",
    "arml_power",
    "eoes",
    "ethics_bowl_appe",
    "ethics_bowl_nhseb",
    "ichto",
    "icpc",
    "iiot",
    "ijso_practical",
    "ioaa_group",
    "ioai_team",
    "iol_team",
    "jessup",
    "odyssey_of_the_mind",
    "pumac_power",
    "purple_comet",
    "vis_moot",
    "wmtc",
}
COMMUNICATION_BUDGETS = {
    "arml_local": (18, 3, 1200),
    "arml_national_power": (30, 2, 1200),
    "arml_national_team": (30, 2, 1200),
    "arml_power": (30, 2, 1200),
    "cfa_research_challenge": (10, 3, 1200),
    "ethics_bowl_appe": (10, 3, 1000),
    "ethics_bowl_nhseb": (10, 3, 1000),
    "fyziklani": (20, 4, 1200),
    "gcch_harvard": (10, 3, 1200),
    "hmmt_guts": (16, 3, 1200),
    "ieo_business_case": (12, 3, 1200),
    "ioaa_group": (16, 3, 1200),
    "iol_team": (18, 4, 1200),
    "jessup": (10, 3, 1200),
    "purple_comet": (18, 4, 1200),
    "vis_moot": (10, 3, 1200),
    "wharton_investment": (12, 3, 1200),
    "wmtc": (16, 3, 1200),
    "wsc_writing": (8, 3, 1200),
}
COUNTED_ACTIONS = [
    "speak",
    "write_scratchpad",
    "propose",
    "challenge",
    "provide_evidence",
    "revise",
    "decide",
]
ROLE_NOTE = "role-specific rule expertise is a benchmark coordination overlay"
DELIBERATION_NOTE = (
    "structured deliberation actions are a benchmark traceability overlay"
)
COMMUNICATION_NOTE = (
    "limited communication is a benchmark pressure overlay, not an official message cap"
)

ROLE_OVERRIDES = {
    "iol_team": [
        ("captain and synthesizer", ["Track timing and submission.", "Synthesize the final linguistic explanation."]),
        ("data-pattern analyst", ["Infer patterns from the language data.", "State candidate mappings explicitly."]),
        ("hypothesis tester", ["Search for counterexamples to proposed mappings.", "Challenge unsupported generalizations."]),
        ("verifier and explanation editor", ["Check every form against the hypothesis.", "Make the final explanation complete and readable."]),
    ],
    "ioaa_group": [
        ("captain and synthesizer", ["Allocate the astronomy task and track timing.", "Own the final shared answer."]),
        ("observational data analyst", ["Extract reliable quantities from provided observations.", "Track units and uncertainty."]),
        ("physics and modeling specialist", ["Build the physical model and assumptions.", "Connect equations to the observed system."]),
        ("numerical verifier", ["Recompute numerical results independently.", "Check scales, units, and significant figures."]),
        ("report editor", ["Assemble a coherent solution.", "Check required plots, tables, and answer format."]),
    ],
    "ioai_team": [
        ("captain and submission lead", ["Track task-specific rules and submission requirements.", "Resolve model-selection disagreements."]),
        ("data and modeling specialist", ["Prepare data and candidate models.", "State modeling assumptions."]),
        ("experiment and evaluation specialist", ["Design comparisons and inspect metrics.", "Guard hidden-test integrity."]),
        ("tool and provenance lead", ["Track allowed tools and websites.", "Record sources and reproducibility details."]),
    ],
    "wro": [
        ("captain and rules lead", ["Track season, category, timing, and field rules.", "Coordinate the final run strategy."]),
        ("hardware builder", ["Track construction and materials constraints.", "Own mechanical reliability checks."]),
        ("programmer and run analyst", ["Track controller and software rules.", "Analyze test runs and field scoring."]),
    ],
    "ichto": [
        ("reporter", ["Present and defend the team solution.", "Track reporter speaking and response clocks."]),
        ("opponent", ["Identify the central weakness in another solution.", "Lead opposition and discussion within the role rules."]),
        ("reviewer", ["Compare report and opposition fairly.", "Apply review criteria and summarize unresolved issues."]),
    ],
}

SECTION_PATTERNS = {
    "timeline": re.compile(
        r"\b(time|minute|hour|day|deadline|late|round|stage|batch|before|after|"
        r"progressive|submit by|lock)\b",
        re.IGNORECASE,
    ),
    "resource_policy": re.compile(
        r"\b(calculator|internet|code|software|device|phone|computer|laptop|"
        r"material|note|paper|pencil|tool|equipment|reference)\b",
        re.IGNORECASE,
    ),
    "research_integrity": re.compile(
        r"\b(plagiarism|outside|advisor|mentor|source|cite|citation|copyright|"
        r"generative ai|answer key|hidden solution|contact)\b",
        re.IGNORECASE,
    ),
    "collaboration_protocol": re.compile(
        r"\b(team|collaborat|confer|communicat|captain|member|active player|"
        r"opponent|speaker|driver|navigator)\b",
        re.IGNORECASE,
    ),
    "deliverable_format": re.compile(
        r"\b(answer|report|deck|slide|presentation|write|essay|oral|format|"
        r"artifact|submission|flag|source code|pitch|memorandum)\b",
        re.IGNORECASE,
    ),
    "evaluation_criteria": re.compile(
        r"\b(score|point|judge|penalty|award|win|grade|rubric|rank|correct|"
        r"evaluate|criterion|criteria)\b",
        re.IGNORECASE,
    ),
}


def append_unique(values: list[str], additions: list[str]) -> list[str]:
    result = list(values)
    for item in additions:
        if item not in result:
            result.append(item)
    return result


def build_rule_sections(card: dict[str, Any]) -> dict[str, list[str]]:
    existing = card.get("rule_sections") or {}
    if existing:
        return existing

    sections: dict[str, list[str]] = {}
    constraints = [str(item) for item in card.get("human_constraints") or []]
    for category, pattern in SECTION_PATTERNS.items():
        matches = [item for item in constraints if pattern.search(item)]
        if matches:
            sections[category] = matches

    resources = describe_resources(card.get("resources") or {})
    if resources:
        sections["resource_policy"] = append_unique(
            sections.get("resource_policy", []), [resources]
        )

    answer_format = str(card.get("answer_format") or "").strip()
    if answer_format:
        sections["deliverable_format"] = append_unique(
            sections.get("deliverable_format", []), [answer_format]
        )

    time_note = str((card.get("provenance") or {}).get("official_time_note") or "").strip()
    if time_note:
        sections["timeline"] = append_unique(
            sections.get("timeline", []), [time_note]
        )

    if "collaboration_protocol" not in sections:
        collaboration = str((card.get("team") or {}).get("collaboration") or "").strip()
        sections["collaboration_protocol"] = [
            collaboration or "Coordinate only with registered teammates."
        ]
    return sections


def preferred_expertise(title: str) -> list[str]:
    lowered = title.lower()
    if any(word in lowered for word in ("captain", "lead", "strategy", "splitter")):
        return ["timeline", "collaboration_protocol", "deliverable_format"]
    if any(word in lowered for word in ("writer", "scribe", "note-taker", "editor")):
        return ["deliverable_format", "evaluation_criteria"]
    if any(word in lowered for word in ("verifier", "tester", "checker", "judge")):
        return ["evaluation_criteria", "deliverable_format"]
    if any(word in lowered for word in ("research", "reference", "opponent prep")):
        return ["research_integrity", "resource_policy"]
    if any(
        word in lowered
        for word in (
            "driver",
            "navigator",
            "modeler",
            "analysis",
            "calculation",
            "data recorder",
            "forensics",
            "pwn",
            "reverse",
            "web / crypto",
        )
    ):
        return ["resource_policy", "deliverable_format"]
    if any(word in lowered for word in ("oralist", "speaker", "question")):
        return ["collaboration_protocol", "evaluation_criteria"]
    return []


def assign_expertise(card: dict[str, Any], sections: dict[str, list[str]]) -> None:
    available = list(sections)
    for index, role in enumerate(card.get("agent_roles") or []):
        access = list(role.get("information_access") or [])
        role["information_access"] = append_unique(access, ["contest_rules"])
        if role.get("rule_expertise"):
            continue
        preferred = preferred_expertise(str(role.get("title") or ""))
        expertise = [category for category in preferred if category in sections]
        if not expertise and available:
            expertise = [available[index % len(available)]]
        role["rule_expertise"] = expertise


def apply_role_overrides(card: dict[str, Any]) -> None:
    overrides = ROLE_OVERRIDES.get(card["competition_id"])
    if not overrides:
        return
    roles = card.get("agent_roles") or []
    if len(roles) != len(overrides):
        raise ValueError(
            f"{card['competition_id']} has {len(roles)} roles, "
            f"but {len(overrides)} overrides"
        )
    for role, (title, duties) in zip(roles, overrides):
        role["title"] = title
        role["duties"] = duties
        role.pop("rule_expertise", None)


def remove_overlay_note(provenance: dict[str, Any], note: str) -> None:
    adaptations = [
        item for item in provenance.get("adaptations") or [] if item != note
    ]
    if adaptations:
        provenance["adaptations"] = adaptations
    else:
        provenance.pop("adaptations", None)


def configure(card: dict[str, Any]) -> dict[str, Any]:
    competition_id = card["competition_id"]
    apply_role_overrides(card)
    provenance = dict(card.get("provenance") or {})
    comparability = dict(card.get("comparability") or {})
    dimensions = dict(comparability.get("dimensions") or {})

    if competition_id in ROLE_SPECIALIZED:
        sections = build_rule_sections(card)
        card["rule_sections"] = sections
        assign_expertise(card, sections)
        policy = dict(card.get("information_policy") or {})
        policy["mode"] = "role_specialized"
        policy["shared"] = [
            "problem",
            "contest_rules",
            "team_discussion",
            "scratchpad",
        ]
        policy["coordination_requirement"] = (
            "All teammates may consult the complete rules, but each role must "
            "track and communicate its assigned rule sections."
        )
        card["information_policy"] = policy
        provenance["adaptations"] = append_unique(
            list(provenance.get("adaptations") or []), [ROLE_NOTE]
        )
    else:
        card.pop("information_policy", None)
        card.pop("rule_sections", None)
        for role in card.get("agent_roles") or []:
            role.pop("information_access", None)
            role.pop("rule_expertise", None)
        remove_overlay_note(provenance, ROLE_NOTE)

    if competition_id in STRUCTURED_DELIBERATION:
        card["deliberation"] = {
            "mode": "structured",
            "min_challenges": 1,
            "decision_maker": "submitter",
            "evaluation_dimensions": [
                "evidence_responsiveness",
                "revision_after_challenge",
                "decision_traceability",
                "authority_bias",
                "majority_bias",
            ],
        }
        provenance["adaptations"] = append_unique(
            list(provenance.get("adaptations") or []), [DELIBERATION_NOTE]
        )
        dimensions["deliberation"] = "structured_trace_overlay"
    else:
        card.pop("deliberation", None)
        remove_overlay_note(provenance, DELIBERATION_NOTE)
        dimensions.pop("deliberation", None)

    if competition_id in COMMUNICATION_BUDGETS:
        team_budget, per_agent_budget, max_chars = COMMUNICATION_BUDGETS[
            competition_id
        ]
        card["communication"] = {
            "mode": "limited",
            "team_message_budget": team_budget,
            "per_agent_message_budget": per_agent_budget,
            "max_message_chars": max_chars,
            "counted_actions": COUNTED_ACTIONS,
        }
        provenance["adaptations"] = append_unique(
            list(provenance.get("adaptations") or []), [COMMUNICATION_NOTE]
        )
        dimensions["communication"] = "adapted_coordination_budget"
    else:
        card.pop("communication", None)
        remove_overlay_note(provenance, COMMUNICATION_NOTE)
        dimensions.pop("communication", None)

    card["provenance"] = provenance
    comparability["dimensions"] = dimensions
    card["comparability"] = comparability
    return card


def main() -> int:
    changed = 0
    for path in sorted(RULES.glob("*.json")):
        if path.name == "schema.json":
            continue
        card = json.loads(path.read_text(encoding="utf-8"))
        before = json.dumps(card, ensure_ascii=False, sort_keys=True)
        configure(card)
        after = json.dumps(card, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        path.write_text(
            json.dumps(card, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        changed += 1
        print(card["competition_id"])
    print(
        f"updated {changed} cards; role-specialized={len(ROLE_SPECIALIZED)}, "
        f"deliberation={len(STRUCTURED_DELIBERATION)}, "
        f"limited-communication={len(COMMUNICATION_BUDGETS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
