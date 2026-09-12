#!/usr/bin/env python3
"""Generate contest manifests and run OTC/vanilla contest-session batches.

Covers deterministic structured-gold competitions (short-answer / multipart
packets). Excludes CTF / NYU / programming contests by default.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "data" / "benchmarks"
MANIFEST_ROOT = REPO_ROOT / "data" / "contest_manifests" / "generated"
PYTHON = Path(r"e:\agent_olympiad\.venv\Scripts\python.exe")

sys.path.insert(0, str(REPO_ROOT / "src"))
from contest_config import BASELINE_NAMES, BASELINE_ALIASES, canonical_baseline
from contest_batch_summary import summarize
from contest_budget import resolve_contest_budget  # noqa: E402
from rules.loader import load_rule_card  # noqa: E402
from run_competition_batch import inspect_contest_run  # noqa: E402
from contest_run_identity import RunCompatibilityError, inspect_contest_output  # noqa: E402

# Deterministic structured gold; no CTF / NYU / code contests.
DEFAULT_COMPETITIONS = (
    "arml_local,"
    "arml_national_team,"
    "science_bowl,"
    "qanta,"
    "mystery_hunt,"
    "history_olympiad,"
    "purple_comet,"
    "hmmt_guts,"
    "wmtc"
)

TASK_FAMILIES = {
    "arml_local": "mathematics",
    "arml_national_team": "mathematics",
    "arml_national_power": "mathematics",
    "arml_power": "mathematics",
    "science_bowl": "short_answer",
    "qanta": "short_answer",
    "mystery_hunt": "puzzle",
    "history_olympiad": "short_answer",
    "purple_comet": "mathematics",
    "hmmt_guts": "mathematics",
    "wmtc": "mathematics",
}

COMPETITION_DESCRIPTIONS = {
    "arml_local": (
        "ARML local mathematics team rounds: solve a numbered set of contest "
        "problems and submit one shared answer sheet."
    ),
    "arml_national_team": (
        "ARML national team mathematics rounds: teammates divide a difficult "
        "numbered problem set and combine answers on one sheet."
    ),
    "arml_national_power": (
        "ARML National Power Round: a long collaborative proof / exploration "
        "packet. Produce a clear written solution with justifications; partial "
        "credit is rubric-based when an exact answer key is unavailable."
    ),
    "arml_power": (
        "ARML Power Contest (mail-in): collaborative multi-part proof packets. "
        "Write structured solutions with reasoning; exact short-answer keys may "
        "be unavailable and grading may be unsupported until a rubric judge runs."
    ),
    "science_bowl": (
        "Science Bowl toss-up and bonus questions across scientific subjects, "
        "answered directly with a short choice, term, or value."
    ),
    "qanta": (
        "Academic quiz-bowl questions: identify the requested person, place, "
        "work, event, or concept from progressively specific clues."
    ),
    "mystery_hunt": (
        "MIT Mystery Hunt-style puzzles: infer the puzzle mechanism and extract "
        "a final answer word or phrase."
    ),
    "history_olympiad": (
        "History Bowl/Olympiad packets containing many numbered history toss-up "
        "and bonus questions that require concise factual answers."
    ),
    "purple_comet": (
        "Purple Comet online team mathematics: solve a timed numbered set for "
        "the middle- or high-school division and submit short final answers."
    ),
    "hmmt_guts": (
        "HMMT Guts Round: a fast team mathematics contest with a long numbered "
        "packet (36 questions in the 2024 case); prioritize broad answer-sheet "
        "coverage and preserve every solved numbered answer."
    ),
    "wmtc": (
        "World Mathematics Team Championship team round: solve 14 linked or "
        "standalone numbered mathematics questions on one shared answer sheet."
    ),
}

# Packet contests: split into per-question tasks when prompts are numbered.
SPLIT_PARTS = {"arml_local", "arml_national_team"}

# Rubric / reference-only packets still get a single-task contest session.
RUBRIC_PACKET_COMPETITIONS = frozenset({"arml_national_power", "arml_power"})

# Benchmarks whose rows are individual questions/puzzles rather than full
# contests. Group them into the natural event represented by their metadata.
GROUPED_QUESTION_COMPETITIONS = frozenset(
    {"science_bowl", "qanta", "mystery_hunt"}
)

def budget_for(
    competition: str, team_size: int, system_variant: str = "otc"
) -> tuple[int, int]:
    """(max_turns, max_api_calls) for one competition.

    Turns come from the official clock (5 min/turn, cap 90, see
    contest_budget.py); API calls allow one call per agent per turn plus the
    single coach call. The rule-card ``otc`` baseline spends one private think
    call plus one action per seat per turn and one turn-0 Coach call.
    """
    max_turns = resolve_contest_budget(competition).max_turns
    if canonical_baseline(system_variant) == "otc":
        card = load_rule_card(competition)
        think_calls = 1
        if card is not None:
            turn_policy = (
                (card.simulation.get("open_table_coach") or {}).get("contestant_turn_policy")
                or {}
            )
            think_calls = int(turn_policy.get("private_think_calls_per_turn") or 1)
        return max_turns, max_turns * team_size * (1 + think_calls) + 1
    return max_turns, max_turns * team_size + 1


def team_size_for(competition: str, requested: int | None, system_variant: str) -> int:
    """``otc`` runs the card's default roster unless --team-size is inside its range."""
    if canonical_baseline(system_variant) != "otc":
        return requested or 3
    card = load_rule_card(competition)
    if card is None:
        raise SystemExit(f"otc needs data/rules/{competition}/collaboration.json")
    if requested is None:
        return card.team_size_default
    if not card.team_size_min <= requested <= card.team_size_max:
        raise SystemExit(
            f"--team-size {requested} is outside the {competition} card range "
            f"{card.team_size_min}-{card.team_size_max}"
        )
    return requested

