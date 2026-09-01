"""Generate *_short_answers.json from official answer-key rubrics / benchmark gold.

Usage:
  python collectors/sync_short_answers_from_answer_keys.py
  python collectors/apply_curated_short_answers.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / "data" / "rubrics"
BENCH = ROOT / "data" / "benchmarks"


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)} problems={sum(1 for k in data if not str(k).startswith('_'))}")


def from_answer_key(comp: str, key_path: Path, *, single_part: bool) -> None:
    rub = json.loads(key_path.read_text(encoding="utf-8"))
    answers = rub.get("answers") or {}
    out: dict = {
        "_comment": (
            f"Short-answer mapping aligned from {key_path.relative_to(ROOT)}. "
            "Applied into benchmarks via collectors/apply_curated_short_answers.py."
        ),
        "_dataset": comp,
        "_kind": "short_answer_mapping",
        "_source_rubric": str(key_path.relative_to(ROOT)),
    }
    for pid, spec in answers.items():
        if not isinstance(spec, dict):
            continue
        if single_part:
            if "expected" not in spec:
                continue
            entry = {"expected": str(spec["expected"])}
            if spec.get("aliases"):
                entry["aliases"] = list(spec["aliases"])
            if spec.get("official_guidance"):
                entry["official_guidance"] = spec["official_guidance"]
            if spec.get("official_choice"):
                entry["official_choice"] = spec["official_choice"]
            out[pid] = {"1": entry}
        else:
            # multipart nested map (history olympiad Q1..)
            parts = {}
            for qid, qspec in spec.items():
                if str(qid).startswith("_") or not isinstance(qspec, dict):
                    continue
                if "expected" not in qspec:
                    continue
                entry = {"expected": str(qspec["expected"])}
                if qspec.get("aliases"):
                    entry["aliases"] = list(qspec["aliases"])
                if qspec.get("official_guidance"):
                    entry["official_guidance"] = qspec["official_guidance"]
                parts[str(qid)] = entry
            if parts:
                out[pid] = parts
    write_json(RUBRICS / f"{comp}_short_answers.json", out)


def from_cfa() -> None:
    probs = json.loads((BENCH / "cfa_research_challenge" / "benchmark.json").read_text(encoding="utf-8"))
    out: dict = {
        "_comment": "CFA Research Challenge champion recommendation labels from gold_label.expected_answer.",
        "_dataset": "cfa_research_challenge",
        "_kind": "short_answer_mapping",
    }
    for d in probs:
        g = d.get("gold_label") if isinstance(d.get("gold_label"), dict) else {}
        ea = g.get("expected_answer")
        if isinstance(ea, str) and ea.strip():
            out[d["problem_id"]] = {"1": {"expected": ea.strip()}}
    write_json(RUBRICS / "cfa_research_challenge_short_answers.json", out)


def main() -> None:
    from_answer_key("science_bowl", RUBRICS / "science_bowl_official_answer_key_v1.json", single_part=True)
    from_answer_key("qanta", RUBRICS / "qanta_upstream_answer_key_v1.json", single_part=True)
    from_answer_key("mystery_hunt", RUBRICS / "mystery_hunt_official_answer_key_v1.json", single_part=True)
    from_answer_key("nyu_ctf_bench", RUBRICS / "nyu_ctf_bench_upstream_answer_key_v1.json", single_part=True)
    from_answer_key("history_olympiad", RUBRICS / "history_olympiad_official_answer_key_v1.json", single_part=False)
    from_cfa()


if __name__ == "__main__":
    main()
