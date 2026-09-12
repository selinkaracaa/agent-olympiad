import json
import re
from typing import Any, Iterable, Optional

from action_wire import render_text_protocol_lines, normalize_invocation
from tool_registry import (
    ACTION_REGISTRY,
    DELIBERATION_ACTION_NAMES,
    ActionSpec,
    action_matches,
    canonical_action_name,
    validate_action_payload,
)

# The text protocol's prompt is rendered from the registry: names, payload
# layouts and descriptions come from the same ``ActionSpec`` objects the
# environment validates against, so the two can no longer drift.  Only the
# grouping and the contest-rule prose below are hand-written.

_CORE_ACTIONS = ("speak", "work", "rest", "submit")
_BOARD_ACTIONS = (
    "select_problem",
    "skip_problem",
    "inspect_problem",
    "triage_problem",
    "review_answer",
    "verify_problem",
)
_WORKSPACE_ACTIONS = ("remember", "recall", "share_note", "check_budget", "direct_message")

# Runtime-specific phrasing where the registry description is deliberately
# neutral between the two runtimes.
_ENV_NOTES = {
    "work": (
        "Record work for the team. On a board contest: PAYLOAD <problem_id> | <answer> "
        "records that item's answer (and claims it). Without a problem_id: the "
        "answer for the item you hold, or the shared scratchpad when you hold none."
    ),
    "submit": "Submit the team's complete final answer (only when ready).",
    "submit_code": (
        "Judge code; when a remote gateway is configured, submit after local "
        "sample AC and return its verdict (remote AC finalizes)."
    ),
    "inspect_problem": (
        "One item plus its full answer history; with no PAYLOAD, the whole board "
        "(or, in a programming contest, the latest code and run history)."
    ),
    "select_problem": "Take an item; one per agent at a time.",
    "skip_problem": "Hand your current item back (or name one).",
    "review_answer": (
        "Approve or reject the answer version currently recorded for an item "
        "(the version id is shown by inspect_problem)."
    ),
    "share_note": "Share stored notes with the team, e.g. M1, M2.",
    "direct_message": "Message named teammates only.",
    "check_budget": "Turns, tokens, and how much of the board is still blank.",
}

ACTION_INSTRUCTIONS = """\
Respond with ONE of these formats:

1) Plain text — treated as speak (broadcast to all agents).
2) Structured action:
   ACTION: <action_type> | PAYLOAD: <content>
   Multi-field payloads separate fields with " | " in the order shown; [...] is optional.

Available action types:
{core_lines}
{tool_lines}
{workspace_lines}
Rules:
- Use only tools listed as allowed for this contest.
- Each turn you get at most ONE model call: act, or rest.
- submit must contain the complete team answer.
- Be substantive; build on prior discussion."""

BOARD_RULES = """\

Board rules:
- Only the latest recorded answer for an item is graded. An item with nothing
  recorded scores zero, so a considered guess beats leaving it blank.
- Recording an answer already recorded for that item is rejected — it changes
  nothing. Change your approach or move to an item that is still blank.
- There is no correctness feedback in this contest. Reviewing a teammate's
  recorded answer is the only check available."""

ACTION_BLOCK_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*\|\s*PAYLOAD:\s*(?P<payload>.*?)(?=^\s*ACTION:|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

# Legacy single-line matcher kept for reference; multi-line payloads need ACTION_BLOCK_RE.
ACTION_LINE_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*\|\s*PAYLOAD:\s*(?P<payload>.*)$",
    re.IGNORECASE | re.MULTILINE,
)

SCOPED_ACTION_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*"
    r"(?:\|\s*TARGET:\s*(?P<target>.*?)\s*)?"
    r"\|\s*PAYLOAD:\s*(?P<payload>.*)\s*$",
    re.IGNORECASE | re.DOTALL,
)

TOLERANT_SCOPED_ACTION_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*"
    r"(?:(?:\||\r?\n)\s*TARGET:\s*(?P<target>.*?))?"
    r"(?:\||\r?\n)\s*PAYLOAD:\s*(?P<payload>.*)\s*$",
    re.IGNORECASE | re.DOTALL,
)


def _specs(names: Iterable[str]) -> list[ActionSpec]:
    return [ACTION_REGISTRY[name] for name in names if name in ACTION_REGISTRY]


