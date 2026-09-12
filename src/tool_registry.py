"""Typed action registry and capability resolver.

This module is deliberately independent of environment and agent-system
implementations.  Both vanilla and strategic systems can consume the same
resolved action specs and adapt their legacy action names at the boundary.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Iterable, Literal, Mapping

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
    # Legacy ``ACTION: name | PAYLOAD: text`` wire format.  Names the argument
    # that receives the whole payload when the action takes exactly one text
    # field; multi-field actions declare an ordered ``|``-split in
    # ``legacy_payload_fields`` instead.  ``None`` means the action has no
    # text-payload form and is only reachable through typed invocation.
    legacy_payload_fields: tuple[str, ...] | None = None

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


def _action(
    name: str,
    description: str,
    arguments: tuple[ArgumentSpec, ...],
    *,
    visibility: Visibility = "team",
    pack: str = "common",
    tool_calls: int = 0,
    submission_attempts: int = 0,
    terminal: bool = False,
    evaluator: bool = False,
    evaluator_name: str | None = None,
    submission: bool = False,
    runtimes: frozenset[str] = ALL_RUNTIMES,
    legacy_payload: tuple[str, ...] | None | Literal["auto"] = "auto",
) -> ActionSpec:
    if legacy_payload == "auto":
        # Single-text actions map the whole payload onto their one argument;
        # everything else needs an explicit split order or is typed-only.
        text_fields = [
            argument.name
            for argument in arguments
            if argument.type == "string" and not argument.enum
        ]
        legacy_fields: tuple[str, ...] | None
        if len(arguments) == 0:
            legacy_fields = ()
        elif len(arguments) == 1 and len(text_fields) == 1:
            legacy_fields = (arguments[0].name,)
        else:
            legacy_fields = None
    else:
        legacy_fields = legacy_payload
    return ActionSpec(
        name=name,
        description=description,
        arguments=arguments,
        visibility=visibility,
        pack=pack,
        budget=BudgetSemantics(
            turns=1,
            tool_calls=tool_calls,
            submission_attempts=submission_attempts,
            terminal=terminal,
        ),
        handler_name=name,
        evaluator=evaluator,
        evaluator_name=evaluator_name,
        submission=submission,
        runtimes=runtimes,
        legacy_payload_fields=legacy_fields,
    )


_SPECS = (
    _action(
        "select_problem",
        "Select (claim) a contest problem to work on.",
        (_PROBLEM_ID,),
        visibility="contest",
    ),
    _action("speak", "Broadcast a message to the team.", (_TEXT,)),
    _action(
        "direct_message",
        "Send a private message to one teammate or a named sub-group of teammates.",
        (_RECIPIENTS, _TEXT),
        visibility="private",
        # Legacy ``message_group``: ``Agent_2, Agent_3 | message``.
        legacy_payload=("recipients", "content"),
    ),
    _action(
        "work",
        (
            "Record durable work for the team: a candidate answer or draft for "
            "one problem. Pass problem_id to record against a specific problem "
            "(and make it your current one); without it the work goes to your "
            "current problem."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        # Legacy ``submit_problem``: ``<item> | <answer>``; ``write_scratchpad``
        # maps the whole payload onto ``content`` via its alias.
        legacy_payload=("problem_id", "content"),
    ),
    # Desk actions: read-only inspection, personal notes, and team triage.
    # They are the contestant's desk, not contest-specific instruments, so
    # every task family and both runtimes receive them.
    _action(
        "inspect_problem",
        (
            "Read one problem's statement plus its complete answer-version, "
            "review, and submission history without changing the team's "
            "active problem. Without problem_id it shows your current problem "
            "(or the whole board / latest code history where that applies). "
            "Self-verification context only; it never counts as an "
            "independent review."
        ),
        (
            _OPTIONAL_PROBLEM_ID,
            ArgumentSpec(
                "focus",
                description="Optional aspect to re-check, such as edge cases.",
                required=False,
            ),
        ),
        visibility="private",
        legacy_payload=("problem_id", "focus"),
    ),
    _action(
        "triage_problem",
        (
            "Set the team's working priority for one problem, or mark it "
            "hopeless. Hopeless problems stay on the sheet and their latest "
            "draft is still submitted at the deadline."
        ),
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "priority",
                description="Team priority for this problem.",
                enum=("high", "normal", "low", "hopeless"),
            ),
            _REASON,
        ),
        visibility="team",
        legacy_payload=("problem_id", "priority", "reason"),
    ),
    _action(
        "remember",
        (
            "Store a private note that survives outside the visible transcript, "
            "optionally tagged to one problem. Use work for candidate answers, "
            "remember for intermediate results, dead ends, and reminders."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        visibility="private",
        # Legacy form is ``[<item> |] <note>``: the optional tag comes first.
        legacy_payload=("problem_id", "content"),
    ),
    _action(
        "recall",
        (
            "Search your own notes and notes teammates have shared, ranked by "
            "problem tag, query match, and recency."
        ),
        (
            ArgumentSpec(
                "query",
                description="Optional keywords to match.",
                required=False,
            ),
            ArgumentSpec(
                "problem_id",
                description="Optional problem tag to prioritise.",
                required=False,
            ),
        ),
        visibility="private",
        legacy_payload=("problem_id", "query"),
    ),
    _action(
        "share_note",
        "Publish one of your stored notes to the whole team.",
        (
            ArgumentSpec(
                "note_id",
                description=(
                    "Id of the note returned by remember or recall "
                    "(several ids may be comma-separated)."
                ),
            ),
        ),
        visibility="team",
    ),
    # Leader-only (centralized baseline): replace one teammate's work list.
    _action(
        "assign_problem",
        (
            "Leader only: replace one teammate's enforced work list with the "
            "given problems. The teammate is scheduled onto the first listed "
            "problem from the next round."
        ),
        (
            ArgumentSpec(
                "agent",
                description="Exact teammate name to reassign.",
            ),
            ArgumentSpec(
                "problem_ids",
                type="array",
                items="string",
                description="Problems this teammate may work on, in order.",
            ),
            _REASON,
        ),
        visibility="team",
        runtimes=SESSION_ONLY,
        legacy_payload=("agent", "problem_ids", "reason"),
    ),
    _action(
        "request_review",
        "Ask a teammate to review the current active problem; this does not approve it.",
        (
            _TEXT,
            ArgumentSpec(
                "reviewer",
                description="Optional teammate name.",
                required=False,
            ),
        ),
        runtimes=SESSION_ONLY,
        legacy_payload=("content",),
    ),
    _action(
        "review_answer",
        "Independently review another agent's current answer version.",
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "version_hash",
                description="Exact current answer version being reviewed.",
            ),
            ArgumentSpec(
                "decision",
                description="Review outcome.",
                enum=("approve", "reject"),
            ),
            ArgumentSpec("content", description="Review findings and evidence."),
        ),
        legacy_payload=("problem_id", "version_hash", "decision", "content"),
    ),
    _action(
        "submit",
        "Submit a final answer for evaluation.",
        (ArgumentSpec("answer", description="Complete final answer."),),
        visibility="team",
        submission_attempts=1,
        evaluator=True,
        evaluator_name="task_evaluator",
        submission=True,
    ),
    _action(
        "skip_problem",
        "Skip (release) the current problem.",
        (_REASON,),
        visibility="contest",
    ),
    _action(
        "finish_contest",
        "Finish only after every task has a valid submission and required final review.",
        (_REASON,),
        visibility="contest",
        terminal=True,
        runtimes=SESSION_ONLY,
    ),
    _action("rest", "Pass the current turn.", (_REASON,), visibility="private"),
    # Structured deliberation (rule cards with ``deliberation.mode ==
    # "structured"``): a proposal ledger with targeted challenge / evidence /
    # revision and a designated decision maker. Only the ``otc`` baseline
    # resolves this pack, and only when the competition's card asks for it.
    _action(
        "propose",
        (
            "Open a numbered proposal (a candidate answer, approach, or split of "
            "work) for the team to challenge, support, or decide on."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        pack="deliberation",
    ),
    _action(
        "challenge",
        "Raise a concrete objection to an open proposal you did not author.",
        (_PROPOSAL_ID, _TEXT),
        pack="deliberation",
        legacy_payload=("proposal_id", "content"),
    ),
    _action(
        "provide_evidence",
        "Attach a check, derivation, or counterexample to an open proposal.",
        (_PROPOSAL_ID, _TEXT),
        pack="deliberation",
        legacy_payload=("proposal_id", "content"),
    ),
    _action(
        "revise",
        "Author only: replace the current claim of your open proposal.",
        (_PROPOSAL_ID, _TEXT),
        pack="deliberation",
        legacy_payload=("proposal_id", "content"),
    ),
    _action(
        "decide",
        "Decision maker only: accept, reject, or defer an open proposal.",
        (
            _PROPOSAL_ID,
            ArgumentSpec(
                "outcome",
                description="Decision on the proposal.",
                enum=("accept", "reject", "defer"),
            ),
            ArgumentSpec("reason", description="Why the team decides this way."),
        ),
        pack="deliberation",
        legacy_payload=("proposal_id", "outcome", "reason"),
    ),
    _action(
        "use_calculator",
        "Evaluate a mathematical expression.",
        (ArgumentSpec("expression", description="Arithmetic expression."),),
        visibility="private",
        pack="math",
        tool_calls=1,
    ),
    _action(
        "execute_code",
        (
            "Execute code in the contest sandbox. For programming tasks the same "
            "source is also run on the official sample input and compared with "
            "the expected output; only a sample AC counts as local run evidence."
        ),
        (
            ArgumentSpec("code", description="Source code to execute."),
            ArgumentSpec(
                "language",
                description="Runtime language; defaults to Python.",
                required=False,
            ),
        ),
        visibility="private",
        pack="programming",
        tool_calls=1,
    ),
    _action(
        "submit_code",
        "Submit source code to the programming evaluator.",
        (
            ArgumentSpec("code", description="Complete source code."),
            ArgumentSpec(
                "language", description="Submission language.", required=False
            ),
        ),
        pack="programming",
        tool_calls=1,
        submission_attempts=1,
        evaluator=True,
        evaluator_name="programming_judge",
        submission=True,
    ),
    _action(
        "web_search",
        "Search permitted web resources.",
        (ArgumentSpec("query", description="Search query."),),
        visibility="private",
        pack="research",
        tool_calls=1,
    ),
    _action(
        "read_lab_equipment",
        "Read declared laboratory equipment data.",
        (
            ArgumentSpec(
                "resource",
                description="Equipment or reading identifier.",
                required=False,
            ),
        ),
        visibility="private",
        pack="resources",
        tool_calls=1,
    ),
    _action(
        "read_star_chart",
        "Read a declared star-chart resource.",
        (
            ArgumentSpec(
                "resource",
                description="Chart or observation identifier.",
                required=False,
            ),
        ),
        visibility="private",
        pack="resources",
        tool_calls=1,
    ),
    # Workboard-only review: a three-state opinion on the currently recorded
    # board answer. The contest-session path binds reviews to an immutable
    # version hash (``review_answer``), which the board does not have, so this
    # stays an ``env`` action rather than an alias.
    _action(
        "verify_problem",
        (
            "Review the answer currently recorded for one board item: "
            "agree, disagree, or unsure, followed by a comment."
        ),
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "content",
                description="Verdict keyword (agree|disagree|unsure) then comment.",
            ),
        ),
        visibility="team",
        pack="workboard",
        runtimes=ENV_ONLY,
        legacy_payload=("problem_id", "content"),
    ),
    # Legacy workspace helpers. The contest-session engine injects the same
    # information into every prompt (BUDGET block, rule guidance, private
    # notes projection), so these have no session counterpart.
    _action(
        "check_budget",
        "Show turns, API calls, tokens, contest clock, and how much of the board is blank.",
        (),
        visibility="private",
        pack="workspace",
        runtimes=ENV_ONLY,
    ),
    _action(
        "query_rules",
        "Show the contest rule card as visible to your role.",
        (),
        visibility="private",
        pack="workspace",
        runtimes=ENV_ONLY,
    ),
    _action(
        "write_private_notes",
        "Replace your private notes block (visible only to you in later prompts).",
        (_TEXT,),
        visibility="private",
        pack="workspace",
        runtimes=ENV_ONLY,
    ),
)

ACTION_REGISTRY: Mapping[str, ActionSpec] = MappingProxyType(
    {spec.name: spec for spec in _SPECS}
)

COMMON_ACTION_NAMES = frozenset(
    name for name, spec in ACTION_REGISTRY.items() if spec.pack == "common"
)
# Read-only or personal bookkeeping actions that never mutate answers or
# submissions. Contest runners keep these available whenever the agent may
# act at all, regardless of coach assignment or workflow gates.
DESK_ACTION_NAMES = frozenset(
    {"inspect_problem", "triage_problem", "remember", "recall", "share_note"}
)
# Sub-bundles of the desk: baselines switch these on or off independently.
MEMORY_ACTION_NAMES = frozenset({"remember", "recall", "share_note"})
DESK_READONLY_ACTION_NAMES = frozenset({"inspect_problem", "triage_problem"})
LEADER_ACTION_NAMES = frozenset({"assign_problem"})
# Card-driven structured deliberation; resolved only by the ``otc`` baseline.
DELIBERATION_ACTION_NAMES = frozenset(
    {"propose", "challenge", "provide_evidence", "revise", "decide"}
)
# Bumped whenever the canonical action surface changes shape; recorded in
# contest results so mixed-version comparisons are visible.
# v4: added the ``deliberation`` pack (five actions) for rule-card baselines.
# v5: unified the legacy environment surface onto this registry — ``verify``,
#     the workboard verbs and the workspace helpers became aliases or
#     runtime-tagged specs; ``work`` gained ``problem_id``.
ACTION_SET_VERSION = 5
PACK_NAMES: tuple[str, ...] = (
    "common",
    "deliberation",
    "math",
    "programming",
    "research",
    "resources",
    "workboard",
    "workspace",
)
PACK_ACTION_NAMES: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        pack: frozenset(
            name for name, spec in ACTION_REGISTRY.items() if spec.pack == pack
        )
        for pack in PACK_NAMES
    }
)
# Packs whose actions are contest instruments (calculator, sandbox, search,
# physical resources).  Everything else is the contestant's desk.
TOOL_PACKS: frozenset[str] = frozenset({"math", "programming", "research", "resources"})
# Packs a runtime exposes unconditionally: ``common`` everywhere, plus the
# legacy desk packs when resolving for the environment runtime.
ALWAYS_ON_PACKS: frozenset[str] = frozenset({"common"})
ENV_DESK_PACKS: frozenset[str] = frozenset({"workboard", "workspace"})


def actions_for_runtime(runtime: str) -> frozenset[str]:
    """Canonical action names a runtime implements."""
    return frozenset(
        name for name, spec in ACTION_REGISTRY.items() if runtime in spec.runtimes
    )


def _hopeless_transform(arguments: dict[str, Any]) -> dict[str, Any]:
    """``mark_hopeless <item> | <reason>`` / ``<item> | undo`` -> triage."""
    reason = str(arguments.pop("reason", "") or "").strip()
    if reason.lower() in {"undo", "clear", "false", "reopen"}:
        return {**arguments, "priority": "normal", "reason": ""}
    return {**arguments, "priority": "hopeless", "reason": reason}


@dataclass(frozen=True)
class LegacyAlias:
    """An old wire name mapped onto a canonical action.

    ``fields`` overrides the canonical spec's ``legacy_payload_fields`` for the
    ``|``-split of a text payload; ``defaults`` seeds fixed arguments; and
    ``transform`` rewrites the parsed arguments when a rename is not enough.
    """

    canonical: str
    fields: tuple[str, ...] | None = None
    defaults: Mapping[str, Any] = field(default_factory=dict)
    transform: Callable[[dict[str, Any]], dict[str, Any]] | None = None


# Boundary adapters translate old environment protocol names; the names are
# never registry keys, so canonical dispatch tables stay alias-free.
LEGACY_ALIASES: Mapping[str, LegacyAlias] = MappingProxyType(
    {
        # Original protocol names.
        "submit_final": LegacyAlias("submit", fields=("answer",)),
        "sleep": LegacyAlias("rest", fields=("reason",)),
        "write_scratchpad": LegacyAlias("work", fields=("content",)),
        # Programming self-check folded into the desk inspection action.
        "verify": LegacyAlias("inspect_problem", fields=("focus",)),
        # Workboard verbs with a direct desk counterpart.
        "list_problems": LegacyAlias("inspect_problem", fields=()),
        "open_problem": LegacyAlias("inspect_problem", fields=("problem_id",)),
        "claim_problem": LegacyAlias("select_problem", fields=("problem_id",)),
        "release_problem": LegacyAlias("skip_problem", fields=("reason",)),
        "submit_problem": LegacyAlias("work", fields=("problem_id", "content")),
        "set_priority": LegacyAlias("triage_problem", fields=("problem_id", "priority")),
        "mark_hopeless": LegacyAlias(
            "triage_problem",
            fields=("problem_id", "reason"),
            transform=_hopeless_transform,
        ),
        # Workspace verbs.
        "publish_memory": LegacyAlias("share_note", fields=("note_id",)),
        "message_group": LegacyAlias("direct_message", fields=("recipients", "content")),
    }
)
LEGACY_ACTION_ALIASES: Mapping[str, str] = MappingProxyType(
    {alias: item.canonical for alias, item in LEGACY_ALIASES.items()}
)
LEGACY_ENV_ACTIONS = LEGACY_ACTION_ALIASES
_ALIASES_BY_CANONICAL: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        canonical: frozenset(
            alias for alias, target in LEGACY_ACTION_ALIASES.items() if target == canonical
        )
        for canonical in set(LEGACY_ACTION_ALIASES.values())
    }
)


def canonical_action_name(name: str) -> str:
    """Map a legacy wire name onto its registry name (identity otherwise)."""
    key = str(name or "").strip().lower()
    return LEGACY_ACTION_ALIASES.get(key, key)


def action_name_variants(name: str) -> frozenset[str]:
    """Every spelling of one action: the canonical name plus its aliases.

    Rule cards, phase allowlists and communication budgets were written
    against whichever spelling their author knew; membership tests should
    accept any of them.
    """
    canonical = canonical_action_name(name)
    return frozenset({canonical, *_ALIASES_BY_CANONICAL.get(canonical, ())})


def action_matches(name: str, names: Iterable[str]) -> bool:
    """``name in names`` that is blind to legacy spellings on either side."""
    variants = action_name_variants(name)
    return any(canonical_action_name(item) in variants for item in names)

COMPETITION_TOOL_REGISTRY: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "purple_comet": ("use_calculator",),
        "fyziklani": ("use_calculator", "web_search"),
        "iiot": ("execute_code",),
        "icpc": ("execute_code",),
        "codeforces": ("execute_code",),
        "mcm": ("execute_code", "web_search"),
        "icm": ("execute_code", "web_search"),
        "ieo_business_case": ("web_search",),
        "jessup": ("web_search",),
        "iypt": ("web_search", "execute_code", "use_calculator"),
        "ijso_practical": ("use_calculator", "read_lab_equipment"),
        "ioaa_group": ("use_calculator", "read_star_chart"),
        "iol_team": (),
        "arml_power": (),
        "arml_national_team": (),
        "arml_national_power": (),
        "arml_local": (),
        "hmmt_team": (),
        "hmmt_guts": (),
        "wsc_writing": (),
    }
)
COMPETITION_ACTION_REGISTRY: Mapping[str, tuple[str, ...]] = MappingProxyType(
    {
        "icpc": ("submit_code",),
        "iiot": ("submit_code",),
        "codeforces": ("submit_code",),
    }
)

_PROGRAMMING_COMPETITIONS = frozenset({"icpc", "iiot", "codeforces"})
_MATH_COMPETITIONS = frozenset(
    {
        "arml_local",
        "arml_national_team",
        "purple_comet",
        "hmmt_guts",
        "hmmt_team",
        "wmtc",
        "fyziklani",
        "ijso_practical",
        "ioaa_group",
        "iypt",
    }
)
_RESEARCH_COMPETITIONS = frozenset(
    {"fyziklani", "mcm", "icm", "ieo_business_case", "jessup", "iypt"}
)
_RESOURCE_ACTIONS = PACK_ACTION_NAMES["resources"]


def _string_set(value: Any) -> set[str]:
    if value is None:
        return set()
    if isinstance(value, str):
        return {value.strip()} if value.strip() else set()
    if isinstance(value, Mapping):
        return {str(key).strip() for key, enabled in value.items() if enabled}
    try:
        return {str(item).strip() for item in value if str(item).strip()}
    except TypeError:
        text = str(value).strip()
        return {text} if text else set()


def _requirement_tokens(requirements: Any) -> set[str]:
    if not isinstance(requirements, Mapping):
        return _string_set(requirements)
    tokens: set[str] = set()
    for key in (
        "required_packs",
        "packs",
        "required_tools",
        "tools",
        "required_actions",
        "actions",
        "capabilities",
    ):
        tokens.update(_string_set(requirements.get(key)))
    return tokens


def _requested_names(
    competition: str,
    task_type: str | None,
    requirements: Any,
    capabilities: set[str],
    runtime: str | None = None,
) -> tuple[set[str], set[str]]:
    implemented = actions_for_runtime(runtime) if runtime else set(ACTION_REGISTRY)
    on_packs = ALWAYS_ON_PACKS | (ENV_DESK_PACKS if runtime == "env" else frozenset())
    always_on = {
        name
        for pack in on_packs
        for name in PACK_ACTION_NAMES[pack]
        if name in implemented
    }
    names = set(always_on)
    packs: set[str] = set()
    competition_key = (competition or "").strip().lower()
    task_key = (task_type or "").strip().lower()

    if competition_key in _PROGRAMMING_COMPETITIONS or any(
        marker in task_key for marker in ("program", "coding", "algorithm")
    ):
        packs.add("programming")
    if competition_key in _MATH_COMPETITIONS or any(
        marker in task_key for marker in ("math", "proof", "numeric")
    ):
        packs.add("math")
    if competition_key in _RESEARCH_COMPETITIONS or any(
        marker in task_key for marker in ("research", "case_study", "legal")
    ):
        packs.add("research")

    tokens = _requirement_tokens(requirements) | capabilities
    # ``deliberation`` is granted by a competition's rule card, never by a
    # benchmark capability token.
    known_packs = (
        set(PACK_ACTION_NAMES) - ALWAYS_ON_PACKS - ENV_DESK_PACKS - {"resources", "deliberation"}
    )
    packs.update(tokens & known_packs)
    names.update(tokens & set(ACTION_REGISTRY))
    for pack in packs:
        names.update(PACK_ACTION_NAMES[pack])

    # Use the same contest tool allowlist as the environment. Capabilities may
    # request tools, but must not grant tools forbidden by a known contest.
    from contest_rules import get_contest_rules
    rules = get_contest_rules(competition_key)
    if competition_key in COMPETITION_TOOL_REGISTRY or rules is not None:
        permitted = set(COMPETITION_TOOL_REGISTRY.get(competition_key, ()))
        if not permitted and rules is not None:
            permitted.update(rules.encoded_tools)
        permitted.update(COMPETITION_ACTION_REGISTRY.get(competition_key, ()))
        names = (names & always_on) | (permitted - _RESOURCE_ACTIONS)

    # Physical resources are capabilities, not entitlements inferred from a
    # contest, task type, generic resources pack, or benchmark requirement.
    names.difference_update(_RESOURCE_ACTIONS)
    resources = _RESOURCE_ACTIONS & capabilities
    if competition_key in COMPETITION_TOOL_REGISTRY or rules is not None:
        resources &= permitted
    names.update(resources)
    return names & implemented, tokens


def _handler_markers(
    registered_handlers: Mapping[str, Callable[..., Any] | Any]
    | Iterable[str]
    | None,
) -> set[str]:
    if registered_handlers is None:
        return {
            marker
            for spec in ACTION_REGISTRY.values()
            for marker in (spec.name, spec.handler_marker)
        }
    if isinstance(registered_handlers, Mapping):
        return {str(name) for name in registered_handlers}
    return {str(name) for name in registered_handlers}


def resolve_actions_with_diagnostics(
    competition: str | None = None,
    task_type: str | None = None,
    benchmark_requirements: Any = None,
    declared_capabilities: Iterable[str] | Mapping[str, bool] | None = None,
    registered_handlers: Mapping[str, Callable[..., Any] | Any]
    | Iterable[str]
    | None = None,
    *,
    competition_id: str | None = None,
    system_variant: str | None = None,
    runtime: str | None = None,
) -> Resolution:
    """Resolve available actions without depending on agent-system strategy.

    ``system_variant`` is accepted as migration-friendly context but is
    intentionally ignored.  It can therefore never fork the action surface.
    ``runtime`` (``"env"`` or ``"session"``) restricts the result to actions
    that runtime implements; ``None`` returns the full canonical surface.
    """

    del system_variant
    if runtime is not None and runtime not in ALL_RUNTIMES:
        raise ValueError(f"unknown runtime {runtime!r}; expected one of {RUNTIMES}")
    competition_key = competition if competition is not None else competition_id or ""
    capabilities = _string_set(declared_capabilities)
    requested, tokens = _requested_names(
        competition_key, task_type, benchmark_requirements, capabilities, runtime
    )
    known_tokens = set(ACTION_REGISTRY) | set(PACK_ACTION_NAMES)
    unknown = capabilities - known_tokens
    # Unknown benchmark tokens are also useful diagnostics when requirements
    # use one of the supported action/pack fields.
    unknown.update(tokens - known_tokens)

    handler_markers = _handler_markers(registered_handlers)
    available: set[ActionSpec] = set()
    missing: set[str] = set()
    for name in requested:
        spec = ACTION_REGISTRY[name]
        if spec.name in handler_markers or spec.handler_marker in handler_markers:
            available.add(spec)
        else:
            missing.add(name)
    return Resolution(
        actions=frozenset(available),
        unknown_capabilities=frozenset(unknown),
        missing_handlers=frozenset(missing),
    )


def resolve_actions(
    competition: str | None = None,
    task_type: str | None = None,
    benchmark_requirements: Any = None,
    declared_capabilities: Iterable[str] | Mapping[str, bool] | None = None,
    registered_handlers: Mapping[str, Callable[..., Any] | Any]
    | Iterable[str]
    | None = None,
    *,
    competition_id: str | None = None,
    system_variant: str | None = None,
    runtime: str | None = None,
) -> frozenset[ActionSpec]:
    """Return the immutable set of executable action contracts."""

    return resolve_actions_with_diagnostics(
        competition=competition,
        task_type=task_type,
        benchmark_requirements=benchmark_requirements,
        declared_capabilities=declared_capabilities,
        registered_handlers=registered_handlers,
        competition_id=competition_id,
        system_variant=system_variant,
        runtime=runtime,
    ).actions


def resolve_action_names(*args: Any, **kwargs: Any) -> frozenset[str]:
    """Convenience adapter for parsers that only need canonical names."""

    return frozenset(spec.name for spec in resolve_actions(*args, **kwargs))


def _coerce_specs(
    actions: Iterable[ActionSpec | str],
) -> tuple[ActionSpec, ...]:
    specs = []
    for action in actions:
        spec = ACTION_REGISTRY[action] if isinstance(action, str) else action
        specs.append(spec)
    return tuple(sorted(specs, key=lambda item: item.name))


def render_action_schema(
    actions: Iterable[ActionSpec | str],
) -> dict[str, Any]:
    """Render a strict tagged-union JSON schema for structured model output."""

    variants = []
    for spec in _coerce_specs(actions):
        variants.append(
            {
                "type": "object",
                "properties": {
                    "action": {"const": spec.name},
                    "arguments": dict(spec.argument_schema),
                },
                "required": ["action", "arguments"],
                "additionalProperties": False,
            }
        )
    return {"type": "object", "oneOf": variants}


def render_function_tools(
    actions: Iterable[ActionSpec | str],
) -> list[dict[str, Any]]:
    """Render provider-native custom function definitions from ActionSpecs."""
    return [
        {
            "type": "function",
            "name": spec.name,
            "description": spec.description,
            "parameters": dict(spec.argument_schema),
            # OpenAI-style strict schemas require every property to be
            # required. Keep optional-argument actions valid by disabling
            # strict mode only for those functions.
            "strict": all(argument.required for argument in spec.arguments),
        }
        for spec in _coerce_specs(actions)
    ]


def render_action_instructions(actions: Iterable[ActionSpec | str]) -> str:
    """Render compact prompt text from the same specs used for validation."""

    lines = ["Available actions:"]
    for spec in _coerce_specs(actions):
        arguments = ", ".join(
            f"{argument.name}{'' if argument.required else '?'}"
            for argument in spec.arguments
        )
        signature = f"{spec.name}({arguments})"
        lines.append(f"- {signature}: {spec.description}")
    return "\n".join(lines)


_PYTHON_TYPES: Mapping[str, type[Any] | tuple[type[Any], ...]] = MappingProxyType(
    {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "object": dict,
        "array": list,
    }
)


def validate_action_payload(
    action: str | ActionSpec,
    payload: Mapping[str, Any] | Any,
) -> tuple[str, ...]:
    """Validate action arguments; return all errors instead of raising."""

    spec = ACTION_REGISTRY.get(action) if isinstance(action, str) else action
    if spec is None:
        return (f"unknown action: {action}",)
    if not isinstance(payload, Mapping):
        return (f"{spec.name} arguments must be an object",)

    errors: list[str] = []
    arguments = {argument.name: argument for argument in spec.arguments}
    for argument in spec.arguments:
        if argument.required and argument.name not in payload:
            errors.append(f"missing required argument: {argument.name}")
    for name, value in payload.items():
        argument = arguments.get(name)
        if argument is None:
            errors.append(f"unexpected argument: {name}")
            continue
        expected = _PYTHON_TYPES[argument.type]
        valid = isinstance(value, expected)
        if argument.type in {"integer", "number"} and isinstance(value, bool):
            valid = False
        if not valid:
            errors.append(
                f"argument {name} must have JSON type {argument.type}"
            )
        elif argument.type == "array":
            if not value:
                errors.append(f"argument {name} must contain at least one item")
            element_type = _PYTHON_TYPES[argument.items or "string"]
            for item in value:
                if not isinstance(item, element_type):
                    errors.append(
                        f"argument {name} items must have JSON type "
                        f"{argument.items or 'string'}"
                    )
                    break
                if argument.enum and item not in argument.enum:
                    errors.append(
                        f"argument {name} items must be one of {list(argument.enum)!r}"
                    )
                    break
        elif argument.enum and value not in argument.enum:
            errors.append(
                f"argument {name} must be one of {list(argument.enum)!r}"
            )
    return tuple(errors)


def validate_registry(
    registry: Mapping[str, ActionSpec] = ACTION_REGISTRY,
) -> tuple[str, ...]:
    """Return registry consistency errors for startup checks and tests."""

    errors: list[str] = []
    seen_handlers: set[str] = set()
    for name, spec in registry.items():
        if name != spec.name:
            errors.append(f"registry key {name!r} does not match {spec.name!r}")
        if not name or not name.replace("_", "").isalnum():
            errors.append(f"invalid action name: {name!r}")
        argument_names = [argument.name for argument in spec.arguments]
        if len(argument_names) != len(set(argument_names)):
            errors.append(f"duplicate argument in action: {name}")
        if not spec.handler_name:
            errors.append(f"missing handler marker: {name}")
        seen_handlers.add(spec.handler_name)
        if spec.evaluator and not spec.evaluator_name:
            errors.append(f"evaluator action lacks evaluator name: {name}")
        if spec.budget.submission_attempts and not spec.submission:
            errors.append(f"submission budget on non-submission action: {name}")
        if not spec.runtimes or not spec.runtimes <= ALL_RUNTIMES:
            errors.append(f"invalid runtimes for action {name}: {sorted(spec.runtimes)}")
        if spec.pack not in PACK_NAMES:
            errors.append(f"unknown pack {spec.pack!r} on action {name}")
        if spec.legacy_payload_fields is not None:
            unknown_fields = set(spec.legacy_payload_fields) - set(argument_names)
            if unknown_fields:
                errors.append(
                    f"legacy payload fields not in arguments for {name}: "
                    f"{sorted(unknown_fields)}"
                )
    del seen_handlers
    if {
        name for name, spec in registry.items() if spec.pack == "common"
    } != set(COMMON_ACTION_NAMES):
        errors.append("common pack does not match COMMON_ACTION_NAMES")
    for alias, item in LEGACY_ALIASES.items():
        if alias in registry:
            errors.append(f"legacy alias {alias!r} shadows a registered action")
        target = registry.get(item.canonical)
        if target is None:
            errors.append(f"legacy alias {alias!r} targets unknown action {item.canonical!r}")
            continue
        argument_names = {argument.name for argument in target.arguments}
        bad_fields = set(item.fields or ()) - argument_names
        if bad_fields:
            errors.append(
                f"legacy alias {alias!r} splits into unknown fields {sorted(bad_fields)}"
            )
        bad_defaults = set(item.defaults) - argument_names
        if bad_defaults:
            errors.append(
                f"legacy alias {alias!r} defaults unknown fields {sorted(bad_defaults)}"
            )
    return tuple(errors)


def dispatch_environment_action(
    environment: Any,
    *,
    agent_name: str,
    action_name: str,
    payload: str,
) -> Any:
    """Dispatch canonical task-pack actions against an environment runtime.

    ``NotImplemented`` means the action belongs to the legacy collaboration
    layer rather than this registry.
    """
    if action_name == "submit_code":
        duplicate_error = environment._unchanged_failed_source_error(payload)
        if duplicate_error:
            return duplicate_error
        result = environment._submit_code(payload, agent_name=agent_name)
        environment._record_shared_code_submission(agent_name, payload, result)
        return result
    if action_name == "use_calculator":
        return environment._run_calculator(payload)
    if action_name == "execute_code":
        return environment._run_code(payload)
    if action_name == "web_search":
        return environment._run_web_search(payload)
    resource_roles = {
        "read_lab_equipment": "lab",
        "read_star_chart": "star",
    }
    role = resource_roles.get(action_name)
    if role is not None:
        loaded = environment._tool_asset_text(role, payload)
        return (
            f"[{action_name}]\n{loaded}"
            if loaded
            else f"[{action_name}] No executable fixture for {payload!r}."
        )
    return NotImplemented


__all__ = [
    "ACTION_REGISTRY",
    "ACTION_SET_VERSION",
    "ALL_RUNTIMES",
    "ALWAYS_ON_PACKS",
    "COMMON_ACTION_NAMES",
    "DELIBERATION_ACTION_NAMES",
    "DESK_ACTION_NAMES",
    "DESK_READONLY_ACTION_NAMES",
    "ENV_DESK_PACKS",
    "ENV_ONLY",
    "LEADER_ACTION_NAMES",
    "MEMORY_ACTION_NAMES",
    "PACK_ACTION_NAMES",
    "PACK_NAMES",
    "RUNTIMES",
    "SESSION_ONLY",
    "TOOL_PACKS",
    "LEGACY_ACTION_ALIASES",
    "LEGACY_ALIASES",
    "LEGACY_ENV_ACTIONS",
    "LegacyAlias",
    "COMPETITION_TOOL_REGISTRY",
    "COMPETITION_ACTION_REGISTRY",
    "ActionSpec",
    "ArgumentSpec",
    "BudgetSemantics",
    "Resolution",
    "action_matches",
    "action_name_variants",
    "actions_for_runtime",
    "canonical_action_name",
    "render_action_instructions",
    "render_function_tools",
    "render_action_schema",
    "resolve_action_names",
    "resolve_actions",
    "resolve_actions_with_diagnostics",
    "validate_action_payload",
    "validate_registry",
    "dispatch_environment_action",
]
