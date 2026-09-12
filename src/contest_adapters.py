"""Adapters from contest sessions to existing tools, judges, and gold graders."""

from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from contest_manifest import ContestManifest, ManifestTask
from env import OlympiadEnvironment
from tool_registry import ACTION_REGISTRY, TOOL_PACKS
from evaluation.gold import GoldAnswerEvaluator, answers_match, load_gold_parts
from evaluation.programming_judge import (
    _extract_source,
    judge_programming_submission,
    load_sample_cases,
    samples_dir,
)

SAMPLE_TEXT_LIMIT = 400


def _clip(text: str, limit: int = SAMPLE_TEXT_LIMIT) -> str:
    text = text.rstrip("\n")
    return text if len(text) <= limit else text[:limit] + "…"


def _actual_output(source: str, stdin: str, *, timeout_sec: float) -> str:
    """Re-run one failing sample to capture what the program printed."""
    from isolated_python import IsolationUnavailable, run_python_isolated
    try:
        result = run_python_isolated(source, stdin=stdin, timeout_sec=timeout_sec)
        return result.stdout.replace("\r\n", "\n")
    except IsolationUnavailable:
        return ""


def _repo_root_from_benchmark_root(benchmark_root: str) -> Path | None:
    root = Path(benchmark_root).resolve()
    if root.name == "benchmarks" and root.parent.name == "data":
        return root.parent.parent
    return None


def run_sample_report(
    task: ManifestTask,
    code: str,
    *,
    competition_id: str,
    repo_root: Path | None,
) -> dict[str, Any]:
    """Judge ``code`` against the official sample package of ``task``.

    Returns ``sample_verdict`` ``None`` when the problem ships no samples, so
    callers can fall back to treating a plain local run as evidence.
    """
    benchmark = task.benchmark
    # Samples are fetched from Kattis once and cached under data/benchmarks;
    # a fetch failure simply yields "no samples" rather than an error.
    result = judge_programming_submission(
        benchmark,
        code,
        competition_id=competition_id,
        repo_root=repo_root,
        fetch_kattis=bool(benchmark.get("kattis_id")),
        test_scope="sample",
    )
    if result.verdict == "NO_TESTS":
        return {
            "sample_verdict": None,
            "sample_cases": [],
            "sample_summary": "No official sample cases are available for this task.",
        }
    problem_id = str(benchmark.get("problem_id") or task.parent_problem_id)
    expected_by_name = {
        case.name: case
        for case in load_sample_cases(samples_dir(competition_id, problem_id, repo_root))
    }
    source, language = _extract_source(code)
    timeout_sec = max(1.0, int(benchmark.get("time_limit_ms", 5000)) / 1000)
    cases: list[dict[str, Any]] = []
    for case in result.cases:
        row: dict[str, Any] = {
            "name": case.name,
            "verdict": case.verdict,
            "detail": case.detail,
        }
        sample = expected_by_name.get(case.name)
        if case.verdict != "AC" and sample is not None:
            row["input"] = _clip(sample.stdin)
            row["expected"] = _clip(sample.expected)
            if case.verdict == "WA" and language == "python3":
                row["actual"] = _clip(
                    _actual_output(source, sample.stdin, timeout_sec=timeout_sec)
                )
        cases.append(row)
    if result.verdict == "CE":
        summary = f"Sample judge: compile error. {result.compile_output}".strip()
    else:
        summary = (
            f"Sample judge: {result.verdict} ({result.passed}/{result.total} "
            "official sample cases passed)."
        )
    return {
        "sample_verdict": result.verdict,
        "sample_cases": cases,
        "sample_summary": summary,
    }


