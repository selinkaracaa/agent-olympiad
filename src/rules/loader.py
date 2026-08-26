from __future__ import annotations

from pathlib import Path

from .models import RuleCard
from .storage import load_rule_card_payload


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
    payload = load_rule_card_payload(
        competition_id,
        rules_root=root,
        required=required,
    )
    if payload is None:
        return None
    return RuleCard.from_dict(payload, competition_id=competition_id)
