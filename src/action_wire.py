"""One wire format in, one canonical invocation out.

Agents reach the registry through two encodings:

* typed — ``{"action": "triage_problem", "arguments": {...}}`` (contest
  sessions, provider-native function calls);
* text — ``ACTION: set_priority | PAYLOAD: P3 | high`` (the original
  environment protocol, still what the vanilla baseline emits).

Both runtimes used to parse these separately and with their own spellings.
:func:`normalize_invocation` is the single entry point: it resolves legacy
aliases, splits ``|``-separated text payloads by the spec's declared field
order, coerces obvious scalar/array mismatches, and validates against the
registry.  Handlers downstream only ever see canonical names and argument
dictionaries.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Iterable, Mapping

from tool_registry import (
    ACTION_REGISTRY,
    LEGACY_ALIASES,
    ActionSpec,
    canonical_action_name,
    validate_action_payload,
)

__all__ = [
    "Invocation",
    "normalize_invocation",
    "render_text_signature",
    "render_text_protocol_lines",
    "split_legacy_payload",
]

# Signatures the generic renderer gets wrong because the split rule is
# special-cased in ``_PARTIAL_FILL``.
_SIGNATURE_OVERRIDES: Mapping[str, str] = {
    "recall": "[<problem_id> |] <query>",
}

# When a text payload has fewer ``|`` parts than the spec declares, parts are
# assigned to required fields first, then optional ones in order.  A few
# actions read more naturally the other way round; list them here.
_PARTIAL_FILL: Mapping[str, Mapping[int, tuple[str, ...]]] = {
    # ``recall <query>`` is far more common than ``recall <item>``.
    "recall": {1: ("query",)},
}

_ARRAY_SPLIT = re.compile(r"[,;\n]+|\s{2,}")


@dataclass(frozen=True)
class Invocation:
    """A canonical action call, or the reasons it could not become one."""

    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    invoked_as: str = ""
    spec: ActionSpec | None = None
    errors: tuple[str, ...] = ()
    text_payload: str = ""

    @property
    def ok(self) -> bool:
        return not self.errors and self.spec is not None

    @property
    def is_alias(self) -> bool:
        return bool(self.invoked_as) and self.invoked_as != self.action


def split_legacy_payload(
    spec: ActionSpec,
    fields: tuple[str, ...] | None,
    text: str,
) -> dict[str, Any]:
    """Split a ``|``-separated text payload into the spec's arguments."""
    text = str(text or "").strip()
    if fields is None:
        # No declared layout: the whole payload is the first (required) field.
        if not spec.arguments:
            return {}
        target = next(
            (argument for argument in spec.arguments if argument.required),
            spec.arguments[0],
        )
        return {target.name: text} if text else {}
    if not fields:
        return {}
    if len(fields) == 1:
        return {fields[0]: text} if text else {}
    if not text:
        return {}
    parts = [part.strip() for part in text.split("|", len(fields) - 1)]
    if len(parts) == len(fields):
        return {name: value for name, value in zip(fields, parts) if value}
    override = _PARTIAL_FILL.get(spec.name, {}).get(len(parts))
    if override is not None:
        return {name: value for name, value in zip(override, parts) if value}
    by_name = {argument.name: argument for argument in spec.arguments}
    ordered = [name for name in fields if by_name[name].required] + [
        name for name in fields if not by_name[name].required
    ]
    return {name: value for name, value in zip(ordered, parts) if value}


