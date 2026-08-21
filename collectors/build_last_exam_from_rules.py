#!/usr/bin/env python3
"""Project rule cards and benchmarks into Last Exam packs and thin tasks.

data/rules stays canonical. This writer composes:

  data/last_exam/competitions/{cid}/{input,method,eval}
  data/last_exam/tasks/{cid}/{pid}/base/input/problem.md
  data/last_exam/tasks/{cid}/{pid}/eval/reference.json

Ownership comes from the three rule files, not text heuristics.
Gold, solution PDFs, rubric paths, and evaluator internals stay in eval/.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_ROOT = REPO_ROOT / "data" / "rules"
BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"
OUT_ROOT = REPO_ROOT / "data" / "last_exam"
COMP_ROOT = OUT_ROOT / "competitions"
TASKS_ROOT = OUT_ROOT / "tasks"

sys.path.insert(0, str(REPO_ROOT / "src"))

from rules.storage import COMPONENT_KEYS  # noqa: E402
from rules.ownership import SIMULATION_OWNED_KEYS  # noqa: E402


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def _bullets(lines: list[str]) -> str:
    return "\n".join(f"- {line}" for line in lines) if lines else "- _(none)_"


def _json_block(value: Any) -> str:
    return "```json\n" + json.dumps(value, ensure_ascii=False, indent=2) + "\n```"


def _inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
        return True
    except ValueError:
        return False


def _iter_competition_ids() -> list[str]:
    return sorted(
        directory.name
        for directory in RULES_ROOT.iterdir()
        if directory.is_dir() and (directory / "competition.json").is_file()
    )


def _load_problems(competition_id: str) -> list[dict[str, Any]]:
    path = BENCHMARK_ROOT / competition_id / "benchmark.json"
    if not path.is_file():
        return []
    payload = _load(path)
    rows = payload.get("problems") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"Invalid benchmark list: {path}")
    return [row for row in rows if isinstance(row, dict)]


def project_competition(cid: str) -> dict[str, Any]:
    root = RULES_ROOT / cid
    competition = _load(root / "competition.json")
    collaboration = _load(root / "collaboration.json")
    evaluation = _load(root / "evaluation.json")
    execution = competition.get("execution") or {}
    simulation = collaboration.get("simulation") or {}
    sources = []
    for source in (competition.get("provenance") or {}).get("sources") or []:
        if not isinstance(source, dict):
            continue
        title = source.get("title") or "source"
        url = source.get("url") or ""
        edition = source.get("edition") or ""
        extra = f" ({edition})" if edition else ""
        sources.append(f"[{title}]({url}){extra}" if url else f"{title}{extra}")

    mapping = {
        "competition_id": cid,
        "source": f"data/rules/{cid}",
        "canonical": "data/rules stays the source of truth; this pack is a projection",
        "input": {
            "from_competition.json": sorted(COMPONENT_KEYS["competition"]),
        },
        "method": {
            "from_collaboration.json": sorted(COMPONENT_KEYS["collaboration"]),
            "simulation_owned_keys": sorted(SIMULATION_OWNED_KEYS),
        },
        "eval": {
            "from_evaluation.json": sorted(COMPONENT_KEYS["evaluation"]),
            "hidden_until_grade": True,
            "gold_answers_stay_in": "data/benchmarks and data/rubrics, not this pack",
        },
    }

    ground = [
        f"# Ground rules — `{cid}`",
        "",
        "Official contestant constraints from `data/rules/"
        + cid
        + "/competition.json`.",
        "This is **input**, not the agent collaboration method.",
        "",
        f"- Rule id: `{competition.get('rule_id')}`",
        f"- Profile: `{competition.get('profile')}`",
        f"- Protocol: `{competition.get('protocol')}`",
    ]
    if sources:
        ground += ["", "## Sources", "", _bullets(sources)]
    ground += [
        "",
        "## Contest briefing",
        "",
        str(competition.get("rules_text") or "").strip() or "_(empty)_",
        "",
        "## Binding contestant constraints",
        "",
        _bullets(
            [
                str(item).strip()
                for item in (competition.get("human_constraints") or [])
                if str(item).strip()
            ]
        ),
    ]
    _write(COMP_ROOT / cid / "input" / "ground_rules.md", "\n".join(ground))

    environment = [
        f"# Environment — `{cid}`",
        "",
        "## Roster",
        "",
        _json_block(competition.get("team") or {}),
        "",
        "## Allowed tools",
        "",
        _bullets([str(item) for item in (competition.get("allowed_tools") or [])]),
        "",
        "## Resources",
        "",
        _json_block(competition.get("resources") or {}),
        "",
        "## Official execution facts",
        "",
        _json_block(execution),
        "",
        "## Deliverable",
        "",
        _json_block(competition.get("deliverable") or {}),
    ]
    _write(COMP_ROOT / cid / "input" / "environment.md", "\n".join(environment))

    method = [
        f"# Method — `{cid}`",
        "",
        "How this benchmark's agents are asked to work. Projected from "
        f"`data/rules/{cid}/collaboration.json`.",
        "",
        "## Agent constraints",
        "",
        _bullets(
            [
                str(item).strip()
                for item in (collaboration.get("agent_constraints") or [])
                if str(item).strip()
            ]
        ),
        "",
        "## Information / deliberation / communication",
        "",
        _json_block(
            {
                "information_policy": collaboration.get("information_policy") or {},
                "deliberation": collaboration.get("deliberation") or {},
                "communication": collaboration.get("communication") or {},
            }
        ),
        "",
        "## Simulation",
        "",
        _json_block(simulation),
        "",
        "## Rule sections",
        "",
        _json_block(collaboration.get("rule_sections") or {}),
    ]
    _write(COMP_ROOT / cid / "method" / "collaboration.md", "\n".join(method))
    _dump(
        COMP_ROOT / cid / "method" / "roles.json",
        {
            "source": f"data/rules/{cid}/collaboration.json#agent_roles",
            "information_policy": (collaboration.get("information_policy") or {}).get("mode"),
            "roles": [
                {
                    "name": role.get("name"),
                    "title": role.get("title"),
                    "may_submit": role.get("may_submit"),
                    "duties": role.get("duties") or [],
                }
                for role in (collaboration.get("agent_roles") or [])
                if isinstance(role, dict)
            ],
        },
    )

    scoring = evaluation.get("scoring") or {}
    eval_md = [
        f"# Eval — `{cid}` (hidden until grade)",
        "",
        "Do not stage this file to the agent at start.",
        "",
        "## Evaluator",
        "",
        _json_block(
            {
                "evaluator_id": scoring.get("evaluator_id"),
                "evaluator_status": scoring.get("evaluator_status"),
                "recommended_evaluator_id": scoring.get("recommended_evaluator_id"),
                "mode": scoring.get("mode"),
                "unit": scoring.get("unit"),
                "rubric_path": scoring.get("rubric_path"),
            }
        ),
        "",
        "## Evaluation guidance",
        "",
        str(evaluation.get("evaluation_guidance") or "").strip() or "_(none)_",
        "",
        "## Official performance",
        "",
        _json_block(scoring.get("official_performance") or {}),
        "",
        "## Rule compliance",
        "",
        _json_block(scoring.get("rule_compliance") or {}),
        "",
        "## Collaboration quality",
        "",
        _json_block(scoring.get("collaboration_quality") or {}),
        "",
        "## Current repository availability",
        "",
        _json_block(scoring.get("current_repository_availability") or {}),
        "",
        "## Submission adaptation",
        "",
        _json_block(evaluation.get("submission") or {}),
    ]
    _write(COMP_ROOT / cid / "eval" / "scoring.md", "\n".join(eval_md))
    _dump(COMP_ROOT / cid / "mapping.json", mapping)
    _dump(
        COMP_ROOT / cid / "pack.json",
        {
            "competition_id": cid,
            "rule_id": competition.get("rule_id"),
            "profile": competition.get("profile"),
            "protocol": competition.get("protocol"),
            "visibility": {
                "agent_at_start": ["input", "method"],
                "hidden_until_grade": ["eval"],
            },
        },
    )
    return {
        "competition_id": cid,
        "rule_id": competition.get("rule_id"),
        "profile": competition.get("profile"),
        "protocol": competition.get("protocol"),
        "n_roles": len(collaboration.get("agent_roles") or []),
        "path": f"data/last_exam/competitions/{cid}",
        "source": f"data/rules/{cid}",
    }


def _agent_assets(row: dict[str, Any]) -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    if row.get("is_solution_pdf"):
        return out
    for item in row.get("assets") or []:
        if not isinstance(item, dict):
            continue
        if item.get("role") not in (None, "agent_visible"):
            continue
        rel = item.get("path")
        if not rel:
            continue
        path = (REPO_ROOT / str(rel)).resolve()
        if path.is_file() and _inside_repo(path) and path not in seen:
            out.append(path)
            seen.add(path)
    source_file = row.get("source_file")
    if source_file and not row.get("is_solution_pdf"):
        path = (REPO_ROOT / str(source_file)).resolve()
        name = path.name.lower()
        if "sol" in name or "answer" in name or "key" in name:
            return out
        if path.is_file() and _inside_repo(path) and path not in seen:
            out.append(path)
    return out


def project_task(cid: str, row: dict[str, Any]) -> dict[str, Any]:
    problem_id = str(row.get("problem_id") or "").strip()
    if not problem_id:
        raise ValueError(f"{cid}: missing problem_id")
    task_root = TASKS_ROOT / cid / problem_id
    if task_root.exists():
        shutil.rmtree(task_root)
    input_dir = task_root / "base" / "input"
    input_dir.mkdir(parents=True, exist_ok=True)

    input_files = []
    description = str(row.get("problem_description") or "").strip()
    if description:
        _write(
            input_dir / "problem.md",
            f"# {row.get('title') or row.get('topic') or problem_id}\n\n{description}",
        )
        input_files.append("problem.md")

    for src in _agent_assets(row):
        dest = input_dir / src.name
        if dest.exists():
            dest = input_dir / f"{src.parent.name}__{src.name}"
        pointer = dest.with_suffix(dest.suffix + ".path")
        rel = src.relative_to(REPO_ROOT).as_posix()
        pointer.write_text(rel + "\n", encoding="utf-8")
        input_files.append(pointer.name)

    evaluation = row.get("evaluation") or {}
    gold = row.get("gold_label") or {}
    _dump(
        task_root / "eval" / "reference.json",
        {
            "visibility": "hidden_until_grade",
            "gold_pointer": f"data/benchmarks/{cid}/benchmark.json#{problem_id}.gold_label",
            "has_gold_answer": bool(
                gold.get("expected_answer") or gold.get("parts") or gold.get("answers")
            ),
            "evaluator_id": evaluation.get("evaluator_id"),
            "evaluator_status": evaluation.get("status"),
            "problem_package": evaluation.get("problem_package"),
            "test_provenance": evaluation.get("test_provenance"),
            "rubric_path": evaluation.get("rubric_path"),
            "deliverable": evaluation.get("deliverable"),
            "limitations": evaluation.get("limitations") or [],
            "solution_file": row.get("solution_file"),
        },
    )
    card = {
        "task_id": f"{cid}/{problem_id}",
        "competition_id": cid,
        "problem_id": problem_id,
        "title": row.get("title") or row.get("topic") or problem_id,
        "year": row.get("year"),
        "team_size": row.get("team_size"),
        "source_url": row.get("source_url"),
        "inherits_competition_pack": f"competitions/{cid}",
        "rule_card": f"data/rules/{cid}",
        "input": {
            "visibility": "agent_at_start",
            "files": [{"name": name, "path": f"base/input/{name}"} for name in input_files],
        },
        "method": {
            "visibility": "agent_at_start",
            "path": f"competitions/{cid}/method",
        },
        "eval": {
            "visibility": "hidden_until_grade",
            "path": f"eval/reference.json",
            "competition_eval": f"competitions/{cid}/eval",
        },
    }
    _dump(task_root / "task_card.json", card)
    return card


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--competitions", nargs="*", default=None)
    parser.add_argument("--limit-per-competition", type=int, default=None)
    parser.add_argument(
        "--packs-only",
        action="store_true",
        help="Rebuild competition packs without restaging tasks",
    )
    args = parser.parse_args()

    if COMP_ROOT.exists():
        shutil.rmtree(COMP_ROOT)
    selected = args.competitions or _iter_competition_ids()
    catalog = [project_competition(cid) for cid in selected]
    _dump(
        COMP_ROOT / "index.json",
        {
            "description": "One last-exam pack per data/rules competition.",
            "n_competitions": len(catalog),
            "competitions": catalog,
        },
    )

    cards: list[dict[str, Any]] = []
    existing_cards_path = OUT_ROOT / "task_cards.json"
    if args.packs_only and existing_cards_path.is_file():
        cards = list((_load(existing_cards_path) or {}).get("tasks") or [])
    elif not args.packs_only:
        if TASKS_ROOT.exists():
            shutil.rmtree(TASKS_ROOT)
        for cid in selected:
            rows = _load_problems(cid)
            if args.limit_per_competition is not None:
                rows = rows[: args.limit_per_competition]
            for row in rows:
                cards.append(project_task(cid, row))

    _dump(
        OUT_ROOT / "index.json",
        {
            "description": (
                "Last Exam layout: shared competition packs plus thin problem tasks. "
                "data/rules remains canonical. data/base is a previous generator output."
            ),
            "status": "generated_from_data_rules",
            "source_rules": "data/rules",
            "source_benchmarks": "data/benchmarks",
            "generate": "python collectors/build_last_exam_from_rules.py",
            "n_competitions": len(catalog),
            "n_tasks": len(cards),
            "competitions_index": "competitions/index.json",
            "visibility": {
                "agent_at_start": [
                    "competitions/<cid>/input",
                    "competitions/<cid>/method",
                    "tasks/<cid>/<pid>/base/input",
                ],
                "hidden_until_grade": [
                    "competitions/<cid>/eval",
                    "tasks/<cid>/<pid>/eval",
                ],
            },
        },
    )
    _dump(
        OUT_ROOT / "task_cards.json",
        {
            "description": "Thin Last Exam task cards. Each task inherits one competition pack.",
            "n_tasks": len(cards),
            "tasks": cards,
        },
    )
    print(
        json.dumps(
            {
                "n_competitions": len(catalog),
                "n_tasks": len(cards),
                "root": "data/last_exam",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
