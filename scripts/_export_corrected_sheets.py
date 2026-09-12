"""Export corrected OTC/Vanilla by-competition tables for Google Sheets."""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
out = repo / "results" / "gold_suite_sheets_20260903"
out.mkdir(parents=True, exist_ok=True)

DESC = {
    "arml_local": "ARML local mathematics team rounds featuring multi-part problems completed collaboratively on one shared answer sheet.",
    "science_bowl": "Fast-paced science toss-up and bonus questions covering biology, chemistry, physics, mathematics, earth science, and energy.",
    "arml_national_team": "ARML National Team Round where teammates divide ten challenging mathematics problems and combine their answers.",
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
    "qanta": 240,
    "mystery_hunt": 261,
    "history_olympiad": 5642,
    "purple_comet": 350,
    "hmmt_guts": 36,
    "wmtc": 42,
}
ORDER = [
    "arml_local",
    "science_bowl",
    "arml_national_team",
    "qanta",
    "mystery_hunt",
    "history_olympiad",
    "purple_comet",
    "hmmt_guts",
    "wmtc",
]


def f(x) -> float:
    try:
        return float(str(x).replace("%", "").strip() or 0)
    except Exception:
        return 0.0


def acc_s(a: float) -> str:
    return f"{a:.3f}".rstrip("0").rstrip(".")


def mean_tokens(root: Path) -> float | None:
    toks: list[float] = []
    for p in root.glob("*/contest_session.json"):
        d = json.loads(p.read_text(encoding="utf-8"))
        t = (d.get("budget") or {}).get("tokens_used")
        if t is None:
            m = d.get("metrics") or {}
            t = m.get("tokens_used") or m.get("tokens")
        if t is not None:
            toks.append(float(t))
    return sum(toks) / len(toks) if toks else None


def from_summary(rows: list[dict], tok_fallback: float | None = None) -> dict:
    ok = [r for r in rows if str(r.get("status", "ok")).lower() in {"ok", ""} or r.get("task_utility")]
    if not ok:
        ok = rows
    n = len(ok)
    utils = [f(r.get("task_utility")) for r in ok]
    if all(u == 0 for u in utils):
        utils = []
        for r in ok:
            sc, mx = f(r.get("score")), f(r.get("max_score"))
            utils.append(sc / mx if mx else 0.0)
    nz = sum(1 for u in utils if u > 0)
    return {
        "N": n,
        "Acc": sum(utils) / n if n else 0.0,
        "CS": sum(f(r.get("coordination_score") or r.get("CS")) for r in ok) / n if n else 0.0,
        "API": sum(f(r.get("api_calls_used") or r.get("api_calls")) for r in ok) / n if n else 0.0,
        "tok": tok_fallback,
        "turns": sum(f(r.get("turns_used") or r.get("turns")) for r in ok) / n if n else 0.0,
        "nz": f"{nz}/{n}",
    }


def agg_gold(rows: list[dict], model_key: str) -> dict[str, dict]:
    by: dict[str, list] = defaultdict(list)
    for r in rows:
        if r.get("model") != model_key:
            continue
        by[r["competition"]].append(r)
    outd: dict[str, dict] = {}
    for cid, rs in by.items():
        utils = []
        for r in rs:
            a = str(r.get("accuracy") or "")
            if a.endswith("%"):
                utils.append(f(a[:-1]) / 100.0)
            else:
                sc, mx = f(r.get("score")), f(r.get("max_score"))
                utils.append(sc / mx if mx else 0.0)
        n = len(rs)
        nz = sum(1 for u in utils if u > 0)
        outd[cid] = {
            "N": n,
            "Acc": sum(utils) / n if n else 0.0,
            "CS": sum(f(r.get("CS")) for r in rs) / n if n else 0.0,
            "API": sum(f(r.get("api_calls")) for r in rs) / n if n else 0.0,
            "tok": sum(f(r.get("tokens")) for r in rs) / n if n else 0.0,
            "turns": sum(f(r.get("turns")) for r in rs) / n if n else 0.0,
            "nz": f"{nz}/{n}",
        }
    return outd


def total(d: dict[str, dict]) -> dict:
    n = sum(v["N"] for v in d.values())
    return {
        "N": n,
        "Acc": sum(v["N"] * v["Acc"] for v in d.values()) / n,
        "CS": sum(v["N"] * v["CS"] for v in d.values()) / n,
        "API": sum(v["N"] * v["API"] for v in d.values()) / n,
        "tok": sum(v["N"] * (v["tok"] or 0) for v in d.values()) / n,
        "turns": sum(v["N"] * v["turns"] for v in d.values()) / n,
        "nz": f"{sum(int(v['nz'].split('/')[0]) for v in d.values())}/{n}",
    }


