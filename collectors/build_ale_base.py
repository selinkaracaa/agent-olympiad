#!/usr/bin/env python3
"""Convert data/benchmarks into an Agents-Last-Exam-style layout under data/base.

Layout (mirrors agents-last-exam-data):

  data/base/
    README.md
    task_cards.json
    tasks/
      <competition_id>/
        <problem_id>/
          base/                 # default variant
            input/              # agent-visible materials at run start
              task_sop.md
              input_environment_spec.md
              problem.md        # when text description exists
              <linked assets>
            software/           # optional runtime fixtures
              README.txt

Gold / solution files are intentionally excluded from input/ (same split as ALE:
input data vs gated reference). Pointers stay in task_cards.json metadata.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"
RULES_ROOT = REPO_ROOT / "pipeline" / "rules"
RAW_ROOT = REPO_ROOT / "data" / "raw"
BASE_ROOT = REPO_ROOT / "data" / "base"
TASKS_ROOT = BASE_ROOT / "tasks"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_problems(competition_id: str) -> list[dict[str, Any]]:
    path = BENCHMARK_ROOT / competition_id / "benchmark.json"
    if not path.exists():
        return []
    payload = _load_json(path)
    rows = payload.get("problems") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"Invalid benchmark list: {path}")
    return rows


def _load_rules(competition_id: str) -> dict[str, Any] | None:
    path = RULES_ROOT / f"{competition_id}.json"
    if not path.exists():
        return None
    return _load_json(path)


def _load_runtime(competition_id: str) -> dict[str, Any] | None:
    # Some tracks store runtime under a shorter raw folder name.
    candidates = [
        RAW_ROOT / competition_id / "runtime.json",
        RAW_ROOT / competition_id.split("_")[0] / "runtime.json",
    ]
    # Known aliases
    aliases = {
        "ijso_practical": "ijso",
        "ieo_business_case": "business_case",
    }
    if competition_id in aliases:
        candidates.insert(0, RAW_ROOT / aliases[competition_id] / "runtime.json")
    for path in candidates:
        if path.exists():
            return _load_json(path)
    return None


def _safe_link_or_pointer(src: Path, dest: Path) -> str:
    """Link src into dest; fall back to a .path pointer file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() or dest.is_symlink():
        dest.unlink()
    try:
        os.symlink(src, dest)
        return "symlink"
    except OSError:
        pointer = dest.with_suffix(dest.suffix + ".path")
        if pointer.exists():
            pointer.unlink()
        rel = os.path.relpath(src, start=dest.parent)
        pointer.write_text(rel.replace("\\", "/") + "\n", encoding="utf-8")
        return "pointer"


def _agent_visible_paths(
    row: dict[str, Any], repo_root: Path
) -> list[tuple[Path, str]]:
    """Return (absolute_path, role_label) for agent-visible inputs."""
    out: list[tuple[Path, str]] = []
    seen: set[Path] = set()

    for item in row.get("assets") or []:
        if item.get("role") not in (None, "agent_visible"):
            continue
        rel = item.get("path")
        if not rel:
            continue
        path = (repo_root / str(rel)).resolve()
        if path.is_file() and path not in seen:
            out.append((path, "asset"))
            seen.add(path)

    source_file = row.get("source_file")
    if source_file:
        path = (repo_root / str(source_file)).resolve()
        if path.is_file() and path not in seen:
            out.append((path, "source"))
            seen.add(path)

    return out


