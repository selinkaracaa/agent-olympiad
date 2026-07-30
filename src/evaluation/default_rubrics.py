"""Default structured rubrics for open-ended contest families."""

from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUBRIC_DIR = REPO_ROOT / "data" / "rubrics"


DEFAULT_RUBRICS: dict[str, dict] = {
    "wsc_writing_28_v1": {
        "rubric_id": "wsc_writing_28_v1",
        "title": "WSC collaborative writing rubric",
        "total_points": 28,
        "criteria": [
            {
                "id": "focus_argument",
                "name": "Focus & argumentation",
                "max_score": 7,
                "observable": True,
                "description": "Clear thesis, coherent argument structure, and sustained focus on the prompt.",
            },
            {
                "id": "theme_evidence",
                "name": "Theme & evidence",
                "max_score": 7,
                "observable": True,
                "description": "Uses the assigned theme and supporting evidence effectively.",
            },
            {
                "id": "style_clarity",
                "name": "Style & clarity",
                "max_score": 7,
                "observable": True,
                "description": "Clear, readable collaborative prose with appropriate style.",
            },
            {
                "id": "originality",
                "name": "Originality & persuasiveness",
                "max_score": 7,
                "observable": True,
                "description": "Insightful, persuasive, and non-generic contribution.",
            },
        ],
        "not_observable_from_deck": ["live discussion dynamics", "oral presentation"],
    },
    "team_power_proof_40_v1": {
        "rubric_id": "team_power_proof_40_v1",
        "title": "Team power / proof-packet rubric",
        "total_points": 40,
        "criteria": [
            {
                "id": "correctness",
                "name": "Mathematical correctness",
                "max_score": 16,
                "observable": True,
                "description": "Results and proofs are mathematically correct against the official marking notes.",
            },
            {
                "id": "completeness",
                "name": "Coverage of required parts",
                "max_score": 12,
                "observable": True,
                "description": "All required sub-parts are attempted with substantive solutions.",
            },
            {
                "id": "reasoning",
                "name": "Clarity of reasoning",
                "max_score": 8,
                "observable": True,
                "description": "Arguments are structured, justified, and readable.",
            },
            {
                "id": "presentation",
                "name": "Written presentation",
                "max_score": 4,
                "observable": True,
                "description": "Notation, organization, and exposition are professional.",
            },
        ],
        "not_observable_from_deck": ["oral defense"],
    },
    "worked_answer_100_v1": {
        "rubric_id": "worked_answer_100_v1",
        "title": "Worked-answer / marking-scheme packet",
        "total_points": 100,
        "criteria": [
            {
                "id": "accuracy",
                "name": "Answer accuracy",
                "max_score": 50,
                "observable": True,
                "description": "Final answers and key intermediate claims match the official marking scheme.",
            },
            {
                "id": "method",
                "name": "Method & justification",
                "max_score": 30,
                "observable": True,
                "description": "Methods are valid and sufficiently justified for the awarded marks.",
            },
            {
                "id": "coverage",
                "name": "Part coverage",
                "max_score": 20,
                "observable": True,
                "description": "Required sub-questions are addressed.",
            },
        ],
        "not_observable_from_deck": [],
    },
    "moot_memorial_100_v1": {
        "rubric_id": "moot_memorial_100_v1",
        "title": "Moot court written memorial rubric",
        "total_points": 100,
        "criteria": [
            {
                "id": "legal_analysis",
                "name": "Legal analysis",
                "max_score": 35,
                "observable": True,
                "description": "Accurate, issue-spotting legal analysis grounded in international law.",
            },
            {
                "id": "argumentation",
                "name": "Argumentation",
                "max_score": 30,
                "observable": True,
                "description": "Persuasive Applicant/Respondent arguments with coherent structure.",
            },
            {
                "id": "authorities",
                "name": "Authorities & citation",
                "max_score": 20,
                "observable": True,
                "description": "Relevant authorities are cited and used appropriately.",
            },
            {
                "id": "writing",
                "name": "Written memorial quality",
                "max_score": 15,
                "observable": True,
                "description": "Clarity, organization, and professional memorial style.",
            },
        ],
        "not_observable_from_deck": [
            "oral advocacy",
            "rebuttal performance",
            "courtroom demeanor",
        ],
    },
    "practical_report_40_v1": {
        "rubric_id": "practical_report_40_v1",
        "title": "Team practical written-report rubric (instruments not observed)",
        "total_points": 40,
        "criteria": [
            {
                "id": "procedure",
                "name": "Procedure understanding",
                "max_score": 10,
                "observable": True,
                "description": "Describes a coherent experimental procedure and controls.",
            },
            {
                "id": "analysis",
                "name": "Data analysis & reasoning",
                "max_score": 15,
                "observable": True,
                "description": "Analyses, calculations, and scientific reasoning in the report.",
            },
            {
                "id": "conclusions",
                "name": "Conclusions & uncertainty",
                "max_score": 10,
                "observable": True,
                "description": "Conclusions follow from stated data; uncertainties discussed.",
            },
            {
                "id": "communication",
                "name": "Report communication",
                "max_score": 5,
                "observable": True,
                "description": "Clear tables/figures/text presentation in the written report.",
            },
        ],
        "not_observable_from_deck": [
            "physical instrument operation",
            "lab safety behavior",
            "true measured raw data fidelity",
        ],
    },
    "numerical_sheet_reference_40_v1": {
        "rubric_id": "numerical_sheet_reference_40_v1",
        "title": "Numerical team sheet graded against official solutions",
        "total_points": 40,
        "criteria": [
            {
                "id": "answers",
                "name": "Answer correctness",
                "max_score": 32,
                "observable": True,
                "description": "Final answers match official solutions (equivalent forms allowed).",
            },
            {
                "id": "completeness",
                "name": "Completeness",
                "max_score": 8,
                "observable": True,
                "description": "All required problems have attempted final answers.",
            },
        ],
        "not_observable_from_deck": [],
    },
}


def ensure_default_rubrics() -> dict[str, Path]:
    RUBRIC_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    for rubric_id, payload in DEFAULT_RUBRICS.items():
        path = RUBRIC_DIR / f"{rubric_id}.json"
        if not path.exists():
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        paths[rubric_id] = path
    # Keep existing business-case rubric if present.
    business = RUBRIC_DIR / "business_case_slides_50.json"
    if business.exists():
        paths["business_case_slides_50_v1"] = business
    return paths
