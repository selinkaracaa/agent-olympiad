from __future__ import annotations

from .models import BenchmarkProblem, RuleCard, TeamMember, TeamSpec


def _default_members(size: int) -> list[TeamMember]:
    roles = ["captain and synthesizer", "primary solver", "independent verifier"]
    return [
        TeamMember(
            name=f"Agent_{index + 1}",
            role=roles[index] if index < len(roles) else "specialist and completeness checker",
        )
        for index in range(size)
    ]


def form_team(
    problem: BenchmarkProblem,
    rules: RuleCard,
    requested_size: int | None = None,
    *,
    allow_noncomparable: bool = False,
) -> TeamSpec:
    """Build a reproducible roster, defaulting to the official benchmark size."""
    official_size = problem.team_size
    size = requested_size if requested_size is not None else official_size
    if size < 2:
        raise ValueError("--team-size must be >= 2")
    if not rules.team_size_min <= size <= rules.team_size_max:
        raise ValueError(
            f"--team-size must be between {rules.team_size_min} "
            f"and {rules.team_size_max}"
        )
    comparable = size == official_size
    if not comparable and not allow_noncomparable:
        raise ValueError(
            f"{problem.problem_id} official team size is {official_size}; "
            "pass --allow-noncomparable-team-size for an experimental override"
        )
    return TeamSpec(
        members=tuple(_default_members(size)),
        official_team_size=official_size,
        actual_team_size=size,
        officially_comparable=comparable,
    )