# Known OCR/diagram repairs for ARML Local packets.
ARML_PROMPT_OVERRIDES: dict[str, dict[str, str]] = {
    "arml_local_2010": {
        "3": (
            "At a meeting of the Nuclear Powerplant Workers of America, every person "
            "has 3, 4, 5, 6, or 7 fingers on each hand. The probability of having k "
            "fingers on one hand is 2^(2-|5-k|)/10. The numbers of fingers on the left "
            "and right hands are independent. Compute the probability that a member "
            "has at least 10 fingers total."
        ),
        "10": (
            "In the multiplication puzzle, A, B, C, D, E, and F are distinct non-zero "
            "digits. The aligned equations shown in the original diagram are "
            "ABC × D = DEC and ABC × E = FEC, where juxtaposition denotes decimal "
            "digits. Compute the six-digit number ABCDEF."
        ),
    },
}


def _gradeable_question_ids(problem: dict) -> list[str]:
    ids: list[str] = []
    for part in (problem.get("gold_label") or {}).get("parts") or []:
        expected = part.get("expected")
        if (
            isinstance(expected, str)
            and expected.strip()
            and part.get("match_mode") != "reference_llm"
            and float(part.get("points") or 0) > 0
            and part.get("id") is not None
        ):
            ids.append(str(part["id"]))
    return ids


def _safe_session_id(value: object) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip()).strip("_").lower()


def _natural_session_id(competition: str, problem: dict) -> str:
    """Return the real contest/packet unit for a question-level benchmark row."""
    problem_id = str(problem["problem_id"])
    if competition == "science_bowl":
        parent = problem.get("parent_session_id")
        if parent:
            return _safe_session_id(parent)
        year = problem.get("year") or "unknown"
        packet = problem.get("packet") or problem.get("source_file") or problem_id
        return _safe_session_id(f"science_bowl_{year}_{packet}")
    if competition == "qanta":
        year = problem.get("year") or "unknown"
        tournament = problem.get("tournament") or "unknown_tournament"
        return _safe_session_id(f"qanta_{year}_{tournament}")
    if competition == "mystery_hunt":
        year = problem.get("year")
        return (
            _safe_session_id(f"mystery_hunt_{year}")
            if year is not None
            else problem_id
        )
    return problem_id


