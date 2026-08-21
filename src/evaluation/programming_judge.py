"""Local programming judge: run submissions against bundled sample tests.

ICPC/IIOT full secret tests + DomJudge are still future work. This module:
  1. Loads .in/.ans pairs from data/benchmarks/<comp>/samples/<problem_id>/
  2. Optionally downloads Kattis samples.zip when kattis_id is known
  3. Executes Python (and simple CPython via python3) under a timeout
  4. Returns AC/WA/TLE/RE style verdicts; WA burns 20 min of remaining contest clock
"""

from __future__ import annotations

import json
import re
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[2]
UA = "agent-olympiad-local-judge/1.0 (research; sample tests only)"


@dataclass
class TestCase:
    name: str
    stdin: str
    expected: str


@dataclass
class CaseResult:
    name: str
    verdict: str  # AC | WA | TLE | RE
    stdout: str = ""
    stderr: str = ""
    detail: str = ""


@dataclass
class JudgeResult:
    graded: bool
    method: str
    verdict: str  # AC | WA | TLE | RE | NO_TESTS
    score: float | None
    max_score: float | None
    cases: list[CaseResult] = field(default_factory=list)
    reason: str = ""
    wrong_submission: bool = False

    def to_grade_dict(self, *, submitted_by: str | None = None) -> dict[str, Any]:
        return {
            "graded": self.graded,
            "method": self.method,
            "verdict": self.verdict,
            "score": self.score,
            "max_score": self.max_score,
            "correct": self.verdict == "AC",
            "reason": self.reason,
            "cases": [asdict(c) for c in self.cases],
            "wrong_submission": self.wrong_submission,
            "submitted_by": submitted_by,
        }


