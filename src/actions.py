import json
import re
from typing import Optional

ACTION_INSTRUCTIONS = """\
Respond with ONE of these formats:

1) Plain text — treated as speak (broadcast to all agents).
2) Structured action:
   ACTION: <action_type> | PAYLOAD: <content>

Available action types:
- speak           — broadcast a message to the team
- write_scratchpad — update the shared working notes
- sleep           — pass this turn (optional reason in PAYLOAD)
{programming_lines}
- submit_final    — submit the team's final answer (only when ready)
{tool_lines}
{workspace_lines}
Rules:
- Use only tools listed as allowed for this contest.
- Each turn you get at most ONE model call: act, or sleep.
- submit_final must contain the complete team answer.
- Be substantive; build on prior discussion."""

WORKBOARD_INSTRUCTIONS = """\

Problem board ({item_count} items — the team's shared answer sheet):
- list_problems    — every item: status, who is on it, what is recorded
- open_problem     — PAYLOAD: <item> — the item plus its full answer history
- claim_problem    — PAYLOAD: <item> — take an item; one per agent at a time
- release_problem  — PAYLOAD: <item> — hand it back
- submit_problem   — PAYLOAD: <item> | <answer> — record an answer
- verify_problem   — PAYLOAD: <item> | agree|disagree|unsure <comment>
- mark_hopeless    — PAYLOAD: <item> | <reason>
- set_priority     — PAYLOAD: <item> | high|normal|low

Board rules:
- Only the latest recorded answer for an item is graded. An item with nothing
  recorded scores zero, so a considered guess beats leaving it blank.
- Recording an answer already recorded for that item is rejected — it changes
  nothing. Change your approach or move to an item that is still blank.
- There is no correctness feedback in this contest. Reviewing a teammate's
  recorded answer is the only check available."""

WORKSPACE_INSTRUCTIONS = """\

Shared workspace:
- remember       — PAYLOAD: [<item> |] <note> — store a note only you can read
- recall         — PAYLOAD: [<item> |] <query> — search your notes and the team's
- publish_memory — PAYLOAD: M1, M2 — share stored notes with the team
- check_budget   — turns, tokens, and how much of the board is still blank
- message_group  — PAYLOAD: <names> | <message> — message named teammates only"""

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


def build_action_instructions(
    allowed_tools: list[str],
    *,
    programming_contest: bool = False,
    structured_deliberation: bool = False,
    private_notes: bool = False,
    board_item_count: int = 0,
    workspace_actions: bool = True,
) -> str:
    if allowed_tools:
        tool_lines = "\n".join(f"- {tool}" for tool in allowed_tools)
    else:
        tool_lines = "(no tools — paper and pencil only)"
    programming_lines = (
        "- submit_code     — judge code; when a remote gateway is configured, "
        "submit after local sample AC and return its verdict (remote AC finalizes)"
        if programming_contest
        else ""
    )
    workspace_lines = ""
    if board_item_count:
        workspace_lines += WORKBOARD_INSTRUCTIONS.format(
            item_count=board_item_count
        )
    if workspace_actions:
        workspace_lines += WORKSPACE_INSTRUCTIONS
    rendered = ACTION_INSTRUCTIONS.format(
        programming_lines=programming_lines,
        tool_lines=tool_lines,
        workspace_lines=workspace_lines,
    )
    additions = []
    if private_notes:
        additions.append(
            "- write_private_notes — update notes visible only to you"
        )
    if structured_deliberation:
        additions.append(
            "- propose/challenge/provide_evidence/revise/decide — structured "
            "deliberation; targeted payloads use 'P<number> | <content>'"
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
    if action not in allowed_actions:
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
            if action not in allowed_actions:
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
    bare_rest = re.fullmatch(r"(?i)ACTION\s*:\s*rest", candidate)
    if bare_rest is not None and "rest" in allowed_actions:
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
    if action not in allowed_actions:
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
        if allowed_actions is not None and action_type not in allowed_actions:
            result = env.execute_action(
                agent_name,
                "sleep",
                f"blocked prohibited action '{action_type}'",
            )
            results.append(result)
            continue
        if action_type == "submit_final" and submitters is not None and agent_name not in submitters:
            if getattr(getattr(env, "rules_mode", None), "value", None) == "enforced":
                result = env.execute_action(agent_name, action_type, payload)
                results.append(result)
                continue
            result = env.execute_action(agent_name, "write_scratchpad", payload)
            results.append(f"(redirected submit_final to scratchpad) {result}")
            continue
        result = env.execute_action(agent_name, action_type, payload)
        results.append(result)
        if env.submitted:
            break
    return results


def extract_final_answer_from_text(response: str) -> Optional[str]:
    """Pull payload from submit_final if present, else return full text."""
    for action_type, payload in parse_agent_response(response):
        if action_type == "submit_final":
            return payload
    stripped = response.strip()
    return stripped if stripped else None
