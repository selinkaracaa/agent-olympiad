"""Generate first-draft cards for competitions missing from the rule-card store."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from write_role_duties import duties_for

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
INDEX = REPO / "data" / "benchmarks" / "index.json"
sys.path.insert(0, str(REPO / "src"))

from rules import iter_rule_card_ids, write_rule_card_payload  # noqa: E402

TOOL_REGISTRY = {
    "purple_comet": ["use_calculator"],
    "fyziklani": ["use_calculator"],
    "iiot": ["execute_code"],
    "icpc": ["execute_code"],
    "mcm": ["execute_code", "web_search"],
    "icm": ["execute_code", "web_search"],
    "ieo_business_case": ["use_calculator", "execute_code", "web_search"],
    "jessup": ["web_search"],
    "ijso_practical": ["use_calculator", "inspect_environment"],
    "ioaa_group": ["use_calculator", "read_star_chart"],
    "iol_team": [],
    "arml_power": [],
    "arml_national_team": [],
    "arml_national_power": [],
    "arml_local": [],
    "hmmt_team": [],
    "hmmt_guts": [],
    "wsc_writing": [],
    "cfa_research_challenge": ["use_calculator", "execute_code", "web_search"],
    "eoes": ["use_calculator", "inspect_environment"],
    "ethics_bowl_appe": [],
    "ethics_bowl_nhseb": [],
    "ichto": ["use_calculator", "execute_code", "web_search"],
    "pumac_power": ["use_calculator", "execute_code", "web_search"],
    "vis_moot": ["web_search"],
    "wharton_investment": ["use_calculator", "execute_code", "web_search"],
    "ccdc": ["inspect_environment"],
    "debatebench": [],
    "gcch_harvard": ["use_calculator", "execute_code", "web_search"],
    "ioai_team": ["execute_code", "web_search"],
    "wro": ["inspect_environment"],
    "envirothon": ["web_search"],
    "science_olympiad": ["use_calculator", "read_official_materials"],
    "odyssey_of_the_mind": [],
    "wmtc": [],
    "qanta": [],
    "science_bowl": [],
    "mystery_hunt": ["execute_code", "web_search"],
    "nyu_ctf_bench": ["execute_code", "web_search"],
    "cybench": [
        "inspect_environment",
        "start_environment",
        "execute_environment_command",
        "reset_environment",
    ],
    "history_olympiad": [],
}

# Explicit team ranges for draft cards. Defaults must match runnable benchmarks.
TEAM = {
    "ijso_practical": (3, 3, 3),
    "ieo_business_case": (3, 5, 5),
    "iol_team": (2, 4, 4),
    "ioaa_group": (5, 5, 5),
    "arml_power": (2, 15, 15),
    "arml_national_team": (15, 15, 15),
    "arml_national_power": (15, 15, 15),
    "wsc_writing": (3, 3, 3),
    "jessup": (2, 5, 5),
    "iiot": (4, 4, 4),
    "icpc": (3, 3, 3),
    "cfa_research_challenge": (3, 4, 5),
    "eoes": (3, 3, 3),
    "ethics_bowl_appe": (5, 5, 5),
    "ethics_bowl_nhseb": (5, 5, 5),
    "ichto": (3, 3, 3),
    "pumac_power": (8, 8, 8),
    "vis_moot": (2, 5, 5),
    "wharton_investment": (3, 5, 5),
    "ccdc": (8, 8, 8),
    "debatebench": (8, 8, 8),
    "gcch_harvard": (2, 4, 5),
    "history_olympiad": (4, 4, 4),
    "ioai_team": (4, 4, 4),
    "science_olympiad": (15, 15, 15),
    "wro": (2, 3, 3),
    "odyssey_of_the_mind": (5, 7, 7),
    "fyziklani": (1, 5, 5),
    "hmmt_guts": (6, 8, 8),
    "mystery_hunt": (8, 12, 12),
    "nyu_ctf_bench": (4, 5, 6),
    "cybench": (4, 5, 6),
}

PROTOCOLS = {
    "iol_team": "shared_answer",
    "ioaa_group": "shared_answer",
    "arml_power": "shared_answer",
    "arml_national_team": "shared_answer",
    "arml_national_power": "shared_answer",
    "hmmt_guts": "progressive_release",
    "fyziklani": "progressive_release",
    "mystery_hunt": "progressive_release",
    "history_olympiad": "buzzer_match_session_proxy",
    "icpc": "single_workstation_programming",
    "iiot": "single_workstation_programming",
    "cybench": "ctf_sandbox",
    "nyu_ctf_bench": "ctf_sandbox",
    "ccdc": "cyber_defense_proxy",
    "ijso_practical": "lab_practical_proxy",
    "eoes": "lab_practical_proxy",
    "ioaa_group": "shared_answer",
    "science_olympiad": "event_packet_proxy",
    "wro": "robotics_rules_proxy",
    "ieo_business_case": "research_artifact",
    "cfa_research_challenge": "research_artifact",
    "wharton_investment": "research_artifact",
    "gcch_harvard": "research_artifact",
    "jessup": "presentation_and_cross_examination",
    "vis_moot": "presentation_and_cross_examination",
    "ethics_bowl_appe": "presentation_and_cross_examination",
    "ethics_bowl_nhseb": "presentation_and_cross_examination",
    "ichto": "presentation_and_cross_examination",
    "debatebench": "presentation_and_cross_examination",
    "wsc_writing": "staged_collaborative_writing",
    "odyssey_of_the_mind": "creative_performance_proxy",
    "ioai_team": "research_artifact",
    "pumac_power": "shared_answer",
}

SOURCES = {
    "iol_team": [("IOL Regulations", "https://ioling.org/rules/rules.pdf")],
    "ioaa_group": [("IOAA", "https://ioaastrophysics.org/")],
    "arml_power": [("ARML Rules", "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public")],
    "arml_national_team": [("ARML Rules", "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public")],
    "arml_national_power": [("ARML Rules", "https://arml.com/ARML/arml_2019/page/index.php?page=competition_rules&page_type=public")],
    "ijso_practical": [("IJSO Statutes", "https://ijsoweb.org/qna/IJSO-Statutes-Qatar-2019.pdf")],
    "ieo_business_case": [("IEO Regulations", "https://files.ieo-official.org/IEO_Regulations_of_Competition.pdf")],
    "hmmt_guts": [("HMMT Testing", "https://www.hmmt.org/www/tournaments/testing")],
    "fyziklani": [("Physics Brawl Online Rules", "https://physicsbrawl.org/download/2025/rules-en-250901.pdf")],
    "icpc": [("ICPC Programming Environment", "https://icpc.global/worldfinals/programming-environment")],
    "iiot": [("IIOT Regulations", "https://iio.team/documents/Regulations.pdf")],
    "cybench": [("Cybench", "https://github.com/andyzorigin/cybench")],
    "nyu_ctf_bench": [("NYU CTF Bench", "https://github.com/NYU-LLM-CTF/NYU_CTF_Bench")],
    "mystery_hunt": [("MIT Mystery Hunt", "https://puzzles.mit.edu/")],
    "wsc_writing": [("World Scholar's Cup", "https://scholarscup.org/events/")],
    "jessup": [("Jessup", "https://www.ilsa.org/jessup/")],
    "cfa_research_challenge": [("CFA Research Challenge", "https://www.cfainstitute.org/insights/events/research-challenge")],
    "ethics_bowl_appe": [("APPE Ethics Bowl", "https://www.appe-ethics.org/cases-rules-guidelines/")],
    "ethics_bowl_nhseb": [("NHSEB", "https://nhseb.org/case-library")],
    "history_olympiad": [("History Olympiad", "https://www.historyolympiad.com/resources/")],
    "science_olympiad": [("Science Olympiad", "https://www.soinc.org/")],
    "wro": [("WRO", "https://wro-association.org/")],
    "odyssey_of_the_mind": [("Odyssey of the Mind", "https://odysseyofthemind.com/past-problems/")],
    "ccdc": [("NCCDC", "https://www.nationalccdc.org/")],
    "debatebench": [("DebateBench / BP", "https://huggingface.co/datasets")],
    "pumac_power": [("PUMaC Archives", "https://jason-shi-f9dm.squarespace.com/archives")],
    "vis_moot": [("Vis Moot", "https://www.vismoot.org/")],
    "wharton_investment": [("Wharton Global Youth", "https://globalyouth.wharton.upenn.edu/")],
    "gcch_harvard": [("GCCH 2026", "https://www.thecasecompetition.org/gcch-2026")],
    "ichto": [("IChTo", "http://ichto.org/en/problems/")],
    "eoes": [("EOES", "https://www.eoes.science/Previous%20olympiads/previous.html")],
    "ioai_team": [("IOAI", "https://ioai-official.org/resources/")],
}


def tools_for(cid: str) -> list[str]:
    tools = ["query_rules", *TOOL_REGISTRY.get(cid, [])]
    # preserve order, unique
    seen = set()
    out = []
    for tool in tools:
        if tool not in seen:
            seen.add(tool)
            out.append(tool)
    return out


def paper_only(cid: str) -> bool:
    return not any(
        t in tools_for(cid)
        for t in (
            "use_calculator",
            "execute_code",
            "web_search",
            "inspect_environment",
            "start_environment",
            "execute_environment_command",
            "read_official_materials",
            "read_star_chart",
        )
    )


def roles_for(size: int, titles: list[str], protocol: str = "") -> list[dict]:
    roles = []
    for i in range(size):
        title = titles[i] if i < len(titles) else "specialist and completeness checker"
        roles.append(
            {
                "name": f"Agent_{i + 1}",
                "title": title,
                "may_submit": i == 0,
                "duties": duties_for(title, protocol, may_submit=i == 0),
            }
        )
    return roles


TITLE_BANK = {
    "shared_answer": [
        "captain and synthesizer",
        "algebra / analysis specialist",
        "geometry specialist",
        "combinatorics specialist",
        "number theory specialist",
        "verifier",
        "problem splitter",
        "writeup checker",
    ],
    "progressive_release": [
        "captain and batch submitter",
        "fast solver A",
        "fast solver B",
        "verifier",
        "strategy lead",
        "scribe",
        "backup solver",
        "completeness checker",
    ],
    "single_workstation_programming": [
        "driver / synthesizer",
        "navigator / algorithm designer",
        "tester / edge-case hunter",
        "language reference reader",
    ],
    "ctf_sandbox": [
        "team lead",
        "web / crypto specialist",
        "pwn / reverse specialist",
        "forensics specialist",
        "note-taker / flag consolidator",
        "backup operator",
    ],
    "research_artifact": [
        "captain / editor",
        "analyst",
        "quant / modeler",
        "research lead",
        "slide / report designer",
    ],
    "presentation_and_cross_examination": [
        "captain / oralist",
        "researcher",
        "writer",
        "opponent prep",
        "judge-question specialist",
    ],
    "lab_practical_proxy": [
        "experiment lead",
        "data recorder",
        "analysis / calculations",
    ],
    "staged_collaborative_writing": [
        "planner / editor",
        "writer A",
        "writer B",
    ],
    "buzzer_match_session_proxy": [
        "captain",
        "history specialist",
        "geography / arts specialist",
        "science / misc specialist",
    ],
    "default": [
        "captain",
        "primary solver",
        "secondary solver",
        "verifier",
        "specialist",
        "scribe",
        "researcher",
    ],
}


def resources_for(cid: str, tools: list[str]) -> dict:
    res = {
        "internet": "allowed" if "web_search" in tools else "forbidden",
        "calculator": "allowed" if "use_calculator" in tools else "forbidden",
        "code_execution": "allowed" if "execute_code" in tools or "execute_environment_command" in tools else "forbidden",
        "paper_pencil": "allowed",
        "provided_materials_only": "web_search" not in tools,
    }
    if cid in {"icpc", "iiot"}:
        res["internet"] = "judge_only_or_forbidden"
        res["shared_workstation"] = True
    if cid == "purple_comet":
        res["solution_method_search"] = "forbidden"
        res["ai_tools"] = "forbidden"
    if cid == "fyziklani":
        res["generative_ai"] = "forbidden"
        res["internet"] = "allowed"
    if cid == "mystery_hunt":
        res["internet"] = "allowed"
        res["external_teams"] = "forbidden"
    if cid == "cybench":
        res["internet"] = "task_dependent"
        res["sandbox"] = "required"
    if cid in {"ijso_practical", "eoes"}:
        res["physical_lab"] = "proxy_unavailable"
    if cid == "wsc_writing":
        res["electronic_devices"] = "forbidden"
        res["internet"] = "forbidden"
    return res


def constraints_for(cid: str, name: str, tools: list[str], protocol: str, eval_unit: str) -> list[str]:
    base = [
        f"You are a human teammate in {name}, not an unconstrained AI assistant.",
        "Obey the rule card resources and allowed tools exactly.",
        "Do not contact coaches, other teams, or outsiders during the run.",
        "Do not claim access to answer keys, hidden tests, or judge-only files.",
    ]
    if paper_only(cid):
        base.append("Only paper-and-pencil style reasoning is available; do not invent calculators or browsers.")
    if "web_search" in tools:
        base.append("Web search is allowed only as contest rules permit; do not solicit outside human help.")
    else:
        base.append("Internet lookup is forbidden.")
    if "use_calculator" in tools:
        base.append("Use the calculator only for calculation, not as a substitute for contest reasoning.")
    if "execute_code" in tools:
        base.append("Code execution is limited to solving the contest task; do not escape the intended sandbox.")
    if protocol == "progressive_release":
        base.append("Do not assume later problem batches are visible before the current batch is handled.")
    if protocol == "single_workstation_programming":
        base.append("Treat the team as sharing one workstation; coordinate typing and testing.")
    if protocol == "ctf_sandbox":
        base.append("Work only inside the isolated challenge environment when runtime tools are available.")
    if eval_unit == "question":
        base.append("This row is one question/challenge unit, not necessarily a full live contest session.")
    if cid in {"ijso_practical", "eoes", "wro", "ccdc", "science_olympiad"}:
        base.append("Physical/live environment fidelity is incomplete; mark uncertain instrument actions explicitly.")
    if cid in {"ethics_bowl_appe", "ethics_bowl_nhseb", "debatebench", "jessup", "vis_moot", "ichto"}:
        base.append("Prepare arguments that can withstand judge or opponent questioning; avoid one-sided assertion.")
    if cid == "wsc_writing":
        base.append("Follow staged writing: plan together, write individually, then peer-edit without finishing a teammate's unfinished essay.")
    if cid == "fyziklani":
        base.append("Generative AI assistance is prohibited under online Physics Brawl rules.")
    return base


def answer_format_for(protocol: str, ctype: str) -> str:
    if protocol == "single_workstation_programming":
        return "Submit source code or the required program output for the programming judge."
    if protocol == "ctf_sandbox":
        return "Submit the recovered flag(s) / subtask answers clearly labeled."
    if protocol == "research_artifact":
        return "Submit a structured report or slide outline covering analysis, recommendation, and evidence."
    if protocol == "presentation_and_cross_examination":
        return "Submit the written memorial/case analysis and a concise oral outline."
    if protocol == "staged_collaborative_writing":
        return "Submit three essays or the staged writing portfolio required by the prompt."
    if protocol == "lab_practical_proxy":
        return "Submit a lab-style report: data, calculations, tables/graphs description, and conclusions."
    if ctype == "test_based":
        return "Submit the team's final answers in numbered order, using exact values when required."
    return "Submit the complete team deliverable requested by the problem statement."


def scoring_for(ctype: str, goldish: bool) -> dict:
    if goldish and ctype == "test_based":
        return {"mode": "gold", "unit": "problem_or_question"}
    if ctype == "test_based":
        return {"mode": "gold_or_judge", "unit": "problem_or_question"}
    return {"mode": "rubric", "unit": "artifact"}


def profile_for(cid: str, protocol: str, eval_unit: str) -> str:
    if cid in {
        "ijso_practical",
        "eoes",
        "wro",
        "ccdc",
        "science_olympiad",
        "odyssey_of_the_mind",
        "history_olympiad",
        "hmmt_guts",
        "fyziklani",
        "mystery_hunt",
        "debatebench",
        "ethics_bowl_appe",
        "ethics_bowl_nhseb",
    }:
        return "proxy"
    if eval_unit == "question":
        return "proxy"
    if cid in {"cybench", "nyu_ctf_bench"}:
        return "benchmark_native"
    return "official_equivalent"


def build_card(olympiad: dict, goldish: bool) -> dict:
    cid = olympiad["id"]
    name = olympiad["name"]
    ctype = olympiad.get("type") or "test_based"
    eval_unit = olympiad.get("eval_unit") or "session"
    amin, adef, amax = TEAM[cid]
    protocol = PROTOCOLS.get(cid, "shared_answer" if ctype == "test_based" else "research_artifact")
    tools = tools_for(cid)
    titles = TITLE_BANK.get(protocol, TITLE_BANK["default"])
    sources = [
        {"title": title, "url": url, "retrieved_at": "2026-08-10"}
        for title, url in SOURCES.get(cid, [(name, olympiad.get("source_url") or "")])
        if url
    ]
    return {
        "schema_version": "1.0",
        "rule_id": f"{cid}:draft_v1",
        "competition_id": cid,
        "profile": profile_for(cid, protocol, eval_unit),
        "protocol": protocol,
        "team": {
            "active_min": amin,
            "active_default": adef,
            "active_max": amax,
            "collaboration": "Collaborate only within the team under contest rules.",
        },
        "execution": {},
        "simulation": {
            "max_turns": 40 if eval_unit == "question" else 80 if adef >= 8 else 60,
            "scheduler": "src_collaboration_draft",
        },
        "allowed_tools": tools,
        "resources": resources_for(cid, tools),
        "human_constraints": constraints_for(cid, name, tools, protocol, eval_unit),
        "agent_roles": roles_for(adef, titles, protocol),
        "deliverable": {
            "answer_format": answer_format_for(protocol, ctype),
            "shared": True,
            "mime_types": ["text/plain"],
        },
        "scoring": scoring_for(ctype, goldish),
        "submission": {
            "max_count": 1,
        },
        "rules_text": (
            f"Draft rule card for {name}. Team size default {adef}. "
            f"Protocol={protocol}. Tools={tools or ['none']}. "
            "This is an initial machine-readable contestant rule profile for Agent Olympiad; "
            "verify against the cited official source before claiming full official equivalence."
        ),
        "provenance": {
            "status": "draft_v1",
            "sources": sources,
            "adaptations": [
                "max_turns is a safety budget, not necessarily the official wall-clock limit",
                "specialist roles are a research roster overlay",
                "physical/oral/live opponent fidelity may be incomplete in src/",
            ],
        },
        "comparability": {
            "overall": "draft",
            "dimensions": {
                "roster": "approximate",
                "timing": "adapted",
                "tools": "src_tool_surface",
                "scoring": scoring_for(ctype, goldish)["mode"],
                "environment": "proxy" if profile_for(cid, protocol, eval_unit) == "proxy" else "partial",
            },
        },
    }


def goldish_for(cid: str) -> bool:
    path = REPO / "data" / "benchmarks" / cid / "benchmark.json"
    if not path.exists():
        return False
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("problems") or []
    return any(
        (it.get("gold_label") or {}).get("expected_answer")
        or (it.get("gold_label") or {}).get("parts")
        or (it.get("gold_label") or {}).get("answers")
        for it in items
    )


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    existing = set(iter_rule_card_ids(RULES))
    written = []
    for olympiad in index["olympiads"]:
        cid = olympiad["id"]
        if cid in existing:
            continue
        if cid not in TEAM:
            raise SystemExit(f"Missing TEAM range for {cid}")
        card = build_card(olympiad, goldish_for(cid))
        write_rule_card_payload(cid, card, rules_root=RULES)
        written.append(cid)
    print(f"Wrote {len(written)} draft rule cards")
    for cid in written:
        print(f"  - {cid}")


if __name__ == "__main__":
    main()
