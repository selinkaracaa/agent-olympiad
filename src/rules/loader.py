from __future__ import annotations

import json
from pathlib import Path

from .models import RuleCard, RuleCardError


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RULES_ROOT = REPO_ROOT / "data" / "rules"


def load_rule_card(
    competition_id: str,
    *,
    rules_root: Path | None = None,
    required: bool = False,
) -> RuleCard | None:
    """Load one competition rule card without letting the model choose it."""
    root = Path(rules_root) if rules_root is not None else DEFAULT_RULES_ROOT
    path = root / f"{competition_id}.json"
    if not path.is_file():
        if required:
            raise FileNotFoundError(
                f"No rule card for competition {competition_id!r}: {path}"
            )
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuleCardError(f"Invalid JSON in rule card {path}: {exc}") from exc
    return RuleCard.from_dict(payload, competition_id=competition_id)
