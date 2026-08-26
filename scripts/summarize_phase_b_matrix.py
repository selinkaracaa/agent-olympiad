"""Summarize ARML Local phase B model × schema matrix."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "results/phase_b/meeting_arml_local/phase_b_matrix.json"

SCHEMAS = ["single_agent", "centralized", "round_table", "decentralized"]
TEAMS = ["gpt", "claude", "gemini", "hetero"]
SHORT = {
    "single_agent": "single",
    "centralized": "centr.",
    "round_table": "round",
    "decentralized": "decen.",
}


def main() -> None:
    data = json.loads(MATRIX.read_text(encoding="utf-8"))
    results = data.get("results", [])

    task: dict[tuple[str, str], float] = {}
    cs: dict[tuple[str, str], float] = {}
    for r in results:
        team = r.get("team")
        schema = r.get("schema")
        if team and schema:
            task[(team, schema)] = float(r["grade_score"])
            cs[(team, schema)] = float(r["coordination_score"])

    print("=== Full matrix (task /40 · CS) ===")
    header = f"{'':12}" + "".join(f"{SHORT[s]:>12}" for s in SCHEMAS)
    print(header)
    for team in TEAMS:
        cells = []
        for schema in SCHEMAS:
            key = (team, schema)
            if key not in task:
                cells.append("...")
            else:
                cells.append(f"{task[key]:.1f}·{cs[key]:.1f}")
        print(f"{team:12}" + "".join(f"{c:>12}" for c in cells))

    print("\n=== Column averages (task /40) ===")
    for schema in SCHEMAS:
        vals = [task[(t, schema)] for t in TEAMS if (t, schema) in task]
        if vals:
            print(f"  {SHORT[schema]:8}: {sum(vals)/len(vals):.2f}  (n={len(vals)})")

    print("\n=== Row averages (task /40) ===")
    for team in TEAMS:
        vals = [task[(team, s)] for s in SCHEMAS if (team, s) in task]
        if vals:
            print(f"  {team:8}: {sum(vals)/len(vals):.2f}  (n={len(vals)})")

    print("\n=== Column averages (CS) ===")
    for schema in SCHEMAS:
        vals = [cs[(t, schema)] for t in TEAMS if (t, schema) in cs]
        if vals:
            print(f"  {SHORT[schema]:8}: {sum(vals)/len(vals):.2f}  (n={len(vals)})")

    print("\n=== Best schema per team (task) ===")
    for team in TEAMS:
        options = [(s, task[(team, s)]) for s in SCHEMAS if (team, s) in task]
        if options:
            best_schema, best_score = max(options, key=lambda x: x[1])
            print(f"  {team}: {SHORT[best_schema]} = {best_score:.1f}")

    print("\n=== Solo → best team protocol (task delta) ===")
    for team in TEAMS:
        solo = task.get((team, "single_agent"))
        team_scores = [
            task[(team, s)] for s in SCHEMAS if s != "single_agent" and (team, s) in task
        ]
        if solo is not None and team_scores:
            best = max(team_scores)
            print(f"  {team}: {solo:.1f} → {best:.1f}  (Δ {best - solo:+.1f})")

    print(f"\nCells completed: {len(results)} / 16")
    missing = [(t, s) for t in TEAMS for s in SCHEMAS if (t, s) not in task]
    if missing:
        print("Missing:", ", ".join(f"{t}/{SHORT[s]}" for t, s in missing))


if __name__ == "__main__":
    main()
