"""Build paste-ready TSVs for Google Sheets tabs 3-6.

Composition (corrected suite + ARML protocol-v3 power rounds):
  - science_bowl / qanta: original gold
  - mystery_hunt / history / purple_comet / hmmt_guts / wmtc: OTC from
    task-routing low-acc rerun; Vanilla from original gold
  - arml_national_team: clean 50-turn (kept when protocol-v3 not yet preferred;
    protocol-v3 batch replaces it when present)
  - arml_local / arml_national_team / arml_national_power / arml_power:
    results/arml_all_protocol_v3_{otc,vanilla}_20260909 (power scores come
    from post-hoc rubric_llm via score_power_rubrics.py)
  - tab6 ICPC: gold_suite_sheets icpc_* TSVs (OTC + Vanilla only)
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
out = repo / "results" / "gold_suite_sheets_20260903" / "paste_tabs"
out.mkdir(parents=True, exist_ok=True)

DESC = {
    "arml_local": "ARML local mathematics team rounds featuring multi-part problems completed collaboratively on one shared answer sheet.",
    "science_bowl": "Fast-paced science toss-up and bonus questions covering biology, chemistry, physics, mathematics, earth science, and energy.",
    "arml_national_team": "ARML National Team Round where teammates divide ten challenging mathematics problems and combine their answers.",
    "arml_national_power": "ARML National Power Round — multi-part proof / exploration packets (50 pts) graded with per-contest rubrics.",
    "arml_power": "ARML Power Contest — multi-part proof / exploration packets (40 pts) graded with per-contest rubrics.",
    "qanta": "Quiz-bowl questions with progressively revealed clues requiring identification of a person, place, work, event, or concept.",
    "mystery_hunt": "MIT Mystery Hunt-style puzzles requiring teams to discover hidden mechanisms and extract a final answer.",
    "history_olympiad": "History questions requiring concise identification of historical people, places, events, and concepts.",
    "purple_comet": "A timed online team mathematics contest with short-answer problems for middle- and high-school divisions.",
    "hmmt_guts": "A fast HMMT team mathematics round where new problem sets are released throughout the contest.",
    "wmtc": "World Mathematics Team Championship rounds featuring challenging individual and collaborative mathematics problems.",
}
TQ = {
    "arml_local": 44,
    "science_bowl": 140,
    "arml_national_team": 108,
    "arml_national_power": 11,
    "arml_power": 15,
    "qanta": 240,
    "mystery_hunt": 261,
    "history_olympiad": 5642,
    "purple_comet": 350,
    "hmmt_guts": 36,
    "wmtc": 42,
}
ORDER = list(DESC)

ARML_PROTOCOL_OTC = repo / "results" / "arml_all_protocol_v3_otc_20260909"
ARML_PROTOCOL_VAN = repo / "results" / "arml_all_protocol_v3_vanilla_20260909"
ARML_COMPS = {
    "arml_local",
    "arml_national_team",
    "arml_national_power",
    "arml_power",
}


def f(x) -> float:
    try:
        return float(str(x).replace("%", "").strip() or 0)
    except Exception:
        return 0.0


def acc_s(a: float) -> str:
    return f"{a:.3f}".rstrip("0").rstrip(".")


def pct(a: float) -> str:
    return f"{a * 100:.2f}%"


# contest_session_v4 desk-action diagnostics (blank for older sessions).
DESK_COLUMNS = {
    "protocol": None,
    "inspect": "inspect_count",
    "notes": "notes_recorded",
    "notes_shared": "notes_shared",
    "recalls": "recall_count",
    "triage": "triage_changes",
    "hopeless": "items_hopeless",
    "repeat_drafts": "repeat_draft_attempts",
}


def desk_columns(d: dict) -> dict:
    diagnostics = d.get("diagnostics") or {}
    columns = {"protocol": d.get("protocol_version") or ""}
    for column, key in DESK_COLUMNS.items():
        if key is not None:
            value = diagnostics.get(key)
            columns[column] = "" if value is None else value
    return columns


def session_metrics(path: Path) -> dict:
    d = json.loads(path.read_text(encoding="utf-8"))
    grade = d.get("grade") or {}
    metrics = d.get("metrics") or {}
    budget = d.get("budget") or {}
    timing = d.get("timing") or {}
    collab = metrics.get("collaboration") or metrics.get("multi_agent") or {}
    score = grade.get("score")
    max_score = grade.get("max_score")
    if score is None:
        score = metrics.get("score") or 0
    if max_score is None:
        max_score = metrics.get("max_score") or 0
    score = float(score or 0)
    max_score = float(max_score or 0)
    util = metrics.get("task_utility")
    if util is None:
        util = grade.get("task_utility")
    if util is None:
        util = score / max_score if max_score else 0.0
    else:
        util = float(util)
    comm = float(
        metrics.get("communication_score")
        or collab.get("communication")
        or collab.get("Communication")
        or metrics.get("communication")
        or 0
    )
    plan = float(
        metrics.get("planning_score")
        or collab.get("planning")
        or collab.get("Planning")
        or metrics.get("planning")
        or 0
    )
    cs = float(
        metrics.get("coordination_score")
        or collab.get("coordination_score")
        or collab.get("CS")
        or 0
    )
    if not cs and (comm or plan):
        cs = (comm + plan) / 2
    return {
        "score": score,
        "max_score": max_score,
        "accuracy": pct(util),
        "Communication": round(comm, 2) if comm else "",
        "Planning": round(plan, 2) if plan else "",
        "CS": round(cs, 2) if cs else "",
        "turns": budget.get("turns_used") or metrics.get("turns_used") or "",
        "api_calls": budget.get("api_calls_used") or metrics.get("api_calls_used") or "",
        "tokens": budget.get("tokens_used") or metrics.get("tokens_used") or "",
        "sec": round(float(timing.get("elapsed_seconds") or budget.get("wall_seconds_used") or 0), 0)
        or "",
        "util": util,
        "comm": comm,
        "plan": plan,
        "cs": cs,
        "turns_n": float(budget.get("turns_used") or 0),
        "api_n": float(budget.get("api_calls_used") or 0),
        "tok_n": float(budget.get("tokens_used") or 0),
        **desk_columns(d),
    }


def load_summary_rows(
    summary: Path,
    sessions_root: Path,
    model: str,
    *,
    competitions: set[str] | None = None,
) -> list[dict]:
    rows = []
    if not summary.is_file():
        return rows
    for r in csv.DictReader(summary.open(encoding="utf-8"), delimiter="\t"):
        pid = r["problem_id"]
        cid = r.get("competition_id") or ""
        if competitions is not None and cid not in competitions:
            continue
        if r.get("status") and r["status"] not in {"ok", "skipped_complete"}:
            # still include if session exists and was graded
            sess = sessions_root / pid / "contest_session.json"
            if not sess.exists():
                continue
        sess = sessions_root / pid / "contest_session.json"
        if sess.exists():
            m = session_metrics(sess)
        else:
            util = f(r.get("task_utility"))
            sc, mx = f(r.get("score")), f(r.get("max_score"))
            m = {
                "score": sc,
                "max_score": mx,
                "accuracy": pct(util),
                "Communication": "",
                "Planning": "",
                "CS": f(r.get("coordination_score")),
                "turns": r.get("turns_used") or "",
                "api_calls": r.get("api_calls_used") or "",
                "tokens": "",
                "sec": round(f(r.get("wall_seconds")), 0) or "",
                "util": util,
                "comm": 0.0,
                "plan": 0.0,
                "cs": f(r.get("coordination_score")),
                "turns_n": f(r.get("turns_used")),
                "api_n": f(r.get("api_calls_used")),
                "tok_n": 0.0,
                **{column: "" for column in DESK_COLUMNS},
            }
        rows.append(
            {
                "model": model,
                "competition": cid,
                "problem_id": pid,
                **{
                    k: m[k]
                    for k in [
                        "score",
                        "max_score",
                        "accuracy",
                        "Communication",
                        "Planning",
                        "CS",
                        "turns",
                        "api_calls",
                        "tokens",
                        "sec",
                        *DESK_COLUMNS,
                    ]
                },
                "_util": m["util"],
                "_cs": m["cs"],
                "_api": m["api_n"],
                "_tok": m["tok_n"],
                "_turns": m["turns_n"],
            }
        )
    return rows


def write_tsv(path: Path, rows: list[list]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, delimiter="\t", lineterminator="\n").writerows(rows)


def enrich_gold(rows: list[dict], model: str) -> list[dict]:
    out_rows = []
    for r in rows:
        util = f(str(r["accuracy"]).rstrip("%")) / 100.0
        out_rows.append(
            {
                **r,
                "model": model,
                "_util": util,
                "_cs": f(r.get("CS")),
                "_api": f(r.get("api_calls")),
                "_tok": f(r.get("tokens")),
                "_turns": f(r.get("turns")),
            }
        )
    return out_rows


def main() -> None:
    gold_otc = list(
        csv.DictReader(
            (repo / "results/gold_suite_sheets_20260903/otc_per_session.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )
    gold_van = list(
        csv.DictReader(
            (repo / "results/gold_suite_sheets_20260903/vanilla_per_session.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )

    # Low-accuracy OTC protocol-fix rerun (History / MH / Purple / HMMT / WMTC)
    low = load_summary_rows(
        repo / "results/otc_task_routing_low_accuracy_20260904/summary.tsv",
        repo / "results/otc_task_routing_low_accuracy_20260904",
        "OTC",
    )
    low_by_comp = {r["competition"] for r in low}

    # Prefer full ARML protocol-v3 batches when complete enough.
    arml_otc = load_summary_rows(
        ARML_PROTOCOL_OTC / "summary.tsv",
        ARML_PROTOCOL_OTC,
        "OTC",
        competitions=ARML_COMPS,
    )
    arml_van = load_summary_rows(
        ARML_PROTOCOL_VAN / "summary.tsv",
        ARML_PROTOCOL_VAN,
        "Vanilla",
        competitions=ARML_COMPS,
    )
    arml_otc_comps = {r["competition"] for r in arml_otc}
    arml_van_comps = {r["competition"] for r in arml_van}

    # Fallback: clean National Team if protocol batch missing that competition.
    nat_otc = load_summary_rows(
        repo / "results/arml_national_team_clean_50turn_otc_20260904/summary.tsv",
        repo / "results/arml_national_team_clean_50turn_otc_20260904",
        "OTC",
    )
    nat_van = load_summary_rows(
        repo / "results/arml_national_team_clean_50turn_vanilla_20260904/summary.tsv",
        repo / "results/arml_national_team_clean_50turn_vanilla_20260904",
        "Vanilla",
    )

    replace_otc = ARML_COMPS | low_by_comp
    replace_van = ARML_COMPS

    otc_rows = [
        r for r in enrich_gold(gold_otc, "OTC") if r["competition"] not in replace_otc
    ]
    otc_rows += low + arml_otc
    if "arml_national_team" not in arml_otc_comps:
        otc_rows += nat_otc

    van_rows = [
        r for r in enrich_gold(gold_van, "Vanilla") if r["competition"] not in replace_van
    ]
    van_rows += arml_van
    if "arml_national_team" not in arml_van_comps:
        van_rows += nat_van

    missing_otc = [c for c in ORDER if c not in {r["competition"] for r in otc_rows}]
    missing_van = [c for c in ORDER if c not in {r["competition"] for r in van_rows}]
    if missing_otc or missing_van:
        print("WARNING missing competitions OTC:", missing_otc, "Vanilla:", missing_van)

    comp_rank = {c: i for i, c in enumerate(ORDER)}
    otc_rows.sort(key=lambda r: (comp_rank.get(r["competition"], 99), r["problem_id"]))
    van_rows.sort(key=lambda r: (comp_rank.get(r["competition"], 99), r["problem_id"]))

    def agg(rows: list[dict]) -> dict[str, dict]:
        by: dict[str, list] = defaultdict(list)
        for r in rows:
            by[r["competition"]].append(r)
        outd = {}
        for cid, rs in by.items():
            n = len(rs)
            nz = sum(1 for r in rs if r["_util"] > 0)
            outd[cid] = {
                "N": n,
                "Acc": sum(r["_util"] for r in rs) / n,
                "CS": sum(r["_cs"] for r in rs) / n,
                "API": sum(r["_api"] for r in rs) / n,
                "tok": sum(r["_tok"] for r in rs) / n,
                "turns": sum(r["_turns"] for r in rs) / n,
                "nz": f"{nz}/{n}",
            }
        return outd

    def total(d: dict[str, dict]) -> dict:
        present = {k: v for k, v in d.items() if k in ORDER}
        n = sum(v["N"] for v in present.values())
        return {
            "N": n,
            "Acc": sum(v["N"] * v["Acc"] for v in present.values()) / n if n else 0.0,
            "CS": sum(v["N"] * v["CS"] for v in present.values()) / n if n else 0.0,
            "API": sum(v["N"] * v["API"] for v in present.values()) / n if n else 0.0,
            "tok": sum(v["N"] * v["tok"] for v in present.values()) / n if n else 0.0,
            "turns": sum(v["N"] * v["turns"] for v in present.values()) / n if n else 0.0,
            "nz": f"{sum(int(v['nz'].split('/')[0]) for v in present.values())}/{n}",
        }

    otc_agg = agg(otc_rows)
    van_agg = agg(van_rows)
    otc_tot = total(otc_agg)
    van_tot = total(van_agg)

    header3 = [
        "Competition",
        "Description",
        "sessions",
        "total_questions",
        "Acc",
        "CS",
        "mean API",
        "mean tok",
        "mean turns",
        "non-zero scores",
    ]

    def block(title: str, data: dict[str, dict], tot: dict) -> list[list]:
        rows = [[title], header3]
        for cid in ORDER:
            if cid not in data:
                continue
            m = data[cid]
            rows.append(
                [
                    cid,
                    DESC[cid],
                    m["N"],
                    TQ[cid],
                    acc_s(m["Acc"]),
                    round(m["CS"], 2),
                    round(m["API"], 2),
                    int(round(m["tok"])),
                    round(m["turns"], 2),
                    m["nz"],
                ]
            )
        rows.append(
            [
                "TOTAL",
                "",
                tot["N"],
                sum(TQ[c] for c in ORDER if c in data),
                acc_s(tot["Acc"]),
                round(tot["CS"], 2),
                round(tot["API"], 2),
                int(round(tot["tok"])),
                round(tot["turns"], 2),
                tot["nz"],
            ]
        )
        return rows

    tab3 = block("Open_table_coach", otc_agg, otc_tot)
    tab3.append([])
    tab3 += block("Vanilla", van_agg, van_tot)
    write_tsv(out / "tab3_by_competition.tsv", tab3)

    h4 = [
        "model",
        "competition",
        "problem_id",
        "score",
        "max_score",
        "accuracy",
        "Communication",
        "Planning",
        "CS",
        "turns",
        "api_calls",
        "tokens",
        "sec",
        *DESK_COLUMNS,
    ]
    tab4 = [h4] + [[r.get(k, "") for k in h4] for r in otc_rows]
    write_tsv(out / "tab4_otc_per_session.tsv", tab4)
    tab5 = [h4] + [[r.get(k, "") for k in h4] for r in van_rows]
    write_tsv(out / "tab5_vanilla_per_session.tsv", tab5)

    icpc_sum = list(
        csv.DictReader(
            (repo / "results/gold_suite_sheets_20260903/icpc_session_summary.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )
    icpc_task = list(
        csv.DictReader(
            (repo / "results/gold_suite_sheets_20260903/icpc_per_task.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )
    tab6 = [["gpt-5.4 mini"]]
    h6s = [
        "model",
        "contest",
        "Acc",
        "score",
        "max_score",
        "CS",
        "Comm",
        "Plan",
        "AAR",
        "AB",
        "turns",
        "api_calls",
        "tokens",
        "penalty_min",
        "remote_attempts",
    ]
    tab6.append(h6s)
    for r in icpc_sum:
        if r["model"] not in {"OTC", "Vanilla"}:
            continue
        tab6.append([r.get(k, "") for k in h6s])
    tab6.append([])
    h6t = [
        "model",
        "contest",
        "task_id",
        "score",
        "max_score",
        "accuracy",
        "state",
        "terminal_verdict",
    ]
    tab6.append(h6t)
    for r in icpc_task:
        if r["model"] not in {"OTC", "Vanilla"}:
            continue
        tab6.append([r.get(k, "") for k in h6t])
    write_tsv(out / "tab6_icpc.tsv", tab6)

    print("wrote", out)
    for p in sorted(out.glob("tab*.tsv")):
        print(p.name, "lines", sum(1 for _ in p.open(encoding="utf-8")))
    print("OTC TOTAL", acc_s(otc_tot["Acc"]), otc_tot["nz"], "N", otc_tot["N"])
    print("Van TOTAL", acc_s(van_tot["Acc"]), van_tot["nz"], "N", van_tot["N"])
    for cid in ORDER:
        if cid in otc_agg:
            print(
                f"  OTC {cid:24s} Acc={acc_s(otc_agg[cid]['Acc']):6s} "
                f"N={otc_agg[cid]['N']} nz={otc_agg[cid]['nz']}"
            )


if __name__ == "__main__":
    main()
