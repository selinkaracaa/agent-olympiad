"""Safe package loading for ``ao.icpc-package/v1`` bundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import JudgeError, Limits, ProblemPackage, Subtask, TestCase, TestGroup

SCHEMA_VERSION = "ao.icpc-package/v1"


def _inside(root: Path, candidate: Path) -> Path:
    resolved = candidate.resolve()
    if resolved != root and root not in resolved.parents:
        raise JudgeError(f"Package path escapes root: {candidate}")
    return resolved


def _positive_int(raw: Any, name: str) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError) as exc:
        raise JudgeError(f"{name} must be a positive integer.") from exc
    if value <= 0:
        raise JudgeError(f"{name} must be a positive integer.")
    return value


def _group_entries(raw_groups: Any) -> list[dict[str, Any]]:
    if isinstance(raw_groups, dict):
        return [{"id": key, **dict(value)} for key, value in raw_groups.items()]
    if isinstance(raw_groups, list):
        return [dict(value) for value in raw_groups]
    raise JudgeError("groups must be a list or object.")


def _load_group(root: Path, raw: dict[str, Any]) -> TestGroup:
    group_id = str(raw.get("id") or "").strip()
    scope = str(raw.get("scope") or group_id).lower()
    if not group_id or scope not in {"sample", "secret"}:
        raise JudgeError("Every group needs an id and sample/secret scope.")
    directory = _inside(root, root / str(raw.get("tests") or raw.get("path") or group_id))
    if not directory.is_dir():
        raise JudgeError(f"Test group directory is missing: {directory}")
    tests: list[TestCase] = []
    for input_path in sorted(directory.glob("*.in")):
        answer_path = input_path.with_suffix(".ans")
        if not answer_path.is_file():
            answer_path = input_path.with_suffix(".out")
        if not answer_path.is_file():
            raise JudgeError(f"Missing answer for {input_path.name}.")
        tests.append(
            TestCase(
                name=input_path.stem,
                scope=scope,  # type: ignore[arg-type]
                group=group_id,
                input_path=_inside(root, input_path),
                answer_path=_inside(root, answer_path),
            )
        )
    return TestGroup(id=group_id, scope=scope, tests=tuple(tests))  # type: ignore[arg-type]


def load_problem_package(path: str | Path) -> ProblemPackage:
    root = Path(path).resolve()
    manifest_path = root / "package.json"
    if not manifest_path.is_file():
        raise JudgeError(f"Missing problem package manifest: {manifest_path}")
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JudgeError(f"Invalid problem package manifest: {exc}") from exc
    if raw.get("schema_version") != SCHEMA_VERSION:
        raise JudgeError(f"Unsupported package schema; expected {SCHEMA_VERSION}.")

    limits_raw = dict(raw.get("limits") or {})
    limits = Limits(
        time_ms=_positive_int(
            limits_raw.get("time_ms", raw.get("time_limit_ms")), "limits.time_ms"
        ),
        memory_mb=_positive_int(
            limits_raw.get("memory_mb", raw.get("memory_limit_mb")),
            "limits.memory_mb",
        ),
        output_kb=_positive_int(
            limits_raw.get("output_kb", raw.get("output_limit_kb", 1024)),
            "limits.output_kb",
        ),
    )

    if "groups" in raw:
        groups = tuple(_load_group(root, item) for item in _group_entries(raw["groups"]))
    else:
        # Compatibility with the original Phase 3 flat-package prototype.
        groups = (
            _load_group(
                root,
                {"id": "secret", "scope": "secret", "tests": raw.get("tests", "tests")},
            ),
        )
    if not groups or not any(group.tests for group in groups):
        raise JudgeError("Problem package contains no tests.")
    group_ids = {group.id for group in groups}
    if len(group_ids) != len(groups):
        raise JudgeError("Test group ids must be unique.")

    checker = dict(raw.get("checker") or {"mode": "token"})
    checker["mode"] = str(checker.get("mode") or checker.get("type") or "token").lower()
    if checker["mode"] not in {"exact", "token", "float", "custom"}:
        raise JudgeError(f"Unsupported checker mode: {checker['mode']}")
    if checker["mode"] == "custom":
        command = checker.get("command")
        if not isinstance(command, list) or not command:
            raise JudgeError("Custom checker requires a non-empty command list.")
        executable = _inside(root, root / str(command[0]))
        if not executable.is_file():
            raise JudgeError("Custom checker executable is missing.")
        checker["command"] = [str(executable), *[str(value) for value in command[1:]]]

    subtasks_raw = raw.get("subtasks")
    if subtasks_raw is None:
        subtasks_raw = [
            {"id": group.id, "points": 1.0, "groups": [group.id]} for group in groups
        ]
    subtasks: list[Subtask] = []
    for item in subtasks_raw:
        item = dict(item)
        groups_for_subtask = tuple(str(value) for value in item.get("groups", ()))
        if not groups_for_subtask or not set(groups_for_subtask) <= group_ids:
            raise JudgeError("Subtask references an unknown or empty test group.")
        min_score = item.get("min_score")
        if min_score is not None:
            min_score = float(min_score)
            if not 0 <= min_score <= 1:
                raise JudgeError("Subtask min_score must be between 0 and 1.")
        points = float(item.get("points", 0))
        if points < 0:
            raise JudgeError("Subtask points cannot be negative.")
        subtasks.append(
            Subtask(
                id=str(item.get("id") or f"subtask-{len(subtasks) + 1}"),
                points=points,
                groups=groups_for_subtask,
                min_score=min_score,
            )
        )

    images = dict(raw.get("images") or {})
    if raw.get("image"):
        images.setdefault("python3", str(raw["image"]))
    images.setdefault("python3", "python:3.12-slim")
    images.setdefault("cpp17", "gcc:14")
    return ProblemPackage(
        problem_id=str(raw.get("problem_id") or root.name),
        root=root,
        limits=limits,
        checker=checker,
        groups=groups,
        subtasks=tuple(subtasks),
        images=images,
    )


def package_from_sample_directory(
    problem_id: str,
    directory: str | Path,
    *,
    time_ms: int = 5000,
    memory_mb: int = 256,
    output_kb: int = 1024,
) -> ProblemPackage:
    """Adapt legacy ``*.in``/``*.ans`` samples without rewriting them."""
    root = Path(directory).resolve()
    tests: list[TestCase] = []
    if root.is_dir():
        for input_path in sorted(root.glob("*.in")):
            answer = input_path.with_suffix(".ans")
            if not answer.is_file():
                answer = input_path.with_suffix(".out")
            if answer.is_file():
                tests.append(
                    TestCase(
                        input_path.stem,
                        input_path,
                        answer,
                        "sample",
                        "sample",
                    )
                )
    group = TestGroup("sample", "sample", tuple(tests))
    return ProblemPackage(
        problem_id=problem_id,
        root=root,
        limits=Limits(time_ms, memory_mb, output_kb),
        checker={"mode": "token"},
        groups=(group,),
        subtasks=(Subtask("sample", 1.0, ("sample",)),),
        images={"python3": "python:3.12-slim", "cpp17": "gcc:14"},
    )
