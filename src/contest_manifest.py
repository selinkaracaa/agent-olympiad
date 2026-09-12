"""Explicit multi-problem contest manifests and benchmark task extraction."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

TaskFamily = Literal[
    "programming",
    "mathematics",
    "short_answer",
    "puzzle",
    "general",
    "mixed",
]

_MATHEMATICS_COMPETITIONS = frozenset(
    {
        "arml_local",
        "arml_national_team",
        "arml_national_power",
        "arml_power",
        "hmmt_guts",
        "hmmt_team",
        "purple_comet",
        "wmtc",
    }
)
_SHORT_ANSWER_COMPETITIONS = frozenset(
    {"history_olympiad", "qanta", "science_bowl"}
)
_PUZZLE_COMPETITIONS = frozenset({"mystery_hunt"})


@dataclass(frozen=True)
class ManifestTask:
    task_id: str
    parent_problem_id: str
    question_id: str | None
    prompt: str
    task_type: str
    max_score: float
    programming: bool
    benchmark: dict[str, Any] = field(repr=False, compare=False)


@dataclass(frozen=True)
class ContestManifest:
    session_id: str
    competition_id: str
    tasks: tuple[ManifestTask, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def task_family(self) -> TaskFamily:
        """Route the contest into a domain workflow, with manifest override support."""
        override = str(self.metadata.get("task_family") or "").strip().lower()
        allowed = {
            "programming",
            "mathematics",
            "short_answer",
            "puzzle",
            "general",
            "mixed",
        }
        if override:
            if override not in allowed:
                raise ValueError(f"unsupported manifest task_family: {override}")
            return override  # type: ignore[return-value]

        competition = self.competition_id.strip().lower()
        if competition in _MATHEMATICS_COMPETITIONS:
            return "mathematics"
        if competition in _SHORT_ANSWER_COMPETITIONS:
            return "short_answer"
        if competition in _PUZZLE_COMPETITIONS:
            return "puzzle"

        families = {_task_family(task) for task in self.tasks}
        if len(families) == 1:
            return families.pop()
        return "mixed"


def _task_family(task: ManifestTask) -> TaskFamily:
    if task.programming:
        return "programming"
    task_type = task.task_type.strip().lower()
    if any(marker in task_type for marker in ("math", "numeric", "proof")):
        return "mathematics"
    if "puzzle" in task_type:
        return "puzzle"
    if any(marker in task_type for marker in ("quiz", "bowl", "short_answer")):
        return "short_answer"
    return "general"


def _public_problem_text(text: str) -> str:
    """Remove appended answer sections before either packet or split delivery."""
    answer_heading = re.search(
        r"(?:^|\s)(?:\d{4}\s+)?(?:Team\s+)?(?:Answers|Solutions)\s+"
        r"(?:[A-Za-z]-)?1[.)]\s+",
        text,
        flags=re.IGNORECASE,
    )
    return (text[: answer_heading.start()] if answer_heading else text).strip()


def _numbered_prompts(text: str, part_ids: list[str]) -> dict[str, str]:
    """Extract known numbered parts without treating arbitrary decimals as tasks."""
    problem_text = _public_problem_text(text)
    starts: list[tuple[str, int, int]] = []
    cursor = 0
    for part_id in part_ids:
        match = re.search(
            rf"(?:^|\s)(?:[A-Za-z]-)?{re.escape(part_id)}[.)]\s+",
            problem_text[cursor:],
        )
        if match is None:
            return {}
        absolute_start = cursor + match.start()
        content_start = cursor + match.end()
        starts.append((part_id, absolute_start, content_start))
        cursor = content_start
    prompts: dict[str, str] = {}
    for index, (part_id, _marker_start, content_start) in enumerate(starts):
        content_end = (
            starts[index + 1][1]
            if index + 1 < len(starts)
            else len(problem_text)
        )
        prompts[part_id] = problem_text[content_start:content_end].strip()
    return prompts


def _benchmark_rows(root: Path, competition_id: str) -> dict[str, dict[str, Any]]:
    path = root / competition_id / "benchmark.json"
    if not path.is_file():
        raise ValueError(f"Missing benchmark file: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"Benchmark must contain a list: {path}")
    return {
        str(row.get("problem_id")): row
        for row in payload
        if isinstance(row, dict) and row.get("problem_id")
    }


def load_contest_manifest(
    path: str | Path,
    *,
    benchmark_root: str | Path,
) -> ContestManifest:
    source = Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"))
    session_id = str(raw.get("session_id") or source.stem).strip()
    competition_id = str(raw.get("competition_id") or "").strip()
    problem_ids = [str(item) for item in raw.get("problem_ids") or []]
    if not session_id or not competition_id or not problem_ids:
        raise ValueError("Manifest requires session_id, competition_id, and problem_ids")

    rows = _benchmark_rows(Path(benchmark_root), competition_id)
    missing = [problem_id for problem_id in problem_ids if problem_id not in rows]
    if missing:
        raise ValueError(f"Manifest problems missing from benchmark: {missing}")

    tasks: list[ManifestTask] = []
    split_parts = bool(raw.get("split_parts"))
    included_question_ids = {
        str(item) for item in raw.get("question_ids") or []
    }
    prompt_overrides = {
        str(key): str(value).strip()
        for key, value in (raw.get("prompt_overrides") or {}).items()
        if str(value).strip()
    }
    for problem_id in problem_ids:
        row = rows[problem_id]
        task_type = str(row.get("task_type") or "")
        evaluation = row.get("evaluation") or {}
        programming = task_type in {"algorithmic_programming", "programming"} or (
            evaluation.get("evaluator_id") == "programming_judge"
        )
        parts = (row.get("gold_label") or {}).get("parts") or []
        if split_parts and not programming and not parts:
            raise ValueError(f"Cannot split {problem_id}: no structured part IDs")
        if split_parts and parts and not programming:
            all_parts = parts
            if included_question_ids:
                parts = [
                    part
                    for part in parts
                    if str(part.get("id")) in included_question_ids
                ]
            all_ids = [
                str(part.get("id"))
                for part in all_parts
                if part.get("id") is not None
            ]
            if included_question_ids - set(all_ids):
                raise ValueError(f"Cannot split {problem_id}: unknown requested question IDs")
            prompts = _numbered_prompts(
                str(row.get("problem_description") or ""),
                all_ids,
            )
            if len(prompts) == len(all_ids):
                for part in parts:
                    question_id = str(part["id"])
                    tasks.append(
                        ManifestTask(
                            task_id=f"{problem_id}:{question_id}",
                            parent_problem_id=problem_id,
                            question_id=question_id,
                            prompt=prompt_overrides.get(
                                question_id,
                                prompts[question_id],
                            ),
                            task_type=task_type,
                            max_score=float(part.get("points", part.get("max_score", 1))),
                            programming=False,
                            benchmark=row,
                        )
                    )
                continue
            raise ValueError(f"Cannot split {problem_id}: numbered prompts do not match part IDs")
        tasks.append(
            ManifestTask(
                task_id=problem_id,
                parent_problem_id=problem_id,
                question_id=None,
                prompt=_public_problem_text(str(
                    row.get("problem_description")
                    or row.get("description")
                    or row.get("prompt")
                    or problem_id
                )),
                task_type=task_type,
                max_score=float(
                    row.get("max_score")
                    or row.get("total_points")
                    or (1 if programming else 1)
                ),
                programming=programming,
                benchmark=row,
            )
        )
    return ContestManifest(
        session_id=session_id,
        competition_id=competition_id,
        tasks=tuple(tasks),
        metadata={
            key: value
            for key, value in raw.items()
            if key not in {"session_id", "competition_id", "problem_ids", "split_parts"}
        },
    )
