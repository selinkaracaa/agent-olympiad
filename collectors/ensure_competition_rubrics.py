"""Create competition-specific rubrics for every benchmark missing one.

Benchmarks currently outnumber competition-prefixed rubric files. This clones
the shared template each contest already uses (or a family default) into
data/rubrics/<competition>_*.json and rewires evaluation.json rubric_path.
"""
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUBRICS = ROOT / "data" / "rubrics"
RULES = ROOT / "data" / "rules"
BENCH = ROOT / "data" / "benchmarks"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clone_criteria_rubric(
    *,
    template_name: str,
    rubric_id: str,
    dataset: str,
    title: str,
    out_name: str,
) -> Path:
    template = load_json(RUBRICS / template_name)
    payload = deepcopy(template)
    payload["rubric_id"] = rubric_id
    payload["dataset"] = dataset
    payload["title"] = title
    payload["derived_from"] = f"data/rubrics/{template_name}"
    out = RUBRICS / out_name
    write_json(out, payload)
    return out


def modeling_report(dataset: str, title: str, out_name: str) -> Path:
    payload = {
        "rubric_id": out_name.replace(".json", ""),
        "dataset": dataset,
        "title": title,
        "total_points": 100,
        "criteria": [
            {
                "id": "problem_framing",
                "name": "Problem framing",
                "max_score": 15,
                "observable": True,
                "description": "Clarifies the modeling question, scope, and success criteria.",
            },
            {
                "id": "model_design",
                "name": "Model design",
                "max_score": 25,
                "observable": True,
                "description": "Builds an appropriate model with justified assumptions and structure.",
            },
            {
                "id": "analysis",
                "name": "Analysis & results",
                "max_score": 25,
                "observable": True,
                "description": "Computations, sensitivity, and results are coherent and decision-relevant.",
            },
            {
                "id": "validation",
                "name": "Validation & limitations",
                "max_score": 15,
                "observable": True,
                "description": "Checks model quality and discusses limitations honestly.",
            },
            {
                "id": "communication",
                "name": "Report communication",
                "max_score": 20,
                "observable": True,
                "description": "Clear written report suitable for a judging panel.",
            },
        ],
        "not_observable_from_deck": [
            "live presentation",
            "99-hour process fidelity",
        ],
    }
    out = RUBRICS / out_name
    write_json(out, payload)
    return out


def research_report(dataset: str, title: str, out_name: str) -> Path:
    payload = {
        "rubric_id": out_name.replace(".json", ""),
        "dataset": dataset,
        "title": title,
        "total_points": 100,
        "criteria": [
            {
                "id": "physics_or_theory",
                "name": "Scientific / theoretical quality",
                "max_score": 35,
                "observable": True,
                "description": "Core theory, models, and claims are sound against the problem statement.",
            },
            {
                "id": "investigation",
                "name": "Investigation design",
                "max_score": 25,
                "observable": True,
                "description": "Experiments, analysis plan, or research protocol are appropriate and complete.",
            },
            {
                "id": "evidence",
                "name": "Evidence & results",
                "max_score": 20,
                "observable": True,
                "description": "Reported evidence supports the conclusions.",
            },
            {
                "id": "presentation",
                "name": "Report / fight materials",
                "max_score": 20,
                "observable": True,
                "description": "Written materials are clear enough for a jury or opponent team.",
            },
        ],
        "not_observable_from_deck": [
            "live oral fight",
            "physical experiment fidelity",
            "months-long preparation process",
        ],
    }
    out = RUBRICS / out_name
    write_json(out, payload)
    return out


def programming_protocol(dataset: str, title: str, out_name: str) -> Path:
    payload = {
        "rubric_id": out_name.replace(".json", ""),
        "dataset": dataset,
        "title": title,
        "rubric_type": "programming_judge_protocol",
        "scoring_direction": "higher_is_better",
        "evaluator_id": "programming_judge",
        "official_scoring_components": [
            {
                "id": "accepted_submissions",
                "name": "Accepted problems / tests",
                "basis": "Official or local judge accept on required tests.",
            },
            {
                "id": "penalty",
                "name": "Time / wrong-submission penalty",
                "basis": "Contest penalty rules when the judge and packet support them.",
            },
        ],
        "other_official_rules": [
            "Score from the programming judge, not from free-form text similarity.",
            "Unauthorized tool use or judge bypass is a compliance failure.",
        ],
        "applicability": {
            "scope": f"{dataset} programming tasks promoted in data/benchmarks/{dataset}/benchmark.json",
            "repository_status": "programming_judge when tests/sandbox are available; otherwise deferred",
        },
    }
    out = RUBRICS / out_name
    write_json(out, payload)
    return out


def envirothon_protocol() -> Path:
    payload = {
        "rubric_id": "envirothon_scoring_protocol_v1",
        "dataset": "envirothon",
        "title": "Envirothon scoring protocol placeholder",
        "rubric_type": "official_scoring_protocol",
        "scoring_direction": "higher_is_better",
        "official_scoring_components": [
            {
                "id": "station_scores",
                "name": "Station / test scores",
                "basis": "Official station or written-test scoring when packet materials are promoted.",
            }
        ],
        "applicability": {
            "scope": "Benchmark shell exists but currently has zero promoted tasks.",
            "repository_status": "deferred_until_benchmark_records_exist",
        },
        "coverage": {
            "promoted_benchmark_records": 0,
            "mapped_records": 0,
        },
    }
    out = RUBRICS / "envirothon_scoring_protocol_v1.json"
    write_json(out, payload)
    return out


