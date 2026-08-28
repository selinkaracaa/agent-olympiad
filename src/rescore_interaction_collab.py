#!/usr/bin/env python3
"""Post-hoc interaction helpfulness (IHS) scoring for Phase B matrix rows.

Adds the second collaboration metric (did interactions help the final answer?)
without re-running contests. Uses chat_history + action_log_tail already stored
in phase_b_matrix.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from llm import make_perplexity_caller  # noqa: E402
from evaluation.collaboration_score import score_interaction_helpfulness  # noqa: E402


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("'").strip('"'))


def _agents_from_row(row: dict) -> list[str]:
    models = row.get("agent_models") or {}
    if isinstance(models, dict) and models:
        return list(models.keys())
    seen: list[str] = []
    for msg in row.get("chat_history") or []:
        name = msg.get("sender")
        if name and name not in seen:
            seen.append(name)
    return seen or ["Solo"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--matrix",
        type=Path,
        default=REPO / "results/phase_b/full_matrix/phase_b_matrix.json",
    )
    parser.add_argument(
        "--competitions",
        default="",
        help="Comma list to restrict (default: all ok rows missing IHS)",
    )
    parser.add_argument("--force", action="store_true", help="Rescore even if IHS present")
    parser.add_argument("--model", default="openai/gpt-5.4-mini")
    parser.add_argument("--limit", type=int, default=0, help="Max cells (0=all)")
    args = parser.parse_args()

    _load_dotenv(REPO / ".env")
    if not os.environ.get("PERPLEXITY_API_KEY"):
        raise SystemExit("PERPLEXITY_API_KEY not set")

    data = json.loads(args.matrix.read_text(encoding="utf-8"))
    rows = data.get("results") or []
    allow = {c.strip() for c in args.competitions.split(",") if c.strip()}
    # Text Agent API (same path as live agents); wrap to RequestFn-shaped callable.
    query = make_perplexity_caller(model=args.model, api="agent")

    def request_fn(req):  # type: ignore[no-untyped-def]
        from llm import LLMResponse

        text = query(req.system_prompt, req.user_prompt)
        return LLMResponse(text=text, provider="perplexity", model=args.model, usage={})

    targets = []
    for i, row in enumerate(rows):
        if row.get("status") != "ok":
            continue
        if allow and row.get("competition") not in allow:
            continue
        if row.get("interaction_helpfulness_score") is not None and not args.force:
            continue
        targets.append(i)

    if args.limit:
        targets = targets[: args.limit]

    print(f"Scoring IHS for {len(targets)} cells → {args.matrix}", flush=True)
    done = 0
    for i in targets:
        # Re-read each time so a concurrent matrix run does not wipe IHS / new cells.
        data = json.loads(args.matrix.read_text(encoding="utf-8"))
        rows = data.get("results") or []
        if i >= len(rows):
            print(f"  skip stale index {i}", flush=True)
            continue
        row = rows[i]
        key = (
            row.get("competition"),
            row.get("team"),
            row.get("schema"),
            row.get("problem_id"),
        )
        if row.get("status") != "ok":
            continue
        if row.get("interaction_helpfulness_score") is not None and not args.force:
            print(f"  skip already scored {key}", flush=True)
            continue

        label = f"{row.get('competition')} · {row.get('team')} · {row.get('schema')}"
        print(f"  [{done+1}/{len(targets)}] {label} ...", flush=True)
        task_results = (
            f"submitted={row.get('submitted')} "
            f"grade_method={row.get('grade_method')} "
            f"score={row.get('grade_score')}/{row.get('grade_max_score')}"
        )
        try:
            result = score_interaction_helpfulness(
                request_fn=request_fn,
                task_text=str(row.get("problem_id") or row.get("competition")),
                agents=_agents_from_row(row),
                schema=str(row.get("schema") or "unknown"),
                chat_history=list(row.get("chat_history") or []),
                action_log=list(row.get("action_log_tail") or []),
                final_answer=str(
                    row.get("final_answer") or row.get("final_answer_preview") or ""
                ),
                task_results=task_results,
            )
            payload = result.to_dict()
            # Merge into whichever row currently matches the key.
            data = json.loads(args.matrix.read_text(encoding="utf-8"))
            rows = data.get("results") or []
            matched = False
            for r in rows:
                rkey = (
                    r.get("competition"),
                    r.get("team"),
                    r.get("schema"),
                    r.get("problem_id"),
                )
                if rkey == key and r.get("status") == "ok":
                    r["interaction_helpfulness_score"] = payload[
                        "interaction_helpfulness_score"
                    ]
                    r["interaction_helpful_fraction"] = payload["helpful_fraction"]
                    r["interaction"] = payload
                    matched = True
                    break
            if not matched:
                print(f"    WARN: row vanished for {key}", flush=True)
            else:
                print(
                    f"    IHS={payload['interaction_helpfulness_score']:.1f} "
                    f"helpful={payload['helpful_count']} "
                    f"neutral={payload['neutral_count']} "
                    f"hurt={payload['hurt_count']}",
                    flush=True,
                )
            data["results"] = rows
            data["interaction_metric"] = "interaction_helpfulness_v1"
            data["ihs_scored"] = sum(
                1 for r in rows if r.get("interaction_helpfulness_score") is not None
            )
            args.matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"    FAIL: {exc}", flush=True)
            data = json.loads(args.matrix.read_text(encoding="utf-8"))
            for r in data.get("results") or []:
                rkey = (
                    r.get("competition"),
                    r.get("team"),
                    r.get("schema"),
                    r.get("problem_id"),
                )
                if rkey == key:
                    r["interaction_error"] = str(exc)
            args.matrix.write_text(json.dumps(data, indent=2), encoding="utf-8")
        done += 1
        time.sleep(1)

    data = json.loads(args.matrix.read_text(encoding="utf-8"))
    n = sum(
        1
        for r in (data.get("results") or [])
        if r.get("interaction_helpfulness_score") is not None
    )
    print(f"Done. ihs_scored={n}", flush=True)


if __name__ == "__main__":
    main()
