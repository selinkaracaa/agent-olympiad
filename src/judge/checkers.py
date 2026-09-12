"""Built-in and trusted custom output checkers."""

from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .models import JudgeError


def _tokens(expected: str, actual: str) -> tuple[list[str], list[str]]:
    return expected.split(), actual.split()


def _infiltration_output(text: str, sizes: list[int]) -> list[list[int]]:
    """Strict case framing, flexible whitespace and arbitrary identifier order."""
    tokens = iter(text.split())
    cells = []
    for case_number, n in enumerate(sizes, 1):
        if next(tokens) != "Case" or next(tokens) != f"{case_number}:":
            raise ValueError("incorrect case label")
        def integer() -> int:
            token = next(tokens)
            if not re.fullmatch(r"[0-9]+", token):
                raise ValueError("expected a nonnegative integer")
            return int(token)
        count = integer()
        if not 1 <= count <= n:
            raise ValueError("invalid set size")
        chosen = [integer() for _ in range(count)]
        if len(set(chosen)) != count or any(not 1 <= x <= n for x in chosen):
            raise ValueError("duplicate or out-of-range cell")
        cells.append(chosen)
    if next(tokens, None) is not None:
        raise ValueError("extra output")
    return cells


def _check_infiltration(expected: str, actual: str, input_path: Path | None) -> tuple[bool, str]:
    """Validate direct domination, using the trusted answer's optimal size."""
    if input_path is None:
        raise JudgeError("Infiltration checker requires test input")
    try:
        tokens = iter(input_path.read_text(encoding="utf-8").split())
        graphs = []
        while (raw_n := next(tokens, None)) is not None:
            n = int(raw_n)
            if not 1 <= n <= 75:
                raise ValueError("invalid number of cells")
            rows = [next(tokens) for _ in range(n)]
            if any(len(row) != n or set(row) - {"0", "1"} for row in rows):
                raise ValueError("invalid adjacency matrix")
            graphs.append(rows)
        sizes = [len(rows) for rows in graphs]
        wanted = _infiltration_output(expected, sizes)
    except (OSError, ValueError, StopIteration) as exc:
        raise JudgeError(f"Invalid Infiltration test fixture: {exc}") from exc
    try:
        received = _infiltration_output(actual, sizes)
    except (ValueError, StopIteration) as exc:
        return False, f"Invalid Infiltration output: {exc}"
    for number, (rows, optimal, chosen) in enumerate(zip(graphs, wanted, received), 1):
        if len(chosen) != len(optimal):
            return False, f"Case {number}: expected minimum set size {len(optimal)}, received {len(chosen)}"
        covered = {cell - 1 for cell in chosen}
        for cell in chosen:
            covered.update(i for i, edge in enumerate(rows[cell - 1]) if edge == "1")
        if len(covered) != len(rows):
            return False, f"Case {number}: selected cells do not directly control all cells"
    return True, ""


def check_output(
    expected: str,
    actual: str,
    checker: dict[str, Any],
    *,
    input_path: Path | None = None,
) -> tuple[bool, str]:
    mode = str(checker.get("mode") or checker.get("type") or "token").lower()
    if mode == "infiltration":
        return _check_infiltration(expected, actual, input_path)
    if mode == "exact":
        accepted = expected == actual
        return accepted, "" if accepted else "exact output mismatch"
    if mode in {"token", "float"}:
        wanted, received = _tokens(expected, actual)
        if len(wanted) != len(received):
            return False, (
                f"token count mismatch: expected {len(wanted)}, received {len(received)}"
            )
        absolute = float(
            checker.get("absolute_tolerance", checker.get("abs_tol", 1e-6 if mode == "float" else 0))
        )
        relative = float(
            checker.get("relative_tolerance", checker.get("rel_tol", 1e-6 if mode == "float" else 0))
        )
        for index, (expected_token, actual_token) in enumerate(
            zip(wanted, received), start=1
        ):
            if expected_token == actual_token:
                continue
            if mode == "float":
                try:
                    expected_number = float(expected_token)
                    actual_number = float(actual_token)
                except ValueError:
                    pass
                else:
                    if (
                        math.isfinite(expected_number)
                        and math.isfinite(actual_number)
                        and math.isclose(
                            expected_number,
                            actual_number,
                            rel_tol=relative,
                            abs_tol=absolute,
                        )
                    ):
                        continue
            return False, f"token {index} mismatch"
        return True, ""
    if mode != "custom":
        raise JudgeError(f"Unsupported checker mode: {mode}")

    command_template = checker.get("command")
    if not isinstance(command_template, list) or not command_template:
        raise JudgeError("Custom checker requires a command list.")
    with tempfile.TemporaryDirectory(prefix="ao_checker_") as temp:
        actual_path = Path(temp) / "actual.txt"
        expected_path = Path(temp) / "expected.txt"
        actual_path.write_text(actual, encoding="utf-8")
        expected_path.write_text(expected, encoding="utf-8")
        replacements = {
            "{input}": str(input_path or ""),
            "{expected}": str(expected_path),
            "{actual}": str(actual_path),
        }
        command = [
            replacements.get(str(argument), str(argument))
            for argument in command_template
        ]
        if not any(str(argument) in replacements for argument in command_template):
            command.extend([str(input_path or ""), str(expected_path), str(actual_path)])
        try:
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=float(checker.get("timeout_sec", 5)),
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise JudgeError(f"Custom checker failed: {exc}") from exc
        detail = ((process.stdout or "") + (process.stderr or "")).strip()[:1000]
        return process.returncode == 0, "" if process.returncode == 0 else (
            detail or "custom checker rejected output"
        )