def build_action_instructions(
    allowed_tools: list[str],
    *,
    programming_contest: bool = False,
    structured_deliberation: bool = False,
    private_notes: bool = False,
    board_item_count: int = 0,
    workspace_actions: bool = True,
    rule_card: bool = False,
) -> str:
    """Render the text-protocol action list for one environment from the registry."""
    core = list(_CORE_ACTIONS)
    if programming_contest:
        core.append("submit_code")
        if not board_item_count:
            # No board: inspect_problem is the "re-open my latest code" desk action.
            core.append("inspect_problem")
    core_lines = "\n".join(render_text_protocol_lines(_specs(core), notes=_ENV_NOTES))

    tools = _specs(canonical_action_name(tool) for tool in allowed_tools)
    if tools:
        tool_lines = "\nTools allowed in this contest:\n" + "\n".join(
            render_text_protocol_lines(tools)
        )
    else:
        tool_lines = "(no tools — paper and pencil only)"

    sections: list[str] = []
    if board_item_count:
        sections.append(
            f"\nProblem board ({board_item_count} items — the team's shared answer sheet):\n"
            + "\n".join(render_text_protocol_lines(_specs(_BOARD_ACTIONS), notes=_ENV_NOTES))
            + BOARD_RULES
        )
    if workspace_actions:
        workspace = list(_WORKSPACE_ACTIONS)
        if rule_card:
            workspace.append("query_rules")
        sections.append(
            "\nShared workspace:\n"
            + "\n".join(render_text_protocol_lines(_specs(workspace), notes=_ENV_NOTES))
        )
    rendered = ACTION_INSTRUCTIONS.format(
        core_lines=core_lines,
        tool_lines=tool_lines,
        workspace_lines="\n".join(sections),
    )
    additions: list[str] = []
    if private_notes:
        additions.extend(render_text_protocol_lines(_specs(["write_private_notes"])))
    if structured_deliberation:
        additions.append(
            "- propose/challenge/provide_evidence/revise/decide — structured "
            "deliberation; targeted payloads use 'P<number> | <content>'"
        )
        additions.extend(
            render_text_protocol_lines(_specs(sorted(DELIBERATION_ACTION_NAMES)))
        )
    if additions:
        rendered += "\n" + "\n".join(additions)
    return rendered


def parse_agent_response(response: str) -> list[tuple[str, str]]:
    """Parse an LLM response into (action_type, payload) pairs."""
    if not response or not response.strip():
        return [("speak", "(empty response)")]

    matches = list(ACTION_BLOCK_RE.finditer(response.strip()))
    if not matches:
        return [("speak", response.strip())]

    actions = []
    for match in matches:
        action = match.group("action").strip().lower()
        payload = match.group("payload").strip()
        actions.append((action, payload))
    return actions


def parse_typed_action(
    response: str,
    allowed_actions: Iterable[ActionSpec],
) -> tuple[str | None, dict[str, Any], str | None]:
    """Parse one strict registry-backed JSON action."""
    text = (response or "").strip()
    if not text:
        return None, {}, "empty response"
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        return None, {}, f"response must be exactly one JSON action object: {exc.msg}"
    if not isinstance(payload, dict) or set(payload) != {"action", "arguments"}:
        return None, {}, "action object must contain only action and arguments"
    action = payload.get("action")
    arguments = payload.get("arguments")
    if not isinstance(action, str):
        return None, {}, "action must be a string"
    return validate_action_invocation(action, arguments, allowed_actions)


def validate_action_invocation(
    action: str,
    arguments: Any,
    allowed_actions: Iterable[ActionSpec],
) -> tuple[str | None, dict[str, Any], str | None]:
    """Validate either a parsed JSON action or a provider-native function call."""
    if not isinstance(arguments, dict):
        return None, {}, "arguments must be an object"
    specs = {spec.name: spec for spec in allowed_actions}
    invocation = normalize_invocation(action, arguments, allowed=specs, specs=specs, coerce=False)
    if not invocation.ok:
        return None, {}, "; ".join(invocation.errors)
    return invocation.action, invocation.arguments, None


