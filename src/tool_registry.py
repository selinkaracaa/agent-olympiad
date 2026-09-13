"""Typed action registry and capability resolver.

Public interface for common, memory, coach and task_specific modules.
Both runtimes consume the same definitions, schemas, validation and resolution.
Capability packs remain permission metadata, not additional ownership modules.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Callable, Iterable, Mapping

from action_modules import ACTION_REGISTRY, MODULE_ACTION_NAMES, TOOL_ACTION_NAMES
from action_modules.contracts import (
    ActionModule, ActionSpec, ArgumentSpec, BudgetSemantics, Resolution,
    Visibility, JsonType, Runtime, RUNTIMES, ALL_RUNTIMES, ENV_ONLY, SESSION_ONLY,
)
from action_modules.task_specific import (
    _PROGRAMMING_COMPETITIONS, _MATH_COMPETITIONS, _RESEARCH_COMPETITIONS,
    _RESOURCE_ACTIONS,
)

COMMON_ACTION_NAMES = MODULE_ACTION_NAMES["common"]
COMMON_TOOL_NAMES = COMMON_ACTION_NAMES & TOOL_ACTION_NAMES
SPECIFIC_TOOL_NAMES = MODULE_ACTION_NAMES["task_specific"] & TOOL_ACTION_NAMES
# Initial capability surface, before optional module and role filtering.
BASE_ACTION_NAMES = frozenset(
    name for name, spec in ACTION_REGISTRY.items()
    if not spec.is_tool and spec.pack == "common"
)
# Read-only or personal bookkeeping actions that never mutate answers or
# submissions. Contest runners keep these available whenever the agent may
# act at all, regardless of coach assignment or workflow gates.
DESK_ACTION_NAMES = frozenset(
    {"inspect_problem", "triage_problem", "remember", "recall", "share_note"}
)
# Sub-bundles of the desk: baselines switch these on or off independently.
MEMORY_ACTION_NAMES = MODULE_ACTION_NAMES["memory"]
DESK_READONLY_ACTION_NAMES = frozenset({"inspect_problem", "triage_problem"})
# Explicit bookkeeping belongs to the common core in every contest setting.
DESK_BOOKKEEPING_ACTION_NAMES = frozenset({"check_budget", "query_rules"})
LEADER_ACTION_NAMES = frozenset({"assign_problem"})
# Card-driven structured deliberation; resolved only by the ``otc`` baseline.
DELIBERATION_ACTION_NAMES = frozenset(
    {"propose", "challenge", "provide_evidence", "revise", "decide"}
)
# v8 separates tool execution from module ownership and adds render_pdf.
# Bumped whenever the canonical action surface changes shape; recorded in
# contest results so mixed-version comparisons are visible.
# v4: added the ``deliberation`` pack (five actions) for rule-card baselines.
# v5: unified the legacy environment surface onto this registry — ``verify``,
#     the workboard verbs and the workspace helpers became aliases or
#     runtime-tagged specs; ``work`` gained ``problem_id``.
# v6: every action is implemented by both runtimes. ``verify_problem`` and
#     ``write_private_notes`` became aliases (``review_answer`` with an
#     optional ``version_hash``; ``remember``); ``check_budget`` and
#     ``query_rules`` joined ``common``; the env gained ``assign_problem``,
#     ``request_review`` and ``finish_contest``.
# v7: the legacy alias layer was removed. Only canonical names are accepted on
#     the wire; ``sleep``, ``submit_final``, ``write_scratchpad``,
#     ``write_private_notes``, ``verify_problem``, ``message_group`` and the
#     old workboard verbs are unknown actions. Rule cards were rewritten.
ACTION_SET_VERSION = 8
# Ownership and render availability changed; existing 29 argument schemas remain.
ACTION_MODULE_VERSION = 3
PACK_NAMES: tuple[str, ...] = (
    "common",
    "deliberation",
    "math",
    "programming",
    "research",
    "resources",
    "artifacts",
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
TOOL_PACKS: frozenset[str] = frozenset(spec.pack for spec in ACTION_REGISTRY.values() if spec.is_tool)
# Packs a runtime exposes unconditionally.
ALWAYS_ON_PACKS: frozenset[str] = frozenset({"common"})


def competition_permissions(competition: str, *, rule_card=None, task_type: str = "") -> set[str] | None:
    """One permission source for both runtimes; ownership never grants tools.

    A present card is authoritative, including an empty allowlist. The audit
    supplies a fallback only for competitions without a card. PDF rendering is
    a delivery capability for document/slide contracts, independent of solver
    access to calculators, search and code execution.
    """
    from rules.loader import load_rule_card
    from artifact_contract import delivery_route
    from contest_rules import get_contest_rules

    card = rule_card if rule_card is not None else load_rule_card(competition)
    if card is not None:
        if card.competition_id != competition:
            raise ValueError("Permission card belongs to another competition")
        permitted = set(card.allowed_tools)
        if delivery_route(card) in {"document", "slides"}:
            permitted.add("render_pdf")
    else:
        rules = get_contest_rules(competition)
        if rules is None:
            return None
        permitted = set(rules.encoded_tools)
    if "execute_code" in permitted and (
        competition in _PROGRAMMING_COMPETITIONS
        or any(marker in task_type.lower() for marker in ("program", "coding", "algorithm"))
    ):
        permitted.add("submit_code")
    return permitted


def _competition_views():
    """Compatibility views derived from cards, never hand-maintained lists."""
    from rules.loader import DEFAULT_RULES_ROOT
    from rules.storage import iter_rule_card_ids
    permissions = {name: competition_permissions(name) or set()
                   for name in iter_rule_card_ids(DEFAULT_RULES_ROOT)}
    return (
        MappingProxyType({name: tuple(sorted(names & TOOL_ACTION_NAMES))
                          for name, names in permissions.items()}),
        MappingProxyType({name: tuple(sorted(names & {"submit_code"}))
                          for name, names in permissions.items()}),
    )


COMPETITION_TOOL_REGISTRY, COMPETITION_ACTION_REGISTRY = _competition_views()


def actions_for_runtime(runtime: str) -> frozenset[str]:
    """Canonical action names a runtime implements."""
    return frozenset(
        name for name, spec in ACTION_REGISTRY.items() if runtime in spec.runtimes
    )


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
    permitted_actions: set[str] | None = None,
) -> tuple[set[str], set[str]]:
    implemented = actions_for_runtime(runtime) if runtime else set(ACTION_REGISTRY)
    always_on = {
        name
        for pack in ALWAYS_ON_PACKS
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
    known_packs = set(PACK_ACTION_NAMES) - ALWAYS_ON_PACKS - {"resources", "deliberation"}
    packs.update(tokens & known_packs)
    names.update(tokens & set(ACTION_REGISTRY))
    for pack in packs:
        names.update(PACK_ACTION_NAMES[pack])

    # Use the same contest tool allowlist as the environment. Capabilities may
    # request tools, but must not grant tools forbidden by a known contest.
    permitted = (permitted_actions if permitted_actions is not None else
                 competition_permissions(competition_key, task_type=task_key))
    if permitted is not None:
        names = always_on | ((permitted & set(ACTION_REGISTRY)) - _RESOURCE_ACTIONS)

    # Physical resources are capabilities, not entitlements inferred from a
    # contest, task type, generic resources pack, or benchmark requirement.
    names.difference_update(_RESOURCE_ACTIONS)
    resources = _RESOURCE_ACTIONS & capabilities
    if permitted is not None:
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
    permitted_actions: Iterable[str] | None = None,
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
        competition_key, task_type, benchmark_requirements, capabilities, runtime,
        set(permitted_actions) if permitted_actions is not None else None,
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
        elif spec.runtimes != ALL_RUNTIMES:
            # v6 invariant: one action vocabulary, implemented on both paths.
            errors.append(f"action {name} is not implemented by every runtime")
        if spec.pack not in PACK_NAMES:
            errors.append(f"unknown pack {spec.pack!r} on action {name}")
        if spec.module not in MODULE_ACTION_NAMES:
            errors.append(f"unknown module {spec.module!r} on action {name}")
        elif name not in MODULE_ACTION_NAMES[spec.module]:
            errors.append(f"incorrect module ownership for action {name}")
        if spec.is_tool and (spec.submission or not spec.budget.tool_calls):
            errors.append(f"invalid tool execution contract for action {name}")
        if spec.text_payload_fields is not None:
            unknown_fields = set(spec.text_payload_fields) - set(argument_names)
            if unknown_fields:
                errors.append(
                    f"text payload fields not in arguments for {name}: "
                    f"{sorted(unknown_fields)}"
                )
    del seen_handlers
    if {
        name for name, spec in registry.items() if spec.module == "common"
    } != set(COMMON_ACTION_NAMES):
        errors.append("common module does not match COMMON_ACTION_NAMES")
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
    if action_name == "render_pdf":
        return environment._run_render_pdf(payload)
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
    "ACTION_MODULE_VERSION",
    "MODULE_ACTION_NAMES",
    "TOOL_ACTION_NAMES",
    "ActionModule",
    "ALL_RUNTIMES",
    "ALWAYS_ON_PACKS",
    "COMMON_ACTION_NAMES",
    "COMMON_TOOL_NAMES",
    "SPECIFIC_TOOL_NAMES",
    "BASE_ACTION_NAMES",
    "competition_permissions",
    "DELIBERATION_ACTION_NAMES",
    "DESK_ACTION_NAMES",
    "DESK_BOOKKEEPING_ACTION_NAMES",
    "DESK_READONLY_ACTION_NAMES",
    "ENV_ONLY",
    "LEADER_ACTION_NAMES",
    "MEMORY_ACTION_NAMES",
    "PACK_ACTION_NAMES",
    "PACK_NAMES",
    "RUNTIMES",
    "SESSION_ONLY",
    "TOOL_PACKS",
    "COMPETITION_TOOL_REGISTRY",
    "COMPETITION_ACTION_REGISTRY",
    "ActionSpec",
    "ArgumentSpec",
    "BudgetSemantics",
    "Resolution",
    "actions_for_runtime",
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
