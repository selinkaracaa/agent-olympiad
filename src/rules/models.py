from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class RuleCardError(ValueError):
    """Raised when a competition rule card is malformed."""


@dataclass(frozen=True)
class AgentRole:
    name: str
    title: str
    duties: tuple[str, ...]
    may_submit: bool = True


@dataclass(frozen=True)
class RuleCard:
    schema_version: str
    rule_id: str
    competition_id: str
    profile: str
    protocol: str
    team_size_min: int
    team_size_default: int
    team_size_max: int
    max_turns: int
    allowed_tools: tuple[str, ...]
    rules_text: str
    human_constraints: tuple[str, ...] = ()
    agent_roles: tuple[AgentRole, ...] = ()
    answer_format: str = ""
    scoring: dict[str, Any] = field(default_factory=dict)
    resources: dict[str, Any] = field(default_factory=dict)
    submission: dict[str, Any] = field(default_factory=dict)
    provenance: dict[str, Any] = field(default_factory=dict)
    comparability: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_dict(cls, raw: dict[str, Any], *, competition_id: str) -> "RuleCard":
        if not isinstance(raw, dict):
            raise RuleCardError("Rule card must be a JSON object.")

        schema_version = str(raw.get("schema_version") or "").strip()
        rule_id = str(raw.get("rule_id") or "").strip()
        protocol = str(raw.get("protocol") or "").strip()
        rules_text = str(raw.get("rules_text") or "").strip()
        if schema_version != "1.0":
            raise RuleCardError("Rule card schema_version must be '1.0'.")
        if not rule_id or not protocol or not rules_text:
            raise RuleCardError("rule_id, protocol, and rules_text must be non-empty.")

        card_competition = str(raw.get("competition_id") or "").strip()
        if card_competition != competition_id:
            raise RuleCardError(
                f"Rule card competition_id={card_competition!r} does not match "
                f"{competition_id!r}."
            )

        team = raw.get("team")
        if not isinstance(team, dict):
            raise RuleCardError("Rule card requires a team object.")
        try:
            minimum = int(team["active_min"])
            default = int(team["active_default"])
            maximum = int(team["active_max"])
        except (KeyError, TypeError, ValueError) as exc:
            raise RuleCardError(
                "team requires integer active_min, active_default, and active_max."
            ) from exc
        if minimum < 1 or not minimum <= default <= maximum:
            raise RuleCardError(
                "team must satisfy 1 <= active_min <= active_default <= active_max."
            )

        execution = raw.get("execution") or {}
        if not isinstance(execution, dict):
            raise RuleCardError("execution must be an object.")
        try:
            max_turns = int(execution.get("max_turns", 50))
        except (TypeError, ValueError) as exc:
            raise RuleCardError("execution.max_turns must be an integer.") from exc
        if max_turns < 1:
            raise RuleCardError("execution.max_turns must be positive.")

        tools = raw.get("allowed_tools", [])
        if not isinstance(tools, list) or not all(isinstance(item, str) for item in tools):
            raise RuleCardError("allowed_tools must be an array of strings.")
        if len(tools) != len(set(tools)):
            raise RuleCardError("allowed_tools must not contain duplicates.")

        profile = str(raw.get("profile") or "").strip()
        if profile not in {
            "official_equivalent",
            "benchmark_native",
            "proxy",
            "non_comparable",
        }:
            raise RuleCardError(
                "profile must be official_equivalent, benchmark_native, proxy, "
                "or non_comparable."
            )

        constraints = raw.get("human_constraints") or []
        if not isinstance(constraints, list) or not all(
            isinstance(item, str) and item.strip() for item in constraints
        ):
            raise RuleCardError("human_constraints must be an array of non-empty strings.")

        roles_raw = raw.get("agent_roles") or []
        if not isinstance(roles_raw, list):
            raise RuleCardError("agent_roles must be an array.")
        roles: list[AgentRole] = []
        for item in roles_raw:
            if not isinstance(item, dict):
                raise RuleCardError("Each agent role must be an object.")
            duties = item.get("duties") or []
            if not isinstance(duties, list) or not all(
                isinstance(duty, str) and duty.strip() for duty in duties
            ):
                raise RuleCardError("agent role duties must be an array of strings.")
            name = str(item.get("name") or "").strip()
            title = str(item.get("title") or "").strip()
            if not name or not title:
                raise RuleCardError("Each agent role needs name and title.")
            roles.append(
                AgentRole(
                    name=name,
                    title=title,
                    duties=tuple(duties),
                    may_submit=bool(item.get("may_submit", True)),
                )
            )

        object_fields: dict[str, dict[str, Any]] = {}
        for field_name in (
            "resources",
            "submission",
            "provenance",
            "comparability",
            "scoring",
        ):
            value = raw.get(field_name) or {}
            if not isinstance(value, dict):
                raise RuleCardError(f"{field_name} must be an object.")
            object_fields[field_name] = dict(value)

        return cls(
            schema_version=schema_version,
            rule_id=rule_id,
            competition_id=card_competition,
            profile=profile,
            protocol=protocol,
            team_size_min=minimum,
            team_size_default=default,
            team_size_max=maximum,
            max_turns=max_turns,
            allowed_tools=tuple(tools),
            rules_text=rules_text,
            human_constraints=tuple(constraints),
            agent_roles=tuple(roles),
            answer_format=str(raw.get("answer_format") or "").strip(),
            scoring=object_fields["scoring"],
            resources=object_fields["resources"],
            submission=object_fields["submission"],
            provenance=object_fields["provenance"],
            comparability=object_fields["comparability"],
            raw=dict(raw),
        )

    def role_for(self, agent_name: str) -> AgentRole | None:
        for role in self.agent_roles:
            if role.name == agent_name:
                return role
        return None

    def roster(self, team_size: int) -> list[AgentRole]:
        if self.agent_roles:
            if len(self.agent_roles) != team_size:
                raise RuleCardError(
                    f"Rule card defines {len(self.agent_roles)} roles but team_size={team_size}."
                )
            return list(self.agent_roles)
        defaults = [
            ("Agent_1", "captain and synthesizer"),
            ("Agent_2", "primary solver"),
            ("Agent_3", "independent verifier"),
        ]
        roster: list[AgentRole] = []
        for index in range(team_size):
            if index < len(defaults):
                name, title = defaults[index]
            else:
                name = f"Agent_{index + 1}"
                title = "specialist and completeness checker"
            roster.append(AgentRole(name=name, title=title, duties=()))
        return roster
