"""Offline-only adapter for mounted LiveOIBench data.

This module validates metadata, returns ``ao.icpc-package/v1`` model objects,
and exports ``<model>_code.json``.  It never downloads data, runs setup scripts,
or invokes the upstream host judge.  Expected-output contents are never read
into returned structures.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

try:
    from judge.models import JudgeError, Limits, ProblemPackage, Subtask, TestCase, TestGroup
except ImportError:  # pragma: no cover - supports ``python src/...py``
    from src.judge.models import (
        JudgeError,
        Limits,
        ProblemPackage,
        Subtask,
        TestCase,
        TestGroup,
    )

SCHEMA_VERSION = "ao.icpc-package/v1"
SUPPORTED_CODE_SUFFIXES = {".cpp", ".py", ".java"}
UNSAFE_SCRIPT_NAMES = {"evaluate.sh", "setup.sh"}


def _inside(root: Path, path: Path) -> Path:
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise JudgeError(f"LiveOIBench path escapes problem root: {path}")
    return resolved


def _read_object(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file():
        raise JudgeError(f"Missing LiveOIBench {label}: {path}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise JudgeError(f"Invalid LiveOIBench {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise JudgeError(f"LiveOIBench {label} must be a JSON object")
    return value


def _positive_limit(raw: Any, name: str, multiplier: float = 1.0) -> int:
    try:
        value = float(raw) * multiplier
    except (TypeError, ValueError) as exc:
        raise JudgeError(f"{name} must be positive") from exc
    if not math.isfinite(value) or value <= 0:
        raise JudgeError(f"{name} must be positive")
    return max(1, round(value))


def _test_pairs(root: Path) -> dict[str, tuple[Path, Path]]:
    tests_dir = _inside(root, root / "tests")
    if not tests_dir.is_dir():
        raise JudgeError(f"Missing LiveOIBench tests directory: {tests_dir}")
    pairs: dict[str, tuple[Path, Path]] = {}
    for input_path in sorted(tests_dir.glob("*.in")):
        input_path = _inside(root, input_path)
        output_path = _inside(root, input_path.with_suffix(".out"))
        if not output_path.is_file():
            output_path = _inside(root, input_path.with_suffix(".ans"))
        if not output_path.is_file():
            raise JudgeError(f"Missing expected output for test {input_path.name}")
        pairs[input_path.stem] = (input_path, output_path)
    if not pairs:
        raise JudgeError("LiveOIBench problem contains no test pairs")
    return pairs


def _subtask_entries(raw: Mapping[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    for key, value in raw.items():
        if not isinstance(value, Mapping):
            raise JudgeError(f"Subtask {key} must be an object")
        entries.append((str(key), dict(value)))
    return entries


def _safe_asset_paths(root: Path, directory: str, suffixes: set[str]) -> list[str]:
    location = _inside(root, root / directory)
    if not location.exists():
        return []
    if not location.is_dir():
        raise JudgeError(f"LiveOIBench asset path is not a directory: {location}")
    return [
        str(_inside(root, path))
        for path in sorted(location.iterdir())
        if path.is_file() and path.suffix.lower() in suffixes
    ]


def load_liveoibench_problem(
    problem_dir: str | Path,
    *,
    problem_id: str | None = None,
) -> ProblemPackage:
    """Validate one mounted problem and map it to ``ProblemPackage``.

    Only paths to test inputs/answers are retained, matching the trusted judge
    model.  This function does not read either file's contents.
    """

    root = Path(problem_dir).resolve()
    if not root.is_dir():
        raise JudgeError(f"LiveOIBench problem directory not found: {root}")
    config = _read_object(_inside(root, root / "problem.json"), "problem.json")
    raw_subtasks = _read_object(
        _inside(root, root / "subtasks.json"), "subtasks.json"
    )
    pairs = _test_pairs(root)

    groups: list[TestGroup] = []
    subtasks: list[Subtask] = []
    covered: set[str] = set()
    for subtask_id, raw in _subtask_entries(raw_subtasks):
        test_names = raw.get("testcases", raw.get("tests"))
        if not isinstance(test_names, list) or not test_names:
            raise JudgeError(f"Subtask {subtask_id} has no testcases")
        names = tuple(str(name) for name in test_names)
        unknown = sorted(set(names) - pairs.keys())
        if unknown:
            raise JudgeError(
                f"Subtask {subtask_id} references unknown tests: {', '.join(unknown)}"
            )
        points = float(raw.get("score", raw.get("points", 0)))
        if not math.isfinite(points) or points < 0:
            raise JudgeError(f"Subtask {subtask_id} has invalid score")
        min_score = raw.get("min_score", raw.get("min-score"))
        if min_score is not None:
            min_score = float(min_score)
            if not 0 <= min_score <= 1:
                raise JudgeError(f"Subtask {subtask_id} min_score must be in [0, 1]")
        tests = tuple(
            TestCase(
                name=name,
                input_path=pairs[name][0],
                answer_path=pairs[name][1],
                scope="secret",
                group=subtask_id,
            )
            for name in names
        )
        groups.append(TestGroup(id=subtask_id, scope="secret", tests=tests))
        subtasks.append(
            Subtask(
                id=subtask_id,
                points=points,
                groups=(subtask_id,),
                min_score=min_score,
            )
        )
        covered.update(names)
    if not groups:
        raise JudgeError("LiveOIBench problem has no subtasks")
    uncovered = sorted(pairs.keys() - covered)
    if uncovered:
        raise JudgeError(f"Tests missing from subtasks: {', '.join(uncovered)}")

    checker_sources = _safe_asset_paths(root, "checkers", {".cpp", ".h", ".py"})
    grader_sources = _safe_asset_paths(root, "graders", {".cpp", ".h", ".py", ".java"})
    unsafe_scripts = []
    graders_dir = _inside(root, root / "graders")
    if graders_dir.is_dir():
        unsafe_scripts = [
            str(_inside(root, graders_dir / name))
            for name in sorted(UNSAFE_SCRIPT_NAMES)
            if (graders_dir / name).is_file()
        ]
    checker: dict[str, Any] = {
        "mode": "custom" if checker_sources else "token",
        "liveoibench_checker_sources": checker_sources,
        "liveoibench_grader_sources": grader_sources,
        "unsafe_scripts_detected": unsafe_scripts,
        "execution_policy": "disabled_adapter_only",
    }
    validated_problem_id = _safe_problem_id(problem_id) if problem_id else infer_problem_id(root)
    return ProblemPackage(
        problem_id=validated_problem_id,
        root=root,
        limits=Limits(
            time_ms=_positive_limit(config.get("time_limit", 1), "time_limit", 1000),
            memory_mb=_positive_limit(config.get("memory_limit", 1024), "memory_limit"),
            output_kb=_positive_limit(config.get("output_limit_kb", 1024), "output_limit_kb"),
        ),
        checker=checker,
        groups=tuple(groups),
        subtasks=tuple(subtasks),
        images={"python3": "python:3.12-slim", "cpp17": "gcc:14"},
    )


def infer_problem_id(root: Path) -> str:
    """Infer ``competition-year-round-task`` from the final four path parts."""

    if len(root.parts) < 4:
        raise JudgeError("Cannot infer problem_id; pass it explicitly")
    parts = root.parts[-4:]
    if any(not part or part in {".", ".."} for part in parts):
        raise JudgeError("Invalid LiveOIBench problem path")
    return "-".join(parts)


def sanitized_package_metadata(package: ProblemPackage) -> dict[str, Any]:
    """Return agent-safe metadata with no test or expected-output contents."""

    return {
        "schema_version": SCHEMA_VERSION,
        "problem_id": package.problem_id,
        "limits": {
            "time_ms": package.time_limit_ms,
            "memory_mb": package.memory_limit_mb,
            "output_kb": package.output_limit_kb,
        },
        "checker": {
            key: value for key, value in package.checker.items()
            if key not in {"command"}
        },
        "groups": [
            {
                "id": group.id,
                "scope": group.scope,
                "test_names": [test.name for test in group.tests],
                "test_count": len(group.tests),
            }
            for group in package.groups
        ],
        "subtasks": [
            {
                "id": subtask.id,
                "points": subtask.points,
                "groups": list(subtask.groups),
                "min_score": subtask.min_score,
            }
            for subtask in package.subtasks
        ],
        "secrets": {
            "expected_outputs_loaded": False,
            "test_inputs_loaded": False,
            "unsafe_host_judge_executed": False,
        },
    }


def _safe_filename(value: str) -> str:
    if not value or Path(value).name != value or value in {".", ".."}:
        raise ValueError(f"Unsafe solution filename: {value!r}")
    if Path(value).suffix.lower() not in SUPPORTED_CODE_SUFFIXES:
        raise ValueError(f"Unsupported solution filename: {value}")
    return value


def _safe_problem_id(value: str) -> str:
    if (
        not value
        or value in {".", ".."}
        or "/" in value
        or "\\" in value
        or not re.fullmatch(r"[A-Za-z0-9_.+-]+", value)
    ):
        raise ValueError(f"Unsafe problem_id: {value!r}")
    return value


def build_code_export(
    candidates: Iterable[Mapping[str, Any]] | Mapping[str, Any],
) -> dict[str, dict[str, str]]:
    """Build LiveOIBench's ``problem_id -> filename -> code`` schema."""

    if isinstance(candidates, Mapping):
        if all(isinstance(value, Mapping) for value in candidates.values()):
            output: dict[str, dict[str, str]] = {}
            for raw_problem, solutions in candidates.items():
                problem_id = _safe_problem_id(str(raw_problem))
                output[problem_id] = {}
                for raw_name, raw_value in solutions.items():
                    filename = _safe_filename(str(raw_name))
                    code = raw_value.get("code") if isinstance(raw_value, Mapping) else raw_value
                    if not isinstance(code, str) or not code.strip():
                        raise ValueError(f"Solution {problem_id}/{filename} has empty code")
                    output[problem_id][filename] = code
            return output
        candidates = [candidates]

    output = {}
    for index, row in enumerate(candidates):
        problem_id = _safe_problem_id(str(row.get("problem_id") or ""))
        filename = _safe_filename(
            str(
                row.get("filename")
                or row.get("solution_file")
                or f"solution_{index}.cpp"
            )
        )
        code = row.get("code") or row.get("source") or row.get("final_answer")
        if not isinstance(code, str) or not code.strip():
            raise ValueError(f"Candidate {problem_id}/{filename} has empty code")
        problem = output.setdefault(problem_id, {})
        if filename in problem and problem[filename] != code:
            raise ValueError(f"Conflicting duplicate candidate {problem_id}/{filename}")
        problem[filename] = code
    return {problem: dict(sorted(files.items())) for problem, files in sorted(output.items())}


