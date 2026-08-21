from __future__ import annotations

import sys
from pathlib import Path


DRAFT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DRAFT_ROOT))

from rules_v2 import RuleRepository  # noqa: E402


def show(repository: RuleRepository, task: dict, team_size: int | None = None) -> None:
    resolved = repository.resolve(task, team_size=team_size)
    roles = ", ".join(role["role_id"] for role in resolved.roster)
    print(
        f"{resolved.ruleset_id}\n"
        f"  selector={resolved.selector}\n"
        f"  team_size={resolved.team_size}\n"
        f"  roster={roles}"
    )


def main() -> None:
    repository = RuleRepository.open(DRAFT_ROOT)
    show(repository, {"competition_id": "hmmt_guts", "season": "feb", "team_size": 8})
    show(repository, {"competition_id": "hmmt_guts", "season": "nov", "team_size": 6})
    show(repository, {"competition_id": "wharton_investment"}, team_size=4)
    show(repository, {"competition_id": "wharton_investment"}, team_size=6)
    show(repository, {"competition_id": "wsc_writing", "team_size": 3})


if __name__ == "__main__":
    main()
