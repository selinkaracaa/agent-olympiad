"""Canonical task_specific action definitions; no runtime dependencies."""
from __future__ import annotations

from functools import partial
from .contracts import ArgumentSpec, make_action
from types import MappingProxyType
from typing import Mapping

_action = partial(make_action, module="task_specific")

SPECS = (
    _action(
        "submit_code",
        "Submit source code to the programming evaluator.",
        (
            ArgumentSpec("code", description="Complete source code."),
            ArgumentSpec(
                "language", description="Submission language.", required=False
            ),
        ),
        pack="programming",
        tool_calls=1,
        submission_attempts=1,
        evaluator=True,
        evaluator_name="programming_judge",
        submission=True,
    ),
    _action(
        "read_lab_equipment",
        "Read declared laboratory equipment data.",
        (
            ArgumentSpec(
                "resource",
                description="Equipment or reading identifier.",
                required=False,
            ),
        ),
        visibility="private",
        pack="resources",
        tool_calls=1,
        is_tool=True,
    ),
    _action(
        "read_star_chart",
        "Read a declared star-chart resource.",
        (
            ArgumentSpec(
                "resource",
                description="Chart or observation identifier.",
                required=False,
            ),
        ),
        visibility="private",
        pack="resources",
        tool_calls=1,
        is_tool=True,
    ),
)


_PROGRAMMING_COMPETITIONS = frozenset({"icpc", "iiot", "codeforces"})
_MATH_COMPETITIONS = frozenset(
    {
        "arml_local",
        "arml_national_team",
        "purple_comet",
        "hmmt_guts",
        "hmmt_team",
        "wmtc",
        "fyziklani",
        "ijso_practical",
        "ioaa_group",
        "iypt",
    }
)
_RESEARCH_COMPETITIONS = frozenset(
    {"fyziklani", "mcm", "icm", "ieo_business_case", "jessup", "iypt"}
)
_RESOURCE_ACTIONS = frozenset(spec.name for spec in SPECS if spec.pack == "resources")

# Runtime adaptation is competition-owned, independent of the experiment setting.
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from contest_manifest import ContestManifest
    from rules.models import RuleCard
    from .contracts import ActionSpec

REPO_ROOT = Path(__file__).resolve().parents[2]


def is_answer_sheet_contest(manifest: ContestManifest) -> bool:
    if manifest.metadata.get("artifact_contract"):
        return True  # One reviewed, frozen deliverable; no answer rewrite on submit.
    return len(manifest.tasks) > 1 and all(
        not task.programming for task in manifest.tasks
    ) and (
        manifest.competition_id.startswith("arml")
        or all(task.task_type == "team_contest" for task in manifest.tasks)
    )


@dataclass(frozen=True)
class CompetitionInterface:
    competition_id: str
    delivery: str
    actions: frozenset[ActionSpec]
    issues: tuple[str, ...] = ()

    def report(self) -> dict[str, Any]:
        return {
            "competition_id": self.competition_id,
            "delivery": self.delivery,
            "actions": sorted(spec.name for spec in self.actions),
            "tools": sorted(spec.name for spec in self.actions if spec.is_tool),
            "limitations": list(self.issues),
        }


def _has_resource(benchmark: dict[str, Any], action: str) -> bool:
    role = {"read_lab_equipment": "lab", "read_star_chart": "star"}[action]
    fixtures = benchmark.get("tool_fixtures") or {}
    if any(role in str(key).lower() for key in fixtures):
        return True
    for asset in benchmark.get("assets") or []:
        if not isinstance(asset, dict):
            continue
        path = Path(str(asset.get("path") or ""))
        label = f"{asset.get('role', '')} {path}".lower()
        if not path.is_absolute():
            path = REPO_ROOT / path
        if role in label and path.is_file():
            return True
    return False


def resolve_contest_interface(
    manifest: ContestManifest, *, rule_card: RuleCard | None = None,
) -> CompetitionInterface:
    """Bind implemented actions to a competition's rules, data and deliverable.

    Unsupported card verbs and missing physical fixtures are reported, never
    synthesized as no-op tools. The same competition interface serves all settings.
    """
    from tool_registry import (ACTION_REGISTRY, TOOL_ACTION_NAMES,
                               competition_permissions, resolve_actions_with_diagnostics, _string_set)
    from rules.loader import load_rule_card
    from contest_rules import get_contest_rules

    card = rule_card or load_rule_card(manifest.competition_id)
    if card is not None and card.competition_id != manifest.competition_id:
        raise ValueError("Competition interface received a different competition's card")
    issues: set[str] = set()
    specs: set[ActionSpec] = set()
    permitted = competition_permissions(manifest.competition_id, rule_card=card,
        task_type="programming" if any(task.programming for task in manifest.tasks) else "")
    if permitted is not None:
        unknown = permitted - set(ACTION_REGISTRY)
        issues.update(f"unimplemented_card_action:{name}" for name in unknown)
        # Source submission is a judged competition action, not workstation access.
        if any(task.programming for task in manifest.tasks) and "execute_code" in permitted:
            permitted.add("submit_code")
    for task in manifest.tasks:
        benchmark = task.benchmark
        declared = _string_set(benchmark.get("available_capabilities"))
        if permitted is not None:
            declared.update(permitted & TOOL_ACTION_NAMES)
        for name in _RESOURCE_ACTIONS:
            if _has_resource(benchmark, name):
                declared.add(name)
            else:
                if name in declared or (permitted is not None and name in permitted):
                    issues.add(f"missing_runtime_resource:{task.task_id}:{name}")
                declared.discard(name)
        resolution = resolve_actions_with_diagnostics(
            competition=manifest.competition_id, task_type=task.task_type,
            benchmark_requirements=benchmark.get("tool_requirements") or {},
            declared_capabilities=declared,
            registered_handlers=set(ACTION_REGISTRY), runtime="session",
            permitted_actions=permitted,
        )
        issues.update(f"unknown_capability:{name}" for name in resolution.unknown_capabilities)
        for spec in resolution.actions:
            if (spec.is_tool or spec.name == "submit_code") and permitted is not None and spec.name not in permitted:
                continue
            specs.add(spec)
    delivery = "per_task_answer"
    if all(task.programming for task in manifest.tasks) and manifest.tasks:
        delivery = "programming_judge"
    if is_answer_sheet_contest(manifest):
        delivery = "answer_sheet"
        submit = ACTION_REGISTRY["submit"]
        specs.discard(submit)
        specs.discard(ACTION_REGISTRY["request_review"])
        specs.add(replace(submit, description=(
            "Submit the complete current answer sheet once and end the contest."
        ), arguments=()))
    if manifest.metadata.get("artifact_contract"):
        delivery = "artifact"
        # Replace the ordinary preview tool, rather than exposing two native
        # functions with the same name and different delivery visibility.
        specs = {spec for spec in specs if spec.name != "render_pdf"}
        specs.add(replace(ACTION_REGISTRY["render_pdf"], visibility="team"))
    rules = get_contest_rules(manifest.competition_id)
    if rules is not None:
        issues.update(f"rule_model_gap:{field.name}:{field.status}" for field in rules.gaps())
    if card is not None:
        fidelity = (card.raw.get("comparability") or {}).get("fidelity") or {}
        if isinstance(fidelity, dict):
            issues.update(
                f"simulation_fidelity:{name}:{value}" for name, value in fidelity.items()
                if any(marker in str(value) for marker in ("not_simulated", "proxy", "unavailable"))
            )
    return CompetitionInterface(manifest.competition_id, delivery, frozenset(specs), tuple(sorted(issues)))