def _group_problems(competition: str, problems: list[dict]) -> list[tuple[str, list[dict]]]:
    """Group question rows into contest sessions while preserving source order."""
    if competition not in GROUPED_QUESTION_COMPETITIONS:
        return [(str(problem["problem_id"]), [problem]) for problem in problems]
    groups: dict[str, list[dict]] = defaultdict(list)
    for problem in problems:
        groups[_natural_session_id(competition, problem)].append(problem)
    return list(groups.items())


def write_manifests(competitions: list[str]) -> list[Path]:
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for competition in competitions:
        problems = json.loads(
            (BENCH_ROOT / competition / "benchmark.json").read_text(encoding="utf-8")
        )
        desired_paths: set[Path] = set()
        for session_id, session_problems in _group_problems(competition, problems):
            included: list[tuple[dict, list[str]]] = []
            for problem in session_problems:
                gradeable = _gradeable_question_ids(problem)
                rubric_only = (
                    competition in RUBRIC_PACKET_COMPETITIONS
                    and bool(str(problem.get("problem_description") or "").strip())
                )
                if gradeable or rubric_only:
                    included.append((problem, gradeable))
            if not included:
                continue
            problem_ids = [str(problem["problem_id"]) for problem, _ in included]
            split_parts = (
                competition in SPLIT_PARTS
                and len(included) == 1
                and bool(included[0][1])
            )
            payload: dict = {
                "session_id": session_id,
                "competition_id": competition,
                "problem_ids": problem_ids,
                "description": (
                    f"OTC contest-session manifest for {session_id} "
                    f"({len(problem_ids)} tasks)"
                ),
                "split_parts": split_parts,
                "task_family": TASK_FAMILIES.get(competition, "general"),
                "competition_description": COMPETITION_DESCRIPTIONS.get(
                    competition,
                    "Solve the provided contest task and submit its required deliverable.",
                ),
            }
            if split_parts:
                problem, gradeable = included[0]
                problem_id = str(problem["problem_id"])
                payload["question_ids"] = gradeable
                overrides = ARML_PROMPT_OVERRIDES.get(problem_id)
                if overrides:
                    payload["prompt_overrides"] = {
                        key: value
                        for key, value in overrides.items()
                        if key in gradeable
                    }
            path = MANIFEST_ROOT / f"{session_id}.json"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            paths.append(path)
            desired_paths.add(path)

        # Remove obsolete one-question manifests for only the competitions being
        # regenerated. Keeping them would make directory-level counts misleading.
        for path in MANIFEST_ROOT.glob("*.json"):
            if path in desired_paths:
                continue
            try:
                existing = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if existing.get("competition_id") == competition:
                path.unlink()
    return paths


def case_complete(out_dir: Path, expected_identity: dict) -> bool:
    return inspect_contest_output(out_dir, expected_identity) == "complete"