def _write_task_sop(
    path: Path,
    *,
    competition_id: str,
    row: dict[str, Any],
    input_names: list[str],
    has_software: bool,
) -> None:
    problem_id = str(row.get("problem_id") or "")
    title = str(row.get("title") or row.get("topic") or problem_id)
    competition = str(row.get("competition") or competition_id)
    year = row.get("year")
    team_size = row.get("team_size")
    task_type = row.get("task_type")
    deliverable = (row.get("evaluation") or {}).get("deliverable") or "team_submission"
    source_url = row.get("source_url")

    lines = [
        "# Task SOP",
        "",
        "## Reference Environment",
        f"- Competition: {competition}",
        f"- Competition id: `{competition_id}`",
        f"- Problem id: `{problem_id}`",
        f"- Task type: `{task_type}`",
        f"- Team size: {team_size}",
    ]
    if year is not None:
        lines.append(f"- Year / edition: {year}")
    if source_url:
        lines.append(f"- Source: {source_url}")
    lines += [
        "",
        "## Goal",
        (
            "As a multi-agent team, solve the olympiad-style team task using only "
            "the materials under `base/input`. Produce the required deliverable "
            f"(`{deliverable}`)."
        ),
        "",
        "## Task directory",
        "- Variant root: `base`",
        "- Input directory: `base/input`",
    ]
    if has_software:
        lines.append("- Software fixtures: `base/software`")
    lines += [
        "",
        "## Inputs",
    ]
    if input_names:
        for name in input_names:
            lines.append(f"- `{name}`")
    else:
        lines.append("- (no staged binary inputs; see `problem.md` / this SOP)")
    lines += [
        "",
        f"## Title",
        title,
        "",
        "## Deterministic Evaluation Rule",
        (
            "Gold answers and official solution booklets are not provided in "
            "`input/`. Scoring uses the evaluator declared on the task card "
            "(gold match, rubric LLM judge, slide judge, or deferred sandbox)."
        ),
        "",
        "## Deliverables",
        f"Return the team `{deliverable}` expected by this competition.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_environment_spec(
    path: Path,
    *,
    competition_id: str,
    row: dict[str, Any],
    rules: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
) -> None:
    lines = [
        "# Input Environment and Settings",
        "",
        "## System",
        f"- Competition id: `{competition_id}`",
        f"- Problem id: `{row.get('problem_id')}`",
        f"- Task type: `{row.get('task_type')}`",
        f"- Eval unit: `{row.get('eval_unit') or 'session'}`",
        f"- Status: `{row.get('status')}`",
        "",
    ]

    if rules:
        lines += [
            "## Team / Tooling Rules",
            f"- Display name: {rules.get('display_name') or competition_id}",
            f"- Default team size: {rules.get('team_size_default')}",
            f"- Allowed tools: {', '.join(rules.get('allowed_tools') or []) or '(none listed)'}",
            "",
            "### Rules text",
            str(rules.get("rules_text") or "(no rules_text)"),
            "",
        ]

    if runtime:
        lines += [
            "## Runtime",
            f"- Status: `{runtime.get('status')}`",
        ]
        if runtime.get("image"):
            lines.append(f"- Image: `{runtime.get('image')}`")
        if runtime.get("solver_image"):
            lines.append(f"- Solver image: `{runtime.get('solver_image')}`")
        if runtime.get("notes"):
            lines += ["", str(runtime.get("notes")), ""]
        else:
            lines.append("")

    evaluation = row.get("evaluation") or {}
    if evaluation:
        lines += [
            "## Evaluation Hints (for harness, not a gold key)",
            f"- Evaluator: `{evaluation.get('evaluator_id')}`",
            f"- Evaluator status: `{evaluation.get('status')}`",
        ]
        if evaluation.get("rubric_path"):
            lines.append(f"- Rubric path: `{evaluation.get('rubric_path')}`")
        if evaluation.get("deliverable"):
            lines.append(f"- Deliverable: `{evaluation.get('deliverable')}`")
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def _write_software_readme(
    path: Path, competition_id: str, runtime: dict[str, Any]
) -> None:
    lines = [
        "Stage software handoff",
        "======================",
        "",
        f"Competition: {competition_id}",
        f"Runtime status: {runtime.get('status')}",
        "",
    ]
    if runtime.get("notes"):
        lines += [str(runtime["notes"]), ""]
    if runtime.get("image"):
        lines.append(f"Base image: {runtime['image']}")
    if runtime.get("solver_image"):
        lines.append(f"Solver image: {runtime['solver_image']}")
    if runtime.get("compose_file"):
        lines.append(f"Compose file (in raw tree): {runtime['compose_file']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def build_task(
    competition_id: str,
    row: dict[str, Any],
    *,
    rules: dict[str, Any] | None,
    runtime: dict[str, Any] | None,
    clean: bool,
) -> dict[str, Any]:
    problem_id = str(row.get("problem_id") or "").strip()
    if not problem_id:
        raise ValueError(f"{competition_id}: missing problem_id")

    task_root = TASKS_ROOT / competition_id / problem_id / "base"
    input_dir = task_root / "input"
    software_dir = task_root / "software"

    if clean and task_root.exists():
        shutil.rmtree(task_root)
    input_dir.mkdir(parents=True, exist_ok=True)

    input_names: list[str] = []
    link_modes: list[str] = []

    description = str(row.get("problem_description") or "").strip()
    if description:
        problem_md = input_dir / "problem.md"
        problem_md.write_text(
            f"# {row.get('title') or row.get('topic') or problem_id}\n\n{description}\n",
            encoding="utf-8",
        )
        input_names.append("problem.md")

    for src, _role in _agent_visible_paths(row, REPO_ROOT):
        dest = input_dir / src.name
        # Avoid name collisions across assets
        if dest.exists() or dest.is_symlink() or (dest.with_suffix(dest.suffix + ".path")).exists():
            dest = input_dir / f"{src.parent.name}__{src.name}"
        mode = _safe_link_or_pointer(src, dest)
        link_modes.append(mode)
        if mode == "symlink":
            input_names.append(dest.name)
        else:
            input_names.append(dest.with_suffix(dest.suffix + ".path").name)

    has_software = runtime is not None
    if has_software:
        software_dir.mkdir(parents=True, exist_ok=True)
        _write_software_readme(software_dir / "README.txt", competition_id, runtime)

    _write_task_sop(
        input_dir / "task_sop.md",
        competition_id=competition_id,
        row=row,
        input_names=input_names,
        has_software=has_software,
    )
    input_names = ["task_sop.md", *input_names]

    _write_environment_spec(
        input_dir / "input_environment_spec.md",
        competition_id=competition_id,
        row=row,
        rules=rules,
        runtime=runtime,
    )
    input_names.append("input_environment_spec.md")

    # Deduplicate while preserving order
    seen_names: set[str] = set()
    ordered_names: list[str] = []
    for name in input_names:
        if name not in seen_names:
            ordered_names.append(name)
            seen_names.add(name)

    gold = row.get("gold_label") or {}
    evaluation = row.get("evaluation") or {}
    card = {
        "task_id": f"{competition_id}/{problem_id}",
        "title": row.get("title") or row.get("topic") or problem_id,
        "summary": (description[:280] + "…") if len(description) > 280 else description,
        "category": competition_id,
        "subdomain": row.get("task_type"),
        "task_split": row.get("eval_unit") or "session",
        "competition": row.get("competition"),
        "year": row.get("year"),
        "team_size": row.get("team_size"),
        "source_url": row.get("source_url"),
        "source_repo_path": f"tasks/{competition_id}/{problem_id}",
        "variant": "base",
        "input_files": [
            {
                "name": name,
                "path": f"input/{name}",
                "description": "Agent-facing staged input",
            }
            for name in ordered_names
        ],
        "software": (
            [f"See base/software/README.txt (runtime status={runtime.get('status')})"]
            if runtime
            else []
        ),
        "evaluation": evaluation,
        "has_gold_answer": bool(
            gold.get("expected_answer")
            or gold.get("parts")
            or gold.get("answers")
        ),
        "solution_file": row.get("solution_file"),
        "status": row.get("status"),
        "link_modes": sorted(set(link_modes)) if link_modes else [],
        "taxonomy": {
            "domain_code": competition_id,
            "subdomain_code": row.get("task_type"),
        },
    }
    return card


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--competitions",
        nargs="*",
        default=None,
        help="Optional subset of competition ids (default: all with benchmark.json)",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove each task base/ before rewriting",
    )
    parser.add_argument(
        "--limit-per-competition",
        type=int,
        default=None,
        help="Optional cap of problems per competition (for smoke tests)",
    )
    args = parser.parse_args()

    index = _load_json(BENCHMARK_ROOT / "index.json")
    olympiad_ids = [o["id"] for o in index.get("olympiads", [])]
    if args.competitions:
        selected = list(args.competitions)
    else:
        selected = [
            d.name
            for d in sorted(BENCHMARK_ROOT.iterdir())
            if d.is_dir() and (d / "benchmark.json").exists()
        ]
        # Prefer catalog order when present
        ordered = [oid for oid in olympiad_ids if oid in selected]
        ordered += [oid for oid in selected if oid not in ordered]
        selected = ordered

    BASE_ROOT.mkdir(parents=True, exist_ok=True)
    TASKS_ROOT.mkdir(parents=True, exist_ok=True)

    cards: list[dict[str, Any]] = []
    skipped: list[str] = []

    for competition_id in selected:
        rows = _load_problems(competition_id)
        if not rows:
            skipped.append(competition_id)
            continue
        if args.limit_per_competition is not None:
            rows = rows[: args.limit_per_competition]
        rules = _load_rules(competition_id)
        runtime = _load_runtime(competition_id)
        for row in rows:
            try:
                cards.append(
                    build_task(
                        competition_id,
                        row,
                        rules=rules,
                        runtime=runtime,
                        clean=args.clean,
                    )
                )
            except Exception as exc:  # noqa: BLE001 — collect and continue
                skipped.append(f"{competition_id}/{row.get('problem_id')}: {exc}")

    cards_path = BASE_ROOT / "task_cards.json"
    cards_path.write_text(
        json.dumps(
            {
                "description": (
                    "Agent Olympiad task cards in Agents-Last-Exam-style layout. "
                    "Each card points at tasks/<competition>/<problem_id>/base/."
                ),
                "layout": "tasks/<competition_id>/<problem_id>/base/{input,software}",
                "source_benchmarks": "data/benchmarks",
                "n_tasks": len(cards),
                "tasks": cards,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "n_tasks": len(cards),
        "n_competitions": len({c["category"] for c in cards}),
        "skipped": skipped,
        "base_root": str(BASE_ROOT.relative_to(REPO_ROOT)).replace("\\", "/"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
