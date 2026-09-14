"""Shared immutable contracts for all four modules."""
from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Mapping

ActionModule = Literal["common", "memory", "coach", "task_specific"]

Visibility = Literal["private", "team", "contest"]
JsonType = Literal["string", "integer", "number", "boolean", "object", "array"]

# The two execution paths that consume this registry.  ``env`` is the legacy
# collaboration environment (``env.Environment`` + workboard); ``session`` is
# the contest-session engine (``contest_actions`` + ``ContestSession``).  A spec
# lists the runtimes that implement it; resolvers filter on it so neither path
# ever advertises an action it cannot execute.
Runtime = Literal["env", "session"]
RUNTIMES: tuple[Runtime, ...] = ("env", "session")
ALL_RUNTIMES: frozenset[str] = frozenset(RUNTIMES)
ENV_ONLY: frozenset[str] = frozenset({"env"})
SESSION_ONLY: frozenset[str] = frozenset({"session"})


@dataclass(frozen=True)
class ArgumentSpec:
    """One JSON-compatible action argument."""

    name: str
    type: JsonType = "string"
    description: str = ""
    required: bool = True
    enum: tuple[Any, ...] = ()
    # Element type for ``array`` arguments. ``enum`` then constrains elements.
    items: JsonType | None = None

    def to_schema(self) -> dict[str, Any]:
        schema: dict[str, Any] = {"type": self.type}
        if self.description:
            schema["description"] = self.description
        if self.type == "array":
            items: dict[str, Any] = {"type": self.items or "string"}
            if self.enum:
                items["enum"] = list(self.enum)
            # Non-emptiness is enforced by validate_action_payload rather than
            # ``minItems`` so provider strict-schema support is never a question.
            schema["items"] = items
        elif self.enum:
            schema["enum"] = list(self.enum)
        return schema


@dataclass(frozen=True)
class BudgetSemantics:
    """Units charged when an action succeeds."""

    turns: int = 1
    tool_calls: int = 0
    submission_attempts: int = 0
    terminal: bool = False


@dataclass(frozen=True)
class ActionSpec:
    """Immutable contract shared by prompts, parsers, and dispatch adapters."""

    name: str
    description: str
    arguments: tuple[ArgumentSpec, ...]
    visibility: Visibility
    pack: str
    budget: BudgetSemantics
    handler_name: str
    handler_callable: bool = True
    evaluator: bool = False
    evaluator_name: str | None = None
    submission: bool = False
    runtimes: frozenset[str] = ALL_RUNTIMES
    # Text wire format ``ACTION: name | PAYLOAD: text``.  Names the argument
    # that receives the whole payload when the action takes exactly one text
    # field; multi-field actions declare an ordered ``|``-split in
    # ``text_payload_fields`` instead.  ``None`` means the action has no
    # text-payload form and is only reachable through typed invocation.
    text_payload_fields: tuple[str, ...] | None = None
    module: ActionModule = "common"

    # Execution kind is independent of ownership and competition permission.
    is_tool: bool = False

    @property
    def handler_marker(self) -> str:
        """Stable marker used to match a registered runtime handler."""

        return self.handler_name

    @property
    def primary_argument(self) -> str | None:
        """The argument a single-payload tool implementation consumes.

        The first required argument, else the first argument (``resource`` on
        the read-only fixtures), else ``None`` for argument-less actions.
        """
        for argument in self.arguments:
            if argument.required:
                return argument.name
        return self.arguments[0].name if self.arguments else None

    @property
    def argument_fields(self) -> tuple[str, ...]:
        return tuple(argument.name for argument in self.arguments)

    @property
    def argument_schema(self) -> Mapping[str, Any]:
        required = [
            argument.name for argument in self.arguments if argument.required
        ]
        schema: dict[str, Any] = {
            "type": "object",
            "properties": {
                argument.name: argument.to_schema() for argument in self.arguments
            },
            "additionalProperties": False,
        }
        if required:
            schema["required"] = required
        return MappingProxyType(schema)


@dataclass(frozen=True)
class Resolution:
    """Resolved specs plus machine-readable reasons for omitted requests."""

    actions: frozenset[ActionSpec]
    unknown_capabilities: frozenset[str] = field(default_factory=frozenset)
    missing_handlers: frozenset[str] = field(default_factory=frozenset)

    @property
    def names(self) -> frozenset[str]:
        return frozenset(spec.name for spec in self.actions)

    @property
    def diagnostics(self) -> tuple[str, ...]:
        messages = [
            f"unknown capability: {name}"
            for name in sorted(self.unknown_capabilities)
        ]
        messages.extend(
            f"missing handler: {name}" for name in sorted(self.missing_handlers)
        )
        return tuple(messages)


_TEXT = ArgumentSpec("content", description="Action content.")
_REASON = ArgumentSpec(
    "reason", description="Optional reason for the action.", required=False
)
_PROBLEM_ID = ArgumentSpec(
    "problem_id", description="Identifier of the problem to select."
)
_RECIPIENTS = ArgumentSpec(
    "recipients",
    type="array",
    items="string",
    description=(
        "Exact teammate names that should privately receive the message; "
        "one name for a point-to-point message, several for a sub-group."
    ),
)
_OPTIONAL_PROBLEM_ID = ArgumentSpec(
    "problem_id",
    description="Problem identifier; defaults to the active problem.",
    required=False,
)
_PROPOSAL_ID = ArgumentSpec(
    "proposal_id",
    description="Exact proposal id such as P1 returned by propose.",
)


def make_action(
    name: str,
    description: str,
    arguments: tuple[ArgumentSpec, ...],
    *,
    visibility: Visibility = "team",
    pack: str = "common",
    module: ActionModule = "common",
    turns: int = 1,
    tool_calls: int = 0,
    is_tool: bool = False,
    submission_attempts: int = 0,
    terminal: bool = False,
    evaluator: bool = False,
    evaluator_name: str | None = None,
    submission: bool = False,
    runtimes: frozenset[str] = ALL_RUNTIMES,
    text_payload: tuple[str, ...] | None | Literal["auto"] = "auto",
) -> ActionSpec:
    if text_payload == "auto":
        # Single-text actions map the whole payload onto their one argument;
        # everything else needs an explicit split order or is typed-only.
        text_fields = [
            argument.name
            for argument in arguments
            if argument.type == "string" and not argument.enum
        ]
        payload_fields: tuple[str, ...] | None
        if len(arguments) == 0:
            payload_fields = ()
        elif len(arguments) == 1 and len(text_fields) == 1:
            payload_fields = (arguments[0].name,)
        else:
            payload_fields = None
    else:
        payload_fields = text_payload
    return ActionSpec(
        name=name,
        description=description,
        arguments=arguments,
        visibility=visibility,
        pack=pack,
        module=module,
        is_tool=is_tool,
        budget=BudgetSemantics(
            turns=turns,
            tool_calls=tool_calls,
            submission_attempts=submission_attempts,
            terminal=terminal,
        ),
        handler_name=name,
        evaluator=evaluator,
        evaluator_name=evaluator_name,
        submission=submission,
        runtimes=runtimes,
        text_payload_fields=payload_fields,
    )

