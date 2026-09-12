"""Export gold-suite / ICPC session sheets with wall-clock columns when present."""

from __future__ import annotations

import json
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
out_dir = repo / "results" / "gold_suite_sheets_20260903"
out_dir.mkdir(parents=True, exist_ok=True)

# Current OTC rows use the judge-oracle gate (sample AC + one independent
# review of either decision unlocks submit_code). Pre-fix OTC runs are kept as
# "OTC (pre-fix)" so the before/after is auditable.
runs = [
    ("OTC", "WF 2012", repo / "results" / "icpc_wf_2012_otc_judge_oracle_perplexity_gpt54mini_native_20260904"),
    ("OTC (pre-fix)", "WF 2012", repo / "results" / "icpc_wf_2012_pair_perplexity_gpt54mini_native_20260903"),
    ("Vanilla", "WF 2012", repo / "results" / "icpc_wf_2012_vanilla_perplexity_gpt54mini_native_20260903"),
    ("OTC", "WF 2014", repo / "results" / "icpc_wf_2014_otc_judge_oracle_perplexity_gpt54mini_native_20260904"),
    ("OTC (pre-fix)", "WF 2014", repo / "results" / "icpc_wf_2014_otc_perplexity_gpt54mini_native_20260904"),
    ("Vanilla", "WF 2014", repo / "results" / "icpc_wf_2014_vanilla_perplexity_gpt54mini_native_20260903"),
]

notes_map = {
    ("OTC", "WF 2012"): "fibonacci WA x3 -> AC; bustour TLE",
    ("OTC (pre-fix)", "WF 2012"): "AC: fibonacci (1 submit); bustour sample-AC never submitted",
    ("Vanilla", "WF 2012"): "all submits on fibonacci; no AC",
    ("OTC", "WF 2014"): "game TLE; only 2 sample-AC in 88 local runs",
    ("OTC (pre-fix)", "WF 2014"): "never submit_code (review gate starved)",
    ("Vanilla", "WF 2014"): "SAMPLE_WA / WA; no AC",
}

summary_rows = [
    [
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
        "sim_min_used",
        "max_sim_min",
        "penalty_min",
        "wall_seconds",
        "started_at",
        "ended_at",
        "remote_attempts",
        "notes",
        "artifact",
    ]
]
task_rows = [
    [
        "model",
        "contest",
        "task_id",
        "score",
        "max_score",
        "accuracy",
        "state",
        "terminal_verdict",
        "attempts",
    ]
]

for model, contest, root in runs:
    payload = json.loads((root / "contest_session.json").read_text(encoding="utf-8"))
    grade = payload.get("grade") or {}
    metrics = payload.get("metrics") or {}
    budget = payload.get("budget") or {}
    timing = payload.get("timing") or {}
    tasks = payload.get("tasks") or {}
    events = ((payload.get("memory") or {}).get("events")) or []
    remote = sum(1 for e in events if e.get("kind") == "submit_code")
    score = float(grade.get("score") or metrics.get("score") or 0)
    max_score = float(grade.get("max_score") or metrics.get("max_score") or len(tasks) or 12)
    wall = (
        timing.get("elapsed_seconds")
        if timing.get("elapsed_seconds") is not None
        else budget.get("wall_seconds_used")
    )
    summary_rows.append(
        [
            model,
            contest,
            f"{(score / max_score) if max_score else 0:.4f}",
            str(int(score) if score == int(score) else score),
            str(int(max_score) if max_score == int(max_score) else max_score),
            str(metrics.get("coordination_score", "")),
            str(metrics.get("communication_score", "")),
            str(metrics.get("planning_score", "")),
            f"{float(metrics.get('active_agent_rate') or 0):.4f}",
            f"{float(metrics.get('action_balance') or 0):.4f}",
            str(budget.get("turns_used", "")),
            str(budget.get("api_calls_used", "")),
            str(budget.get("tokens_used", "")),
            str(budget.get("simulated_minutes_used", "")),
            str(budget.get("max_simulated_minutes", "")),
            str(budget.get("penalty_minutes", "")),
            "" if wall is None else f"{float(wall):.3f}",
            str(timing.get("started_at") or budget.get("wall_started_at") or ""),
            str(timing.get("ended_at") or ""),
            str(remote),
            notes_map[(model, contest)],
            str(root.relative_to(repo)).replace("\\", "/"),
        ]
    )
    for task_id, task in sorted(tasks.items()):
        tscore = float(task.get("score") or 0)
        subs = task.get("submissions")
        n_att = len(subs) if isinstance(subs, list) else ""
        task_rows.append(
            [
                model,
                contest,
                task_id,
                str(int(tscore) if tscore == int(tscore) else tscore),
                "1",
                f"{tscore:.0%}",
                str(task.get("state") or ""),
                str(task.get("terminal_verdict") or ""),
                str(n_att),
            ]
        )

sum_path = out_dir / "icpc_session_summary.tsv"
task_path = out_dir / "icpc_per_task.tsv"
for path, rows in ((sum_path, summary_rows), (task_path, task_rows)):
    path.write_text("\n".join("\t".join(r) for r in rows) + "\n", encoding="utf-8")
    print(path.name, len(rows) - 1)