def main() -> None:
    gold_rows = list(
        csv.DictReader((out / "all_per_session.tsv").open(encoding="utf-8"), delimiter="\t")
    )
    otc_gold = agg_gold(gold_rows, "OTC")
    van_gold = agg_gold(gold_rows, "Vanilla")

    nat_otc = list(
        csv.DictReader(
            (repo / "results/arml_national_team_clean_50turn_otc_20260904/summary.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )
    nat_van = list(
        csv.DictReader(
            (repo / "results/arml_national_team_clean_50turn_vanilla_20260904/summary.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )
    nat_otc_m = from_summary(
        nat_otc,
        tok_fallback=mean_tokens(repo / "results/arml_national_team_clean_50turn_otc_20260904"),
    )
    nat_van_m = from_summary(
        nat_van,
        tok_fallback=mean_tokens(repo / "results/arml_national_team_clean_50turn_vanilla_20260904")
        or 8155,
    )

    low = list(
        csv.DictReader(
            (repo / "results/otc_task_routing_low_accuracy_20260904/summary.tsv").open(
                encoding="utf-8"
            ),
            delimiter="\t",
        )
    )
    by_comp: dict[str, list] = defaultdict(list)
    for r in low:
        by_comp[r["competition_id"]].append(r)

    low_m: dict[str, dict] = {}
    for cid, rs in by_comp.items():
        toks: list[float] = []
        for r in rs:
            p = (
                repo
                / "results/otc_task_routing_low_accuracy_20260904"
                / r["problem_id"]
                / "contest_session.json"
            )
            if p.exists():
                d = json.loads(p.read_text(encoding="utf-8"))
                t = (d.get("budget") or {}).get("tokens_used")
                if t is not None:
                    toks.append(float(t))
        low_m[cid] = from_summary(rs, tok_fallback=(sum(toks) / len(toks) if toks else None))

    otc_corr: dict[str, dict] = {}
    for cid in ORDER:
        if cid == "arml_national_team":
            otc_corr[cid] = nat_otc_m
        elif cid in low_m:
            otc_corr[cid] = low_m[cid]
        else:
            otc_corr[cid] = otc_gold[cid]

    van_corr = dict(van_gold)
    van_corr["arml_national_team"] = nat_van_m
    otc_tot = total(otc_corr)
    van_tot = total(van_corr)

    header = [
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

    def block(title: str, note: str, data: dict[str, dict], tot: dict) -> list[list]:
        rows: list[list] = [[title], [note], header]
        for cid in ORDER:
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
                    int(round(m["tok"] or 0)),
                    round(m["turns"], 2),
                    m["nz"],
                ]
            )
        rows.append(
            [
                "TOTAL",
                "",
                tot["N"],
                sum(TQ.values()),
                acc_s(tot["Acc"]),
                round(tot["CS"], 2),
                round(tot["API"], 2),
                int(round(tot["tok"])),
                round(tot["turns"], 2),
                tot["nz"],
            ]
        )
        return rows

    rows_upload: list[list] = []
    rows_upload += block(
        "Open_table_coach (CORRECTED 2026-09-07)",
        "OTC Acc uses National clean 50-turn + low-accuracy routing rerun; Local/ScienceBowl/Qanta remain original gold",
        otc_corr,
        otc_tot,
    )
    rows_upload.append([])
    rows_upload += block(
        "Vanilla (National clean substituted; other comps original gold)",
        "Vanilla National uses clean 50-turn (0%); other Vanilla rows remain original gold",
        van_corr,
        van_tot,
    )
    rows_upload.append([])
    rows_upload.append(["Low-accuracy OTC rerun detail (strategic_team, 50 turns)"])
    rows_upload.append(
        [
            "competition",
            "N",
            "Acc",
            "nonzero",
            "mean CS",
            "mean API",
            "mean turns",
            "mean wall_s",
            "deadline_rate",
            "vs_gold_OTC",
        ]
    )
    gold_acc = {
        "mystery_hunt": 0.004,
        "history_olympiad": 0.08,
        "purple_comet": 0.0,
        "hmmt_guts": 0.0,
        "wmtc": 0.0,
    }
    for cid in [
        "mystery_hunt",
        "history_olympiad",
        "purple_comet",
        "hmmt_guts",
        "wmtc",
    ]:
        m = low_m[cid]
        rs = by_comp[cid]
        dl = sum(1 for r in rs if str(r.get("deadline_submission", "")).lower() == "true")
        wall = sum(f(r.get("wall_seconds")) for r in rs) / len(rs)
        rows_upload.append(
            [
                cid,
                m["N"],
                acc_s(m["Acc"]),
                m["nz"],
                round(m["CS"], 2),
                round(m["API"], 1),
                round(m["turns"], 1),
                round(wall, 0),
                f"{dl}/{m['N']}",
                acc_s(gold_acc[cid]),
            ]
        )

    rows_upload.append([])
    rows_upload.append(["National Team clean 50-turn paired"])
    rows_upload.append(
        ["year", "OTC Acc", "OTC score", "Van Acc", "OTC deadline", "OTC wall_s", "Van wall_s"]
    )
    nat_otc_by = {r["problem_id"]: r for r in nat_otc}
    nat_van_by = {r["problem_id"]: r for r in nat_van}
    for pid in sorted(nat_otc_by):
        o = nat_otc_by[pid]
        v = nat_van_by.get(pid, {})
        year = pid.split("_")[-1]
        rows_upload.append(
            [
                year,
                acc_s(f(o.get("task_utility"))),
                f"{o.get('score')}/{o.get('max_score')}",
                acc_s(f(v.get("task_utility"))),
                o.get("deadline_submission"),
                round(f(o.get("wall_seconds")), 0),
                round(f(v.get("wall_seconds")), 0),
            ]
        )

    csv_path = out / "corrected_for_google_sheets.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows_upload)

    tsv_path = out / "by_competition_corrected.tsv"
    with tsv_path.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, delimiter="\t").writerows(rows_upload)

    print("wrote", csv_path)
    print("wrote", tsv_path)
    print("OTC TOTAL Acc", acc_s(otc_tot["Acc"]), otc_tot["nz"])
    print("Van TOTAL Acc", acc_s(van_tot["Acc"]), van_tot["nz"])
    for cid in ORDER:
        print(
            cid,
            "OTC",
            acc_s(otc_corr[cid]["Acc"]),
            otc_corr[cid]["nz"],
            "| Van",
            acc_s(van_corr[cid]["Acc"]),
            van_corr[cid]["nz"],
        )


if __name__ == "__main__":
    main()
