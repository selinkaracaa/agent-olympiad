from __future__ import annotations

from dataclasses import dataclass, field
import statistics
from typing import Any

import requests

from .models import RuleCard


@dataclass
class Leaderboard:
    competition_name: str
    entries: list[dict[str, Any]]
    scale_id: str
    comparison_status: str
    officially_comparable: bool = False
    agent_name: str = "Agent Team"
    agent_score: float = 0.0
    history: list[dict[str, Any]] = field(default_factory=list)
    problem_scores: dict[str, float] = field(default_factory=dict)

    @classmethod
    def simulated(cls, competition_name: str, scores: list[float]) -> "Leaderboard":
        entries = [
            {"name": f"Human Team {index + 1}", "score": float(score), "source": "simulated"}
            for index, score in enumerate(scores)
        ]
        return cls(
            competition_name,
            entries,
            scale_id="normalized_100",
            comparison_status="synthetic",
            officially_comparable=False,
        )

    @classmethod
    def codeforces(
        cls,
        contest_id: int,
        *,
        count: int = 100,
        timeout: float = 10,
    ) -> "Leaderboard":
        response = requests.get(
            "https://codeforces.com/api/contest.standings",
            params={"contestId": contest_id, "from": 1, "count": count, "showUnofficial": "true"},
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("status") != "OK":
            raise RuntimeError(payload.get("comment", "Codeforces API returned an error"))
        entries = []
        for row in payload["result"]["rows"]:
            party = row.get("party", {})
            members = party.get("members") or []
            name = "+".join(member.get("handle", "?") for member in members) or "unknown"
            entries.append(
                {"name": name, "score": float(row.get("points", 0)), "source": "codeforces"}
            )
        return cls(
            f"Codeforces {contest_id}",
            entries,
            scale_id="codeforces_points",
            comparison_status="not_comparable",
            officially_comparable=False,
        )

    def update(
        self,
        normalized_score: float,
        problem_id: str,
        *,
        score_scale_id: str = "normalized_100",
        evaluator_id: str | None = None,
        team_comparable: bool = True,
    ) -> dict[str, Any]:
        self.problem_scores[problem_id] = max(0.0, min(100.0, float(normalized_score)))
        self.agent_score = statistics.fmean(self.problem_scores.values())
        comparable = (
            score_scale_id == self.scale_id
            and self.comparison_status != "not_comparable"
        )
        snapshot = self.snapshot(include_agent=comparable)
        snapshot.update(
            {
                "agent_score": self.agent_score,
                "agent_scale_id": score_scale_id,
                "evaluator_id": evaluator_id,
                "team_comparable": team_comparable,
                "officially_comparable": bool(
                    comparable and team_comparable and self.officially_comparable
                ),
            }
        )
        if not comparable:
            snapshot["comparison_status"] = "not_comparable"
            snapshot["reason"] = (
                f"Agent score scale {score_scale_id!r} cannot be ranked against "
                f"{self.scale_id!r}."
            )
        self.history.append(
            {"problem_id": problem_id, "problems_scored": len(self.problem_scores), **snapshot}
        )
        return snapshot

    def snapshot(self, *, include_agent: bool = True) -> dict[str, Any]:
        ranked = list(self.entries)
        if include_agent:
            ranked.append(
                {
                    "name": self.agent_name,
                    "score": self.agent_score,
                    "source": "run",
                }
            )
        ranked.sort(key=lambda item: item["score"], reverse=True)
        payload: dict[str, Any] = {
            "competition": self.competition_name,
            "participants": len(ranked),
            "scale_id": self.scale_id,
            "comparison_status": self.comparison_status,
            "top": ranked[:10],
        }
        if not include_agent:
            return payload
        rank = next(
            index
            for index, item in enumerate(ranked, 1)
            if item["name"] == self.agent_name
        )
        above = ranked[rank - 2] if rank > 1 else None
        below = ranked[rank] if rank < len(ranked) else None
        payload.update(
            {
                "rank": rank,
                "score": self.agent_score,
                "gap_to_above": (
                    round(float(above["score"]) - self.agent_score, 3)
                    if above
                    else 0.0
                ),
                "gap_to_below": (
                    round(self.agent_score - float(below["score"]), 3)
                    if below
                    else 0.0
                ),
            }
        )
        return payload

    def view(self) -> str:
        if self.comparison_status == "not_comparable":
            return (
                f"{self.competition_name}: external standings use {self.scale_id}; "
                "the local normalized score is not rank-comparable."
            )
        snap = self.snapshot()
        return (
            f"{snap['competition']}: rank {snap['rank']}/{snap['participants']}, "
            f"score {snap['score']:.2f}/100 (synthetic, non-official)."
        )


def build_leaderboard(
    rules: RuleCard,
    codeforces_contest: int | None = None,
) -> Leaderboard:
    if codeforces_contest is not None:
        return Leaderboard.codeforces(codeforces_contest)
    return Leaderboard.simulated(
        rules.display_name,
        rules.leaderboard.get("human_scores", [95, 85, 75, 65, 55]),
    )
