"""Build latest tab3-style overview with protocol-v3 ARML + corrected gold suite."""
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
ARML = {
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


def competition_of(pid: str) -> str:
    if pid.startswith("arml_national_power"):
        return "arml_national_power"
    if pid.startswith("arml_national_team"):
        return "arml_national_team"
    if pid.startswith("arml_power"):
        return "arml_power"
    if pid.startswith("arml_local"):
        return "arml_local"
    return ""


def session_row(model: str, path: Path) -> dict | None:
    d = json.loads(path.read_text(encoding="utf-8"))
    pid = path.parent.name
    cid = competition_of(pid) or str(d.get("competition_id") or "")
    g = d.get("grade") or {}
    m = d.get("metrics") or {}
    b = d.get("budget") or {}
    collab = m.get("collaboration") or m.get("multi_agent") or {}

    # Skip power sessions that have not been rubric-scored yet.
    if cid in {"arml_national_power", "arml_power"}:
        if g.get("method") == "contest_session_v1" and g.get("score") is None:
            return None
        tasks = g.get("tasks") or {}
        if tasks and all(t.get("status") == "unavailable" for t in tasks.values()):
            return None

    util = m.get("task_utility")
    if util is None:
        util = g.get("task_utility")
    sc, mx = g.get("score"), g.get("max_score")
    if util is None:
        util = float(sc) / float(mx) if sc is not None and mx else 0.0
    else:
        util = float(util)

    cs = float(m.get("coordination_score") or collab.get("coordination_score") or 0)
    if not cs:
        comm = float(
            m.get("communication_score")
            or collab.get("communication")
            or collab.get("Communication")
            or 0
        )
        plan = float(
            m.get("planning_score") or collab.get("planning") or collab.get("Planning") or 0
        )
        if comm or plan:
            cs = (comm + plan) / 2

    return {
        "model": model,
        "competition": cid,
        "problem_id": pid,
        "_util": util,
        "_cs": cs,
        "_api": float(b.get("api_calls_used") or m.get("api_calls_used") or 0),
        "_tok": float(b.get("tokens_used") or m.get("tokens_used") or 0),
        "_turns": float(b.get("turns_used") or m.get("turns_used") or 0),
    }


def load_gold(path: Path, model: str, exclude: set[str]) -> list[dict]:
    rows = []
    for r in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"):
        if r["competition"] in exclude:
            continue
        util = f(str(r["accuracy"]).rstrip("%")) / 100.0
        rows.append(
            {
                "model": model,
                "competition": r["competition"],
                "problem_id": r["problem_id"],
                "_util": util,
                "_cs": f(r.get("CS")),
                "_api": f(r.get("api_calls")),
                "_tok": f(r.get("tokens")),
                "_turns": f(r.get("turns")),
            }
        )
    return rows


def load_batch(root: Path, model: str, comps: set[str]) -> list[dict]:
    rows = []
    for path in sorted(root.glob("*/contest_session.json")):
        row = session_row(model, path)
        if row is None or row["competition"] not in comps:
            continue
        rows.append(row)
    return rows


def load_low_acc() -> list[dict]:
    root = repo / "results" / "otc_task_routing_low_accuracy_20260904"
    rows = []
    for r in csv.DictReader((root / "summary.tsv").open(encoding="utf-8"), delimiter="\t"):
        sess = root / r["problem_id"] / "contest_session.json"
        if not sess.exists():
            continue
        row = session_row("OTC", sess)
        if row is None:
            continue
        row["competition"] = r["competition_id"]
        rows.append(row)
    return rows


def agg(rows: list[dict]) -> dict[str, dict]:
    by: dict[str, list] = defaultdict(list)
    for r in rows:
        by[r["competition"]].append(r)
    out: dict[str, dict] = {}
    for cid, rs in by.items():
        n = len(rs)
        nz = sum(1 for r in rs if r["_util"] > 0)
        out[cid] = {
            "N": n,
            "Acc": sum(r["_util"] for r in rs) / n,
            "CS": sum(r["_cs"] for r in rs) / n,
            "API": sum(r["_api"] for r in rs) / n,
            "tok": sum(r["_tok"] for r in rs) / n,
            "turns": sum(r["_turns"] for r in rs) / n,
            "nz": f"{nz}/{n}",
        }
    return out


def total(data: dict[str, dict]) -> dict:
    present = {k: v for k, v in data.items() if k in ORDER}
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


def emit(title: str, data: dict[str, dict]) -> list[list]:
    lines: list[list] = [
        [title],
        [
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
        ],
    ]
    for cid in ORDER:
        if cid not in data:
            continue
        m = data[cid]
        lines.append(
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
    t = total(data)
    lines.append(
        [
            "TOTAL",
            "",
            t["N"],
            sum(TQ[c] for c in ORDER if c in data),
            acc_s(t["Acc"]),
            round(t["CS"], 2),
            round(t["API"], 2),
            int(round(t["tok"])),
            round(t["turns"], 2),
            t["nz"],
        ]
    )
    return lines


def main() -> None:
    low = load_low_acc()
    low_comps = {r["competition"] for r in low}

    otc = load_gold(
        repo / "results/gold_suite_sheets_20260903/otc_per_session.tsv",
        "OTC",
        ARML | low_comps,
    )
    otc += low
    otc += load_batch(
        repo / "results/arml_all_protocol_v3_otc_20260909",
        "OTC",
        ARML,
    )

    van = load_gold(
        repo / "results/gold_suite_sheets_20260903/vanilla_per_session.tsv",
        "Vanilla",
        ARML,
    )
    van += load_batch(
        repo / "results/arml_all_protocol_v3_vanilla_20260909",
        "Vanilla",
        ARML,
    )

    otc_a = agg(otc)
    van_a = agg(van)
    rows = emit("Open_table_coach", otc_a) + [[]] + emit("Vanilla", van_a)

    path = out / "tab3_by_competition_latest.tsv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        csv.writer(fh, delimiter="\t", lineterminator="\n").writerows(rows)

    for line in rows:
        print("\t".join(str(x) for x in line))
    print(f"\n# wrote {path}")
    print("# OTC comps:", ", ".join(c for c in ORDER if c in otc_a))
    print("# Van comps:", ", ".join(c for c in ORDER if c in van_a))
    if "arml_national_power" not in otc_a or "arml_power" not in otc_a:
        print("# note: OTC power rows omitted until batch finishes + rubric scoring")


if __name__ == "__main__":
    main()
