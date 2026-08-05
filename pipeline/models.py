from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ProblemAsset:
    path: Path
    mime_type: str
    role: str = "agent_visible"
    page_start: int | None = None
    page_end: int | None = None


@dataclass(frozen=True)
class BenchmarkProblem:
    problem_id: str
    competition_id: str
    task_type: str
    problem_description: str
    team_size: int
    gold_label: dict[str, Any]
    evaluation: dict[str, Any]
    total_points: float | None
    source_file: str | None
    solution_file: str | None
    assets: tuple[ProblemAsset, ...]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(
        cls,
        raw: dict[str, Any],
        *,
        competition_id: str,
        repository_root: Path,
    ) -> "BenchmarkProblem":
        problem_id = str(raw.get("problem_id") or "").strip()
        description = str(raw.get("problem_description") or "").strip()
        if not problem_id:
            raise ValueError("Benchmark problem is missing problem_id")

        row_competition = str(
            raw.get("competition_id") or competition_id
        ).strip()
        if row_competition != competition_id:
            raise ValueError(
                f"{problem_id} belongs to {row_competition!r}, "
                f"not requested competition {competition_id!r}"
            )

        team_size = int(raw.get("team_size") or 0)
        if team_size < 2:
            raise ValueError(f"{problem_id} requires a team_size >= 2")

        assets: list[ProblemAsset] = []
        for item in raw.get("assets") or []:
            if item.get("role") != "agent_visible":
                continue
            path = (repository_root / str(item.get("path") or "")).resolve()
            if path.is_file():
                assets.append(
                    ProblemAsset(
                        path=path,
                        mime_type=str(item.get("mime_type") or "application/octet-stream"),
                        role="agent_visible",
                        page_start=item.get("page_start"),
                        page_end=item.get("page_end"),
                    )
                )

        source_file = raw.get("source_file")
        source_path = (
            (repository_root / str(source_file)).resolve() if source_file else None
        )
        if source_path is not None and not source_path.is_file():
            raise ValueError(
                f"{problem_id} declares missing source_file: {source_file}"
            )
        if source_path and source_path.is_file() and not any(
            asset.path == source_path for asset in assets
        ):
            mime_type = (
                "application/pdf"
                if source_path.suffix.lower() == ".pdf"
                else "image/" + source_path.suffix.lower().lstrip(".")
            )
            assets.append(
                ProblemAsset(
                    path=source_path,
                    mime_type=mime_type,
                    role="agent_visible",
                )
            )
        if not description:
            if not assets:
                raise ValueError(
                    f"{problem_id} has neither problem_description nor "
                    "an agent-visible source asset"
                )
            description = (
                "The problem statement is provided in the attached official "
                "competition packet."
            )

        points = raw.get("total_points")
        return cls(
            problem_id=problem_id,
            competition_id=competition_id,
            task_type=str(raw.get("task_type") or ""),
            problem_description=description,
            team_size=team_size,
            gold_label=dict(raw.get("gold_label") or {}),
            evaluation=dict(raw.get("evaluation") or {}),
            total_points=float(points) if points is not None else None,
            source_file=str(source_file) if source_file else None,
            solution_file=str(raw.get("solution_file")) if raw.get("solution_file") else None,
            assets=tuple(assets),
            raw=dict(raw),
        )

    @property
    def title(self) -> str:
        return str(
            self.raw.get("title")
            or self.raw.get("topic")
            or self.problem_id
        )


@dataclass(frozen=True)
class RuleCard:
    competition_id: str
    display_name: str
    team_size_min: int
    team_size_default: int
    team_size_max: int
    max_turns: int
    allowed_tools: tuple[str, ...]
    exclusive_tools: dict[str, int]
    rules_text: str
    leaderboard: dict[str, Any]
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_dict(
        cls,
        raw: dict[str, Any],
        *,
        competition_id: str,
    ) -> "RuleCard":
        card_id = str(raw.get("competition_id") or "")
        if card_id != competition_id:
            raise ValueError(
                f"Rule card competition_id={card_id!r} does not match "
                f"{competition_id!r}"
            )
        minimum = int(raw.get("team_size_min", 0))
        maximum = int(raw.get("team_size_max", 0))
        default = int(raw.get("team_size_default", minimum))
        if minimum < 2 or maximum < minimum or not minimum <= default <= maximum:
            raise ValueError(
                "Rule card needs 2 <= team_size_min <= "
                "team_size_default <= team_size_max"
            )
        return cls(
            competition_id=competition_id,
            display_name=str(raw.get("display_name") or competition_id),
            team_size_min=minimum,
            team_size_default=default,
            team_size_max=maximum,
            max_turns=int(raw.get("max_turns", 40)),
            allowed_tools=tuple(str(item) for item in raw.get("allowed_tools", [])),
            exclusive_tools={
                str(key): int(value)
                for key, value in (raw.get("exclusive_tools") or {}).items()
            },
            rules_text=str(raw.get("rules_text") or ""),
            leaderboard=dict(raw.get("leaderboard") or {}),
            raw=dict(raw),
        )


@dataclass(frozen=True)
class CompetitionPacket:
    competition_id: str
    problem: BenchmarkProblem
    rules: RuleCard

    @property
    def problem_id(self) -> str:
        return self.problem.problem_id


@dataclass(frozen=True)
class TeamMember:
    name: str
    role: str


@dataclass(frozen=True)
class TeamSpec:
    members: tuple[TeamMember, ...]
    official_team_size: int
    actual_team_size: int
    officially_comparable: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "members": [asdict(member) for member in self.members],
            "official_team_size": self.official_team_size,
            "actual_team_size": self.actual_team_size,
            "officially_comparable": self.officially_comparable,
        }
