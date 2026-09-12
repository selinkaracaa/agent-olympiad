"""Content-based identity and non-mutating reuse checks for contest runs.

An output directory belongs to one resolved experiment. Legacy artifacts are
readable, but cannot be certified for reuse by guessing their missing settings.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any

from contest_manifest import ContestManifest
from contest_config import PROTOCOL_VERSION, ContestRunConfig
from tool_registry import ACTION_SET_VERSION


class RunCompatibilityError(ValueError):
    """Existing output cannot safely be used for the requested experiment."""


def content_hash(value: Any) -> str:
    encoded = json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_run_identity(
    manifest: ContestManifest,
    config: ContestRunConfig,
    *,
    execution: dict[str, Any],
    evaluation: dict[str, Any],
    source_root: Path | None = None,
) -> dict[str, Any]:
    """Freeze effective settings; record hashes rather than benchmark gold text.

    Source matching is deliberately conservative: all Python modules under src
    must match, including prompts and adapters. Output paths, timestamps, alias
    spelling and API credentials are not part of experiment identity.
    """
    resolved = {
        item.name: getattr(config, item.name)
        for item in fields(config)
        if item.name not in {
            "features", "rule_card", "otc_policy", "require_review",
            "require_final_review", "start_seat",
        }
    }
    resolved.update(
        baseline=asdict(config.features),
        review_required=config.review_required,
        final_review_required=config.final_review_required,
        start_seat=config.start_seat % config.team_size,
        rule_card_hash=content_hash(asdict(config.rule_card)) if config.rule_card else None,
    )
    root = source_root or Path(__file__).resolve().parent
    sources = {
        str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(
            path.read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        for path in sorted(root.rglob("*.py"))
    }
    settings = {
        "schema_version": 1,
        "protocol_version": PROTOCOL_VERSION,
        "action_set_version": ACTION_SET_VERSION,
        "session_id": manifest.session_id,
        "competition_id": manifest.competition_id,
        "task_ids": [task.task_id for task in manifest.tasks],
        "manifest_hash": content_hash(asdict(manifest)),
        "config": resolved,
        "execution": execution,
        "evaluation": evaluation,
        "source_hashes": sources,
    }
    return {"fingerprint": content_hash(settings), "settings": settings}


def _differences(old: Any, new: Any, prefix: str = "") -> list[str]:
    if isinstance(old, dict) and isinstance(new, dict):
        changed = []
        for key in sorted(old.keys() | new.keys()):
            path = f"{prefix}.{key}" if prefix else key
            if key not in old or key not in new:
                changed.append(path)
            else:
                changed.extend(_differences(old[key], new[key], path))
        return changed
    return [] if old == new else [prefix]


def validate_run_identity(
    stored: Any, expected: dict[str, Any], *, artifact: Path,
) -> None:
    def reject(reason: str) -> None:
        raise RunCompatibilityError(
            f"Cannot reuse {artifact}: {reason}. Use a fresh --output directory; "
            "the existing artifacts have not been changed."
        )

    if not isinstance(stored, dict) or not isinstance(stored.get("settings"), dict):
        reject("missing resolved run identity (legacy or incomplete artifact)")
    if stored.get("fingerprint") != content_hash(stored["settings"]):
        reject("stored run identity is corrupt")
    if stored["fingerprint"] != expected["fingerprint"]:
        differences = _differences(stored["settings"], expected["settings"])
        reject("configuration mismatch: " + ", ".join(differences[:12]))


def _read_artifact(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("expected a JSON object")
        return payload
    except (OSError, ValueError) as exc:
        raise RunCompatibilityError(f"Cannot reuse {path}: invalid artifact ({exc})") from exc


def _inspect_contest_output(
    out_dir: Path, expected: dict[str, Any],
) -> tuple[str, dict[str, Any] | None]:
    """Return new/resume/complete, or raise on incompatible/corrupt artifacts.

    This check never writes, starts providers, or submits anything to a judge.
    Both batch schedulers and the CLI use it before deciding to skip or resume.
    """
    config_path = out_dir / "run_config.json"
    if config_path.exists():
        validate_run_identity(_read_artifact(config_path), expected, artifact=config_path)
    settings = expected["settings"]
    checkpoint_path = out_dir / "contest_checkpoint.json"
    if checkpoint_path.exists():
        checkpoint = _read_artifact(checkpoint_path)
        validate_run_identity(checkpoint.get("run_identity"), expected, artifact=checkpoint_path)
        if (
            checkpoint.get("protocol_version") != settings["protocol_version"]
            or checkpoint.get("action_set_version") != settings["action_set_version"]
            or not isinstance(checkpoint.get("session"), dict)
            or not isinstance(checkpoint.get("memory"), str)
        ):
            raise RunCompatibilityError(f"Cannot reuse {checkpoint_path}: invalid checkpoint envelope")
    result_path = out_dir / "contest_session.json"
    if result_path.exists():
        result = _read_artifact(result_path)
        validate_run_identity(result.get("run_identity"), expected, artifact=result_path)
        for key in ("session_id", "competition_id", "protocol_version", "action_set_version"):
            if result.get(key) != settings[key]:
                raise RunCompatibilityError(f"Cannot reuse {result_path}: inconsistent {key}")
        if result.get("system_variant") != settings["config"]["system_variant"]:
            raise RunCompatibilityError(f"Cannot reuse {result_path}: inconsistent system_variant")
        if (
            not isinstance(result.get("grade"), dict)
            or not isinstance(result.get("metrics"), dict)
            or "task_utility" not in result["metrics"]
            or not isinstance(result.get("session_checkpoint"), dict)
            or result["session_checkpoint"].get("final_summary") is None
        ):
            raise RunCompatibilityError(f"Cannot reuse {result_path}: incomplete final result")
        return "complete", result
    return ("resume" if checkpoint_path.exists() else "new"), None


def inspect_contest_output(out_dir: Path, expected: dict[str, Any]) -> str:
    """Read-only reuse decision against the requested experiment identity."""
    return _inspect_contest_output(out_dir, expected)[0]


def read_completed_contest_result(
    out_dir: Path, expected: dict[str, Any],
) -> dict[str, Any]:
    """Return the exact final payload that passed identity/envelope validation.

    Do not re-open the result after checking it: exporters must consume the
    validated snapshot, not potentially replaced bytes at the same path.
    """
    state, result = _inspect_contest_output(out_dir, expected)
    if state != "complete" or result is None:
        raise RunCompatibilityError(f"Cannot summarize {out_dir}: final result is {state}")
    return result