def export_code_json(
    candidates: Iterable[Mapping[str, Any]] | Mapping[str, Any],
    model: str,
    output: str | Path,
) -> Path:
    """Atomically write a validated ``<model>_code.json`` file."""

    if not model or "/" in model or "\\" in model or model in {".", ".."}:
        raise ValueError("model must be a safe path component")
    destination = Path(output)
    if destination.exists() and destination.is_dir():
        destination = destination / f"{model}_code.json"
    elif destination.suffix.lower() != ".json":
        destination = destination / f"{model}_code.json"
    payload = build_code_export(candidates)
    _write_json_atomic(destination, payload)
    return destination


def load_contestant_data(path: str | Path) -> list[dict[str, Any]]:
    """Load local contestant JSON, JSONL, or optionally parquet.

    JSON requires only the standard library.  Parquet raises a clear dependency
    error unless pandas or pyarrow is installed.
    """

    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(source)
    if source.suffix.lower() in {".json", ".jsonl", ".ndjson"}:
        text = source.read_text(encoding="utf-8")
        if source.suffix.lower() == ".json":
            payload = json.loads(text)
            if isinstance(payload, list):
                rows = payload
            elif isinstance(payload, Mapping) and isinstance(payload.get("rows"), list):
                rows = payload["rows"]
            elif isinstance(payload, Mapping):
                rows = [
                    {"contest_id": key, **dict(value)}
                    for key, value in payload.items() if isinstance(value, Mapping)
                ]
            else:
                raise ValueError("Contestant JSON must be an object or array")
        else:
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        if not all(isinstance(row, Mapping) for row in rows):
            raise ValueError("Every contestant row must be an object")
        return [dict(row) for row in rows]
    if source.suffix.lower() != ".parquet":
        raise ValueError("Contestant data must be JSON, JSONL, or parquet")
    try:
        import pandas as pd  # type: ignore

        return pd.read_parquet(source).to_dict(orient="records")
    except ImportError:
        try:
            import pyarrow.parquet as parquet  # type: ignore

            return parquet.read_table(source).to_pylist()
        except ImportError as exc:
            raise RuntimeError(
                "Parquet import requires optional pandas or pyarrow; JSON works without either"
            ) from exc


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser("export", help="Export <model>_code.json")
    export.add_argument("--input", required=True, type=Path)
    export.add_argument("--model", required=True)
    export.add_argument("--output", required=True, type=Path)

    inspect = commands.add_parser(
        "import-problem", help="Validate mounted problem metadata without judging"
    )
    inspect.add_argument("--problem-dir", required=True, type=Path)
    inspect.add_argument("--problem-id")
    inspect.add_argument("--output", required=True, type=Path)

    contestants = commands.add_parser(
        "import-contestants", help="Normalize local contestant JSON/parquet"
    )
    contestants.add_argument("--input", required=True, type=Path)
    contestants.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)

    if args.command == "export":
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        export_code_json(payload, args.model, args.output)
    elif args.command == "import-problem":
        package = load_liveoibench_problem(args.problem_dir, problem_id=args.problem_id)
        _write_json_atomic(args.output, sanitized_package_metadata(package))
    else:
        _write_json_atomic(args.output, load_contestant_data(args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
