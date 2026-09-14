"""Shared dataset metadata and judge-only scorecard projection.

These helpers do not infer licensing, evaluation readiness, or train/test splits.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path


def complete_metadata(row: dict, competition_id: str, root: Path) -> dict:
    row.setdefault("competition_id", competition_id)
    row.setdefault("eval_unit", "problem" if competition_id == "codeforces" else "session")
    row.setdefault("split", "unspecified")
    row.setdefault("license", dict(status="not_verified", spdx_id=None,
                                   redistribution_allowed=None,
                                   note="Upstream redistribution terms have not been verified."))
    for item in row.get("assets", []):
        target = root / item["path"]
        if target.is_file() and not item.get("sha256"):
            item["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    row.setdefault("provenance", dict(
        status="source_linked", source_url=row.get("source_url"),
        source_file=row.get("source_file"), solution_file=row.get("solution_file"),
        files=[{k: a[k] for k in ("path", "role", "sha256") if k in a}
               for a in row.get("assets", [])],
        verification_scope="Source locations and asset hashes; licensing and authorship are separate."))
    row.setdefault("asset_policy", "Only agent_visible assets may enter contestant context; judge_only assets are evaluator-only.")
    evaluation = row.setdefault("evaluation", {})
    evaluation.setdefault("scorecard_path", f"data/rubrics/task_scorecards/{competition_id}.json")
    evaluation.setdefault("scorecard_key", row["problem_id"])
    return row


def scorecard(row: dict, root: Path, *, read_json=None, hash_file=None) -> dict:
    read_json = read_json or (lambda p: json.loads((root / p).read_text(encoding="utf-8-sig")))
    hash_file = hash_file or (lambda p: hashlib.sha256((root / p).read_bytes()).hexdigest())
    e = row.get("evaluation", {})
    paths = e.get("rubric_paths") or ([e["rubric_path"]] if e.get("rubric_path") else [])
    rubrics = []
    for p in paths:
        data = read_json(p)
        criteria = data.get("criteria", [])
        numeric = bool(criteria) and all(isinstance(c, dict) and "max_score" in c for c in criteria)
        numeric = numeric and abs(sum(float(c["max_score"]) for c in criteria) - float(data.get("total_points", -1))) < 1e-6
        rubrics.append(dict(path=p, sha256=hash_file(p),
                            format="numeric_rubric" if numeric else "official_protocol_or_answer_map",
                            rubric_id=data.get("rubric_id"), total_points=data.get("total_points"),
                            criteria=deepcopy(criteria) if numeric else [],
                            not_observable_from_deck=data.get("not_observable_from_deck", [])))
    parts = row.get("gold_label", {}).get("parts", [])
    weighted = [dict(id=str(p["id"]), points=p.get("points", 1)) for p in parts if p.get("expected")]
    return dict(problem_id=row["problem_id"], year=row.get("year"),
                evaluation_status=e.get("status"), evaluator_id=e.get("evaluator_id"),
                rubrics=rubrics, answer_key_path=e.get("answer_key_path"),
                rubric_variant=e.get("rubric_variant"), official_rubric_map=e.get("official_rubric_map"),
                judge_assets=[deepcopy(a) for a in row.get("assets", []) if a.get("role") == "judge_only"],
                limitations=e.get("limitations"), rubric_reuse=e.get("rubric_reuse"),
                scoring_basis=e.get("score_basis", e.get("rubric_reuse", {}).get("scoring_basis", "Existing scoring basis retained.")),
                numeric_rubric_available=any(r["format"] == "numeric_rubric" for r in rubrics),
                gold_part_weights=weighted,
                gold_max_score=sum(float(p["points"]) for p in weighted) if weighted else None)


def update_track_index(index: dict, cid: str, rows: list[dict]) -> None:
    track = next((x for x in index.get("olympiads", []) if x["id"] == cid), None)
    if track is None:
        return
    track.update(problems_collected=len(rows), catalog_status="active" if rows else "empty",
                 eval_units=sorted({r["eval_unit"] for r in rows}),
                 evaluation_status_counts=dict(Counter(r.get("evaluation", {}).get("status", "unknown") for r in rows)))
    index["active_tracks"] = sum(t.get("problems_collected", 0) > 0 for t in index["olympiads"])
    index["total_records"] = sum(t.get("problems_collected", 0) for t in index["olympiads"])