def run_one(
    manifest: Path,
    *,
    out_root: Path,
    team_size: int,
    max_turns: int,
    max_api_calls: int,
    system_variant: str,
) -> dict:
    problem_id = manifest.stem
    out_dir = out_root / problem_id
    cmd = [
        str(PYTHON),
        "-u",
        str(REPO_ROOT / "src" / "run_competition_batch.py"),
        "--live",
        "--provider",
        "perplexity",
        "--model",
        "openai/gpt-5.4-mini",
        "--contest-manifest",
        str(manifest),
        "--system-variant",
        system_variant,
        "--action-calling",
        "native",
        "--team-size",
        str(team_size),
        "--max-turns",
        str(max_turns),
        "--max-api-calls",
        str(max_api_calls),
        "--max-total-tokens",
        "220000",
        "--no-judge-task",
        "--no-judge-cce",
        "--output",
        str(out_dir),
    ]
    try:
        output_state, expected_identity = inspect_contest_run(cmd[3:])
    except (ValueError, SystemExit) as exc:
        return {
            "problem_id": problem_id, "status": "blocked",
            "reason": str(exc), "out_dir": str(out_dir),
        }
    if output_state == "complete":
        return {"problem_id": problem_id, "status": "skipped_complete",
                "out_dir": str(out_dir), "run_identity": expected_identity}
    if output_state == "resume":
        cmd.append("--resume")
    out_dir.mkdir(parents=True, exist_ok=True)
    # The baseline decides the review workflow; no override is passed.
    log_path = out_dir / "run.log"
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n==== RUN {problem_id} ====\n")
        log.flush()
        proc = subprocess.run(
            cmd,
            cwd=str(REPO_ROOT),
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
    reason = ""
    try:
        status = "ok" if proc.returncode == 0 and case_complete(out_dir, expected_identity) else "error"
    except RunCompatibilityError as exc:
        status, reason = "error", str(exc)
    return {
        "problem_id": problem_id,
        "status": status,
        "run_identity": expected_identity,
        "returncode": proc.returncode,
        "reason": reason,
        "out_dir": str(out_dir),
    }



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--competitions",
        default=DEFAULT_COMPETITIONS,
        help="Comma-separated competition ids",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "otc_gold_suite_v5",
    )
    parser.add_argument(
        "--system-variant",
        default="otc",
        choices=(*BASELINE_NAMES, *BASELINE_ALIASES),
    )
    parser.add_argument(
        "--team-size",
        type=int,
        default=None,
        help="Seats per team (default 3; for otc the rule card's default roster).",
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--skip-existing-roots",
        default=None,
        help="Retired option; reuse requires the same --output and matching run identity.",
    )
    args = parser.parse_args()
    if args.skip_existing_roots is not None:
        parser.error(
            "--skip-existing-roots is retired: cross-root skipping was not implemented. "
            "Use the same --output to resume identity-matched runs, or a fresh directory."
        )
    args.system_variant = canonical_baseline(args.system_variant)

    competitions = [item.strip() for item in args.competitions.split(",") if item.strip()]
    manifests = write_manifests(competitions)
    if args.limit is not None:
        manifests = manifests[: args.limit]
    args.output.mkdir(parents=True, exist_ok=True)
    index_path = args.output / "manifest_index.json"
    index_path.write_text(
        json.dumps([str(path.relative_to(REPO_ROOT)) for path in manifests], indent=2),
        encoding="utf-8",
    )
    print(
        f"Wrote {len(manifests)} manifests under {MANIFEST_ROOT} | "
        f"variant={args.system_variant}",
        flush=True,
    )

    results = []
    for index, manifest in enumerate(manifests, start=1):
        competition = json.loads(manifest.read_text(encoding="utf-8"))["competition_id"]
        team_size = team_size_for(competition, args.team_size, args.system_variant)
        max_turns, max_api = budget_for(competition, team_size, args.system_variant)
        print(
            f"[{index}/{len(manifests)}] {manifest.stem} "
            f"variant={args.system_variant} (team={team_size}, turns={max_turns}, api={max_api})",
            flush=True,
        )
        result = run_one(
            manifest,
            out_root=args.output,
            team_size=team_size,
            max_turns=max_turns,
            max_api_calls=max_api,
            system_variant=args.system_variant,
        )
        print(f"  -> {result['status']} {result.get('reason', '')}", flush=True)
        results.append(result)
        summarize(args.output, [path.stem for path in manifests], run_results=results)
        if result["status"] == "blocked":
            # Do not export incompatible old sessions as this batch's results.
            return 2

    summary = summarize(args.output, [path.stem for path in manifests], run_results=results)
    ok = sum(1 for row in results if row["status"] in {"ok", "skipped_complete"})
    print(f"DONE {ok}/{len(results)} complete | summary={summary}", flush=True)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
