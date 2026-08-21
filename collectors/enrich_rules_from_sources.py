"""
 Enrich the rule-card store using crawled sources + curated simulator matrix.

Usage:
  python collectors/enrich_rules_from_sources.py
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from constraint_hygiene import clean_constraints

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
SOURCES = RULES / "sources"
INDEX = REPO / "data" / "benchmarks" / "index.json"
sys.path.insert(0, str(REPO / "src"))

from rules import load_rule_card_payload, write_rule_card_payload  # noqa: E402

# Curated from docs/DATA_COLLECTION.md Simulator Matrix + official pages.
# These are contestant-facing hard constraints, not model guesses.
CURATED: dict[str, dict] = {
    "iol_team": {
        "time": "About 4 hours for the team contest.",
        "constraints": [
            "Exactly one shared team answer sheet for the whole team.",
            "Free collaboration among teammates is allowed.",
            "No calculators, phones, internet, or other electronic devices.",
            "No external dictionaries, notes, or reference materials unless organizers provide them.",
            "Work only from the official problem packet and blank paper.",
            "Write complete answers with enough linguistic justification for marking.",
        ],
    },
    "ioaa_group": {
        "time": "About 90 minutes for the group competition (edition-dependent).",
        "constraints": [
            "Use only organizer-provided calculators; personal calculators are banned.",
            "Geometry tools (compass, ruler, protractor) and organizer constants sheets are allowed when provided.",
            "No internet and no participant-brought formula collections.",
            "Box final numerical answers with units when required.",
            "Treat star charts / data tables as official provided materials only.",
        ],
    },
    "arml_local": {
        "time": "About 45 minutes.",
        "constraints": [
            "Paper and pencil only; calculators are banned on every ARML round.",
            "No phones, computers, internet, books, or notes.",
            "Collaborate freely within the six-person team.",
            "Submit one shared short-answer sheet; answers are usually exact values.",
            "Do not look up contest archives or answer keys.",
        ],
    },
    "arml_power": {
        "time": "About 1 hour per power round.",
        "constraints": [
            "Paper and pencil only; no calculators or electronic devices.",
            "Write proofs / justifications, not only final numbers.",
            "No internet, books, or outside help.",
            "Treat the packet as one shared team power round.",
        ],
    },
    "arml_national_team": {
        "time": "About 20 minutes.",
        "constraints": [
            "Paper and pencil only; no calculators or electronic devices.",
            "Team of about 15 students shares one answer process.",
            "Answers are short numerical values; no proofs required for the team round.",
            "No internet or outside references.",
        ],
    },
    "arml_national_power": {
        "time": "About 1 hour.",
        "constraints": [
            "Paper and pencil only; no calculators or electronic devices.",
            "Write multi-part proofs / justifications for the power round.",
            "No internet, phones, or outside help.",
        ],
    },
    "ijso_practical": {
        "time": "About 3–4 hours.",
        "constraints": [
            "Use only organizer-provided lab equipment and stationery.",
            "Organizer-provided calculator only; personal calculators may incur penalties.",
            "No bags, phones, internet, or personal formula sheets in the exam hall.",
            "Produce a lab report with data, calculations, tables, and graphs.",
            "Physical wet-lab fidelity may be proxied in software; do not invent instrument readings not provided.",
        ],
    },
    "ieo_business_case": {
        "time": "Preparation window plus presentation (often ~24h prep).",
        "constraints": [
            "Online and offline research materials and ordinary software are allowed.",
            "No contact with anyone outside the team during the case window.",
            "Deliver a slide deck / strategic report suitable for oral presentation.",
            "Do not modify the submission after the lock/deadline.",
        ],
    },
    "hmmt_guts": {
        "time": "80 minutes.",
        "constraints": [
            "No calculators, books, notes, drawing aids, laptops, or phones.",
            "Problems arrive in short batches (3 or 4); submit a batch before receiving the next.",
            "Answers are short-answer / numerical; collaborate within the team only.",
            "Do not assume later batches are visible early.",
            "Pencil and organizer scratch paper only.",
        ],
    },
    "fyziklani": {
        "time": "About 3 hours online.",
        "constraints": [
            "Online Physics Brawl: internet and literature are allowed; calculators are allowed.",
            "Generative AI is strictly prohibited and is grounds for disqualification.",
            "Submit numerical / short answers through the contest interface model.",
            "Do not contact non-participants for help.",
            "Note: in-person Fyziklání forbids internet; this benchmark follows the online ruleset.",
        ],
    },
    "purple_comet": {
        "time": "HS about 90 minutes / MS about 60 minutes (plus multi-day window historically).",
        "constraints": [
            "Up to six teammates may share one computer.",
            "Calculators and computation tools may evaluate expressions; they must not invent the method.",
            "No generative AI tools.",
            "No searching for solution methods or answer keys.",
            "Final answers must be non-negative integers in contest order.",
        ],
    },
    "wsc_writing": {
        "constraints": [
            "The team receives three to four prompts drawn from the six World Scholar's Cup subject areas.",
            "The team answers exactly three prompts.",
            "Each of the three teammates answers a different prompt.",
            "First prepare with teammates without using devices, then write independently, then review one another's work at the end.",
            "Write the response with pen or pencil.",
            "Responses may use a form appropriate to the prompt, including creative pieces, persuasive arguments, poems, or essays.",
        ],
    },
    "jessup": {
        "time": "Multi-month memorial preparation plus oral rounds.",
        "constraints": [
            "Legal research on public sources and provided databases is allowed.",
            "No outside coaching that writes the memorial for the team.",
            "Prepare Applicant and Respondent written memorials plus oral outlines.",
            "Arguments must withstand judge questioning.",
        ],
    },
    "iiot": {
        "time": "About 3–4 hours.",
        "constraints": [
            "Team of 4 shares two contest computers / VMs.",
            "Network access is restricted to the online judge; no general web browsing.",
            "Only C++ is accepted.",
            "USB and personal materials are disabled / forbidden.",
            "Use organizer-provided language reference only.",
            "Submit code to an automated judge mindset (AC/WA/TLE/RE).",
        ],
    },
    "icpc": {
        "time": "5 hours.",
        "constraints": [
            "Team of 3 shares exactly one workstation.",
            "No public internet on the contest machine; no root/sudo.",
            "Languages limited to the official environment set (C/C++/Java/Kotlin/Python 3).",
            "Only permitted printed reference materials (e.g. Team Reference Document rules) apply.",
            "No phones, extra devices, or outside human help.",
            "Submit programs to an automated judge; score by solves and time penalty.",
        ],
    },
    "science_bowl": {
        "time": "Official toss-up/bonus timing windows; this benchmark is question-level.",
        "constraints": [
            "No calculators, phones, internet, or notes.",
            "Toss-up: the recognized individual answers without team consultation.",
            "Bonus: team consultation is allowed; captain gives the official answer.",
            "Multiple-choice answers must choose W/X/Y/Z when present.",
            "Do not invent buzzer hardware, interruption scoring, or an opposing team.",
        ],
    },
    "qanta": {
        "time": "Question-level quiz-bowl proxy.",
        "constraints": [
            "No internet lookups or notes databases.",
            "Give a short canonical quiz-bowl answer, not an essay.",
            "Do not invent later clues or buzzer timing advantages.",
            "Collaborate only as the prompt structure allows.",
        ],
    },
    "wmtc": {
        "time": "Team-round session timing (edition-dependent).",
        "constraints": [
            "Paper and pencil team round only.",
            "No calculators, phones, or internet.",
            "Ignore individual/relay content if a source PDF mixed sections.",
            "Submit exact simplified mathematical answers on one shared sheet.",
        ],
    },
    "history_olympiad": {
        "time": "Bowl round / packet timing.",
        "constraints": [
            "No phones, internet, or notes during the bowl.",
            "Answer in History Bowl style from the provided clues only.",
            "Do not invent opposing-team buzzer dynamics beyond the prompt.",
        ],
    },
    "mystery_hunt": {
        "time": "Open-ended hunt timing; this row is one puzzle.",
        "constraints": [
            "Internet and ordinary tools are generally allowed for Mystery Hunt solving.",
            "Do not ask other competing teams for answers.",
            "Respect answer checker / rate-limit norms; do not spam guesses recklessly.",
            "Submit the canonical puzzle answer string.",
        ],
    },
    "cybench": {
        "time": "Agent iteration budget rather than human contest clock.",
        "constraints": [
            "Work inside the isolated challenge environment when runtime tools exist.",
            "Do not read judge-only metadata, solution folders, or hidden flags from the host.",
            "Use the provided target host, not host localhost shortcuts.",
            "Recover and submit the flag / subtask answers only.",
        ],
    },
    "nyu_ctf_bench": {
        "time": "Challenge-level CTF proxy.",
        "constraints": [
            "Treat each row as one CTF challenge.",
            "Use only authorized challenge assets and tools.",
            "Do not consult writeups for the same challenge if aiming for fair evaluation.",
            "Submit the flag string clearly.",
        ],
    },
    "cfa_research_challenge": {
        "constraints": [
            "Use only publicly available information.",
            "Produce an equity research report / presentation artifact.",
            "Advisor/mentor guidance is limited; outsiders must not write the report.",
            "Support recommendations with evidence and valuation reasoning.",
        ],
    },
    "ethics_bowl_appe": {
        "constraints": [
            "Cases may be studied in advance; answers are judged on reasoning quality.",
            "Be relevant, clear, and deliberative; anticipate judge questions.",
            "No outside coaching during the round.",
            "Do not invent a live opposing team unless the protocol provides one.",
        ],
    },
    "ethics_bowl_nhseb": {
        "constraints": [
            "Focus on ethical analysis, stakeholder impacts, and thoughtful deliberation.",
            "Be prepared for moderator/judge follow-ups.",
            "No phones or outside help during the presentation window.",
        ],
    },
    "debatebench": {
        "constraints": [
            "Follow British Parliamentary / WUDC role constraints implied by the transcript task.",
            "Do not invent evidence that the materials do not support.",
            "Respond as a debating team, not as an unconstrained essay writer.",
        ],
    },
    "vis_moot": {
        "constraints": [
            "Prepare arbitration memorials from the Vis problem packet.",
            "Legal research is allowed; outside drafting help is not.",
            "Write for both advocacy and oral defense.",
        ],
    },
    "wharton_investment": {
        "constraints": [
            "Research publicly available market information.",
            "Produce an investment thesis / portfolio rationale as a team.",
            "No contact with prohibited outside advisors beyond contest rules.",
        ],
    },
    # The organizer publishes no rulebook, so anything beyond the event page would
    # be invented. Constraints come from docs/rules_lowconf_2026-08-12.md instead.
    "gcch_harvard": {
        "constraints": [
            "Solve the business case as a team deliverable.",
        ],
    },
    "ichto": {
        "constraints": [
            "Prepare chemistry tournament reports/arguments for presentation and opposition.",
            "Cite reasoning clearly; be ready for opponent and jury questioning.",
            "Do not fabricate experimental results not supported by materials.",
        ],
    },
    "pumac_power": {
        "constraints": [
            "Power-round style proofs / multi-part math writeups.",
            "Use only tools explicitly allowed by the rule card.",
            "No answer-key lookup.",
        ],
    },
    "eoes": {
        "constraints": [
            "Team experimental science practical packet.",
            "Use organizer-style calculator / lab constraints; no internet.",
            "Physical instruments may be proxied; do not invent unavailable readings.",
        ],
    },
    "ioaa_group_extra": {},
    "ioai_team": {
        "constraints": [
            "Solve the team AI challenge from provided materials.",
            "Code and research tools are allowed only as listed in the rule card.",
            "Do not exfiltrate hidden tests or private grading data.",
        ],
    },
    "science_olympiad": {
        "constraints": [
            "Follow the free sample-event packet constraints.",
            "Use only allowed references listed for the event; many official manuals are membership-locked.",
            "No unrestricted web search unless the event rules explicitly allow it.",
        ],
    },
    "wro": {
        "constraints": [
            "Follow the season Games & Rules packet for the chosen age group / category.",
            "Robot construction and run scoring are physical; software is a proxy unless a simulator exists.",
            "Do not invent field scores unsupported by the rules packet.",
        ],
    },
    "odyssey_of_the_mind": {
        "constraints": [
            "Creative long-term / spontaneous problem solving under OM constraints.",
            "No outside assistance producing the solution for the team.",
            "Scoring packets may be incomplete in public data; stay faithful to the public synopsis.",
        ],
    },
    "ccdc": {
        "constraints": [
            "Cyber defense scenario brief / team packet only in this dataset.",
            "Live injects and full range VMs are not fully available; mark proxy limits.",
            "Do not attack systems outside the authorized scenario environment.",
        ],
    },
}


def load_crawl_bits(cid: str) -> dict:
    man = SOURCES / cid / "manifest.json"
    if not man.exists():
        return {"status": "missing", "quotes": [], "source_files": [], "urls": []}
    data = json.loads(man.read_text(encoding="utf-8"))
    quotes = []
    files = []
    urls = []
    for src in data.get("sources") or []:
        urls.append(src.get("url") or "")
        if src.get("status") == "ok":
            files.append(src.get("text_file") or src.get("raw_file"))
            preview = (src.get("text_preview") or "").strip()
            if preview:
                # keep a short grounded excerpt for provenance
                snippet = re.sub(r"\s+", " ", preview)[:500]
                quotes.append({"url": src.get("url"), "excerpt": snippet})
    # A "fallback notes" archive is something we wrote by hand after a blocked or
    # failed fetch, so it must not be reported as a successful crawl.
    fetched = [f for f in files if f and "fallback" not in Path(f).name.lower()]
    if not files:
        status = "error"
    elif not fetched:
        status = "fallback_notes"
    elif len(fetched) < len(files):
        status = "partial"
    else:
        status = "ok"
    return {"status": status, "quotes": quotes, "source_files": files, "urls": [u for u in urls if u]}


def default_constraints(cid: str, card: dict) -> list[str]:
    name = card.get("rules_text") or cid
    tools = card.get("allowed_tools") or []
    res = card.get("resources") or {}
    out = [
        f"You are a human contestant on the {cid} team, not an unconstrained assistant.",
        "Obey allowed tools and resource limits exactly.",
        "Do not contact coaches, other teams, or outsiders during the run.",
        "Do not access answer keys, solutions, or judge-only files.",
    ]
    if res.get("internet") in {"forbidden", False}:
        out.append("Internet access is forbidden.")
    if res.get("calculator") in {"forbidden", False}:
        out.append("Calculators are forbidden.")
    if "web_search" in tools:
        out.append("Web search is allowed only as contest rules permit.")
    if "execute_code" in tools:
        out.append("Use code execution only to solve the assigned contest task.")
    if (card.get("scoring") or {}).get("mode") == "gold":
        out.append("Aim for objectively checkable final answers matching the contest format.")
    return out


def enrich_card(cid: str, card: dict, crawl: dict) -> dict:
    curated = CURATED.get(cid, {})
    constraints = list(curated.get("constraints") or [])
    if not constraints:
        constraints = default_constraints(cid, card)

    # Always keep anti-cheating lines unique and first-class.
    mandatory = [
        "You must behave like a human teammate under official contest rules.",
        "Do not claim tools, internet, or materials that the rule card forbids.",
        "Do not look up answer keys or hidden solutions.",
    ]
    if "agent_constraints" in card:
        card["agent_constraints"] = mandatory
        candidates = constraints
    else:
        candidates = mandatory + constraints
    merged = []
    for item in candidates:
        if item not in merged:
            merged.append(item)

    provenance = dict(card.get("provenance") or {})
    external_manifest = bool(provenance.get("manifest"))
    time_note = curated.get("time")
    base_rules = str(card.get("rules_text") or "").strip()
    # Avoid duplicating enrichment suffixes on repeated runs.
    base_rules = re.split(r"\s*Official timing note:", base_rules, maxsplit=1)[0].strip()
    base_rules = re.split(r"\s*Grounded from crawled official source", base_rules, maxsplit=1)[0].strip()
    rules_bits = [base_rules]
    if time_note:
        rules_bits.append(f"Official timing note: {time_note}")
    if crawl.get("quotes") and not external_manifest:
        rules_bits.append(
            "Grounded from crawled official source excerpt(s); see provenance.crawled_excerpts."
        )
    rules_text = " ".join(bit for bit in rules_bits if bit).strip()

    if not external_manifest:
        sources = list(provenance.get("sources") or [])
        # refresh retrieved_at and attach local archives when crawl succeeded
        refreshed = []
        seen = set()
        for url in crawl.get("urls") or []:
            if url in seen:
                continue
            seen.add(url)
            refreshed.append(
                {
                    "title": next(
                        (s.get("title") for s in sources if s.get("url") == url),
                        url,
                    ),
                    "url": url,
                    "retrieved_at": datetime.now(timezone.utc).date().isoformat(),
                    "local_text": next(
                        (
                            f
                            for f in crawl.get("source_files") or []
                            if f and Path(f).name.startswith(Path(url).name[:20])
                        ),
                        (crawl.get("source_files") or [None])[0],
                    ),
                }
            )
        for src in sources:
            url = src.get("url")
            if url and url not in seen:
                refreshed.append(src)
                seen.add(url)
        provenance["sources"] = refreshed or sources
        provenance["crawl_status"] = crawl.get("status")
        provenance["crawled_excerpts"] = crawl.get("quotes") or []
        provenance["enriched_at"] = datetime.now(timezone.utc).isoformat()
        provenance["status"] = {
            "ok": "source_enriched_v1",
            "partial": "source_enriched_partial_v1",
            "fallback_notes": "hand_written_fallback_v1",
        }.get(str(crawl.get("status")), "draft_v1_unenriched_crawl")
        if time_note:
            provenance["official_time_note"] = time_note

    contestant_rules, research_notes = clean_constraints(merged)
    if research_notes:
        provenance["research_notes"] = research_notes
    else:
        provenance.pop("research_notes", None)

    card["human_constraints"] = contestant_rules
    card["rules_text"] = rules_text
    card["provenance"] = provenance

    deliverable = dict(card.get("deliverable") or {})
    if not deliverable.get("answer_format"):
        protocol = card.get("protocol") or ""
        if protocol == "shared_answer":
            deliverable["answer_format"] = (
                "Submit one shared numbered answer sheet with exact values where required."
            )
        elif protocol == "progressive_release":
            deliverable["answer_format"] = (
                "Submit answers for the currently released batch only, in order."
            )
        elif protocol == "single_workstation_programming":
            deliverable["answer_format"] = "Submit source code for the automated judge."
        elif protocol == "ctf_sandbox":
            deliverable["answer_format"] = "Submit recovered flag(s) clearly labeled."
        if deliverable.get("answer_format"):
            card["deliverable"] = deliverable

    return card


def main() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    updated = []
    for olympiad in index["olympiads"]:
        cid = olympiad["id"]
        card = load_rule_card_payload(cid, rules_root=RULES, required=True)
        crawl = load_crawl_bits(cid)
        enriched = enrich_card(cid, card, crawl)
        write_rule_card_payload(cid, enriched, rules_root=RULES)
        updated.append((cid, crawl.get("status"), len(enriched["human_constraints"])))
    print(f"enriched {len(updated)} rule cards")
    for cid, status, n in updated:
        print(f"  {cid}: crawl={status} constraints={n}")


if __name__ == "__main__":
    main()