def samples_dir(competition_id: str, problem_id: str, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    return root / "data" / "benchmarks" / competition_id / "samples" / problem_id


def load_sample_cases(directory: Path) -> list[TestCase]:
    if not directory.is_dir():
        return []
    cases: list[TestCase] = []
    inputs = sorted(directory.glob("*.in"))
    for inp in inputs:
        ans = inp.with_suffix(".ans")
        if not ans.exists():
            # Kattis sometimes uses .out
            ans = inp.with_suffix(".out")
        if not ans.exists():
            continue
        cases.append(
            TestCase(
                name=inp.stem,
                stdin=inp.read_text(encoding="utf-8", errors="replace"),
                expected=ans.read_text(encoding="utf-8", errors="replace"),
            )
        )
    # Also accept paired sample-N.in / sample-N.ans naming already covered by *.in
    return cases


def ensure_kattis_samples(
    kattis_id: str,
    dest: Path,
    *,
    force: bool = False,
) -> list[TestCase]:
    """Download open.kattis.com samples.zip into dest if missing."""
    existing = load_sample_cases(dest)
    if existing and not force:
        return existing
    dest.mkdir(parents=True, exist_ok=True)
    url = f"https://open.kattis.com/problems/{kattis_id}/file/statement/samples.zip"
    req = Request(url, headers={"User-Agent": UA})
    try:
        with urlopen(req, timeout=30) as resp:
            data = resp.read()
    except Exception as exc:
        raise RuntimeError(f"Failed to fetch Kattis samples for {kattis_id}: {exc}") from exc
    zip_path = dest / "samples.zip"
    zip_path.write_bytes(data)
    with zipfile.ZipFile(zip_path) as zf:
        zf.extractall(dest)
    return load_sample_cases(dest)


def _normalize_output(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _extract_python_code(submission: str) -> str:
    """Prefer fenced python block; else whole submission."""
    fence = re.search(r"```(?:python|py)?\n(.*?)```", submission, re.S | re.I)
    if fence:
        return fence.group(1).strip()
    return submission.strip()


def run_python_cases(
    code: str,
    cases: list[TestCase],
    *,
    timeout_sec: float = 5.0,
) -> list[CaseResult]:
    results: list[CaseResult] = []
    with tempfile.TemporaryDirectory(prefix="ao_judge_") as tmp:
        script = Path(tmp) / "main.py"
        script.write_text(code, encoding="utf-8")
        for case in cases:
            try:
                proc = subprocess.run(
                    ["python3", str(script)],
                    input=case.stdin,
                    capture_output=True,
                    text=True,
                    timeout=timeout_sec,
                    cwd=tmp,
                )
            except subprocess.TimeoutExpired:
                results.append(CaseResult(name=case.name, verdict="TLE", detail="timeout"))
                continue
            if proc.returncode != 0:
                results.append(
                    CaseResult(
                        name=case.name,
                        verdict="RE",
                        stdout=proc.stdout or "",
                        stderr=(proc.stderr or "")[:2000],
                        detail=f"exit {proc.returncode}",
                    )
                )
                continue
            got = _normalize_output(proc.stdout or "")
            exp = _normalize_output(case.expected)
            if got == exp:
                results.append(CaseResult(name=case.name, verdict="AC", stdout=got))
            else:
                results.append(
                    CaseResult(
                        name=case.name,
                        verdict="WA",
                        stdout=got,
                        detail=f"expected={exp[:200]!r} got={got[:200]!r}",
                    )
                )
    return results


def judge_programming_submission(
    problem: dict[str, Any],
    submission_text: str,
    *,
    competition_id: str,
    repo_root: Path | None = None,
    fetch_kattis: bool = True,
) -> JudgeResult:
    root = repo_root or REPO_ROOT
    problem_id = str(problem.get("problem_id") or "")
    dest = samples_dir(competition_id, problem_id, root)
    cases = load_sample_cases(dest)
    if not cases and fetch_kattis and problem.get("kattis_id"):
        try:
            cases = ensure_kattis_samples(str(problem["kattis_id"]), dest)
        except Exception as exc:
            return JudgeResult(
                graded=False,
                method="programming_sample_judge",
                verdict="NO_TESTS",
                score=None,
                max_score=None,
                reason=f"No local samples and Kattis fetch failed: {exc}",
            )
    if not cases:
        return JudgeResult(
            graded=False,
            method="programming_sample_judge",
            verdict="NO_TESTS",
            score=None,
            max_score=None,
            reason="No sample .in/.ans pairs found; full secret tests still deferred.",
        )

    code = _extract_python_code(submission_text)
    if len(code) < 5:
        return JudgeResult(
            graded=True,
            method="programming_sample_judge",
            verdict="RE",
            score=0.0,
            max_score=1.0,
            reason="Submission has no runnable Python code.",
            wrong_submission=True,
        )

    case_results = run_python_cases(code, cases)
    if not case_results:
        return JudgeResult(
            graded=False,
            method="programming_sample_judge",
            verdict="NO_TESTS",
            score=None,
            max_score=None,
            reason="Judge produced no case results.",
        )

    order = {"RE": 3, "TLE": 2, "WA": 1, "AC": 0}
    worst = max(case_results, key=lambda c: order.get(c.verdict, 0))
    all_ac = all(c.verdict == "AC" for c in case_results)
    verdict = "AC" if all_ac else worst.verdict
    return JudgeResult(
        graded=True,
        method="programming_sample_judge",
        verdict=verdict,
        score=1.0 if all_ac else 0.0,
        max_score=1.0,
        cases=case_results,
        reason=f"{sum(c.verdict == 'AC' for c in case_results)}/{len(case_results)} sample cases AC",
        wrong_submission=not all_ac,
    )


def icpc_rank_key(
    *,
    solved: int,
    penalty_minutes: int,
    last_accept_minute: int = 0,
) -> tuple:
    """ICPC ranking: more solved first, then lower penalty."""
    return (-solved, penalty_minutes, last_accept_minute)


def write_samples_manifest(competition_id: str, problem_id: str, cases: list[TestCase]) -> Path:
    dest = samples_dir(competition_id, problem_id)
    dest.mkdir(parents=True, exist_ok=True)
    manifest = {
        "competition_id": competition_id,
        "problem_id": problem_id,
        "n_cases": len(cases),
        "cases": [c.name for c in cases],
    }
    path = dest / "manifest.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return path