def render_text_signature(spec: ActionSpec) -> str:
    """How the text protocol spells this action's PAYLOAD, e.g. ``[<problem_id> |] <content>``."""
    if spec.name in _SIGNATURE_OVERRIDES:
        return _SIGNATURE_OVERRIDES[spec.name]
    fields = spec.legacy_payload_fields
    if fields is None:
        fields = (spec.primary_argument,) if spec.primary_argument else ()
    if not fields:
        return ""
    by_name = {argument.name: argument for argument in spec.arguments}
    rendered = ""
    for index, name in enumerate(fields):
        argument = by_name[name]
        token = "|".join(argument.enum) if argument.enum else f"<{name}>"
        last = index == len(fields) - 1
        later_required = any(by_name[later].required for later in fields[index + 1 :])
        if argument.required:
            if rendered and not rendered.endswith("|] "):
                rendered += " | "
            rendered += token
        elif not last and later_required:
            rendered += f"[{token} |] "
        elif not last:
            rendered += f"[{token}] "
        else:
            rendered += f" [| {token}]" if rendered.strip() else f"[{token}]"
    return " ".join(rendered.split())


def render_text_protocol_lines(
    specs: Iterable[ActionSpec],
    *,
    notes: Mapping[str, str] | None = None,
) -> list[str]:
    """One ``- name — PAYLOAD: ... — description`` line per spec, in the order given."""
    lines = []
    for spec in specs:
        signature = render_text_signature(spec)
        payload = f" — PAYLOAD: {signature}" if signature else ""
        note = (notes or {}).get(spec.name)
        description = note if note else spec.description
        lines.append(f"- {spec.name}{payload} — {description}")
    return lines


def _coerce_arguments(spec: ActionSpec, arguments: dict[str, Any]) -> dict[str, Any]:
    """Repair the mismatches a text protocol cannot express (arrays, enums)."""
    by_name = {argument.name: argument for argument in spec.arguments}
    coerced: dict[str, Any] = {}
    for name, value in arguments.items():
        argument = by_name.get(name)
        if argument is None:
            coerced[name] = value
            continue
        if argument.type == "array" and isinstance(value, str):
            value = [part.strip() for part in _ARRAY_SPLIT.split(value) if part.strip()]
        elif argument.type == "string" and value is not None and not isinstance(value, str):
            value = str(value)
        if argument.enum and isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in argument.enum:
                value = lowered
        if isinstance(value, str):
            value = value.strip()
            if not value and not argument.required:
                continue
        coerced[name] = value
    return coerced


def normalize_invocation(
    name: str,
    payload: Mapping[str, Any] | str | None,
    *,
    allowed: Iterable[str] | None = None,
    specs: Mapping[str, ActionSpec] | None = None,
    coerce: bool = True,
) -> Invocation:
    """Resolve any wire spelling of an action into a validated canonical call.

    ``payload`` is either an argument mapping (typed protocol) or the raw
    text after ``PAYLOAD:`` (legacy protocol).  ``allowed`` optionally
    restricts the result to a set of action names, matched alias-blind.
    """
    invoked = str(name or "").strip().lower()
    alias = LEGACY_ALIASES.get(invoked)
    canonical = alias.canonical if alias else canonical_action_name(invoked)
    spec = (ACTION_REGISTRY if specs is None else specs).get(canonical)
    text_payload = payload if isinstance(payload, str) else ""
    if spec is None:
        return Invocation(
            action=canonical,
            invoked_as=invoked,
            errors=((f"action {invoked!r} is not available" if specs is not None
                     else f"unknown action: {invoked or '(empty)'}"),),
            text_payload=text_payload,
        )

    if isinstance(payload, Mapping):
        arguments = dict(payload)
    else:
        fields = alias.fields if alias and alias.fields is not None else spec.legacy_payload_fields
        arguments = split_legacy_payload(spec, fields, text_payload)
    if alias is not None:
        for key, value in alias.defaults.items():
            arguments.setdefault(key, value)
        if alias.transform is not None:
            arguments = alias.transform(arguments)
    if coerce:
        arguments = _coerce_arguments(spec, arguments)

    errors = list(validate_action_payload(spec, arguments))
    if allowed is not None:
        permitted = {canonical_action_name(item) for item in allowed}
        if canonical not in permitted:
            errors.append(f"action not available here: {invoked}")
    return Invocation(
        action=canonical,
        arguments=arguments,
        invoked_as=invoked,
        spec=spec,
        errors=tuple(errors),
        text_payload=text_payload,
    )
