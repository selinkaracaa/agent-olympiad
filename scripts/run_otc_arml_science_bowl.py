#!/usr/bin/env python3
"""Generate contest manifests and run OTC contest-session batch for ARML + Science Bowl."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "data" / "benchmarks"
MANIFEST_ROOT = REPO_ROOT / "data" / "contest_manifests" / "generated"

sys.path.insert(0, str(REPO_ROOT / "src"))
from contest_config import BASELINE_NAMES, BASELINE_ALIASES, canonical_baseline
from contest_batch_summary import summarize
from contest_budget import resolve_contest_budget  # noqa: E402
from run_otc_gold_suite import budget_for, team_size_for, run_one  # noqa: E402

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


def write_manifests(competitions: list[str]) -> list[Path]:
    MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for competition in competitions:
        problems = json.loads(
            (BENCH_ROOT / competition / "benchmark.json").read_text(encoding="utf-8")
        )
        for problem in problems:
            problem_id = str(problem["problem_id"])
            gradeable = _gradeable_question_ids(problem)
            if not gradeable:
                continue
            payload: dict = {
                "session_id": problem_id,
                "competition_id": competition,
                "problem_ids": [problem_id],
                "description": f"OTC contest-session manifest for {problem_id}",
            }
            if competition == "arml_local":
                payload["split_parts"] = True
                payload["question_ids"] = gradeable
                overrides = ARML_PROMPT_OVERRIDES.get(problem_id)
                if overrides:
                    payload["prompt_overrides"] = {
                        key: value
                        for key, value in overrides.items()
                        if key in gradeable
                    }
            else:
                # Single-part short-answer contests stay one task.
                payload["split_parts"] = False
            path = MANIFEST_ROOT / f"{problem_id}.json"
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            paths.append(path)
    return paths



def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--competitions",
        default="arml_local,science_bowl",
        help="Comma-separated competition ids",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "results" / "otc_arml_science_bowl_v5",
    )
    parser.add_argument(
        "--system-variant",
        default="otc",
        choices=(*BASELINE_NAMES, *BASELINE_ALIASES),
    )
    parser.add_argument("--team-size", type=int, default=None)
    # Default None = official clock / 5 min per turn (cap 90), API calls =
    # turns * team_size + 1 coach call. See src/contest_budget.py.
    parser.add_argument("--arml-max-turns", type=int, default=None)
    parser.add_argument("--arml-max-api-calls", type=int, default=None)
    parser.add_argument("--sb-max-turns", type=int, default=None)
    parser.add_argument("--sb-max-api-calls", type=int, default=None)
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
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
        if competition == "arml_local":
            turns_override, api_override = args.arml_max_turns, args.arml_max_api_calls
        else:
            turns_override, api_override = args.sb_max_turns, args.sb_max_api_calls
        max_turns = resolve_contest_budget(competition, max_turns=turns_override).max_turns
        team_size = team_size_for(competition, args.team_size, args.system_variant)
        default_turns, default_api = budget_for(competition, team_size, args.system_variant)
        coach_calls = 2 if args.system_variant == "otc" else 1
        calls_per_turn = (default_api - coach_calls) // default_turns
        max_api = api_override if api_override is not None else max_turns * calls_per_turn + coach_calls
        print(
            f"[{index}/{len(manifests)}] {manifest.stem} "
            f"variant={args.system_variant} (turns={max_turns}, api={max_api})",
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
            return 2

    summary = summarize(args.output, [path.stem for path in manifests], run_results=results)
    ok = sum(1 for row in results if row["status"] in {"ok", "skipped_complete"})
    print(f"DONE {ok}/{len(results)} complete | summary={summary}", flush=True)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
