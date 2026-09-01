from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import RuleCardError


COMPONENT_FILES = {
    "competition": "competition.json",
    "collaboration": "collaboration.json",
    "evaluation": "evaluation.json",
}

COMPONENT_KEYS = {
    "competition": {
        "schema_version",
        "rule_id",
        "competition_id",
        "profile",
        "protocol",
        "team",
        "execution",
        "allowed_tools",
        "resources",
        "deliverable",
        "human_constraints",
        "rules_text",
        "provenance",
        "comparability",
    },
    "collaboration": {
        "agent_constraints",
        "agent_roles",
        "information_policy",
        "rule_sections",
        "deliberation",
        "communication",
        "simulation",
    },
    "evaluation": {
        "evaluation_guidance",
        "scoring",
        "submission",
    },
}


class RuleCardStorageError(RuleCardError):
    """Raised when a rule-card file layout is missing or ambiguous."""


def _read_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuleCardStorageError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RuleCardStorageError(f"Rule-card component must be an object: {path}")
    return value


def _bundle_paths(root: Path, competition_id: str) -> dict[str, Path]:
    directory = root / competition_id
    return {
        component: directory / filename
        for component, filename in COMPONENT_FILES.items()
    }


def _has_bundle(root: Path, competition_id: str) -> bool:
    return any(path.exists() for path in _bundle_paths(root, competition_id).values())


def iter_rule_card_ids(rules_root: Path) -> list[str]:
    root = Path(rules_root)
    ids = {
        path.stem
        for path in root.glob("*.json")
        if path.name != "schema.json"
    }
    for directory in root.iterdir():
        if directory.is_dir() and _has_bundle(root, directory.name):
            ids.add(directory.name)
    return sorted(ids)


def load_rule_card_payload(
    competition_id: str,
    *,
    rules_root: Path,
    required: bool = False,
) -> dict[str, Any] | None:
    root = Path(rules_root)
    flat_path = root / f"{competition_id}.json"
    paths = _bundle_paths(root, competition_id)
    has_flat = flat_path.is_file()
    has_bundle = _has_bundle(root, competition_id)

    if has_flat and has_bundle:
        raise RuleCardStorageError(
            f"Rule card {competition_id!r} has both flat and bundled representations."
        )
    if has_flat:
        return _read_object(flat_path)
    if not has_bundle:
        if required:
            raise FileNotFoundError(
                f"No rule card for competition {competition_id!r} under {root}"
            )
        return None

    missing = [path.name for path in paths.values() if not path.is_file()]
    if missing:
        raise RuleCardStorageError(
            f"Bundled rule card {competition_id!r} is missing: {', '.join(missing)}"
        )

    merged: dict[str, Any] = {}
    owners: dict[str, str] = {}
    for component, path in paths.items():
        payload = _read_object(path)
        misplaced = sorted(set(payload) - COMPONENT_KEYS[component])
        if misplaced:
            raise RuleCardStorageError(
                f"{path} contains fields owned by another component: "
                + ", ".join(misplaced)
            )
        duplicates = sorted(set(merged) & set(payload))
        if duplicates:
            first_owner = owners[duplicates[0]]
            raise RuleCardStorageError(
                f"Bundled rule card {competition_id!r} repeats fields in "
                f"{first_owner} and {component}: {', '.join(duplicates)}"
            )
        merged.update(payload)
        owners.update({key: component for key in payload})
    return merged


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if path.is_file() and path.read_text(encoding="utf-8") == rendered:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(rendered, encoding="utf-8")
    temporary.replace(path)


def write_rule_card_payload(
    competition_id: str,
    payload: dict[str, Any],
    *,
    rules_root: Path,
) -> None:
    root = Path(rules_root)
    flat_path = root / f"{competition_id}.json"
    has_flat = flat_path.is_file()
    has_bundle = _has_bundle(root, competition_id)
    if has_flat and has_bundle:
        raise RuleCardStorageError(
            f"Rule card {competition_id!r} has both flat and bundled representations."
        )
    if has_bundle:
        known_keys = set().union(*COMPONENT_KEYS.values())
        unknown = sorted(set(payload) - known_keys)
        if unknown:
            raise RuleCardStorageError(
                "Cannot assign fields to a rule-card component: " + ", ".join(unknown)
            )
        paths = _bundle_paths(root, competition_id)
        for component, keys in COMPONENT_KEYS.items():
            component_payload = {
                key: value for key, value in payload.items() if key in keys
            }
            _write_json(paths[component], component_payload)
        return
    _write_json(flat_path, payload)