def parse_single_structured_action(
    response: str,
    *,
    allowed_actions: set[str],
) -> tuple[str | None, str, str | None]:
    """Parse exactly one explicit action for strict collaboration protocols."""
    text = (response or "").strip()
    if not text:
        return None, "", "empty response"
    matches = list(ACTION_BLOCK_RE.finditer(text))
    if len(matches) != 1:
        return None, "", (
            "response must contain exactly one structured ACTION block; "
            f"received {len(matches)}"
        )
    match = matches[0]
    if match.start() != 0 or match.end() != len(text):
        return None, "", "response must contain only one structured ACTION block"
    action = match.group("action").strip().lower()
    payload = match.group("payload").strip()
    if not action_matches(action, allowed_actions):
        return None, "", (
            f"action '{action}' is not allowed; choose one of "
            f"{sorted(allowed_actions)}"
        )
    return action, payload, None


def parse_scoped_single_action(
    response: str,
    *,
    allowed_actions: set[str],
) -> tuple[str | None, str, str, str | None]:
    """Parse one action, tolerating wrappers while rejecting multiple actions."""
    text = (response or "").strip()
    if not text:
        return None, "", "", "empty response"

    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1]).strip()

    if text.startswith("{") and text.endswith("}"):
        try:
            payload_obj = json.loads(text)
        except json.JSONDecodeError:
            payload_obj = None
        if isinstance(payload_obj, dict):
            action = str(payload_obj.get("action") or "").strip().lower()
            target = str(payload_obj.get("target") or "public").strip()
            payload = str(payload_obj.get("payload") or "").strip()
            if not action_matches(action, allowed_actions):
                return (
                    None,
                    "",
                    "",
                    f"action '{action}' is not allowed; choose one of "
                    f"{sorted(allowed_actions)}",
                )
            return action, target, payload, None

    markers = list(re.finditer(r"(?i)\bACTION\s*:", text))
    if len(markers) != 1:
        return (
            None,
            "",
            "",
            "response must contain exactly one structured ACTION block",
        )
    candidate = text[markers[0].start() :].strip()
    candidate = re.sub(r"\n?```\s*$", "", candidate).strip()
    bare_rest = re.fullmatch(r"(?i)ACTION\s*:\s*(rest|sleep)", candidate)
    if bare_rest is not None and action_matches("rest", allowed_actions):
        return "rest", "public", "", None
    match = SCOPED_ACTION_RE.fullmatch(candidate)
    if match is None:
        match = TOLERANT_SCOPED_ACTION_RE.fullmatch(candidate)
    if match is None:
        return (
            None,
            "",
            "",
            "response must contain exactly one structured ACTION block",
        )
    action = match.group("action").strip().lower()
    if not action_matches(action, allowed_actions):
        return (
            None,
            "",
            "",
            f"action '{action}' is not allowed; choose one of {sorted(allowed_actions)}",
        )
    target = (match.group("target") or "public").strip()
    payload = match.group("payload").strip()
    return action, target, payload, None


def apply_agent_response(
    env,
    agent_name: str,
    response: str,
    *,
    submitters: Optional[set[str]] = None,
    allowed_actions: Optional[set[str]] = None,
) -> list[str]:
    """Parse and execute all actions from an agent response. Returns result strings."""
    results = []
    for action_type, payload in parse_agent_response(response):
        if allowed_actions is not None and not action_matches(action_type, allowed_actions):
            result = env.execute_action(
                agent_name,
                "rest",
                f"blocked prohibited action '{action_type}'",
            )
            results.append(result)
            continue
        if (
            canonical_action_name(action_type) == "submit"
            and submitters is not None
            and agent_name not in submitters
        ):
            if getattr(getattr(env, "rules_mode", None), "value", None) == "enforced":
                result = env.execute_action(agent_name, action_type, payload)
                results.append(result)
                continue
            # ``write_scratchpad`` (not ``work``) so the text always lands on
            # the shared scratchpad rather than on a held board item.
            result = env.execute_action(agent_name, "write_scratchpad", payload)
            results.append(f"(redirected {action_type} to scratchpad) {result}")
            continue
        result = env.execute_action(agent_name, action_type, payload)
        results.append(result)
        if env.submitted:
            break
    return results


def extract_final_answer_from_text(response: str) -> Optional[str]:
    """Pull payload from submit / submit_final if present, else return full text."""
    for action_type, payload in parse_agent_response(response):
        if canonical_action_name(action_type) == "submit":
            return payload
    stripped = response.strip()
    return stripped if stripped else None
