"""Apply the ICPC-level three-component content contract to rule cards.

ICPC is the reference for completeness, not a source of facts for other
competitions.  This collector keeps every competition's existing official facts,
roles, resources, evaluator metadata, provenance, and comparability decisions,
then makes the operational and evaluation layers equally explicit.

Usage:
    python collectors/standardize_rule_card_content.py --dry-run
    python collectors/standardize_rule_card_content.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
INDEX = REPO / "data" / "benchmarks" / "index.json"
sys.path.insert(0, str(REPO / "src"))

from rules import (  # noqa: E402
    describe_resources,
    iter_rule_card_ids,
    load_rule_card_payload,
    write_rule_card_payload,
)

from configure_coordination_rules import (  # noqa: E402
    COMMUNICATION_BUDGETS,
    COUNTED_ACTIONS,
    COMMUNICATION_NOTE,
    DELIBERATION_NOTE,
    ROLE_NOTE,
    ROLE_SPECIALIZED,
    STRUCTURED_DELIBERATION,
    append_unique,
    preferred_expertise,
)


STANDARD_NAME = "icpc_three_component_content_standard"
STANDARD_VERSION = "1.1"
STANDARD_DATE = "2026-08-17"
HAND_AUTHORED_ICPC_QUALITY = frozenset(
    {
        "icpc",
        "arml_local",
        "arml_national_team",
        "arml_national_power",
        "arml_power",
        "fyziklani",
        "hmmt_guts",
        "iiot",
        "ioaa_group",
        "iol_team",
        "pumac_power",
        "purple_comet",
        "wmtc",
    }
)
STANDARD_RULE_SECTIONS = (
    "competition_format",
    "timeline",
    "resource_policy",
    "collaboration_protocol",
    "integrity_and_compliance",
    "deliverable_format",
    "evaluation_criteria",
    "runtime_limitations",
)
GENERATED_SCORING_KEYS = {
    "competition_specific_criteria",
    "official_performance",
    "rule_compliance",
    "collaboration_quality",
    "current_repository_availability",
}
SIMULATION_BOILERPLATE = {
    "You must behave like a human teammate under official contest rules.",
    "Do not claim tools, internet, or materials that the rule card forbids.",
    "Do not look up answer keys or hidden solutions.",
}
NON_BINDING_CONSTRAINTS = {
    "arml_local": {
        "Also Individual (5×10 min pairs) and Relay (6/8/10 min structures) — benchmark track focuses on team round.",
    },
    "ccdc": {
        "Cyber defense scenario brief / team packet only in this dataset.",
        "Live injects and full range VMs are not fully available; mark proxy limits.",
        "Benchmark materials are Team Packets / Wildcard scenario briefs only — live VMs/injects excluded by collection strategy.",
    },
    "cybench": {
        "Research benchmark of professional CTF tasks for agent evaluation; constraints are benchmark harness rules, not a governing olympiad statute.",
    },
    "debatebench": {
        "Benchmark is a cleaned British Parliamentary debate corpus, not itself a governing body.",
        "Repo provenance currently points at Hugging Face datasets — treat as benchmark-native, not official regulations.",
    },
    "ethics_bowl_nhseb": {
        "Competition uses case-based oral ethics bowl format (same family as APPE); detailed timing/roster rules live in NHSEB competition rules (not fully fetched from case-library page).",
    },
    "fyziklani": {
        "Note: in-person Fyziklání forbids internet; this benchmark follows the online ruleset.",
    },
    "mystery_hunt": {
        "Benchmark is question-level puzzle subsample with answers, not a full hunt.",
    },
    "nyu_ctf_bench": {
        "Benchmark packaging of CSAW CTF challenges for LLM agents — not CSAW’s live contest rulebook.",
    },
    "qanta": {
        "QANTA is a research quiz-bowl dataset/project; not a live tournament rulebook.",
        "Benchmark rows are question-level (eval_unit=question), not full matches.",
    },
    "science_bowl": {
        "Benchmark is HS question-level subsample, not full timed matches.",
    },
    "science_olympiad": {
        "Event-specific rules manuals are membership-locked — free sample exams only in this repo’s collection strategy.",
    },
    "wmtc": {
        "Dedicated Rules page fetch returned an embedded ‘WMTC Rules Test’ loader without extractable regulation text — treat detailed calculator/device bans as not retrieved.",
    },
    "wro": {
        "Robot construction and run scoring are physical; software is a proxy unless a simulator exists.",
    },
}

SECTION_PATTERNS = {
    "timeline": re.compile(
        r"\b(time|minute|hour|day|deadline|late|round|stage|batch|before|after|"
        r"progressive|submit by|lock|freeze|halftime|overtime)\b",
        re.IGNORECASE,
    ),
    "resource_policy": re.compile(
        r"\b(calculator|internet|code|software|device|phone|computer|laptop|"
        r"material|note|paper|pencil|tool|equipment|reference|robot|machine)\b",
        re.IGNORECASE,
    ),
    "collaboration_protocol": re.compile(
        r"\b(team|collaborat|confer|communicat|captain|member|active player|"
        r"opponent|speaker|driver|navigator|submitter|writer|teammate)\b",
        re.IGNORECASE,
    ),
    "integrity_and_compliance": re.compile(
        r"\b(plagiarism|outside|advisor|mentor|source|cite|citation|copyright|"
        r"generative ai|answer key|hidden solution|disqualif|forbidden|"
        r"prohibited|unauthorized|assistance)\b",
        re.IGNORECASE,
    ),
    "deliverable_format": re.compile(
        r"\b(answer|report|deck|slide|presentation|write|essay|oral|format|"
        r"artifact|submission|flag|source code|pitch|memorandum|proof)\b",
        re.IGNORECASE,
    ),
    "evaluation_criteria": re.compile(
        r"\b(score|point|judge|penalty|award|win|grade|rubric|rank|correct|"
        r"evaluate|criterion|criteria|accepted|verdict)\b",
        re.IGNORECASE,
    ),
}

PROTOCOL_SUMMARIES = {
    "shared_answer": "The team solves the assigned material and produces one shared answer.",
    "progressive_release": "The team works through material released in stages and commits answers under the event sequence.",
    "research_artifact": "The team researches, authors, and defends a judged artifact.",
    "presentation_and_cross_examination": "The team prepares a case, presents it, and responds to judges or opponents.",
    "buzzer_match_question_proxy": "The task represents a quiz-bowl question without a complete live buzzer match.",
    "buzzer_match_session_proxy": "The task represents a buzzer round or match packet.",
    "lab_practical_proxy": "The task represents a practical or laboratory event through the available interface.",
    "ctf_sandbox": "The team solves a capture-the-flag task inside the authorized challenge boundary.",
    "cyber_defense_proxy": "The task represents a live cyber-defense event through a partial environment.",
    "event_packet_proxy": "The task represents one event packet from a broader multi-event competition.",
    "creative_performance_proxy": "The task represents a judged creative performance through a written proxy.",
    "robotics_rules_proxy": "The task represents a physical robotics event through design, rules, and program text.",
    "staged_collaborative_writing": "The team plans together, writes under the event's individual-work stage, and completes the permitted review stage.",
    "two_workstation_programming": "The team coordinates programming work under the contest's two-machine capacity.",
    "proof_packet": "The team develops and submits a shared proof packet.",
}

PROTOCOL_AGENT_CONSTRAINTS = {
    "shared_answer": [
        "Partition the assigned material, communicate decision-relevant work, independently verify high-risk answers, and reconcile one shared answer before submission.",
    ],
    "progressive_release": [
        "Track which material is currently released, which answers are provisional, and which answers are already committed; do not use or claim access to unreleased stages.",
        "Record dependencies between ordinary puzzles, metas, and final objectives so that handoffs preserve the state needed by later solvers.",
    ],
    "research_artifact": [
        "Keep sourced evidence, analysis, recommendations, and presentation claims distinct, then reconcile them into one internally consistent artifact.",
        "Do not cite a source, experiment, market action, or judge interaction unless it was actually available and observed in the task environment.",
    ],
    "presentation_and_cross_examination": [
        "Observe the competition's phase order: confer only in an authorized conferral period, designate the current speaker, and stop when the modeled phase ends.",
        "Keep the team's presentation, opponent commentary, response, and judge-question answers distinct so each can be evaluated under its own official criterion.",
    ],
    "buzzer_match_question_proxy": [
        "Follow phase-specific buzzer, recognition, speaker, and conferral rules; do not communicate an answer during a phase in which teammate consultation is forbidden.",
        "Do not claim an interrupt, opponent response, moderator ruling, or bonus opportunity unless the current task exposes that state.",
    ],
    "buzzer_match_session_proxy": [
        "Follow phase-specific buzzer, recognition, speaker, and conferral rules; do not communicate an answer during a phase in which teammate consultation is forbidden.",
        "Maintain the current quarter, eligibility-to-answer state, score state, and committed responses without inventing opponent or moderator actions.",
    ],
    "lab_practical_proxy": [
        "Separate provided observations from derived calculations and never invent an instrument reading, specimen state, safety check, or physical manipulation that the task does not expose.",
        "Reconcile units, tables, graphs, uncertainty, and conclusions into the single practical report required by the selected task.",
    ],
    "ctf_sandbox": [
        "Operate only inside the authorized challenge boundary, preserve a reproducible evidence trail, and submit only a flag obtained from the exposed environment.",
    ],
    "cyber_defense_proxy": [
        "Track services, incidents, injects, and authorized changes separately; do not claim network state, red-team activity, or service availability that the runner does not expose.",
    ],
    "event_packet_proxy": [
        "Apply only the rules for the selected season, division, and event; a tournament roster rule does not authorize every roster member to collaborate on one event.",
    ],
    "creative_performance_proxy": [
        "Separate authored text from physical props, staging, improvisation, and judge state, and do not claim that unexposed performance elements occurred.",
    ],
    "robotics_rules_proxy": [
        "Keep design intent, program behavior, observed simulator output, and physical robot-run claims separate; only observed state may be reported as a completed run.",
        "Apply the selected season, category, age group, game document, and official Q&A together; do not combine rules from incompatible robotics tracks.",
    ],
    "staged_collaborative_writing": [
        "Respect the event's shared-planning, private-writing, and review stages; do not transfer text or edits across a stage boundary unless that stage permits it.",
    ],
    "two_workstation_programming": [
        "Coordinate the two available machine leases explicitly, communicate test evidence before handoff, and never claim more simultaneous execution capacity than the contest provides.",
    ],
    "proof_packet": [
        "Assign proof obligations, exchange lemmas and counterexamples, verify every dependency, and merge only mutually consistent arguments into the shared packet.",
    ],
}

COMPETITION_AGENT_CONSTRAINTS = {
    "debatebench": [
        "Keep the four British Parliamentary teams as separate coalitions; do not leak one coalition's private preparation to another coalition.",
    ],
    "ethics_bowl_appe": [
        "For the 2025 APPE national ruleset, treat response, commentary, commentary response, and judge questioning as separate hard-stop phases and allow only one speaker at a time.",
    ],
    "ethics_bowl_nhseb": [
        "For the 2025-2026 NHSEB ruleset, use only the seated team for a match, make no mid-match substitution, and keep the non-presenting team silent during the other team's conferral and response periods.",
    ],
    "history_olympiad": [
        "During tossups, teammates may not confer verbally or in writing and only the contestant who buzzed may answer; conferral is allowed only in the official bonus and category-round phases.",
    ],
    "hmmt_guts": [
        "Use the selected November or February batch size, treat handed-in batch answers as final, and do not claim access to a later batch before it is released.",
    ],
    "ioai_team": [
        "Do not generalize Individual Contest website permissions to the Team Challenge; use only the task-specific environment and the organizer-designated translation site.",
    ],
    "mystery_hunt": [
        "Treat the configured 8-12-agent roster as a benchmark adaptation, not an official MIT Mystery Hunt team-size limit.",
        "Separate task-level answer checking from full-hunt hint, interaction, meta, runaround, and coin-finding state that the current benchmark does not reproduce.",
    ],
    "purple_comet": [
        "The official generative-AI prohibition makes LLM participation non-comparable; record this compliance failure separately even when an answer is correct.",
    ],
    "science_bowl": [
        "Do not confer verbally on tossups; for a bonus, consult only after the bonus is awarded and route the final answer through the captain when the official match state is modeled.",
    ],
    "science_olympiad": [
        "Do not treat the 15-person tournament roster as the active team for one event; require the event's season, division, event rules, corrections, and score sheet before claiming official equivalence.",
    ],
    "wro": [
        "The text runner cannot certify construction, inspection, quarantine, table state, judge decisions, or a physical robot attempt; report those mechanisms as unavailable.",
    ],
    "wsc_writing": [
        "Do not reveal one writer's private drafting state to another writer during the individual-writing stage unless the selected event rules explicitly reopen collaboration.",
    ],
}


def unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = re.sub(r"\s+", " ", str(value)).strip()
        if text and text not in result:
            result.append(text)
    return result


def protected_facts(card: dict[str, Any]) -> dict[str, Any]:
    """Return the competition-specific facts this standardizer must not rewrite."""
    provenance = {
        key: value
        for key, value in (card.get("provenance") or {}).items()
        if key not in {"adaptations", "content_standard"}
    }
    if "research_notes" in provenance:
        protected_notes = [
            item
            for item in provenance["research_notes"]
            if not should_relocate_constraint(card["competition_id"], item)
        ]
        if protected_notes:
            provenance["research_notes"] = protected_notes
        else:
            provenance.pop("research_notes", None)
    dimensions = {
        key: value
        for key, value in ((card.get("comparability") or {}).get("dimensions") or {}).items()
        if key not in {"information", "deliberation", "communication"}
    }
    comparability = dict(card.get("comparability") or {})
    comparability["dimensions"] = dimensions
    scoring = {
        key: value
        for key, value in (card.get("scoring") or {}).items()
        if key not in GENERATED_SCORING_KEYS
    }
    roles = [
        {
            key: value
            for key, value in role.items()
            if key not in {"information_access", "rule_expertise"}
        }
        for role in card.get("agent_roles") or []
    ]
    protected = {
        key: card.get(key)
        for key in (
            "schema_version",
            "rule_id",
            "competition_id",
            "profile",
            "protocol",
            "team",
            "execution",
            "simulation",
            "allowed_tools",
            "resources",
            "deliverable",
            "submission",
        )
    }
    protected["human_constraints"] = [
        item
        for item in card.get("human_constraints") or []
        if not should_relocate_constraint(card["competition_id"], item)
    ]
    return protected | {
        "agent_roles": roles,
        "scoring": scoring,
        "provenance": provenance,
        "comparability": comparability,
    }


def should_relocate_constraint(competition_id: str, constraint: str) -> bool:
    return constraint in SIMULATION_BOILERPLATE or constraint in NON_BINDING_CONSTRAINTS.get(
        competition_id, set()
    )


def relocate_nonbinding_constraints(card: dict[str, Any]) -> None:
    kept: list[str] = []
    relocated: list[str] = []
    for constraint in card.get("human_constraints") or []:
        if should_relocate_constraint(card["competition_id"], constraint):
            relocated.append(constraint)
        else:
            kept.append(constraint)
    card["human_constraints"] = kept
    if not relocated:
        return
    provenance = dict(card.get("provenance") or {})
    notes = list(provenance.get("research_notes") or [])
    provenance["research_notes"] = append_unique(notes, relocated)
    card["provenance"] = provenance


def ensure_sentence(value: str) -> str:
    text = re.sub(r"\s+", " ", value).strip()
    if text and text[-1] not in ".!?":
        text += "."
    return text


def display_names() -> dict[str, str]:
    payload = json.loads(INDEX.read_text(encoding="utf-8"))
    names = {item["id"]: item["name"] for item in payload["olympiads"]}
    # The catalog currently carries a mojibake separator for this display name.
    # Keep the rule card contestant-facing without broadening this task into an
    # index cleanup.
    names["wsc_writing"] = "World Scholar's Cup - Collaborative Writing"
    return names


def resource_summary(resources: dict[str, Any]) -> str:
    text = describe_resources(resources)
    replacements = {
        "running code is requires mutable network environment": (
            "running code requires the mutable network environment"
        ),
        "internet access is task dependent": "internet access is task-dependent",
        "internet access is unknown not verified": "internet access is not verified",
        "calculators is unknown not verified": "calculator permission is not verified",
        "running code is unknown not verified": "code-execution permission is not verified",
        "presentation device is one laptop or tablet single slideshow only": (
            "presentation devices are limited to one laptop or tablet showing a single slideshow"
        ),
        "machine lease enforcement is specified only": (
            "machine-lease enforcement is specified but not implemented"
        ),
        "internet access is forbidden unless year packet explicitly allows": (
            "internet access is forbidden unless the year packet explicitly allows it"
        ),
        "calculators is year packet dependent not exposed by default": (
            "calculator permission is year-packet-dependent and not exposed by default"
        ),
        "running code is year packet dependent not exposed by default": (
            "code-execution permission is year-packet-dependent and not exposed by default"
        ),
        "calculators is event dependent not exposed by default": (
            "calculator permission is event-dependent and not exposed by default"
        ),
        "computer algebra systems is allowed for calculation only": (
            "computer algebra systems are allowed for calculation only"
        ),
        "generative AI is brainstorming only with citation": (
            "generative AI is limited to cited brainstorming"
        ),
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def team_size_text(team: dict[str, Any]) -> str:
    minimum = int(team["active_min"])
    default = int(team["active_default"])
    maximum = int(team["active_max"])
    basis = str(team.get("range_basis") or "source_record").strip()
    official_note = str(team.get("official_roster_note") or "").strip()
    if basis == "benchmark_adaptation":
        statement = (
            f"Benchmark adaptation: the runner uses {default} active agents"
            if minimum == maximum
            else (
                f"Benchmark adaptation: the runner permits {minimum} to {maximum} "
                f"active agents and defaults to {default}"
            )
        )
        if official_note:
            statement += f"; official roster note: {official_note}"
        return ensure_sentence(statement)
    if basis == "mixed_or_unresolved":
        statement = (
            f"Mixed or unresolved rulesets: the runner permits {minimum} to {maximum} "
            f"active agents and defaults to {default}"
        )
        if official_note:
            statement += f"; source boundary: {official_note}"
        return ensure_sentence(statement)
    if minimum == maximum:
        statement = f"The source-recorded active team has {default} members"
    else:
        statement = (
            f"The source-recorded active team may have {minimum} to {maximum} "
            f"members; the runner default is {default}"
        )
    if official_note:
        statement += f"; official roster note: {official_note}"
    return ensure_sentence(statement)


def labeled(label: str, value: str) -> str:
    return f"{label}: {ensure_sentence(value)}"


GENERATED_SECTION_PREFIXES = (
    "Competition model:",
    "Source-recorded competition rule:",
    "Source-recorded timing:",
    "Source-recorded resource policy:",
    "Source-recorded collaboration rule:",
    "Benchmark adaptation:",
    "Benchmark safety rule:",
    "Runner answer contract:",
    "Official deliverable:",
    "Repository evaluation status:",
    "Runtime limitation:",
    "Mixed or unresolved rulesets:",
)


def is_generated_section_entry(card: dict[str, Any], value: str) -> bool:
    text = str(value).strip()
    if text.startswith(GENERATED_SECTION_PREFIXES):
        return True
    generated_exact = {
        PROTOCOL_SUMMARIES.get(card.get("protocol"), ""),
        str((card.get("team") or {}).get("collaboration") or "").strip(),
        resource_summary(card.get("resources") or {}),
        str((card.get("deliverable") or {}).get("answer_format") or "").strip(),
        str((card.get("submission") or {}).get("adaptation") or "").strip(),
    }
    generated_exact.update(
        str(item) for item in (card.get("provenance") or {}).get("proxy_limitations") or []
    )
    if text in generated_exact:
        return True
    return text.startswith(
        (
            "The active team ",
            "The official deliverable is ",
            "Official timing note:",
            "No official numeric duration is encoded ",
            "Do not use hidden solutions, evaluator internals, ",
            "Task performance is ",
            "This rule card is classified as ",
        )
    )


def evaluator_ready(scoring: dict[str, Any]) -> bool:
    return bool(scoring.get("evaluator_id")) and scoring.get("evaluator_status") in {
        "ready",
        "ready_with_limitations",
    }


def performance_sentence(card: dict[str, Any]) -> str:
    scoring = card.get("scoring") or {}
    mode = str(scoring.get("mode") or "declared competition criteria")
    unit = str(scoring.get("unit") or "submission")
    status = str(scoring.get("evaluator_status") or "unassigned")
    evaluator = scoring.get("evaluator_id")
    if evaluator_ready(scoring):
        return (
            f"Task performance is evaluated per {unit} in {mode} mode by "
            f"{evaluator}; repository evaluator status is {status}."
        )
    return (
        f"Task performance is specified per {unit} in {mode} mode, but the "
        f"repository evaluator is {status}; do not invent a completed score."
    )


def build_rule_sections(card: dict[str, Any]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {name: [] for name in STANDARD_RULE_SECTIONS}
    team = card["team"]
    sections["competition_format"] = [
        labeled(
            "Competition model",
            PROTOCOL_SUMMARIES.get(
                card["protocol"],
                f"The team works under the {card['protocol'].replace('_', ' ')} protocol.",
            ),
        ),
        team_size_text(team),
    ]

    time_note = str((card.get("provenance") or {}).get("official_time_note") or "").strip()
    if time_note:
        sections["timeline"].append(labeled("Source-recorded timing", time_note))
    else:
        sections["timeline"].append(
            "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget."
        )

    resource_text = resource_summary(card.get("resources") or {})
    if resource_text:
        sections["resource_policy"].append(
            labeled("Source-recorded resource policy", resource_text)
        )
    else:
        sections["resource_policy"].append(
            "Benchmark safety rule: use only the tools and materials explicitly exposed by the task environment."
        )

    collaboration = str(team.get("collaboration") or "").strip()
    sections["collaboration_protocol"].append(
        labeled(
            "Source-recorded collaboration rule",
            collaboration
            or "Coordinate only with registered teammates through permitted channels.",
        )
    )
    sections["integrity_and_compliance"].append(
        "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition."
    )

    public_deliverable = card.get("deliverable") or {}
    answer_format = str(public_deliverable.get("answer_format") or "").strip()
    if answer_format:
        sections["deliverable_format"].append(
            labeled("Runner answer contract", answer_format)
        )
    submission = card.get("submission") or {}
    deliverable = str(public_deliverable.get("official_deliverable") or "submission").replace(
        "_", " "
    )
    sections["deliverable_format"].append(
        labeled("Official deliverable", deliverable)
    )
    adaptation = str(submission.get("adaptation") or "").strip()
    if adaptation:
        sections["deliverable_format"].append(
            labeled("Benchmark adaptation", adaptation)
        )

    sections["evaluation_criteria"].append(
        labeled("Repository evaluation status", performance_sentence(card))
    )

    limitations = list((card.get("provenance") or {}).get("proxy_limitations") or [])
    if limitations:
        sections["runtime_limitations"].extend(
            labeled("Runtime limitation", str(item)) for item in limitations
        )
    else:
        overall = str((card.get("comparability") or {}).get("overall") or card["profile"])
        sections["runtime_limitations"].append(
            "Runtime limitation: this rule card is classified as "
            f"{overall}; do not claim that unmodeled official mechanisms occurred."
        )

    for constraint in card.get("human_constraints") or []:
        matched = False
        for section_name, pattern in SECTION_PATTERNS.items():
            if pattern.search(constraint):
                sections[section_name].append(
                    labeled("Source-recorded competition rule", constraint)
                )
                matched = True
        if not matched:
            sections["competition_format"].append(
                labeled("Source-recorded competition rule", constraint)
            )

    legacy = card.get("rule_sections") or {}
    if (card.get("provenance") or {}).get(
        "discard_pre_source_review_rule_sections"
    ):
        legacy = {}
    aliases = {
        "research_integrity": "integrity_and_compliance",
        "official_collaboration_constraints": "collaboration_protocol",
        "off_workstation_permissions": "collaboration_protocol",
        "shared_workstation_protocol": "collaboration_protocol",
        "workstation_queue": "collaboration_protocol",
        "problem_coordination": "collaboration_protocol",
        "handoff_protocol": "collaboration_protocol",
        "review_protocol": "evaluation_criteria",
        "failure_recovery": "evaluation_criteria",
        "emergent_behavior": "evaluation_criteria",
    }
    for name, values in legacy.items():
        target = aliases.get(name, name)
        sections.setdefault(target, [])
        sections[target].extend(
            str(value)
            for value in values
            if not is_generated_section_entry(card, str(value))
        )

    return {name: unique_strings(values) for name, values in sections.items()}


def build_agent_constraints(card: dict[str, Any]) -> list[str]:
    resources = resource_summary(card.get("resources") or {})
    submitters = [
        str(role.get("name"))
        for role in card.get("agent_roles") or []
        if role.get("may_submit", True)
    ]
    constraints = [
        "Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.",
        str((card.get("team") or {}).get("collaboration") or "").strip(),
        resources,
        "Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.",
        "Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.",
    ]
    constraints.extend(PROTOCOL_AGENT_CONSTRAINTS.get(card.get("protocol"), []))
    constraints.extend(
        COMPETITION_AGENT_CONSTRAINTS.get(card.get("competition_id"), [])
    )
    if submitters:
        constraints.append(
            "Only designated submitters may make the shared submission: "
            + ", ".join(submitters)
            + "."
        )
    if card.get("profile") != "official_equivalent":
        constraints.append(
            "Use only the official mechanisms that the current task actually exposes; do not claim physical, oral, live-opponent, judge, or environment actions that were not observed."
        )
    return unique_strings(constraints)


def assign_role_metadata(
    card: dict[str, Any], sections: dict[str, list[str]], *, specialized: bool
) -> None:
    roles = card.get("agent_roles") or []
    available = [name for name in STANDARD_RULE_SECTIONS if sections.get(name)]
    for index, role in enumerate(roles):
        role["information_access"] = ["contest_rules"]
        if not specialized:
            role["rule_expertise"] = []
            continue
        title = str(role.get("title") or "")
        preferred = []
        for name in preferred_expertise(title):
            mapped = (
                "integrity_and_compliance"
                if name == "research_integrity"
                else name
            )
            if mapped in sections and mapped not in preferred:
                preferred.append(mapped)
        lowered_title = title.lower()
        if any(word in lowered_title for word in ("designer", "slide", "report editor")):
            preferred = ["deliverable_format", "evaluation_criteria"]
        if "analyst" in lowered_title and not preferred:
            preferred = ["integrity_and_compliance", "evaluation_criteria"]
        if any(word in lowered_title for word in ("writer", "oralist", "speaker")):
            preferred = append_unique(["resource_policy"], preferred)
        if not preferred and available:
            preferred = [available[index % len(available)]]
        role["rule_expertise"] = preferred

    if specialized and len(roles) > 1:
        expertise_sets = {tuple(role.get("rule_expertise") or []) for role in roles}
        if len(expertise_sets) < 2 and len(available) > 1:
            for index, role in enumerate(roles):
                role["rule_expertise"] = [available[index % len(available)]]


def configure_collaboration(card: dict[str, Any]) -> None:
    competition_id = card["competition_id"]
    sections = build_rule_sections(card)
    specialized = competition_id in ROLE_SPECIALIZED
    assign_role_metadata(card, sections, specialized=specialized)
    card["agent_constraints"] = build_agent_constraints(card)
    card["rule_sections"] = sections
    card["information_policy"] = {
        "mode": "role_specialized" if specialized else "shared",
        "shared": [
            "problem",
            "contest_rules",
            "team_discussion",
            "scratchpad",
        ],
        "coordination_requirement": (
            "All teammates may consult the complete public contest rules. "
            "Private reasoning becomes shared state only when communicated; assigned rule "
            "expertise creates tracking responsibility, not exclusive access."
        ),
    }

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
    else:
        card["deliberation"] = {
            "mode": "unstructured",
            "min_challenges": 0,
            "evaluation_dimensions": [
                "evidence_responsiveness",
                "decision_traceability",
            ],
        }

    budget = COMMUNICATION_BUDGETS.get(competition_id)
    if budget:
        team_budget, per_agent_budget, max_chars = budget
        card["communication"] = {
            "mode": "limited",
            "team_message_budget": team_budget,
            "per_agent_message_budget": per_agent_budget,
            "max_message_chars": max_chars,
            "counted_actions": list(COUNTED_ACTIONS),
        }
    else:
        card["communication"] = {"mode": "unlimited"}

    provenance = dict(card.get("provenance") or {})
    adaptations = list(provenance.get("adaptations") or [])
    if specialized:
        adaptations = append_unique(adaptations, [ROLE_NOTE])
    if competition_id in STRUCTURED_DELIBERATION:
        adaptations = append_unique(adaptations, [DELIBERATION_NOTE])
    if budget:
        adaptations = append_unique(adaptations, [COMMUNICATION_NOTE])
    provenance["adaptations"] = adaptations
    card["provenance"] = provenance

    comparability = dict(card.get("comparability") or {})
    dimensions = dict(comparability.get("dimensions") or {})
    dimensions["information"] = (
        "role_specialized_tracking_overlay" if specialized else "shared_public_rules"
    )
    dimensions["deliberation"] = (
        "structured_trace_overlay"
        if competition_id in STRUCTURED_DELIBERATION
        else "unstructured_observation"
    )
    dimensions["communication"] = (
        "adapted_coordination_budget" if budget else "unlimited_runner_channel"
    )
    comparability["dimensions"] = dimensions
    card["comparability"] = comparability


def repository_unavailable_mechanisms(card: dict[str, Any]) -> list[str]:
    unavailable: list[str] = []
    merged = dict(card.get("execution") or {})
    merged.update(card.get("simulation") or {})
    for name, value in merged.items():
        lowered = str(value).lower()
        if lowered in {
            "unavailable",
            "not_implemented",
            "specified_only",
            "specified_not_enforced",
        } or lowered.endswith("_unavailable"):
            unavailable.append(name)
    return unavailable


def configure_evaluation(card: dict[str, Any]) -> None:
    scoring = dict(card.get("scoring") or {})
    current_guidance = str(card.get("evaluation_guidance") or "").strip()
    specific = str(scoring.get("competition_specific_criteria") or "").strip()
    already_standardized = (
        ((card.get("provenance") or {}).get("content_standard") or {}).get("name")
        == STANDARD_NAME
    )
    if not specific and current_guidance and not already_standardized:
        specific = current_guidance
    if specific:
        scoring["competition_specific_criteria"] = specific

    status = str(scoring.get("evaluator_status") or "unassigned")
    mode = str(scoring.get("mode") or "declared competition criteria")
    unit = str(scoring.get("unit") or "submission")
    provenance = card.get("provenance") or {}
    research_status = str(provenance.get("status") or "documented_from_available_sources")
    source_review = dict(provenance.get("source_review") or {})
    official_scoring = dict(scoring.get("official_scoring") or {})
    evaluation_criteria = list((card.get("rule_sections") or {}).get("evaluation_criteria") or [])
    scoring["official_performance"] = {
        "source_status": research_status,
        "source_review_status": source_review.get("completion_status", "not_reviewed"),
        "mechanics_completeness": official_scoring.get("completeness", "not_fully_encoded"),
        "mode": mode,
        "unit": unit,
        "criteria": evaluation_criteria,
        "mechanics": list(official_scoring.get("mechanics") or []),
        "tie_breakers": list(official_scoring.get("tie_breakers") or []),
        "source_refs": list(official_scoring.get("source_refs") or []),
        "unresolved": list(official_scoring.get("unresolved") or []),
        "repository_evaluator_id": scoring.get("evaluator_id"),
        "repository_evaluator_status": status,
    }
    competition_specific_violations = list(
        scoring.get("official_rule_violations") or []
    )
    scoring["rule_compliance"] = {
        "reported_separately_from_performance": True,
        "violation_types": [
            {
                "id": "unauthorized_tool_or_resource",
                "condition": "A contestant uses a tool, material, device, website, machine, or execution surface forbidden by this competition.",
            },
            {
                "id": "outside_assistance",
                "condition": "The team receives problem-solving help from a person or service outside the permitted team and official channels.",
            },
            {
                "id": "hidden_solution_or_evaluator_access",
                "condition": "A contestant accesses hidden answers, tests, rubrics, evaluator internals, or judge state not released by the event.",
            },
            {
                "id": "unauthorized_submission",
                "condition": "A non-submitter files or replaces the shared submission, or the team exceeds the declared submission contract.",
            },
            {
                "id": "competition_specific_constraint",
                "condition": "The team violates a competition-specific constraint recorded in competition_format, timeline, resource_policy, collaboration_protocol, integrity_and_compliance, or deliverable_format.",
            },
        ]
        + competition_specific_violations,
        "reporting": [
            "total_violations",
            "violations_by_type",
            "first_violation_turn",
            "performance_with_illegal_actions",
            "compliant_performance",
        ],
    }
    scoring["collaboration_quality"] = {
        "benchmark_diagnostic_only": True,
        "reported_separately_from_performance": True,
        "metric_groups": {
            "task_allocation_and_coverage": [
                "time_to_useful_task_allocation",
                "duplicate_effort_before_coverage",
                "workload_and_specialization_balance",
            ],
            "evidence_and_verification": [
                "decision_relevant_evidence_shared",
                "independent_checks",
                "review_caused_corrections",
            ],
            "handoff_and_shared_state": [
                "handoff_completeness",
                "private_reasoning_loss",
                "stale_state_decisions",
            ],
            "recovery_and_replanning": [
                "failure_to_diagnosis_latency",
                "new_evidence_before_retry",
                "evidence_responsive_replanning",
            ],
            "communication_efficiency": [
                "decision_relevant_communication",
                "avoidable_message_overhead",
                "unresolved_disagreement_at_submission",
            ],
        },
        "anti_metrics": [
            "Do not reward message count by itself.",
            "Do not reward equal speaking time or fixed roles by itself.",
            "Do not infer shared knowledge from private reasoning that was never communicated.",
            "Do not let collaboration quality overwrite the competition's official task score unless the official rubric explicitly does so.",
        ],
    }
    submission = card.get("submission") or {}
    scoring["current_repository_availability"] = {
        "evaluator_ready": evaluator_ready(scoring),
        "evaluator_status": status,
        "official_environment_fully_reproduced": card.get("profile")
        == "official_equivalent",
        "official_wall_clock_enforced": False,
        "declared_unavailable_mechanisms": repository_unavailable_mechanisms(card),
        "proxy_limitations": list(provenance.get("proxy_limitations") or []),
        "required_selectors": list(
            (card.get("execution") or {}).get("required_selectors") or []
        ),
        "submission_adaptation": submission.get("adaptation"),
    }
    card["scoring"] = scoring

    public_deliverable = card.get("deliverable") or {}
    answer_format = str(public_deliverable.get("answer_format") or "").strip()
    deliverable = str(public_deliverable.get("official_deliverable") or "submission").replace(
        "_", " "
    )
    guidance = []
    if specific:
        guidance.append(f"Competition-specific criteria: {specific}")
    if official_scoring.get("mechanics"):
        guidance.append(
            "Official scoring mechanics: "
            + " ".join(str(item) for item in official_scoring["mechanics"])
        )
    if official_scoring.get("unresolved"):
        guidance.append(
            "Unresolved official evaluation state: "
            + " ".join(str(item) for item in official_scoring["unresolved"])
        )
    guidance.extend(
        [
            f"Task performance: evaluate the {deliverable} per {unit} in {mode} mode and enforce this answer contract: {answer_format}",
            (
                f"Repository status: the evaluator is {status}. "
                + (
                    "Use the declared evaluator and preserve any stated limitations."
                    if evaluator_ready(scoring)
                    else "Do not invent a completed benchmark grade or claim evaluator readiness."
                )
            ),
            "Rule compliance: report prohibited tools, outside assistance, hidden-answer access, unauthorized submission, and competition-specific violations separately from task performance.",
            "Collaboration quality: assess allocation, evidence exchange, verification, handoffs, recovery, replanning, and communication efficiency without rewarding fixed roles, equal airtime, or message volume by themselves.",
            "Fidelity: identify official mechanisms that the current runner does not reproduce; never treat a proxy action as proof that a physical, oral, live-opponent, judge, or mutable-environment event occurred.",
        ]
    )
    card["evaluation_guidance"] = " ".join(ensure_sentence(item) for item in guidance)


def compose_rules_text(card: dict[str, Any], name: str) -> str:
    deliverable = card.get("deliverable") or {}
    pieces = [
        f"{name}.",
        PROTOCOL_SUMMARIES.get(
            card["protocol"],
            f"The team works under the {card['protocol'].replace('_', ' ')} protocol.",
        ),
        team_size_text(card["team"]),
        str(card["team"].get("collaboration") or "").strip(),
        resource_summary(card.get("resources") or {}),
        (
            f"Submit one shared {str(deliverable.get('official_deliverable') or 'submission').replace('_', ' ')}; "
            f"{str(deliverable.get('answer_format') or '').strip()}"
        ),
        str((card.get("provenance") or {}).get("official_time_note") or "").strip(),
    ]
    if card.get("profile") != "official_equivalent":
        pieces.append(
            "Treat unexposed physical, oral, live-opponent, judge, timing, or environment mechanisms as unavailable rather than simulated facts."
        )
    return " ".join(ensure_sentence(piece) for piece in pieces if str(piece).strip())


def apply_content_standard(card: dict[str, Any], *, name: str) -> dict[str, Any]:
    if card["competition_id"] in HAND_AUTHORED_ICPC_QUALITY:
        return card
    relocate_nonbinding_constraints(card)
    configure_collaboration(card)
    configure_evaluation(card)
    card["rules_text"] = compose_rules_text(card, name)
    provenance = dict(card.get("provenance") or {})
    provenance["content_standard"] = {
        "name": STANDARD_NAME,
        "version": STANDARD_VERSION,
        "applied_at": STANDARD_DATE,
        "reference_card": "data/rules/icpc",
        "official_facts_policy": "competition_specific_primary_sources_only",
        "scope": [
            "competition_constraints",
            "collaboration_operations",
            "evaluation_and_compliance",
            "runtime_fidelity",
        ],
    }
    card["provenance"] = provenance
    return card


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    names = display_names()
    changed = 0
    for competition_id in iter_rule_card_ids(RULES):
        if competition_id in HAND_AUTHORED_ICPC_QUALITY:
            continue
        card = load_rule_card_payload(
            competition_id, rules_root=RULES, required=True
        )
        before = json.dumps(card, ensure_ascii=False, sort_keys=True)
        facts_before = protected_facts(card)
        apply_content_standard(card, name=names.get(competition_id, competition_id))
        if protected_facts(card) != facts_before:
            raise RuntimeError(
                f"content standard changed protected competition facts: {competition_id}"
            )
        after = json.dumps(card, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        changed += 1
        print(competition_id)
        if not args.dry_run:
            write_rule_card_payload(
                competition_id,
                card,
                rules_root=RULES,
            )
    suffix = " (dry run)" if args.dry_run else ""
    print(f"standardized {changed} non-ICPC cards{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