def set_rubric_path(competition: str, rel_path: str) -> None:
    path = RULES / competition / "evaluation.json"
    if not path.exists():
        return
    data = load_json(path)
    scoring = data.setdefault("scoring", {})
    scoring["rubric_path"] = rel_path
    # Keep evaluator_id as-is; only ensure path is competition-owned.
    write_json(path, data)


def main() -> None:
    created: list[tuple[str, str]] = []

    mapping: list[tuple[str, Path]] = [
        (
            "arml_power",
            clone_criteria_rubric(
                template_name="team_power_proof_40_v1.json",
                rubric_id="arml_power_proof_40_v1",
                dataset="arml_power",
                title="ARML Power Contest proof-packet rubric",
                out_name="arml_power_proof_40_v1.json",
            ),
        ),
        (
            "arml_national_power",
            clone_criteria_rubric(
                template_name="team_power_proof_40_v1.json",
                rubric_id="arml_national_power_proof_40_v1",
                dataset="arml_national_power",
                title="ARML National Power proof-packet rubric",
                out_name="arml_national_power_proof_40_v1.json",
            ),
        ),
        (
            "ieo_business_case",
            clone_criteria_rubric(
                template_name="business_case_slides_50.json",
                rubric_id="ieo_business_case_slides_50_v1",
                dataset="ieo_business_case",
                title="IEO business-case slide-deck rubric",
                out_name="ieo_business_case_slides_50_v1.json",
            ),
        ),
        (
            "ijso_practical",
            clone_criteria_rubric(
                template_name="practical_report_40_v1.json",
                rubric_id="ijso_practical_report_40_v1",
                dataset="ijso_practical",
                title="IJSO team practical written-report rubric",
                out_name="ijso_practical_report_40_v1.json",
            ),
        ),
        (
            "jessup",
            clone_criteria_rubric(
                template_name="moot_memorial_100_v1.json",
                rubric_id="jessup_memorial_100_v1",
                dataset="jessup",
                title="Jessup moot memorial rubric",
                out_name="jessup_memorial_100_v1.json",
            ),
        ),
        (
            "vis_moot",
            clone_criteria_rubric(
                template_name="moot_memorial_100_v1.json",
                rubric_id="vis_moot_memorial_100_v1",
                dataset="vis_moot",
                title="Vis Moot memorial rubric",
                out_name="vis_moot_memorial_100_v1.json",
            ),
        ),
        (
            "ioaa_group",
            clone_criteria_rubric(
                template_name="worked_answer_100_v1.json",
                rubric_id="ioaa_group_worked_answer_100_v1",
                dataset="ioaa_group",
                title="IOAA group worked-answer / marking-scheme rubric",
                out_name="ioaa_group_worked_answer_100_v1.json",
            ),
        ),
        (
            "iol_team",
            clone_criteria_rubric(
                template_name="worked_answer_100_v1.json",
                rubric_id="iol_team_worked_answer_100_v1",
                dataset="iol_team",
                title="IOL team worked-answer / marking-scheme rubric",
                out_name="iol_team_worked_answer_100_v1.json",
            ),
        ),
        (
            "hmmt_team",
            clone_criteria_rubric(
                template_name="worked_answer_100_v1.json",
                rubric_id="hmmt_team_worked_answer_100_v1",
                dataset="hmmt_team",
                title="HMMT team round worked-answer rubric",
                out_name="hmmt_team_worked_answer_100_v1.json",
            ),
        ),
        ("mcm", modeling_report("mcm", "MCM modeling report rubric", "mcm_modeling_report_100_v1.json")),
        ("icm", modeling_report("icm", "ICM modeling report rubric", "icm_modeling_report_100_v1.json")),
        ("itym", research_report("itym", "ITYM research report rubric", "itym_research_report_100_v1.json")),
        ("iypt", research_report("iypt", "IYPT research / fight materials rubric", "iypt_research_report_100_v1.json")),
        (
            "icpc",
            programming_protocol("icpc", "ICPC programming judge protocol", "icpc_programming_judge_v1.json"),
        ),
        (
            "iiot",
            programming_protocol("iiot", "IIOT programming judge protocol", "iiot_programming_judge_v1.json"),
        ),
        (
            "codeforces",
            programming_protocol(
                "codeforces",
                "Codeforces programming judge protocol",
                "codeforces_programming_judge_v1.json",
            ),
        ),
        ("envirothon", envirothon_protocol()),
    ]

    for competition, path in mapping:
        rel = f"data/rubrics/{path.name}"
        set_rubric_path(competition, rel)
        created.append((competition, rel))
        print(f"created {rel}")

    # Summary coverage check
    comps = sorted(p.name for p in BENCH.iterdir() if (p / "benchmark.json").exists())
    missing = []
    for c in comps:
        if not any(p.name.startswith(c + "_") or p.stem == c for p in RUBRICS.glob("*.json")):
            missing.append(c)
    print(json.dumps({"benchmarks": len(comps), "still_missing_rubrics": missing, "created": created}, indent=2))


if __name__ == "__main__":
    main()
