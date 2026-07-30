"""Load evaluator registry and dispatch by deliverable / task type."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "data" / "evaluators" / "registry.json"


@dataclass(frozen=True)
class EvaluatorSpec:
    id: str
    task_types: tuple[str, ...]
    submission_mime_types: tuple[str, ...]
    strategy: str
    status: str
    raw: dict[str, Any]


class RegistryError(ValueError):
    """Raised when the evaluator registry cannot resolve a deliverable."""


def load_registry(path: Path | None = None) -> list[EvaluatorSpec]:
    registry_path = Path(path) if path else DEFAULT_REGISTRY
    payload = json.loads(registry_path.read_text(encoding="utf-8"))
    specs: list[EvaluatorSpec] = []
    for item in payload.get("evaluators", []):
        specs.append(
            EvaluatorSpec(
                id=item["id"],
                task_types=tuple(item.get("task_types", [])),
                submission_mime_types=tuple(item.get("submission_mime_types", [])),
                strategy=item.get("strategy", ""),
                status=item.get("status", "unknown"),
                raw=item,
            )
        )
    return specs


def resolve_evaluator_spec(
    task_type: str,
    *,
    registry_path: Path | None = None,
    allow_deferred: bool = False,
) -> EvaluatorSpec:
    specs = load_registry(registry_path)
    matches = [spec for spec in specs if task_type in spec.task_types]
    if not matches:
        raise RegistryError(f"No evaluator registered for task_type={task_type!r}.")
    usable = [
        spec
        for spec in matches
        if allow_deferred
        or not spec.status.startswith("deferred")
        and "missing" not in spec.status
    ]
    # Prefer concrete MVP / existing over deferred.
    preferred = usable or matches
    preferred.sort(
        key=lambda spec: (
            0 if spec.status in {"mvp", "ready"} else 1,
            0 if "deferred" not in spec.status else 1,
            spec.id,
        )
    )
    chosen = preferred[0]
    if not allow_deferred and (
        chosen.status.startswith("deferred") or "missing" in chosen.status
    ):
        raise RegistryError(
            f"Evaluator {chosen.id} for {task_type!r} is not ready "
            f"(status={chosen.status})."
        )
    return chosen


def strategy_kind(spec: EvaluatorSpec) -> str:
    """Map registry strategy strings to coarse kinds: gold | llm_judge | deferred."""
    strategy = spec.strategy.lower()
    if "official_gold" in strategy or strategy.startswith("gold"):
        return "gold"
    if "deferred" in spec.status or "sandbox" in strategy or "physical" in strategy:
        return "deferred"
    if "rubric" in strategy or "multimodal" in strategy or "llm" in strategy:
        return "llm_judge"
    return "unknown"


Dispatcher = Callable[[EvaluatorSpec], Any]
