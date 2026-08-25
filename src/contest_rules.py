"""Contest rules audit: official constraints vs what the env already encodes.

Source of truth for human rules: docs/DATA_COLLECTION.md Simulator Matrix.
This module is the machine-readable gap tracker for Priority 1 (encode real rules).
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Encoding = Literal["encoded", "partial", "missing", "n/a"]


@dataclass(frozen=True)
class RuleField:
    """One contest constraint and how well the simulator supports it."""

    name: str
    official: str
    status: Encoding
    env_knob: str = ""
    notes: str = ""


@dataclass(frozen=True)
class ContestRules:
    competition_id: str
    display_name: str
    team_size: str
    duration: str
    shared_computers: str
    tools_official: str
    scoring_official: str
    penalties_official: str
    search_policy: Literal[
        "forbidden",
        "unrestricted",
        "judge_only",
        "no_solution_lookup",
        "organizer_only",
    ]
    fields: tuple[RuleField, ...] = ()
    # Runtime knobs the env SHOULD apply today
    encoded_tools: tuple[str, ...] = ()
    wrong_submission_penalty_minutes: int | None = None
    max_wrong_submissions: int | None = None
    progressive_batches: bool = False
    allow_partial_credit: bool = True

    def gaps(self) -> list[RuleField]:
        return [f for f in self.fields if f.status in {"partial", "missing"}]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["gap_count"] = len(self.gaps())
        return payload


def _f(name: str, official: str, status: Encoding, env_knob: str = "", notes: str = "") -> RuleField:
    return RuleField(name=name, official=official, status=status, env_knob=env_knob, notes=notes)


CONTEST_RULES: dict[str, ContestRules] = {
    "arml_local": ContestRules(
        competition_id="arml_local",
        display_name="ARML Local",
        team_size="6",
        duration="~1 hour team round (packet)",
        shared_computers="none (paper)",
        tools_official="paper/pencil only; no calculators",
        scoring_official="short numerical answers; 10×4 pts typical",
        penalties_official="none beyond wrong/blank answers",
        search_policy="forbidden",
        encoded_tools=(),
        fields=(
            _f("team_size", "6", "encoded", "TEAM_SIZE_MATRIX"),
            _f("tools", "no calculator / no devices", "encoded", "COMPETITION_TOOL_REGISTRY=[]"),
            _f("turns/time", "fixed contest clock", "encoded", "duration_minutes→max_turns", "proxied wall-clock via minutes_per_turn"),
            _f("gold grading", "official answers", "encoded", "gold_substring_match / gold_answer_v1"),
            _f("search ban", "no internet", "encoded", "web_search not in tools"),
        ),
    ),
    "arml_national_team": ContestRules(
        competition_id="arml_national_team",
        display_name="ARML National — Team",
        team_size="~15",
        duration="team round packet",
        shared_computers="none",
        tools_official="paper only; no calculators",
        scoring_official="short answers",
        penalties_official="none special",
        search_policy="forbidden",
        encoded_tools=(),
        fields=(
            _f("team_size", "~15", "encoded", "TEAM_SIZE_MATRIX=15"),
            _f("tools", "paper only", "encoded", "no tools"),
            _f("turns/time", "contest clock", "partial", "max_turns=50"),
        ),
    ),
    "arml_national_power": ContestRules(
        competition_id="arml_national_power",
        display_name="ARML National — Power",
        team_size="~15",
        duration="power round",
        shared_computers="none",
        tools_official="paper only",
        scoring_official="proofs / written justifications",
        penalties_official="partial credit via rubric",
        search_policy="forbidden",
        encoded_tools=(),
        allow_partial_credit=True,
        fields=(
            _f("tools", "paper only", "encoded", "no tools"),
            _f("rubric grading", "written proofs", "partial", "rubric_llm_v1", "not auto-run in env.grade_submission"),
            _f("turns/time", "contest clock", "partial", "max_turns=50"),
        ),
    ),
    "arml_power": ContestRules(
        competition_id="arml_power",
        display_name="ARML Power (mail-in)",
        team_size="flexible / large",
        duration="mail-in window",
        shared_computers="none",
        tools_official="paper only; no calculators",
        scoring_official="proofs",
        penalties_official="partial credit",
        search_policy="forbidden",
        encoded_tools=(),
        fields=(
            _f("tools", "paper only", "encoded", "no tools"),
            _f("team_size", "flexible", "partial", "TEAM_SIZE_MATRIX=15", "official size varies"),
        ),
    ),
    "icpc": ContestRules(
        competition_id="icpc",
        display_name="ICPC World Finals",
        team_size="3",
        duration="5 hours",
        shared_computers="1 shared workstation",
        tools_official="C/C++/Java/Kotlin/Python; TRD ≤25 pages; no internet",
        scoring_official="# solved then time penalty",
        penalties_official="20 minutes per wrong submission on eventually-solved problems",
        search_policy="forbidden",
        encoded_tools=("execute_code",),
        wrong_submission_penalty_minutes=20,
        fields=(
            _f("execute_code", "local compile/run", "partial", "execute_code", "Python sample judge ready; C++/Java + secret tests deferred"),
            _f("wrong-submit penalty", "20 min", "partial", "wrong_submission_penalty_minutes + simulated clock", "WA burns 20 min of remaining contest clock (not stacked onto ranking)"),
            _f("ranking", "#solved then time", "partial", "icpc_time_score", "time = simulated clock after WA burns; multi-problem WF ranking still open"),
            _f("no internet", "banned", "encoded", "no web_search"),
            _f("turns/time", "5h clock", "encoded", "duration_minutes=300 → turns", "wall-clock proxied via minutes_per_turn"),
            _f("shared computer", "1 workstation", "missing", "", "need exclusive tool lock / queue"),
            _f("team_size", "3", "encoded", "TEAM_SIZE_MATRIX"),
        ),
    ),
    "iiot": ContestRules(
        competition_id="iiot",
        display_name="IIOT",
        team_size="4",
        duration="contest session",
        shared_computers="2 VMs",
        tools_official="C++ only; judge-only network",
        scoring_official="automated judge verdicts",
        penalties_official="time / WA style (judge-dependent)",
        search_policy="judge_only",
        encoded_tools=("execute_code",),
        wrong_submission_penalty_minutes=20,
        fields=(
            _f("team_size", "4", "encoded", "TEAM_SIZE_MATRIX"),
            _f("language lock", "C++ only", "missing", "", "execute_code allows python today"),
            _f("network", "judge only", "partial", "no web_search", "need judge submit channel"),
            _f("online judge", "AC/WA/TLE/RE", "missing", "programming_judge"),
            _f("computers", "2 VMs", "missing", "", "shared-resource model"),
        ),
    ),
    "ieo_business_case": ContestRules(
        competition_id="ieo_business_case",
        display_name="IEO Business Case",
        team_size="3–5",
        duration="case prep window + presentation",
        shared_computers="unrestricted",
        tools_official="any software/internet; no outside humans; slides lock at deadline",
        scoring_official="slide + oral rubric",
        penalties_official="late lock / format",
        search_policy="unrestricted",
        encoded_tools=("web_search",),
        fields=(
            _f("web_search", "allowed", "partial", "web_search", "need answer-leak hook"),
            _f("slide deliverable", "HTML/PDF deck", "partial", "slide_deck_v1", "in-pipeline uses text proxy"),
            _f("oral", "presentation", "missing", "oral_performance_judge"),
            _f("deadline lock", "slides freeze", "missing", ""),
        ),
    ),
    "iol_team": ContestRules(
        competition_id="iol_team",
        display_name="IOL Team",
        team_size="4",
        duration="4 hours",
        shared_computers="none",
        tools_official="paper only",
        scoring_official="partial credit per sub-part",
        penalties_official="none special",
        search_policy="forbidden",
        encoded_tools=(),
        fields=(
            _f("tools", "paper only", "encoded", "no tools"),
            _f("partial credit", "sub-parts", "partial", "rubric_llm_v1"),
            _f("time", "4h", "partial", "max_turns=50"),
        ),
    ),
    "ioaa_group": ContestRules(
        competition_id="ioaa_group",
        display_name="IOAA Group",
        team_size="5",
        duration="group round",
        shared_computers="none",
        tools_official="organizer calculator + charts; no internet",
        scoring_official="boxed numerical answers",
        penalties_official="none special",
        search_policy="forbidden",
        encoded_tools=("use_calculator", "read_star_chart"),
        fields=(
            _f("calculator", "organizer only", "encoded", "use_calculator"),
            _f("star chart", "provided", "partial", "read_star_chart", "stub tool"),
            _f("no internet", "banned", "encoded", "no web_search"),
        ),
    ),
    "ijso_practical": ContestRules(
        competition_id="ijso_practical",
        display_name="IJSO Team Practical",
        team_size="3",
        duration="lab session",
        shared_computers="none",
        tools_official="lab equipment + organizer calculator",
        scoring_official="lab report rubric",
        penalties_official="own calculator → deduction",
        search_policy="forbidden",
        encoded_tools=("use_calculator", "read_lab_equipment"),
        fields=(
            _f("lab instruments", "physical", "partial", "read_lab_equipment", "proxy only"),
            _f("report grading", "rubric", "partial", "rubric_llm_v1"),
        ),
    ),
    "wsc_writing": ContestRules(
        competition_id="wsc_writing",
        display_name="WSC Collaborative Writing",
        team_size="3",
        duration="20+40+15 min stages",
        shared_computers="none (devices banned)",
        tools_official="handwritten only; staged plan/write/edit",
        scoring_official="essay rubric /28",
        penalties_official="cannot finish teammate's unfinished piece in edit stage",
        search_policy="forbidden",
        encoded_tools=(),
        fields=(
            _f("staged protocol", "plan/write/edit", "missing", "", "need stage machine"),
            _f("no devices", "banned", "encoded", "no tools"),
            _f("rubric", "/28", "encoded", "rubric_llm_v1 + wsc_writing_28_v1"),
        ),
    ),
    "jessup": ContestRules(
        competition_id="jessup",
        display_name="Jessup Moot Court",
        team_size="2–5",
        duration="~5 months prep",
        shared_computers="unrestricted",
        tools_official="full legal research DBs",
        scoring_official="memorial + oral",
        penalties_official="format / word limits",
        search_policy="unrestricted",
        encoded_tools=("web_search",),
        fields=(
            _f("memorial rubric", "written", "partial", "rubric_llm_v1"),
            _f("oral", "pleadings", "missing", "oral_performance_judge"),
            _f("search leak", "may find answers", "partial", "web_search", "need anti-cheat hook"),
        ),
    ),
    "iypt": ContestRules(
        competition_id="iypt",
        display_name="IYPT",
        team_size="5",
        duration="Physics Fights",
        shared_computers="any during fight",
        tools_official="all aids; no outside humans",
        scoring_official="Reporter/Opponent/Reviewer debate scores",
        penalties_official="role protocol",
        search_policy="unrestricted",
        encoded_tools=(),
        fields=(
            _f("tools", "all aids", "missing", "", "should allow web_search + code"),
            _f("oral fight roles", "R/O/Reviewer", "missing", ""),
            _f("search leak", "live lookup OK but not outside help", "partial", "", "anti-cheat still needed for answer keys"),
        ),
    ),
    "hmmt_team": ContestRules(
        competition_id="hmmt_team",
        display_name="HMMT Team",
        team_size="6–8",
        duration="team round",
        shared_computers="none",
        tools_official="no calculators / devices",
        scoring_official="short answers or proofs",
        penalties_official="none special",
        search_policy="forbidden",
        encoded_tools=(),
        fields=(
            _f("tools", "paper only", "encoded", "no tools"),
            _f("team_size", "6–8", "partial", "TEAM_SIZE_MATRIX=8"),
        ),
    ),
    "hmmt_guts": ContestRules(
        competition_id="hmmt_guts",
        display_name="HMMT Guts",
        team_size="6–8",
        duration="progressive batches",
        shared_computers="none",
        tools_official="paper only; runner fetches next batch",
        scoring_official="batch answers; time pressure",
        penalties_official="late batches worth less / missed",
        search_policy="forbidden",
        encoded_tools=(),
        progressive_batches=True,
        fields=(
            _f("progressive batches", "3–4 problems at a time", "missing", "progressive_batches", "flag only so far"),
            _f("tools", "paper only", "encoded", "no tools"),
        ),
    ),
    "mcm": ContestRules(
        competition_id="mcm",
        display_name="MCM",
        team_size="3",
        duration="99 hours",
        shared_computers="unrestricted",
        tools_official="any software/internet; AI with disclosure; no outside humans",
        scoring_official="≤25 page modeling report",
        penalties_official="page limit / AI disclosure",
        search_policy="unrestricted",
        encoded_tools=("execute_code", "web_search"),
        fields=(
            _f("tools", "code+web", "encoded", "execute_code,web_search"),
            _f("page limit", "≤25", "missing", ""),
            _f("AI disclosure", "required", "missing", ""),
            _f("search leak", "open web", "partial", "web_search", "need answer-leak hook"),
            _f("time", "99h", "partial", "max_turns=50", "turns proxy only"),
        ),
    ),
    "icm": ContestRules(
        competition_id="icm",
        display_name="ICM",
        team_size="3",
        duration="99 hours",
        shared_computers="unrestricted",
        tools_official="same as MCM",
        scoring_official="≤25 page report",
        penalties_official="page limit / AI disclosure",
        search_policy="unrestricted",
        encoded_tools=("execute_code", "web_search"),
        fields=(
            _f("tools", "code+web", "encoded", "execute_code,web_search"),
            _f("search leak", "open web", "partial", "web_search", "need answer-leak hook"),
        ),
    ),
    "fyziklani": ContestRules(
        competition_id="fyziklani",
        display_name="Fyziklání / Physics Brawl Online",
        team_size="≤5",
        duration="online queue session",
        shared_computers="internet-connected",
        tools_official="internet+calc OK; generative AI banned (online)",
        scoring_official="online judge short answers",
        penalties_official="queue / time",
        search_policy="no_solution_lookup",
        encoded_tools=("use_calculator",),
        fields=(
            _f("calculator", "allowed", "encoded", "use_calculator"),
            _f("internet", "allowed online", "missing", "", "web_search not enabled yet"),
            _f("AI ban", "no generative AI", "partial", "", "policy note only"),
            _f("answer lookup ban", "no solution search", "missing", "", "anti-cheat hook"),
        ),
    ),
    "purple_comet": ContestRules(
        competition_id="purple_comet",
        display_name="Purple Comet",
        team_size="1–6",
        duration="MS 60 / HS 90 min (plus 10-day window variants)",
        shared_computers="1 computer",
        tools_official="calc/CAS OK; no AI; no searching solution methods",
        scoring_official="non-negative integers",
        penalties_official="none special",
        search_policy="no_solution_lookup",
        encoded_tools=("use_calculator",),
        fields=(
            _f("calculator", "allowed", "encoded", "use_calculator"),
            _f("shared computer", "1", "missing", ""),
            _f("no AI / no method search", "banned", "partial", "", "anti-cheat hook"),
        ),
    ),
    "itym": ContestRules(
        competition_id="itym",
        display_name="ITYM",
        team_size="4–6",
        duration="multi-month prep + oral",
        shared_computers="laptop+projector at event",
        tools_official="prep: open; oral: pre-submitted PDF only",
        scoring_official="oral + quiz",
        penalties_official="no live edits during talk",
        search_policy="organizer_only",
        encoded_tools=(),
        fields=(
            _f("prep vs oral phases", "distinct rules", "missing", ""),
            _f("oral judge", "live", "missing", "oral_performance_judge"),
        ),
    ),
}


def get_contest_rules(competition_id: str) -> ContestRules | None:
    return CONTEST_RULES.get(competition_id)


def rules_report() -> dict[str, Any]:
    rows = []
    for cid, rules in sorted(CONTEST_RULES.items()):
        gaps = rules.gaps()
        rows.append(
            {
                "competition_id": cid,
                "display_name": rules.display_name,
                "search_policy": rules.search_policy,
                "encoded_tools": list(rules.encoded_tools),
                "wrong_submission_penalty_minutes": rules.wrong_submission_penalty_minutes,
                "gap_count": len(gaps),
                "gaps": [asdict(g) for g in gaps],
            }
        )
    return {
        "contests": len(rows),
        "total_gaps": sum(r["gap_count"] for r in rows),
        "results": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="Print JSON gap report")
    parser.add_argument("--competition", default=None)
    args = parser.parse_args()
    if args.competition:
        rules = get_contest_rules(args.competition)
        if rules is None:
            raise SystemExit(f"Unknown competition {args.competition}")
        print(json.dumps(rules.to_dict(), indent=2))
        return
    print(json.dumps(rules_report(), indent=2))


if __name__ == "__main__":
    main()
