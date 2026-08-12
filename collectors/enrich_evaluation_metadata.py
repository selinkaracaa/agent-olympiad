"""Enrich every benchmark problem with evaluation metadata and gold_label.parts.

Usage:
  python3 collectors/enrich_evaluation_metadata.py
  python3 collectors/enrich_evaluation_metadata.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO_ROOT / "data" / "benchmarks"

import sys

sys.path.insert(0, str(REPO_ROOT / "src"))
from evaluation.default_rubrics import ensure_default_rubrics

T_SECTION_RE = re.compile(r"T-(\d+)\.\s+")
# Only treat "N." as a problem header when N is 1-12 and followed by a capital/math start.
HEADER_RE = re.compile(
    r"(?:(?<=\n)|(?<=^)|(?<=Solutions\s)|(?<=Solutions))"
    r"(?:Problem\s+)?([1-9]|1[0-2])\.\s+(?=[A-Z(])"
)
SHORT_ANSWER_RE = re.compile(
    r"(?:"
    r"ordered pair is\s*(\([^)]{1,40}\))"
    r"|slope is\s*([−\-]?\d+)"
    r"|answer is\s+([^\n.]{1,60})"
    r"|final answer[:\s]+([^\n.]{1,60})"
    r")",
    re.IGNORECASE,
)


def _sequential_headers(matches: list[re.Match[str]]) -> list[re.Match[str]]:
    """Keep a clean 1..K prefix; drop prose false positives."""
    filtered: list[re.Match[str]] = []
    expected = 1
    for match in matches:
        qid = int(match.group(1))
        if qid == expected:
            filtered.append(match)
            expected += 1
        elif not filtered and qid == 1:
            filtered.append(match)
            expected = 2
    return filtered if len(filtered) >= 2 else []


def split_numbered_sections(text: str) -> list[tuple[str, str]]:
    if not text or not text.strip():
        return []
    t_matches = _sequential_headers(list(T_SECTION_RE.finditer(text)))
    matches = t_matches or _sequential_headers(list(HEADER_RE.finditer(text)))
    if not matches:
        return []
    sections: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if body:
            sections.append((match.group(1), body))
    # Reject pathological splits (too many tiny chunks).
    if len(sections) > 12:
        return []
    return sections


def guess_short_answer(section: str) -> str | None:
    candidates: list[str] = []
    for match in SHORT_ANSWER_RE.finditer(section):
        value = next((g for g in match.groups() if g), None)
        if value:
            candidates.append(value.strip(" .;,"))
    if not candidates:
        return None
    candidates.sort(key=len)
    best = candidates[0]
    return None if len(best) > 80 else best


def build_parts_from_solution(
    expected_answer: str | None,
    total_points: float | None,
    default_count: int | None = None,
) -> list[dict]:
    text = str(expected_answer or "").strip()
    sections = split_numbered_sections(text)
    points = float(total_points or (len(sections) if sections else default_count or 1))

    if sections and (default_count is None or abs(len(sections) - default_count) <= 2):
        each = points / len(sections)
        parts: list[dict] = []
        for qid, body in sections:
            short = guess_short_answer(body)
            parts.append(
                {
                    "id": qid,
                    "expected": short or "",
                    "points": each,
                    "reference": body[:4000],
                    "match_mode": "normalized" if short else "reference_llm",
                    "aliases": [],
                }
            )
        return parts

    # Conservative fallback: one packet reference, or empty shells for known counts.
    if default_count:
        each = points / default_count
        return [
            {
                "id": str(i),
                "expected": "",
                "points": each,
                "reference": text[:8000] if i == 1 else "",
                "match_mode": "reference_llm",
                "aliases": [],
            }
            for i in range(1, default_count + 1)
        ]
    if not text:
        return []
    return [
        {
            "id": "all",
            "expected": "",
            "points": points,
            "reference": text[:8000],
            "match_mode": "reference_llm",
            "aliases": [],
        }
    ]


def plan_for_item(item: dict, rubric_paths: dict[str, Path]) -> dict:
    task_type = item.get("task_type") or "unknown"
    competition_id = item.get("competition_id") or ""
    gold = item.get("gold_label") if isinstance(item.get("gold_label"), dict) else {}
    total_points = item.get("total_points")
    expected = gold.get("expected_answer")

    def rel(path: Path) -> str:
        return str(path.relative_to(REPO_ROOT))

    if task_type == "algorithmic_programming":
        return {
            "evaluation": {
                "evaluator_id": "programming_judge",
                "status": "deferred",
                "reason": "Needs official tests and isolated sandbox.",
            },
            "parts": [],
        }

    if task_type == "business_case":
        source = item.get("source_file")
        assets = item.get("assets")
        if source and not assets:
            item["assets"] = [
                {
                    "path": source,
                    "mime_type": "application/pdf",
                    "role": "agent_visible",
                }
            ]
        return {
            "evaluation": {
                "evaluator_id": "slide_deck_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["business_case_slides_50_v1"]),
                "media": ["images", "pdf"],
                "deliverable": "slide_deck",
            },
            "parts": [],
        }

    if task_type == "modeling_report":
        source = item.get("source_file")
        if source and not item.get("assets"):
            item["assets"] = [
                {"path": source, "mime_type": "application/pdf", "role": "agent_visible"}
            ]
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["worked_answer_100_v1"]),
                "deliverable": "modeling_report",
            },
            "parts": [],
        }

    if task_type == "open_research":
        source = item.get("source_file")
        if source and not item.get("assets"):
            item["assets"] = [
                {"path": source, "mime_type": "application/pdf", "role": "agent_visible"}
            ]
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["worked_answer_100_v1"]),
                "deliverable": "research_presentation",
                "limitations": ["oral fight / live debate not scored"],
            },
            "parts": [],
        }

    if task_type == "collaborative_writing_discussion":
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["wsc_writing_28_v1"]),
                "deliverable": "written_essay",
            },
            "parts": [],
        }

    if task_type == "moot_court":
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["moot_memorial_100_v1"]),
                "deliverable": "written_memorial",
                "limitations": ["oral advocacy not scored"],
            },
            "parts": [],
        }

    if task_type == "team_practical":
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready_with_limitations",
                "rubric_path": rel(rubric_paths["practical_report_40_v1"]),
                "deliverable": "written_report",
                "limitations": [
                    "physical instrument observations unavailable",
                    "report-only proxy for practical mark",
                ],
            },
            "parts": build_parts_from_solution(expected, total_points or 40),
        }

    if task_type == "team_power":
        parts = build_parts_from_solution(expected, total_points or 40)
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["team_power_proof_40_v1"]),
                "deliverable": "proof_packet",
                "fallback_evaluator_id": "gold_answer_v1",
            },
            "parts": parts,
        }

    if task_type == "team_contest":
        # ARML-style numerical sheets vs linguistics/astronomy worked packets.
        if competition_id.startswith("arml_") or "arml" in competition_id:
            default_count = None
            if total_points in (40, 50):
                # Local 10x4; National team often 10x5.
                default_count = 10 if float(total_points) in (40, 50) else None
            parts = build_parts_from_solution(expected, total_points, default_count)
            short_count = sum(1 for part in parts if part.get("expected"))
            # Prefer gold only when we recovered a reasonable short-answer set.
            use_gold = short_count >= max(3, len(parts) // 3) and 5 <= len(parts) <= 12
            return {
                "evaluation": {
                    "evaluator_id": "gold_answer_v1" if use_gold else "rubric_llm_v1",
                    "status": "ready",
                    "rubric_path": rel(rubric_paths["numerical_sheet_reference_40_v1"]),
                    "fallback_evaluator_id": "rubric_llm_v1",
                    "deliverable": "answer_sheet",
                },
                "parts": parts,
            }

        parts = build_parts_from_solution(expected, total_points or 100)
        return {
            "evaluation": {
                "evaluator_id": "rubric_llm_v1",
                "status": "ready",
                "rubric_path": rel(rubric_paths["worked_answer_100_v1"]),
                "deliverable": "worked_answers",
                "fallback_evaluator_id": "gold_answer_v1",
            },
            "parts": parts,
        }

    return {
        "evaluation": {
            "evaluator_id": "rubric_llm_v1",
            "status": "ready",
            "rubric_path": rel(rubric_paths["worked_answer_100_v1"]),
            "deliverable": "document",
        },
        "parts": build_parts_from_solution(expected, total_points),
    }


def enrich_file(path: Path, rubric_paths: dict[str, Path], dry_run: bool) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("problems")
    if not isinstance(items, list):
        raise ValueError(f"Unsupported benchmark shape: {path}")

    counts = {"ready": 0, "deferred": 0, "parts": 0}
    for item in items:
        if not isinstance(item, dict):
            continue
        if not item.get("competition_id"):
            item["competition_id"] = path.parent.name
        plan = plan_for_item(item, rubric_paths)
        item["evaluation"] = plan["evaluation"]
        gold = item.get("gold_label")
        if not isinstance(gold, dict):
            gold = {}
            item["gold_label"] = gold
        if plan["parts"]:
            gold["parts"] = plan["parts"]
            counts["parts"] += 1
        status = str(plan["evaluation"].get("status", ""))
        if status.startswith("ready"):
            counts["ready"] += 1
        elif status == "deferred":
            counts["deferred"] += 1

    if not dry_run:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"file": str(path.relative_to(REPO_ROOT)), **counts, "n": len(items)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    rubric_paths = ensure_default_rubrics()
    summaries = []
    for path in sorted(BENCHMARK_ROOT.glob("*/benchmark.json")):
        summaries.append(enrich_file(path, rubric_paths, dry_run=args.dry_run))
    total_n = sum(s["n"] for s in summaries)
    print(json.dumps({"dry_run": args.dry_run, "problems": total_n, "files": summaries}, indent=2))


if __name__ == "__main__":
    main()
