"""Emit paste-ready per-session rows for completed ARML protocol-v3 runs."""
from __future__ import annotations

import csv
import json
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
out = repo / "results" / "gold_suite_sheets_20260903" / "paste_tabs"
out.mkdir(parents=True, exist_ok=True)

HEADER = [
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
]


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


def pct(a: float) -> str:
    return f"{a * 100:.2f}%"


def row_from_session(model: str, path: Path) -> dict | None:
    d = json.loads(path.read_text(encoding="utf-8"))
    pid = path.parent.name
    cid = competition_of(pid) or str(d.get("competition_id") or "")
    grade = d.get("grade") or {}
    metrics = d.get("metrics") or {}
    budget = d.get("budget") or {}
    timing = d.get("timing") or {}
    collab = metrics.get("collaboration") or metrics.get("multi_agent") or {}

    score = grade.get("score")
    max_score = grade.get("max_score")
    if score is None:
        score = metrics.get("score")
    if max_score is None:
        max_score = metrics.get("max_score")
    score_f = float(score) if score is not None and score != "" else 0.0
    max_f = float(max_score) if max_score is not None and max_score != "" else 0.0

    util = metrics.get("task_utility")
    if util is None:
        util = grade.get("task_utility")
    if util is None:
        util = score_f / max_f if max_f else 0.0
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

    turns = budget.get("turns_used") or metrics.get("turns_used") or ""
    api = budget.get("api_calls_used") or metrics.get("api_calls_used") or ""
    toks = budget.get("tokens_used") or metrics.get("tokens_used") or ""
    sec = timing.get("elapsed_seconds") or budget.get("wall_seconds_used") or ""
    if sec not in ("", None):
        sec = int(round(float(sec)))

    if grade.get("score") is not None:
        score_f = float(grade["score"])
    if grade.get("max_score") is not None:
        max_f = float(grade["max_score"])

    def neat(x: float) -> float | int:
        r = round(float(x), 2)
        return int(r) if abs(r - int(r)) < 1e-9 else r

    return {
        "model": model,
        "competition": cid,
        "problem_id": pid,
        "score": neat(score_f),
        "max_score": neat(max_f),
        "accuracy": pct(util),
        "Communication": round(comm, 2) if comm else "",
        "Planning": round(plan, 2) if plan else "",
        "CS": round(cs, 2) if cs else "",
        "turns": turns,
        "api_calls": api,
        "tokens": toks,
        "sec": sec,
    }


def collect(root: Path, model: str) -> list[dict]:
    rows = []
    for sess in sorted(root.glob("*/contest_session.json")):
        row = row_from_session(model, sess)
        if row:
            rows.append(row)
    return rows


def write(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    otc = collect(repo / "results/arml_all_protocol_v3_otc_20260909", "OTC")
    van = collect(repo / "results/arml_all_protocol_v3_vanilla_20260909", "Vanilla")

    write(out / "arml_protocol_v3_otc_per_session.tsv", otc)
    write(out / "arml_protocol_v3_vanilla_per_session.tsv", van)
    write(out / "arml_protocol_v3_paired_done.tsv", otc + van)

    print("\t".join(HEADER))
    for r in otc + van:
        print("\t".join(str(r[k]) for k in HEADER))
    print(f"\n# wrote {len(otc)} OTC + {len(van)} Vanilla rows")
    print(f"# {out / 'arml_protocol_v3_otc_per_session.tsv'}")
    print(f"# {out / 'arml_protocol_v3_vanilla_per_session.tsv'}")
    print(f"# {out / 'arml_protocol_v3_paired_done.tsv'}")


if __name__ == "__main__":
    main()
