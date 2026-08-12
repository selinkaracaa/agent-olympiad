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
- write_private_notes — save private working notes visible only to you
- submit_final    — submit the team's final answer (only when ready)
{deliberation_lines}
{tool_lines}

Rules:
- Use only tools listed as allowed for this contest.
- Obey the binding human contest rules in your system prompt.
- submit_final must contain the complete team answer.
- Be substantive; build on prior discussion."""

ACTION_BLOCK_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*\|\s*PAYLOAD:\s*(?P<payload>.*?)(?=^\s*ACTION:|\Z)",
    re.IGNORECASE | re.MULTILINE | re.DOTALL,
)

# Legacy single-line matcher kept for reference; multi-line payloads need ACTION_BLOCK_RE.
ACTION_LINE_RE = re.compile(
    r"^\s*ACTION:\s*(?P<action>[\w_]+)\s*\|\s*PAYLOAD:\s*(?P<payload>.*)$",
    re.IGNORECASE | re.MULTILINE,
)


def build_action_instructions(
    allowed_tools: list[str], *, structured_deliberation: bool = False
) -> str:
    if allowed_tools:
        tool_lines = "\n".join(f"- {tool}" for tool in allowed_tools)
    else:
        tool_lines = "(no tools — paper and pencil only)"
    deliberation_lines = ""
    if structured_deliberation:
        deliberation_lines = """\
- propose          — open a proposal; the ledger assigns P1, P2, ...
- challenge        — PAYLOAD: P1 | evidence-based objection
- provide_evidence — PAYLOAD: P1 | evidence relevant to the choice
- revise           — proposal author only; PAYLOAD: P1 | revised claim
- decide           — submitter only; PAYLOAD: P1 | accept/reject/defer | reason"""
    return ACTION_INSTRUCTIONS.format(
        deliberation_lines=deliberation_lines,
        tool_lines=tool_lines,
    )


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


def apply_agent_response(
    env,
    agent_name: str,
    response: str,
    *,
    submitters: Optional[set[str]] = None,
) -> list[str]:
    """Parse and execute all actions from an agent response. Returns result strings."""
    results = []
    for action_type, payload in parse_agent_response(response):
        if action_type == "submit_final" and submitters is not None and agent_name not in submitters:
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
