#!/usr/bin/env python3
"""Migrate bundled rule cards to public input / method / hidden eval ownership."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES_ROOT = REPO_ROOT / "data" / "rules"

SIMULATION_EXECUTION_KEYS = {
    "max_turns",
    "scheduler",
    "turn_budget_basis",
    "exclusive_workstation_lease",
    "run_judging_latency_turns",
    "run_judging_latency_basis",
    "pending_run_policy",
    "eligibility_and_logistics_state",
    "contest_clock_and_scoreboard",
    "repeat_verdict_history",
    "selector_enforcement",
    "live_opponent_and_judges",
    "live_opponent_moderator_and_judges",
    "live_opponent_buzzer_moderator_and_clock",
    "buzzer_opponents_and_moderator",
    "physical_observation_adapter",
    "physical_performance_environment",
    "outside_assistance_provenance",
    "physical_final",
    "full_hunt_unlock_state",
    "hint_and_interaction_state",
    "runaround_and_coin_state",
    "robot_environment",
    "inspection_quarantine_and_field_state",
}

PUBLIC_SUBMISSION_KEYS = {
    "shared",
    "mime_types",
    "task_types",
    "official_deliverable",
    "official_mime_types",
    "official_languages",
    "io_model",
}

ICPC_SIMULATION_CONSTRAINTS = {
    "After a run is submitted, treat it as pending in the contest control system: "
    "the team must wait one simulation turn for the verdict and must not regard "
    "that pending run as Accepted or Rejected until the wait completes.",
    "During the one-turn pending wait, teammates may discuss other problems, plan, "
    "review, or do off-workstation work; they must not assume the pending run's "
    "result, and they must not submit another run for the same pending problem until "
    "the verdict arrives.",
}

GENERATED_PRIVATE_RULES_TEXT_MARKERS = (
    "Performance uses ",
    "repository evaluator status is ",
)


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if not path.is_file() or path.read_text(encoding="utf-8") != rendered:
        path.write_text(rendered, encoding="utf-8")


def _clean_generated_rules_text(text: str) -> str:
    sentences = [part.strip() for part in text.split(". ") if part.strip()]
    kept = [
        sentence
        for sentence in sentences
        if not any(marker.lower() in sentence.lower() for marker in GENERATED_PRIVATE_RULES_TEXT_MARKERS)
    ]
    if not kept:
        return text
    rendered = ". ".join(kept)
    if text.rstrip().endswith(".") and not rendered.endswith("."):
        rendered += "."
    return rendered


def migrate_bundle(directory: Path) -> None:
    competition_path = directory / "competition.json"
    collaboration_path = directory / "collaboration.json"
    evaluation_path = directory / "evaluation.json"
    competition = _load(competition_path)
    collaboration = _load(collaboration_path)
    evaluation = _load(evaluation_path)

    execution = dict(competition.get("execution") or {})
    simulation = dict(collaboration.get("simulation") or {})
    for key in list(execution):
        if key == "draft":
            execution.pop(key)
        elif key in SIMULATION_EXECUTION_KEYS:
            simulation[key] = execution.pop(key)
    competition["execution"] = execution

    submission = dict(evaluation.get("submission") or {})
    deliverable = dict(competition.get("deliverable") or {})
    answer_format = evaluation.pop("answer_format", None)
    if answer_format:
        deliverable["answer_format"] = answer_format
    for key in list(submission):
        if key in PUBLIC_SUBMISSION_KEYS:
            deliverable[key] = submission.pop(key)
    if "pending_latency_turns" in submission:
        simulation.setdefault(
            "run_judging_latency_turns",
            submission.pop("pending_latency_turns"),
        )
    competition["deliverable"] = deliverable
    collaboration["simulation"] = simulation
    evaluation["submission"] = submission

    for role in collaboration.get("agent_roles") or []:
        if isinstance(role, dict):
            role["information_access"] = [
                category
                for category in role.get("information_access", ["contest_rules"])
                if category == "contest_rules"
            ] or ["contest_rules"]

    if directory.name == "icpc":
        constraints = list(competition.get("human_constraints") or [])
        moved = [line for line in constraints if line in ICPC_SIMULATION_CONSTRAINTS]
        competition["human_constraints"] = [
            line for line in constraints if line not in ICPC_SIMULATION_CONSTRAINTS
        ]
        agent_constraints = list(collaboration.get("agent_constraints") or [])
        for line in moved:
            if line not in agent_constraints:
                agent_constraints.append(line)
        collaboration["agent_constraints"] = agent_constraints
        simulation["exclusive_workstation_lease"] = "enforced"
        policy = dict(collaboration.get("information_policy") or {})
        extra_shared = [
            item
            for item in policy.get("shared") or []
            if item not in {"problem", "contest_rules", "team_discussion", "scratchpad"}
        ]
        policy["shared"] = [
            "problem",
            "contest_rules",
            "team_discussion",
            "scratchpad",
        ]
        if extra_shared:
            simulation["shared_team_state"] = extra_shared
        collaboration["information_policy"] = policy
        rules_text = str(competition.get("rules_text") or "")
        rules_text = rules_text.replace(
            "After each submit, wait one simulation turn for the verdict and use that turn on other work. ",
            "After each submit, treat the run as pending until the contest control system returns a verdict. ",
        )
        competition["rules_text"] = rules_text

    for section, lines in (collaboration.get("rule_sections") or {}).items():
        collaboration["rule_sections"][section] = [
            str(line).replace("execution.max_turns", "simulation.max_turns")
            for line in lines
        ]
    policy = collaboration.get("information_policy") or {}
    requirement = str(policy.get("coordination_requirement") or "")
    if "evaluation guidance" in requirement:
        policy["coordination_requirement"] = requirement.replace(
            "public rules and evaluation guidance",
            "public contest rules",
        ).replace(
            "complete public rules and evaluation guidance",
            "complete public contest rules",
        )
        collaboration["information_policy"] = policy

    competition["rules_text"] = _clean_generated_rules_text(
        str(competition.get("rules_text") or "")
    )

    _write(competition_path, competition)
    _write(collaboration_path, collaboration)
    _write(evaluation_path, evaluation)


def main() -> None:
    bundles = [
        directory
        for directory in sorted(RULES_ROOT.iterdir())
        if directory.is_dir()
        and (directory / "competition.json").is_file()
        and (directory / "collaboration.json").is_file()
        and (directory / "evaluation.json").is_file()
    ]
    for directory in bundles:
        migrate_bundle(directory)
    print(f"migrated {len(bundles)} rule-card bundles")


if __name__ == "__main__":
    main()
