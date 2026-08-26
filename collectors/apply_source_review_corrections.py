"""Apply source-audited factual and scope corrections to competition rule cards.

This collector is deliberately separate from the content standardizer.  It may
change competition facts, but only where the accompanying source audit or an
archived primary document identifies the exact correction.  Run this collector
before ``standardize_rule_card_content.py``.

Usage:
    python collectors/apply_source_review_corrections.py --dry-run
    python collectors/apply_source_review_corrections.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
sys.path.insert(0, str(REPO / "src"))

from rules import (  # noqa: E402
    iter_rule_card_ids,
    load_rule_card_payload,
    write_rule_card_payload,
)
from standardize_rule_card_content import HAND_AUTHORED_ICPC_QUALITY  # noqa: E402

AUDIT_DATE = "2026-08-17"
AUDIT_REPORT = "docs/rule_card_icpc_standard_gap_audit_2026-08-17.md"

SOURCE_GRADES = {
    "arml_local": "B",
    "arml_national_power": "B",
    "arml_national_team": "B",
    "arml_power": "C",
    "ccdc": "B",
    "cfa_research_challenge": "B",
    "cybench": "B",
    "debatebench": "C",
    "eoes": "C",
    "ethics_bowl_appe": "A",
    "ethics_bowl_nhseb": "A",
    "fyziklani": "B",
    "gcch_harvard": "D",
    "history_olympiad": "A",
    "hmmt_guts": "B",
    "ichto": "B",
    "ieo_business_case": "B",
    "iiot": "B",
    "ijso_practical": "C",
    "ioaa_group": "B",
    "ioai_team": "C",
    "iol_team": "A",
    "jessup": "B",
    "mystery_hunt": "B",
    "nyu_ctf_bench": "B",
    "odyssey_of_the_mind": "C",
    "pumac_power": "B",
    "purple_comet": "A",
    "qanta": "C",
    "science_bowl": "A",
    "science_olympiad": "D",
    "vis_moot": "C",
    "wharton_investment": "B",
    "wmtc": "D",
    "wro": "B",
    "wsc_writing": "B",
}

SOURCE_COMPLETION = {
    "A": "primary_rules_available_exact_scoring_may_still_need_runtime_support",
    "B": "primary_rules_partial_or_variant_selector_required",
    "C": "material_official_fields_remain_unverified",
    "D": "blocked_no_adequate_current_primary_ruleset",
}

RANGE_BASIS = {
    "arml_power": "mixed_or_unresolved",
    "ccdc": "mixed_or_unresolved",
    "cybench": "benchmark_adaptation",
    "debatebench": "mixed_or_unresolved",
    "history_olympiad": "mixed_or_unresolved",
    "ioaa_group": "mixed_or_unresolved",
    "mystery_hunt": "benchmark_adaptation",
    "nyu_ctf_bench": "benchmark_adaptation",
    "odyssey_of_the_mind": "mixed_or_unresolved",
    "qanta": "benchmark_adaptation",
    "science_olympiad": "benchmark_adaptation",
    "vis_moot": "mixed_or_unresolved",
    "wmtc": "mixed_or_unresolved",
}

SOURCE_GAPS = {
    "arml_local": [
        "The official Local page does not state a numeric point value per Team Round question; coaches and local coordinators grade and submit scores."
    ],
    "arml_national_team": [
        "The official ARML/IRML rules page does not establish a Team Round wall-clock duration."
    ],
    "arml_national_power": [
        "The official ARML/IRML rules page does not establish a Power Round wall-clock duration."
    ],
    "arml_power": [
        "The standalone Power Contest roster, clock, aids policy, and submission window are not established by the archived primary material."
    ],
    "gcch_harvard": [
        "No public rulebook or judging rubric establishes detailed tool, outside-help, page-limit, or scoring rules."
    ],
    "history_olympiad": [
        "The archived 2025 World Championship rules do not automatically govern historical benchmark packets; rules edition and division selectors are required."
    ],
    "mystery_hunt": [
        "Annual hunt mechanics, hints, interactions, metas, runaround state, and coin-finding are not reproduced by the question-level benchmark."
    ],
    "ioai_team": [
        "The 2026 technical appendix explicitly excludes Team Challenge technical details; the exact task guide and environment remain required."
    ],
    "science_olympiad": [
        "No universal event ruleset exists; season, division, event rules, corrections, and score sheet must be selected and archived."
    ],
    "wmtc": [
        "A usable current official rules document was not available; historical or access-gated material cannot authorize current hard constraints."
    ],
    "wro": [
        "The 2026 General Rules are not a ready-to-use national game ruleset; category, age group, game document, national adaptation, and Q&A snapshot remain required."
    ],
}


def unique(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = " ".join(str(value).split()).strip()
        if text and text not in result:
            result.append(text)
    return result


def source(
    *,
    title: str,
    url: str,
    edition: str,
    sections: list[str],
    local_file: str | None = None,
    authority: str = "official",
    archive_status: str = "archived",
) -> dict[str, Any]:
    item: dict[str, Any] = {
        "title": title,
        "url": url,
        "authority": authority,
        "edition": edition,
        "retrieved_at": AUDIT_DATE,
        "sections": sections,
        "archive_status": archive_status,
    }
    if local_file:
        item["local_file"] = local_file
    return item


def replace_sources(card: dict[str, Any], sources: list[dict[str, Any]]) -> None:
    provenance = dict(card.get("provenance") or {})
    previous = provenance.get("sources") or []
    if previous and previous != sources:
        provenance["discovery_sources"] = previous
    provenance["sources"] = sources
    card["provenance"] = provenance


def set_review_metadata(card: dict[str, Any]) -> None:
    competition_id = card["competition_id"]
    grade = SOURCE_GRADES[competition_id]
    provenance = dict(card.get("provenance") or {})
    provenance["source_review"] = {
        "reviewed_at": AUDIT_DATE,
        "audit_report": AUDIT_REPORT,
        "coverage_grade": grade,
        "completion_status": SOURCE_COMPLETION[grade],
        "claim_policy": "unknown_official_values_remain_null_or_explicitly_unresolved",
        "known_gaps": SOURCE_GAPS.get(competition_id, []),
    }
    card["provenance"] = provenance
    card["team"]["range_basis"] = RANGE_BASIS.get(
        competition_id, "source_record"
    )


def set_proxy_limitations(card: dict[str, Any], values: list[str]) -> None:
    provenance = dict(card.get("provenance") or {})
    provenance["proxy_limitations"] = unique(
        list(provenance.get("proxy_limitations") or []) + values
    )
    card["provenance"] = provenance


OFFICIAL_EXECUTION_KEYS = {
    "rules_edition",
    "required_selectors",
    "selector_default",
    "official_minutes",
    "official_phases",
    "official_quarters",
    "robot_attempt_seconds",
    "problem_language",
    "allowed_languages",
}
SIMULATION_ALWAYS_KEYS = {
    "selector_enforcement",
    "full_hunt_unlock_state",
    "hint_and_interaction_state",
    "runaround_and_coin_state",
    "robot_environment",
    "inspection_quarantine_and_field_state",
    "physical_final",
    "live_opponent_and_judges",
    "live_opponent_moderator_and_judges",
    "live_opponent_buzzer_moderator_and_clock",
    "buzzer_opponents_and_moderator",
}


def update_execution(card: dict[str, Any], payload: dict[str, Any]) -> None:
    execution = dict(card.get("execution") or {})
    simulation = dict(card.get("simulation") or {})
    for key, value in payload.items():
        lowered = str(value).lower()
        if key in SIMULATION_ALWAYS_KEYS or lowered in {
            "unavailable",
            "not_implemented",
        }:
            simulation[key] = value
            execution.pop(key, None)
        else:
            execution[key] = value
    card["execution"] = execution
    card["simulation"] = simulation


def set_official_scoring(
    card: dict[str, Any],
    *,
    completeness: str,
    mechanics: list[str],
    tie_breakers: list[str] | None = None,
    source_refs: list[str] | None = None,
    unresolved: list[str] | None = None,
    violations: list[dict[str, str]] | None = None,
) -> None:
    scoring = dict(card.get("scoring") or {})
    scoring["official_scoring"] = {
        "completeness": completeness,
        "mechanics": mechanics,
        "tie_breakers": tie_breakers or [],
        "source_refs": source_refs or [],
        "unresolved": unresolved or [],
    }
    scoring["official_rule_violations"] = violations or []
    card["scoring"] = scoring


def correct_appe(card: dict[str, Any]) -> None:
    card["team"] = {
        "active_min": 1,
        "active_default": 5,
        "active_max": 6,
        "range_basis": "source_record",
        "official_roster_note": (
            "The 2025 national rules allow a team of any roster size, but no more "
            "than six members may actively participate in a match."
        ),
        "collaboration": (
            "The seated participants may confer only in the designated phase; multiple "
            "members may contribute orally, but only one person speaks at a time."
        ),
    }
    update_execution(card, 
        {
            "rules_edition": "2025_national",
            "required_selectors": ["competition_scope"],
            "selector_default": {"competition_scope": "national"},
            "official_minutes": None,
            "official_phases": [
                {"phase": "presenting_team_conferral", "minutes": 2},
                {"phase": "presenting_team_response", "minutes": 10, "hard_stop": True},
                {"phase": "opposing_team_conferral", "minutes": 1},
                {"phase": "opposing_team_commentary", "minutes": 5, "hard_stop": True},
                {"phase": "presenting_team_reply_conferral", "minutes": 1},
                {"phase": "presenting_team_reply", "minutes": 5, "hard_stop": True},
                {"phase": "judge_questioning", "minutes": 10, "hard_stop": True},
            ],
            "second_case_role_reversal": "specified_only",
            "live_opponent_and_judges": "unavailable",
        }
    )
    card["resources"] = {
        "internet": "forbidden",
        "calculator": "forbidden",
        "code_execution": "forbidden",
        "paper_pencil": "scratch_paper_only_after_official_start",
        "provided_materials_only": True,
        "personal_timer": "non_networked_non_storage_reference_only",
    }
    card["allowed_tools"] = ["query_rules"]
    card["human_constraints"] = [
        "Teams may be any roster size, but no more than six members may actively participate in a match.",
        "Once participants are seated and ready, no substitution is allowed for the remainder of the round after the case is announced.",
        "Books and pre-existing notes are prohibited during the match; organizer-provided case material and scratch paper may be used after the official timer starts.",
        "A personal timer is only a reference: it may not connect to the internet or store data, and the moderator's timer is official.",
        "The presenting team receives two minutes to confer and up to ten minutes to respond, with a hard stop at time.",
        "After one minute of conferral, the opposing team has up to five minutes to comment, and only one of its members may speak at a time.",
        "The presenting team then receives one minute to confer and up to five minutes to reply to the commentary, with one speaker at a time.",
        "Judges receive up to ten minutes for questions; team members may briefly huddle before answering and different members may answer different judges.",
        "After the first case, the teams reverse presenting and commenting roles for a second case.",
        "The match winner is determined by judges' sheet outcomes, not by simply summing both teams' raw points.",
    ]
    replace_sources(
        card,
        [
            source(
                title="APPE Intercollegiate Ethics Bowl National Competition Rules",
                url="https://growthzonecmsprodeastus.azureedge.net/sites/36/2025/10/2025-APPE-IEB-National-Rules.pdf",
                edition="2025 national competition",
                sections=[
                    "pp. 4-7 procedural rules and match phases",
                    "pp. 10-13 scoring, ranking, advancement, and tie breakers",
                ],
                local_file="data/rules/sources/ethics_bowl_appe/2025_APPE_IEB_National_Rules.pdf",
            )
        ],
    )
    set_proxy_limitations(
        card,
        [
            "The runner does not reproduce a live opposing team, moderator, three-judge panel, role reversal, oral hard stops, or judge questions.",
            "A text transcript is a benchmark adaptation of the official oral match performance.",
        ],
    )
    card["deliverable"].update(
        {
            "answer_format": (
                "Provide the case response, opposing-team commentary, commentary "
                "reply, and judge-question answers as distinct labeled sections "
                "exposed by the task."
            ),
            "official_deliverable": "live_oral_match_performance",
            "official_mime_types": ["audio/x-live-speech"],
            "mime_types": ["text/plain"],
        }
    )
    card["submission"]["adaptation"] = (
        "The runner accepts a structured text transcript instead of a live "
        "two-team oral match."
    )
    card["scoring"].update(
        {"mode": "official_judge_rubric", "unit": "match", "evaluator_status": "deferred_live_judges"}
    )
    set_official_scoring(
        card,
        completeness="complete_for_2025_national_match",
        mechanics=[
            "Each judge scores a team's answer 0-30: 0-10 for clarity/relevance, 0-10 for identification and discussion of the central moral dimensions, and 0-10 for consideration of alternative viewpoints.",
            "Each judge also scores commentary 0-10, reply to commentary 0-10, and response to judges' questions 0-10.",
            "A team wins a match by winning at least two judges' score sheets, or by winning one sheet and tying the other two; otherwise the match may be tied even when raw totals differ.",
            "Preliminary ranking orders teams by wins, then ties, then point differential before the remaining official tie procedures.",
        ],
        tie_breakers=[
            "The 2025 rules apply head-to-head and further published ranking procedures after wins, ties, and point differential; an impartial random process is the final fallback."
        ],
        source_refs=["2025 APPE National Rules pp. 10-13"],
        violations=[
            {"id": "mid_round_substitution", "condition": "The seated active participants are changed after the case is announced."},
            {"id": "phase_or_speaker_violation", "condition": "A team speaks outside its phase, exceeds a hard stop, or has more than one person speaking at once."},
            {"id": "unauthorized_notes_or_timer", "condition": "A contestant uses pre-existing notes, books, or an internet-connected or data-storing personal timer."},
        ],
    )


def correct_nhseb(card: dict[str, Any]) -> None:
    card["team"] = {
        "active_min": 3,
        "active_default": 5,
        "active_max": 5,
        "roster_max": 7,
        "range_basis": "source_record",
        "official_roster_note": "A team has three to seven students; no more than five are seated in a match.",
        "collaboration": (
            "Only the seated members participate in a match; they may confer in the "
            "designated periods, while the non-presenting team remains silent during the other team's speaking period."
        ),
    }
    update_execution(card, 
        {
            "rules_edition": "2025-2026",
            "required_selectors": ["competition_scope", "match_mode"],
            "selector_default": {"competition_scope": "regional", "match_mode": "in_person"},
            "official_minutes": None,
            "official_phases": [
                {"phase": "presentation_conferral", "minutes": 2},
                {"phase": "presentation", "minutes_by_scope": {"regional": 5, "divisional_or_national": 6}},
                {"phase": "commentary_conferral", "minutes": 2},
                {"phase": "commentary", "minutes": 3},
                {"phase": "response_conferral", "minutes": 2},
                {"phase": "response", "minutes": 3},
                {"phase": "judge_questions", "minutes": 10},
            ],
            "second_case_role_reversal": "specified_only",
            "live_opponent_moderator_and_judges": "unavailable",
        }
    )
    card["resources"] = {
        "internet": "forbidden",
        "calculator": "forbidden",
        "code_execution": "forbidden",
        "paper_pencil": "organizer_provided_scratch_paper_only",
        "provided_materials_only": True,
        "personal_timer": "non_networked_non_storage_reference_only",
    }
    card["allowed_tools"] = ["query_rules"]
    card["human_constraints"] = [
        "A registered team has at least three and at most seven students, with no more than five seated for one match.",
        "Seated participants are selected before the match opens, and substitution is not allowed during a match.",
        "Organizer-provided scratch paper may be used, but outside notes and materials are prohibited and all match materials are collected afterward.",
        "A team timer may not store data or connect to the internet, may not time the opposing team, and is subordinate to the moderator's official time.",
        "The presenting team has two minutes to confer, followed by five minutes at a regional event or six minutes at a divisional playoff or National Championship.",
        "The opposing team has two minutes to confer and three minutes to comment; the presenting team then has two minutes to confer and three minutes to respond.",
        "The judges' question-and-answer period lasts up to ten minutes; a team may briefly confer before answering a judge.",
        "When one team speaks, the other team must remain silent, although it may quietly take notes where the rules permit.",
        "The two teams reverse roles for the second half of the match and a new case and question are used.",
        "Regional rule variations require NHSEB approval and must be communicated to participating teams.",
    ]
    replace_sources(
        card,
        [
            source(
                title="National High School Ethics Bowl Rules Manual",
                url="https://nhseb.org/s/Rules-Manual-2025-2026.pdf",
                edition="2025-2026",
                sections=[
                    "pp. 6-9 match format, phase timing, scoring, materials, and timers",
                    "pp. 12 and 15 regional versus divisional/national presentation time",
                    "pp. 17-23 team composition, team rules, judges, and moderator procedure",
                    "pp. 24-26 sanctions",
                ],
                local_file="data/rules/sources/ethics_bowl_nhseb/2025-2026_NHSEB_Rules_Manual.pdf",
            )
        ],
    )
    set_proxy_limitations(
        card,
        [
            "The runner does not reproduce a live opponent, moderator, three independent judges, oral timing, approved regional variations, or sanctions workflow.",
            "A structured text response cannot reproduce judges' private scoring and match votes.",
        ],
    )
    card.setdefault("deliverable", {}).update(
        {
            "answer_format": (
                "Provide the presentation, opposing-team commentary, response to commentary, "
                "and answers to judges as distinct labeled sections."
            ),
            "official_deliverable": "live_oral_match_performance",
            "official_mime_types": ["audio/x-live-speech"],
            "mime_types": ["text/plain"],
        }
    )
    card.setdefault("submission", {})["adaptation"] = (
        "The runner accepts a structured text transcript instead of a live two-team oral match."
    )
    card["scoring"].update(
        {"mode": "official_judge_rubric", "unit": "match", "evaluator_status": "deferred_live_judges"}
    )
    set_official_scoring(
        card,
        completeness="complete_for_2025_2026_match_core",
        mechanics=[
            "Each judge awards up to 15 points for the presentation: three criteria scored 1-5 each.",
            "Each judge also awards up to 10 points for commentary, 10 for the response to commentary, 20 for responses to judges, and 5 for respectful dialogue.",
            "Each of three judges casts a vote for the team with the higher judge total; an equal total gives each team half of that judge's vote, and the match may end tied.",
        ],
        tie_breakers=[
            "Elimination ties and preliminary ranking use the edition-specific cumulative ranking order in the manual; event scope must be selected before applying it."
        ],
        source_refs=["2025-2026 NHSEB Rules Manual pp. 7-8 and 15-16"],
        violations=[
            {"id": "unseated_or_substituted_participant", "condition": "An unseated member participates or the seated roster changes during the match."},
            {"id": "outside_match_material", "condition": "A contestant uses outside notes or materials rather than organizer-provided match material and scratch paper."},
            {"id": "silence_or_phase_violation", "condition": "A team communicates while the official phase requires it to remain silent or exceeds its phase allowance."},
        ],
    )


def correct_history(card: dict[str, Any]) -> None:
    card["profile"] = "non_comparable"
    card["comparability"]["overall"] = "non_comparable"
    card["team"] = {
        "active_min": 1,
        "active_default": 3,
        "active_max": 4,
        "range_basis": "mixed_or_unresolved",
        "official_roster_note": (
            "The 2025 World Championship uses teams of two or three, with one allowed "
            "to play if teammates are absent; historical benchmark rows still record four and require edition review."
        ),
        "collaboration": (
            "No verbal or written conferral is allowed while a tossup is being read; "
            "official bonus and third-quarter category phases permit team conferral."
        ),
    }
    card["agent_roles"] = list(card.get("agent_roles") or [])[:3]
    update_execution(card, 
        {
            "rules_edition": "2025_world_championship",
            "required_selectors": ["rules_edition", "division"],
            "selector_enforcement": "missing_from_historical_rows",
            "official_minutes": None,
            "official_quarters": [
                {"quarter": 1, "format": "10_tossups_or_8_for_intermediate_elementary", "points_each": 10},
                {"quarter": 2, "format": "8_tossups_with_non_bounceback_bonus", "points_each": 10},
                {"quarter": 3, "format": "category_round", "seconds_per_team": 60, "conferral": True},
                {"quarter": 4, "format": "8_progressive_tossups", "point_values": [30, 20, 10]},
            ],
            "buzzer_opponents_and_moderator": "unavailable",
        }
    )
    card["resources"] = {
        "internet": "forbidden",
        "calculator": "forbidden",
        "code_execution": "forbidden",
        "paper_pencil": "blank_paper_only",
        "provided_materials_only": True,
    }
    card["allowed_tools"] = ["query_rules"]
    card["human_constraints"] = [
        "Under the 2025 World Championship rules, a team plays with two or three students; one student may still compete if teammates are absent.",
        "Incorrect responses never deduct points, although an incorrect tossup response makes that team ineligible to buzz again on that question.",
        "A contestant must buzz before answering a tossup, and only the contestant who buzzed may give the answer.",
        "Teammates may not confer verbally or in writing during tossups, and no notes may be written while a tossup is being read.",
        "A contestant who buzzes has three seconds to begin an answer, subject to the moderator's non-protestable timing judgment.",
        "Second-quarter bonuses allow conferral, are worth ten points, and do not bounce back after an incorrect answer.",
        "The third-quarter category round gives each team sixty seconds, permits conferral, allows passes without return, and may award a twenty-point sweep bonus.",
        "Fourth-quarter tossups are worth thirty, twenty, or ten points depending on where the answer is given.",
        "A tied first or second place is broken by zero-point tossup questions until one team answers correctly.",
        "No pre-existing resources are allowed; a writing utensil and blank paper may be used to take notes where the phase permits.",
    ]
    replace_sources(
        card,
        [
            source(
                title="International History Bowl World Championships Official Rules Summary",
                url="https://www.historyolympiad.com/wp-content/uploads/2025/07/International-History-Bowl-World-Championships-Official-Rules.pdf",
                edition="2025 World Championships",
                sections=["pp. 1-3 four-quarter gameplay", "pp. 4-5 protests, resources, conduct, and supremacy"],
                local_file="data/rules/sources/history_olympiad/2025_International_History_Bowl_World_Championships_Rules.pdf",
            )
        ],
    )
    set_proxy_limitations(
        card,
        [
            "Historical benchmark packets do not declare the governing rules edition, so the 2025 roster and gameplay rules cannot be silently applied to every row.",
            "The runner lacks live opponents, buzzer lockout, moderator answer acceptance, phase clocks, protests, bouncebacks, and category selection state.",
        ],
    )
    card.setdefault("deliverable", {}).update(
        {
            "answer_format": (
                "Return numbered answers for the exposed questions and identify the quarter or "
                "phase; do not claim a live buzz, opponent outcome, or moderator ruling."
            ),
            "official_deliverable": "live_four_quarter_buzzer_match_responses",
            "official_mime_types": ["application/x-live-buzzer-match"],
            "mime_types": ["text/plain"],
        }
    )
    card.setdefault("submission", {})["adaptation"] = (
        "The runner grades a text packet or session without live buzzer, opponent, moderator, or protest state."
    )
    card["scoring"].update(
        {"mode": "edition_specific_match_score", "unit": "session", "evaluator_status": "deferred_ruleset_and_match_engine"}
    )
    set_official_scoring(
        card,
        completeness="complete_for_2025_world_championship_summary",
        mechanics=[
            "Quarter 1 correct tossups are worth 10 points and incorrect answers incur no point deduction.",
            "Quarter 2 correct tossups and their bonuses are each worth 10 points; bonuses do not bounce back.",
            "Quarter 3 awards points for category answers and a 20-point bonus for a complete sweep under the published phase rules.",
            "Quarter 4 correct tossups are worth 30, 20, or 10 points according to the clue boundary reached.",
        ],
        tie_breakers=["A zero-point tossup breaks a tie for first or second; additional tossups continue until one team answers correctly."],
        source_refs=["2025 World Championship Official Rules Summary pp. 1-3"],
        unresolved=["Historical benchmark rows require an edition selector before official match scoring is comparable."],
        violations=[
            {"id": "illegal_tossup_conferral", "condition": "Teammates confer verbally or in writing, or write notes, while a tossup is being read."},
            {"id": "answer_without_buzz_or_wrong_speaker", "condition": "A contestant answers without buzzing or a teammate answers for the contestant who buzzed."},
            {"id": "outside_resource", "condition": "A contestant uses a pre-existing resource during the match."},
        ],
    )


def correct_mystery_hunt(card: dict[str, Any]) -> None:
    card["team"].update(
        {
            "range_basis": "benchmark_adaptation",
            "official_roster_note": "The 2026 FAQ states no official team-size recommendation; 8-12 is only the runner's configured range.",
            "collaboration": "The configured agents may freely coordinate inside their benchmark team; they may not obtain answers from another competing team.",
        }
    )
    update_execution(card, 
        {
            "rules_edition": "2026",
            "full_hunt_unlock_state": "unavailable",
            "hint_and_interaction_state": "unavailable",
            "runaround_and_coin_state": "unavailable",
        }
    )
    card["human_constraints"] = [
        "The MIT Mystery Hunt does not publish an official team-size recommendation or an 8-12 person maximum.",
        "Teams may coordinate internally and use ordinary solving tools and internet resources unless the current hunt or puzzle states a narrower rule.",
        "A team must not ask another competing team for puzzle answers.",
        "Answers must be submitted in the canonical answer form accepted by the current hunt's answer mechanism.",
        "Remote participation does not reproduce every in-person interaction, and the in-person runaround is required to win the 2026 hunt.",
        "The 2026 winner must satisfy the hunt's MIT-student eligibility requirement and is expected to write the following year's hunt.",
    ]
    replace_sources(
        card,
        [
            source(
                title="MIT Mystery Hunt 2026 official site and FAQ",
                url="https://mitmh2026.com/",
                edition="2026",
                sections=["FAQ: team size, remote play, schedule, and win eligibility"],
                archive_status="url_verified_local_binding_text_not_archived",
            ),
            source(
                title="MIT Mystery Hunt and Puzzle Club official archive",
                url="https://puzzles.mit.edu/",
                edition="living archive",
                sections=["Hunt identity, annual structure, coin, and winning-team responsibility"],
                local_file="data/rules/sources/mystery_hunt/01_puzzles.mit.txt",
            ),
        ],
    )
    set_proxy_limitations(
        card,
        [
            "The configured 8-12-agent range is a benchmark capacity choice, not an official roster limit.",
            "Question-level rows omit full-hunt unlocking, metas, hints, interactions, rate limits, runaround, and coin verification.",
        ],
    )
    set_official_scoring(
        card,
        completeness="annual_rules_and_full_hunt_state_not_encoded",
        mechanics=["A task-level answer is accepted only when it matches the current puzzle's answer mechanism; this is not equivalent to winning the full hunt."],
        source_refs=["MIT Mystery Hunt 2026 FAQ and official archive"],
        unresolved=["Full-hunt progression, hint costs, interactions, final runaround, and coin-finding depend on the annual hunt implementation."],
    )


def correct_ioai(card: dict[str, Any]) -> None:
    card["allowed_tools"] = ["query_rules", "execute_code"]
    card["resources"].update(
        {
            "internet": "translation_site_only_unless_team_task_guide_allows_more",
            "code_execution": "task_specific_environment_only",
            "provided_materials_only": True,
        }
    )
    update_execution(card, 
        {
            "rules_edition": "2026_version_4",
            "required_selectors": ["team_challenge_round", "task_guide_version"],
            "selector_enforcement": "task_specific_guide_required",
            "official_minutes": None,
            "team_challenge_environment": "specified_by_separate_task_guide",
            "physical_final": "unavailable",
        }
    )
    card["human_constraints"] = [
        "The Team Challenge is an official team event, but its format, environment, and scoring are task-specific.",
        "Team Challenge tasks are provided in English, and contestants may use only the translation website designated by the organizers.",
        "Contestants may not communicate with people outside the contest hall during the Team Challenge.",
        "Approved and prohibited items follow the Team Challenge rules and task guide; permissions from the Individual Contest technical appendix do not automatically apply.",
        "Team Challenge scoring is announced in the task statements and must not be inferred from the Individual Contest normalization formula.",
        "The Team Challenge duration depends on its format and may range from a few hours to a full day; no single exact official duration is encoded here.",
        "Appeals must be filed through Team Leaders within the organizer's announced window.",
    ]
    replace_sources(
        card,
        [
            source(
                title="IOAI 2026 Contest Rules and Technical Appendix",
                url="https://ioai-official.org/wp-content/uploads/2026/06/IOAI2026-Contest-Rules-and-Tehnical-Appendix.pdf",
                edition="Contest Rules v4 May 2026; Technical Appendix v4 June 2026",
                sections=[
                    "Contest Rules section 3, pp. 8-9: Team Challenge",
                    "Technical Appendix p. 13: Team Challenge technical details are provided separately",
                    "Technical Appendix pp. 14-15 apply to Individual and GAITE, not automatically to Team Challenge",
                ],
                local_file="data/rules/sources/ioai_team/2026_IOAI_Contest_Rules_Technical_Appendix.pdf",
            )
        ],
    )
    set_proxy_limitations(
        card,
        [
            "The exact 2026 Team Challenge guide, simulator task statement, submission surface, and physical final are not encoded by the general contest rules.",
            "The runner cannot reproduce the physical robot final or official appeal process.",
        ],
    )
    card["scoring"]["evaluator_status"] = "deferred_team_task_guide"
    set_official_scoring(
        card,
        completeness="task_specific_not_encoded",
        mechanics=["The Team Challenge uses task-specific scoring announced in its task statements and awards the top team results separately from Individual Contest medals."],
        source_refs=["IOAI 2026 Contest Rules section 3, pp. 8-9"],
        unresolved=["Exact simulator metrics, submission limits, top-10 physical-final mechanics, and tie or appeal rules require the separate 2026 Team Challenge guide."],
    )


def correct_science_olympiad(card: dict[str, Any]) -> None:
    card["team"].update(
        {
            "active_min": 1,
            "active_default": 15,
            "active_max": 15,
            "range_basis": "benchmark_adaptation",
            "roster_max": 15,
            "official_roster_note": "Fifteen is a tournament roster cap, not the active participant count for one event.",
            "collaboration": "Only the participants authorized by the selected season, division, and event rules may collaborate on that event.",
        }
    )
    update_execution(card, 
        {
            "required_selectors": ["season", "division", "event"],
            "selector_enforcement": "missing_from_current_rows",
            "official_minutes": None,
            "event_rules": "not_selected",
            "event_corrections": "not_selected",
            "event_score_sheet": "not_selected",
        }
    )
    card["human_constraints"] = [
        "The Division B or C tournament roster may contain up to fifteen students, but this does not make all fifteen active participants in one event.",
        "Season, division, and event must be selected before active participants, time, tools, references, deliverable, and scoring can be treated as official.",
        "Only the references, calculators, devices, build materials, and safety equipment authorized by the selected event rules may be used.",
        "Official event corrections and clarifications modify the corresponding event rules and must be applied with the selected season packet.",
        "The event score sheet or rubric, not a generic Science Olympiad formula, determines official performance.",
        "No unrestricted web search is allowed unless the selected event rules explicitly authorize it.",
    ]
    replace_sources(
        card,
        [
            source(
                title="Science Olympiad official event and rules portal",
                url="https://www.soinc.org/",
                edition="season-specific; no event selected",
                sections=["Event rules release notice, event pages, corrections, and score sheets"],
                archive_status="binding_event_rules_not_selected_or_archived",
            )
        ],
    )
    set_proxy_limitations(
        card,
        [
            "The current row lacks season, division, and event selectors and therefore cannot select a binding event rulebook.",
            "The runner cannot reproduce event-dependent laboratory apparatus, constructed devices, impound, safety inspection, or physical performance.",
        ],
    )
    card["scoring"]["evaluator_status"] = "deferred_event_rules_not_selected"
    set_official_scoring(
        card,
        completeness="unavailable_until_event_selected",
        mechanics=[],
        unresolved=["All official scoring and tie breakers are event-, division-, and season-specific."],
        source_refs=["Selected Science Olympiad event rules, corrections, and score sheet are required."],
    )


def correct_science_bowl(card: dict[str, Any]) -> None:
    update_execution(card, 
        {
            "rules_edition": "2026_01_29",
            "official_minutes": None,
            "live_opponent_buzzer_moderator_and_clock": "unavailable",
        }
    )
    card["human_constraints"] = [
        "A team has four or five student members, with only four playing at one time.",
        "On tossups, quiet non-verbal communication is allowed, but verbal communication disqualifies the team from that tossup.",
        "Only the contestant recognized after buzzing may answer a tossup, and the first response is the only response counted.",
        "A correct tossup is worth four points and earns that team a bonus question worth ten points.",
        "The team may consult verbally on a bonus, and the captain gives the final bonus answer unless another member is explicitly designated under the rules.",
        "An incorrect interrupt adds four points to the opposing team's score and may leave the opposing team eligible to hear the full tossup.",
        "Challenges must be made by an active contestant within the official challenge window before the next question begins.",
        "The fifth student, coach, and spectators may not communicate with the four active contestants during a match.",
    ]
    replace_sources(
        card,
        [
            source(
                title="2026 National Science Bowl Official Academic Competition Rules",
                url="https://science.osti.gov/-/media/wdts/nsb/pdf/NSB-Resources/Rules2026.pdf",
                edition="2026, revised 2026-01-29",
                sections=["pp. 1-2 eligibility and roster", "pp. 3-9 gameplay, communication, scoring, and challenges", "pp. 10-13 tournament end rules"],
                local_file="data/rules/sources/science_bowl/2026_National_Science_Bowl_Academic_Rules.pdf",
            )
        ],
    )
    set_proxy_limitations(
        card,
        [
            "Question-level benchmark rows omit the opponent, buzzer recognition, interrupt and blurt state, bonus eligibility, match clock, moderator, and challenge process.",
        ],
    )
    set_official_scoring(
        card,
        completeness="complete_core_match_scoring_question_proxy_only",
        mechanics=[
            "A correct tossup is worth 4 points and makes a 10-point bonus available to that team.",
            "An incorrect answer after interrupting a tossup adds 4 points to the opposing team; the detailed double-interrupt rules govern subsequent eligibility.",
            "Match outcome and tournament advancement use the 2026 regional or national format and tie procedures, not question-level exact-answer accuracy alone.",
        ],
        source_refs=["2026 National Science Bowl Official Academic Competition Rules pp. 3-13"],
        unresolved=["The current benchmark evaluates isolated questions rather than official match and tournament state."],
        violations=[
            {"id": "verbal_tossup_conferral", "condition": "Active players communicate verbally during a tossup."},
            {"id": "inactive_person_assistance", "condition": "The fifth member, coach, or spectator communicates with active players during the match."},
        ],
    )


def correct_wro(card: dict[str, Any]) -> None:
    card["team"].update(
        {
            "range_basis": "source_record",
            "official_roster_note": "A 2026 RoboMission team consists of two or three students and is guided by a coach.",
            "collaboration": "The two or three student members design, build, and program the robot; a coach may guide learning but may not build or program it for the team.",
        }
    )
    update_execution(card, 
        {
            "rules_edition": "2026_robomission_general",
            "required_selectors": ["season", "category", "age_group", "jurisdiction", "game_document", "q_and_a_snapshot"],
            "selector_enforcement": "game_and_national_rules_missing_from_current_rows",
            "official_minutes": None,
            "robot_attempt_seconds": 120,
            "robot_environment": "unavailable",
            "inspection_quarantine_and_field_state": "unavailable",
        }
    )
    card["human_constraints"] = [
        "Under the 2026 RoboMission General Rules, a team consists of two or three students and one student with a coach is not a team.",
        "A student may participate in only one team and one WRO category during the season.",
        "Adults may guide and inspire but may not build, code, or program the robot for the team.",
        "The selected national organizer combines the General Rules, age-group game document, local rules, and binding official Q&A into the operative competition rules.",
        "A robot attempt ends after two minutes or earlier upon an official stop condition such as prohibited touching, leaving the table, or a rule violation.",
        "At the end of an attempt the judge scores the observed field state, records full seconds, and the team signs the score sheet; after sign-off no further complaint is allowed.",
        "A disqualified attempt receives the worst possible score and the maximum time of 120 seconds.",
        "Exact mission points, number of rounds, ranking, tie breakers, practice, quarantine, and optional competition elements depend on the selected game and organizer rules.",
    ]
    replace_sources(
        card,
        [
            source(
                title="WRO RoboMission Category General Rules",
                url="https://wro-association.org/wp-content/uploads/WRO-2026-RoboMission-General-Rules.pdf",
                edition="2026",
                sections=[
                    "pp. 2-4 scope, national assembly, team, and age groups",
                    "pp. 5-14 responsibilities, robot rules, event elements, and robot attempt",
                    "pp. 15-16 International Final format and glossary",
                    "p. 19 Appendix D is explicitly non-binding example material",
                ],
                local_file="data/rules/sources/wro/2026_WRO_RoboMission_General_Rules.pdf",
            ),
            source(
                title="WRO 2026 season documents",
                url="https://wro-association.org/competition/2026-season/",
                edition="2026",
                sections=["Category-specific General and Game Rules"],
                archive_status="selected_game_document_not_archived",
            ),
            source(
                title="WRO official Questions and Answers",
                url="https://wro-association.org/competition/questions-answers/",
                edition="2026 season snapshot required",
                sections=["Binding clarifications and additions"],
                archive_status="snapshot_not_selected",
            ),
        ],
    )
    set_proxy_limitations(
        card,
        [
            "The runner has no physical robot, inspection, quarantine, randomized field, judge, score sheet, or national tournament state.",
            "The selected age-group game document, jurisdiction rules, and Q&A snapshot are absent, so exact mission score and ranking are deferred.",
        ],
    )
    card.setdefault("deliverable", {}).update(
        {
            "answer_format": (
                "Submit the program and a structured design/run analysis; label simulated or "
                "hypothetical behavior and do not report an unobserved physical score."
            ),
            "official_deliverable": "inspected_robot_program_and_scored_field_attempt",
            "official_mime_types": ["application/x-physical-robot-attempt"],
            "mime_types": ["text/plain"],
        }
    )
    card.setdefault("submission", {})["adaptation"] = (
        "The runner accepts program text and analysis but cannot accept or score a physical robot attempt."
    )
    card["scoring"].update(
        {"mode": "selected_game_score_then_time", "unit": "robot_attempt", "evaluator_status": "deferred_physical_game_and_selectors"}
    )
    set_official_scoring(
        card,
        completeness="general_attempt_rules_only_game_scoring_unresolved",
        mechanics=[
            "The judge scores the field state when the robot attempt ends and records elapsed time in full seconds.",
            "A disqualified attempt receives the worst possible score and 120 seconds.",
            "Exact points, number of ranked runs, and tie resolution come from the selected game and national tournament format; Appendix D examples are not binding rules.",
        ],
        source_refs=["2026 RoboMission General Rules pp. 13-16; non-binding examples begin p. 19"],
        unresolved=["Age-group mission scoring, national tournament mode, number of runs, Q&A additions, and tie breakers are not selected."],
        violations=[
            {"id": "coach_authorship", "condition": "A coach or other adult builds, codes, or programs the robot for the team."},
            {"id": "field_or_robot_touch", "condition": "A team member touches the robot or mission objects during the run outside an allowed condition."},
            {"id": "unselected_ruleset_claim", "condition": "A score or ranking is claimed without the selected game, national rules, and Q&A snapshot."},
        ],
    )


def correct_unsafe_durations(card: dict[str, Any]) -> None:
    notes = {
        "arml_national_power": "The archived ARML competition-rules page does not establish a 60-minute Power Round clock; no exact official duration is encoded.",
        "arml_national_team": "The archived ARML competition-rules page does not establish a 20-minute Team Round clock; no exact official duration is encoded.",
        "arml_power": "The standalone Power Contest page does not establish a current 60-minute clock; no exact official duration is encoded.",
        "ieo_business_case": "The regulations establish preparation and presentation days but not one exact continuous 1,440-minute official clock.",
        "iiot": "The archived regulations describe the contest but the exact evaluated-edition duration has not been frozen here.",
        "ijso_practical": "The cited statutes say examinations normally last three to four hours; 240 minutes is not encoded as an exact current official duration.",
        "ioaa_group": "The group task is host-designed; the 90-minute 2023 example is not a universal current duration.",
    }
    note = notes.get(card["competition_id"])
    if not note:
        return
    card["execution"]["official_minutes"] = None
    provenance = dict(card.get("provenance") or {})
    provenance["official_time_note"] = note
    card["provenance"] = provenance


def normalize_source_metadata(card: dict[str, Any]) -> None:
    """Make unknown citation metadata explicit without promoting a source."""
    provenance = dict(card.get("provenance") or {})
    raw_sources = provenance.get("sources")
    if not raw_sources:
        return
    sources = [raw_sources] if isinstance(raw_sources, dict) else list(raw_sources)
    normalized: list[dict[str, Any]] = []
    for raw in sources:
        item = dict(raw)
        item.setdefault("authority", "unclassified")
        item.setdefault("edition", "not_frozen")
        item.setdefault("sections", [])
        if "archive_status" not in item:
            if item.get("local_file") or item.get("local_text"):
                item["archive_status"] = "local_capture_available"
            elif item.get("from_report"):
                item["archive_status"] = "locator_only_from_prior_report"
            else:
                item["archive_status"] = "not_locally_archived"
        normalized.append(item)
    provenance["sources"] = normalized
    card["provenance"] = provenance


CORRECTORS = {
    "ethics_bowl_appe": correct_appe,
    "ethics_bowl_nhseb": correct_nhseb,
    "history_olympiad": correct_history,
    "mystery_hunt": correct_mystery_hunt,
    "ioai_team": correct_ioai,
    "science_olympiad": correct_science_olympiad,
    "science_bowl": correct_science_bowl,
    "wro": correct_wro,
}


def apply_source_corrections(card: dict[str, Any]) -> dict[str, Any]:
    competition_id = card["competition_id"]
    if competition_id in HAND_AUTHORED_ICPC_QUALITY:
        return card
    set_review_metadata(card)
    corrector = CORRECTORS.get(competition_id)
    if corrector:
        corrector(card)
        provenance = dict(card.get("provenance") or {})
        provenance["discard_pre_source_review_rule_sections"] = True
        provenance["source_correction_revision"] = "2026-08-17-v1"
        card["provenance"] = provenance
    correct_unsafe_durations(card)
    normalize_source_metadata(card)
    return card


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    changed = 0
    for competition_id in iter_rule_card_ids(RULES):
        if competition_id in HAND_AUTHORED_ICPC_QUALITY:
            continue
        card = load_rule_card_payload(competition_id, rules_root=RULES, required=True)
        before = json.dumps(card, ensure_ascii=False, sort_keys=True)
        apply_source_corrections(card)
        after = json.dumps(card, ensure_ascii=False, sort_keys=True)
        if before == after:
            continue
        changed += 1
        print(competition_id)
        if not args.dry_run:
            write_rule_card_payload(competition_id, card, rules_root=RULES)
    suffix = " (dry run)" if args.dry_run else ""
    print(f"source-corrected {changed} non-ICPC cards{suffix}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