class EnvironmentTaskExecutor:
    """Reuse existing environment tool implementations without sharing their budget."""

    def __init__(
        self,
        manifest: ContestManifest,
        *,
        benchmark_root: str | Path,
    ) -> None:
        self.manifest = manifest
        self.benchmark_root = str(benchmark_root)
        self.repo_root = _repo_root_from_benchmark_root(self.benchmark_root)
        self._environments: dict[str, OlympiadEnvironment] = {}

    def execution_context_key(self, task: ManifestTask) -> str | None:
        """Fingerprint local samples and judge code, without fetching or judging.

        Bundled/custom judges are deliberately not cached: their external
        dependencies cannot be inferred safely from the legacy sample directory.
        Source identity and benchmark limits are added by the caller.
        """
        benchmark = task.benchmark
        evaluation = dict(benchmark.get("evaluation") or {})
        if benchmark.get("official_bundle_path") or any(evaluation.get(k) for k in (
            "official_bundle_path", "official_package_path", "judge_package_path"
        )):
            return None
        directory = samples_dir(self.manifest.competition_id,
                                str(benchmark.get("problem_id") or task.parent_problem_id), self.repo_root)
        if not directory.is_dir():
            return None
        files = sorted(p for p in directory.iterdir() if p.suffix in {".in", ".ans", ".out"} and p.is_file())
        if not files:
            return None
        source_root = Path(__file__).resolve().parent
        files += [source_root / name for name in (
            "contest_adapters.py", "evaluation/programming_judge.py", "isolated_python.py",
            "judge/package.py", "judge/checkers.py", "judge/runners.py", "judge/core.py",
        )]
        digest = hashlib.sha256(b"local-sample-context-v1")
        try:
            for path in files:
                digest.update(str(path.resolve()).encode("utf-8"))
                digest.update(hashlib.sha256(path.read_bytes()).digest())
        except OSError:
            return None
        return digest.hexdigest()

    def _environment(self, task: ManifestTask) -> OlympiadEnvironment:
        if task.parent_problem_id not in self._environments:
            self._environments[task.parent_problem_id] = OlympiadEnvironment(
                self.manifest.competition_id,
                task.parent_problem_id,
                base_path=self.benchmark_root,
                max_turns=100000,
                rules_mode="off",
            )
        return self._environments[task.parent_problem_id]

    def __call__(
        self,
        task: ManifestTask,
        action: str,
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        return self._execute(task, action, arguments)

    def submit_at_deadline(self, task: ManifestTask, code: str) -> dict[str, Any]:
        """Controller-only submission; agents cannot waive the sample gate."""
        if not task.programming:
            raise ValueError("deadline code submission requires a programming task")
        return self._execute(task, "submit_code", {"code": code}, force_submit=True)

    def _execute(
        self,
        task: ManifestTask,
        action: str,
        arguments: dict[str, Any],
        *,
        force_submit: bool = False,
    ) -> dict[str, Any]:
        env = self._environment(task)
        spec = ACTION_REGISTRY.get(action)
        if spec is None or spec.pack not in TOOL_PACKS:
            return {"valid": False, "error": f"Unsupported task action: {action}"}
        payload = str(arguments.get(spec.primary_argument or "") or "")
        sample_report: dict[str, Any] | None = None
        if action in {"execute_code", "submit_code"} and task.programming and not force_submit:
            sample_report = run_sample_report(
                task,
                payload,
                competition_id=self.manifest.competition_id,
                repo_root=self.repo_root,
            )
        if (
            action == "submit_code"
            and sample_report is not None
            and sample_report["sample_verdict"] not in {None, "AC", "JUDGE_ERROR"}
        ):
            # Fail locally for free instead of spending a penalized remote attempt.
            return {
                "valid": False,
                "verdict": f"SAMPLE_{sample_report['sample_verdict']}",
                "result": sample_report["sample_summary"],
                "feedback": {
                    "test_scope": "sample",
                    "verdict": sample_report["sample_verdict"],
                    "cases": sample_report["sample_cases"],
                },
                **sample_report,
            }
        # Typed arguments go straight through the environment's registry-driven
        # dispatcher: the same gate (tool allowlist) and the same tool
        # implementation the legacy protocol uses, with no text re-encoding.
        raw = env.execute_action("Team", action, {spec.primary_argument: payload})
        if action != "submit_code":
            response: dict[str, Any] = {
                "valid": not raw.startswith(("RULE VIOLATION", "Operational error")),
                "result": raw,
            }
            if sample_report is not None:
                response.update(sample_report)
            return response
        try:
            feedback = json.loads(raw)
        except json.JSONDecodeError:
            return {"valid": False, "verdict": "SUBMIT_FAILED", "result": raw}
        remote = feedback.get("remote") or {}
        remote_status = str(remote.get("status") or "").lower()
        verdict = str(remote.get("verdict") or feedback.get("verdict") or "SUBMIT_FAILED")
        if remote_status == "needs_human":
            verdict = "NEEDS_HUMAN"
        sample_only = (
            not remote and str(feedback.get("test_scope") or "").lower() != "remote"
        )
        if sample_only:
            verdict = f"SAMPLE_{verdict.upper()}"
        return {
            "valid": remote_status != "needs_human"
            and not sample_only
            and verdict.upper() not in {"", "PENDING", "SUBMIT_FAILED", "CHALLENGE"},
            "verdict": verdict,
            "feedback": feedback,
        }


class GradingUnavailable(ValueError):
    """A task lacks a supported answer key; this is not an incorrect answer."""


def _grade_non_programming(task: ManifestTask, answer: str, competition_id: str = '') -> tuple[float, float]:
    gold = task.benchmark.get("gold_label") or {}
    def match(expected, actual, aliases=()):
        if competition_id != 'qanta':
            return answers_match(expected, actual, aliases)
        # QANTA braces mark answerline emphasis, not literal answer characters.
        # Exact text only: do not infer surnames, fuzzy spelling or new aliases.
        def clean(value):
            return ' '.join(value.replace('{', '').replace('}', '').casefold().split())
        normalized = clean(actual)
        return bool(normalized) and any(normalized == clean(value) for value in (expected, *aliases))
    final_markers = re.findall(
        r"(?im)\bfinal\s+answer\s*:\s*([^\r\n]+)",
        answer,
    )
    candidate = (
        final_markers[-1].strip().rstrip(".")
        if final_markers
        else answer.strip()
    )
    if task.question_id is not None:
        part = next(
            (
                item
                for item in gold.get("parts") or []
                if str(item.get("id")) == task.question_id
            ),
            None,
        )
        if part is None or part.get("match_mode") == "reference_llm" or not str(part.get("expected") or "").strip():
            raise GradingUnavailable("No supported exact gold for this question")
        maximum = float(part.get("points", part.get("max_score", task.max_score)))
        correct = bool(candidate) and match(
            str(part.get("expected") or ""),
            candidate,
            tuple(str(alias) for alias in part.get("aliases") or ()),
        )
        return (maximum if correct else 0.0), maximum
    parts = gold.get("parts") or []
    if parts:
        gradeable = [
            item
            for item in parts
            if str(item.get("expected") or "").strip()
            and item.get("match_mode") != "reference_llm"
        ]
        if not gradeable:
            raise GradingUnavailable("Reference/rubric evaluator is unavailable")
        # Bare short answers for single-part contests (Science Bowl / Qanta / etc.).
        if len(gradeable) == 1:
            part = gradeable[0]
            maximum = float(part.get("points", part.get("max_score", task.max_score)))
            correct = bool(candidate) and match(
                str(part.get("expected") or ""),
                candidate,
                tuple(str(alias) for alias in part.get("aliases") or ()),
            )
            return (maximum if correct else 0.0), maximum
        result = GoldAnswerEvaluator(load_gold_parts({**gold, "parts": gradeable}), answer).evaluate()
        return float(result.total_score), float(result.max_score)
    expected = str(gold.get("expected_answer") or "")
    if not expected.strip():
        raise GradingUnavailable("No supported gold answer or evaluator")
    maximum = float(task.max_score)
    correct = bool(candidate) and bool(expected) and match(expected, candidate, tuple(gold.get('aliases') or ()))
    return (maximum if correct else 0.0), maximum


def grade_contest_result(
    manifest: ContestManifest,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Grade the latest valid per-task submissions without exposing gold to agents."""
    rows: dict[str, dict[str, Any]] = {}
    normalized: list[float] = []
    total_score = 0.0
    total_max = 0.0
    task_states = result.get("tasks") or {}
    submissions = result.get("submissions") or {}
    for task in manifest.tasks:
        if task.programming:
            state = task_states.get(task.task_id) or {}
            score = 1.0 if state.get("state") == "solved" else 0.0
            maximum = 1.0
        else:
            try:
                score, maximum = _grade_non_programming(
                    task,
                    str(submissions.get(task.task_id) or ""),
                    manifest.competition_id,
                )
            except GradingUnavailable as exc:
                rows[task.task_id] = {
                    "graded": False, "status": "unavailable", "reason": str(exc),
                    "score": None, "max_score": None, "utility": None,
                }
                continue
        rows[task.task_id] = {
            "graded": True,
            "score": score,
            "max_score": maximum,
            "utility": score / maximum if maximum > 0 else 0.0,
        }
        total_score += score
        total_max += maximum
        normalized.append(rows[task.task_id]["utility"])
    all_supported = bool(rows) and len(normalized) == len(rows)
    return {
        "graded": all_supported,
        "evaluation_coverage": len(normalized) / len(rows) if rows else 0.0,
        "graded_tasks": len(normalized),
        "ungraded_tasks": len(rows) - len(normalized),
        "method": "contest_session_v1",
        "score": total_score if normalized else None,
        "max_score": total_max if normalized else None,
        "task_utility": sum(normalized) / len(normalized) if normalized else None,
        "tasks": rows,
    }
