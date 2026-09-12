"""Runtime helpers for the ``otc`` (rule-card Open Table Coach) baseline.

Everything the card asks the engine to enforce is derived here from the
append-only :class:`ContestMemory` ledger plus the live :class:`ContestSession`,
so no extra state has to be checkpointed: the communication budget, silent-work
streaks, the ICPC workstation lease, pending-judging latency and the structured
deliberation ledger are all replays over recorded events.

The module also owns the Coach and private-think prompts so the contest engine
calls it for the single blind turn-0 brief and contestant think-then-act turns.
Legacy opening-summary helpers remain import-compatible but are never invoked
by the current OTC engine.
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterable, Mapping

from communication import CommunicationBudget
from contest_manifest import ContestManifest
from contest_memory import ContestMemory
from contest_session import ContestSession, TaskUnit
from deliberation import DeliberationLedger
from rulecard_policy import (
    DELIBERATION_ACTION_NAMES,
    MESSAGE_ACTION_NAMES,
    WORKSTATION_ACTION_NAMES,
    OpenTablePolicy,
)
from rules.models import RuleCard
from rules.views import agent_view

COACH_AGENT = "Coach"
# Turns a workstation lease survives without the holder touching the keyboard.
LEASE_TURNS = 2
# Actions that count as "working in silence" for the discussion policy.
SILENT_WORK_ACTIONS = frozenset({"work", "execute_code"})
BRIEF_EVENT = "precontest_coach_guidance"
OPENING_EVENT = "coach_opening_summary"
THINK_EVENT = "think"


def _events(memory: ContestMemory) -> list[dict[str, Any]]:
    return memory.archival_snapshot()["events"]


def _agent_turn_actions(
    events: Iterable[dict[str, Any]], agent: str
) -> dict[int, list[str]]:
    """Turn -> action kinds this agent performed (typed actions only)."""
    by_turn: dict[int, list[str]] = {}
    for event in events:
        if event["actor"] != agent:
            continue
        kind = str(event["kind"])
        if kind in {THINK_EVENT, "note"}:
            kind = "remember" if kind == "note" else kind
        by_turn.setdefault(int(event["turn"]), []).append(kind)
    return by_turn


# ---------------------------------------------------------------------------
# Card-enforced state, replayed from memory


def silent_work_streak(memory: ContestMemory, agent: str) -> int:
    """Consecutive most-recent turns in which ``agent`` only worked, never spoke."""
    by_turn = _agent_turn_actions(_events(memory), agent)
    streak = 0
    for turn in sorted(by_turn, reverse=True):
        kinds = set(by_turn[turn]) - {THINK_EVENT}
        if not kinds:
            continue
        if kinds & (MESSAGE_ACTION_NAMES | DELIBERATION_ACTION_NAMES):
            break
        if kinds & SILENT_WORK_ACTIONS:
            streak += 1
            continue
        break
    return streak


def reported_after_last_work(memory: ContestMemory, agent: str) -> bool:
    """False when the agent's latest recorded work has not been followed by a report."""
    by_turn = _agent_turn_actions(_events(memory), agent)
    for turn in sorted(by_turn, reverse=True):
        kinds = set(by_turn[turn]) - {THINK_EVENT}
        if not kinds:
            continue
        if kinds & (MESSAGE_ACTION_NAMES | DELIBERATION_ACTION_NAMES):
            return True
        if kinds & SILENT_WORK_ACTIONS:
            return False
    return True


def workstation_holder(
    memory: ContestMemory,
    task_id: str,
    *,
    current_turn: int,
    lease_turns: int = LEASE_TURNS,
) -> str | None:
    """Agent holding the team-wide keyboard, or None when free.

    The lease belongs to whoever last executed or submitted code on the
    problem and lapses ``lease_turns`` turns after that action.
    """
    holder: str | None = None
    for event in reversed(_events(memory)):
        if event["kind"] not in WORKSTATION_ACTION_NAMES:
            continue
        if not str(event["actor"]).startswith("Agent_"):
            continue
        if int(event["turn"]) + lease_turns > current_turn:
            holder = str(event["actor"])
        break
    return holder


def submission_pending(task: TaskUnit, *, current_turn: int, latency_turns: int) -> bool:
    """True while the card's judging latency hides the latest verdict."""
    if latency_turns <= 0 or not task.submissions:
        return False
    latest = task.submissions[-1]
    return latest.verdict == "PENDING"


def repair_budget_exhausted(
    memory: ContestMemory, task: TaskUnit, *, repair_budget: int
) -> bool:
    """True when a rejected official run was followed by ``repair_budget`` or
    more executions without a sample-AC on a *different* source version.

    Progress after a rejection means a better verdict, not merely changed
    source; churning on the same problem past the card's budget lowers its
    priority so the table moves on.
    """
    latest = task.latest_valid_submission
    if latest is None or latest.verdict == "AC":
        return False
    since_turn = int(latest.turn)
    rejected_hash = latest.version_hash
    executions = 0
    improved = False
    rejected_seen = False
    for event in _events(memory):
        if event["task_id"] != task.task_id or int(event["turn"]) < since_turn:
            continue
        kind = event["kind"]
        payload = event["payload"] if isinstance(event["payload"], dict) else {}
        if kind == "reopen" and payload.get("version_hash") == rejected_hash:
            rejected_seen = True
        if kind == "execute_code" and (rejected_seen or int(event["turn"]) > since_turn):
            executions += 1
        elif (
            kind == "sample_judge_result"
            and payload.get("sample_verdict") == "AC"
            and payload.get("version_hash") != rejected_hash
            and (rejected_seen or int(event["turn"]) > since_turn)
        ):
            improved = True
    return executions >= repair_budget and not improved


def communication_budget(
    memory: ContestMemory, policy: OpenTablePolicy
) -> CommunicationBudget:
    """Rebuild the card's message budget from every counted message so far."""
    counted = policy.counted_message_actions()
    budget = CommunicationBudget(
        {**policy.communication, "counted_actions": sorted(counted)}
    )
    if not counted:
        return budget
    for event in _events(memory):
        kind = str(event["kind"])
        if kind == "note_shared":
            kind = "share_note"
        if kind in counted and str(event["actor"]).startswith("Agent_"):
            budget.record(agent_name=str(event["actor"]), action_type=kind)
    return budget


def deliberation_ledger(memory: ContestMemory) -> DeliberationLedger:
    """Replay recorded deliberation actions into a ledger."""
    ledger = DeliberationLedger()
    for event in _events(memory):
        kind = str(event["kind"])
        if kind not in DELIBERATION_ACTION_NAMES:
            continue
        payload = event["payload"] if isinstance(event["payload"], dict) else {}
        if kind == "propose":
            text = str(payload.get("content") or "")
        elif kind == "decide":
            text = (
                f"{payload.get('proposal_id')} | {payload.get('outcome')} | "
                f"{payload.get('reason')}"
            )
        else:
            text = f"{payload.get('proposal_id')} | {payload.get('content')}"
        ledger.record(
            agent_name=str(event["actor"]),
            action_type=kind,
            payload=text,
            turn=int(event["turn"]),
            may_decide=True,
        )
    return ledger


def challenge_count(memory: ContestMemory) -> int:
    return sum(event["kind"] == "challenge" for event in _events(memory))


def private_think_ledger(
    memory: ContestMemory, agent: str, *, limit: int
) -> list[dict[str, Any]]:
    """The agent's last ``limit`` private think entries, oldest first."""
    rows = [
        {
            "turn": event["turn"],
            "task_id": event["task_id"],
            "content": (event["payload"] or {}).get("content", ""),
        }
        for event in _events(memory)
        if event["kind"] == THINK_EVENT and event["actor"] == agent
    ]
    return rows[-limit:] if limit > 0 else []


def coach_event(memory: ContestMemory, kind: str) -> dict[str, Any] | None:
    return next(
        (event for event in reversed(_events(memory)) if event["kind"] == kind),
        None,
    )


def opening_turn_events(
    memory: ContestMemory, *, turn: int, max_chars: int = 1200
) -> list[dict[str, Any]]:
    """Public contestant events of the opening turn, for the Coach summary."""
    rows: list[dict[str, Any]] = []
    for event in _events(memory):
        if int(event["turn"]) != turn or event["visibility"] != "public":
            continue
        if not str(event["actor"]).startswith("Agent_"):
            continue
        payload = event["payload"]
        if isinstance(payload, dict):
            payload = {
                key: (value[:max_chars] if isinstance(value, str) else value)
                for key, value in payload.items()
            }
        rows.append(
            {
                "actor": event["actor"],
                "kind": event["kind"],
                "task_id": event["task_id"],
                "payload": payload,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# Prompts


def _card_text(card: RuleCard, team_size: int) -> str:
    return json.dumps(agent_view(card, team_size=team_size), ensure_ascii=False)


def role_line(card: RuleCard, agent: str, team_size: int) -> str:
    role = next((r for r in card.roster(team_size) if r.name == agent), None)
    if role is None:
        return ""
    duties = "; ".join(role.duties)
    submit = "may submit" if role.may_submit else "may not submit"
    return f"YOUR ROLE: {role.title} ({submit}). Duties: {duties}"


def coach_brief_prompts(
    card: RuleCard,
    policy: OpenTablePolicy,
    manifest: ContestManifest,
    *,
    team_size: int,
    max_turns: int,
    max_api_calls: int | None,
) -> tuple[str, str]:
    """Turn-0 brief: the Coach has no problem access; advice within scope only."""
    scope = "\n".join(f"- {item}" for item in policy.advice_scope)
    system = (
        f"You are Coach for a {card.competition_id} team during the pre-contest brief. "
        "The problems are not available to you and you must not guess at them. "
        "Give preparation advice only within this scope:\n"
        f"{scope}\n"
        "Do not assign problems (you have not seen them). Do not call actions. "
        "Return plain text, at most "
        f"{policy.char_limit('work') or 2400} characters, organised as short "
        "numbered points the contestants can act on."
    )
    user = (
        f"PRE-CONTEST BRIEF\nCompetition: {card.competition_id}\n"
        f"Task family: {manifest.task_family}\n"
        "Competition format: "
        f"{manifest.metadata.get('competition_description') or 'see rule card'}\n"
        f"Team size: {team_size}; problems on the sheet: {len(manifest.tasks)} "
        f"(statements withheld until turn {policy.brief_turn + 1})\n"
        f"Budget: turns={max_turns}, api_calls={max_api_calls}; every contestant "
        f"turn is one private think call plus one action.\n"
        + (
            "This brief happens before the clock starts (turn 0) and costs the team "
            "no contest turn.\n"
            if policy.brief_turn == 0
            else "This brief occupies turn 1 of the clock.\n"
        )
        + "You exit after this turn-0 brief and are never called again.\n"
        f"CONTEST RULE CARD\n{_card_text(card, team_size)}"
    )
    return system, user


def coach_opening_prompts(
    card: RuleCard,
    policy: OpenTablePolicy,
    manifest: ContestManifest,
    memory: ContestMemory,
    session: ContestSession,
    *,
    team_size: int,
    opening_turn: int,
) -> tuple[str, str]:
    """Turn-2 summary: text for the team plus advisory work assignments."""
    agents = [f"Agent_{index}" for index in range(1, team_size + 1)]
    tasks = [
        {
            "problem_id": task.task_id,
            "type": task.task_type,
            "programming": task.programming,
            "prompt": task.prompt[:1500],
        }
        for task in manifest.tasks
    ]
    system = (
        f"You are Coach for a {card.competition_id} team. This is your final "
        "participation. Read the opening discussion and "
        f"{policy.opening_purpose}. You exit after this message and nobody "
        "coaches afterwards. Do not solve problems and do not call actions. "
        "Return only one JSON object with this schema: "
        '{"summary":"text the whole team reads (<= '
        f"{policy.char_limit('work') or 2400} chars)\","
        '"work_assignments":{"Agent_1":["exact problem_id"]},'
        '"task_order":["exact problem_id"],'
        '"watch_points":["..."]}. '
        "Assignments are advice the contestants may override; every agent name "
        f"must be one of {agents} and every problem_id must be exact."
    )
    user = (
        f"OPENING DISCUSSION (turn {opening_turn})\n"
        f"Team: {agents}\n"
        f"Tasks:\n{json.dumps(tasks, ensure_ascii=False)}\n\n"
        "What contestants said and recorded during the opening turn:\n"
        f"{json.dumps(opening_turn_events(memory, turn=opening_turn), ensure_ascii=False)}\n\n"
        "Task status:\n"
        f"{json.dumps([{'task_id': t.task_id, 'versions': len(t.versions)} for t in session.tasks], ensure_ascii=False)}\n\n"
        f"CONTEST RULE CARD\n{_card_text(card, team_size)}"
    )
    return system, user


def think_system_prompt(
    card: RuleCard,
    policy: OpenTablePolicy,
    agent: str,
    *,
    team_size: int,
    action_names: Iterable[str],
    retain_history: bool = True,
) -> str:
    limit = policy.char_limit("think") or 2400
    return (
        f"You are {agent}, one contestant in a {team_size}-agent {card.competition_id} "
        "team. This is your PRIVATE deliberation for this turn: nobody else sees it. "
        "Weigh the current state, the coach brief and summary, teammates' messages "
        + ("and your own earlier thoughts, then decide which single action you will " if retain_history else
           "and the current shared drafts, then decide which single action you will ")
        + f"take next and why. The actions available this turn are: "
        f"{', '.join(sorted(action_names))}. "
        f"Write plain text, at most {limit} characters, ending with one line "
        "'NEXT ACTION: <action name>'. Do not output JSON and do not call actions."
    )


def protocol_text(
    card: RuleCard,
    policy: OpenTablePolicy,
    *,
    agent: str,
    team_size: int,
    current_turn: int,
    communication: CommunicationBudget,
    lease_holder: str | None,
    pending_verdict: bool,
    silent_streak: int,
    programming: bool,
    open_proposals: tuple[str, ...] = (),
    review_required: bool = True,
) -> str:
    """The card-driven operating rules shown in every contestant system prompt."""
    limits = ", ".join(
        f"{name} {value}" for name, value in sorted(policy.max_chars_by_action.items())
    )
    lines = [
        f"OPEN TABLE COACH PROTOCOL (rule card {card.rule_id})",
        "Coach gave one problem-blind brief at turn 0 before the clock, then "
        "left permanently. There is no opening summary or Coach assignment.",
        ("Mandatory review: a different teammate must approve the current answer "
        "version before submission, including deadline collection. A rejection "
        "blocks submission; revision invalidates prior reviews." if review_required else
        "Basic Open Table: verification may be discussed voluntarily; no independent approval, memory tools, or structured proposal workflow is required. Submit the current version under the competition's format and resource rules."),
        ("Each turn you first think privately (your ledger is shown below), then "
         if review_required else
         "Each turn you first think privately (only this turn's thought is shown below), then ")
        + "take exactly ONE action. Unstructured or invalid output counts as rest.",
        "Your work is recorded on the problem shown as your current problem. To "
        "move to another problem, call work with problem_id=<that problem> in the "
        "same turn (the switch and the draft are one move); a problem that already "
        "has a draft is left for verification and your focus advances to the next "
        "one without a draft.",
        f"Character limits per action: {limits}. Longer content is cut.",
        f"Roles allowed to submit: {', '.join(sorted(policy.submitters))}.",
    ]
    if policy.min_turns:
        lines.append(
            f"The contest cannot end before turn {policy.min_turns}; it is now turn "
            f"{current_turn}."
        )
    discussion = policy.discussion
    if discussion.report_after_work:
        lines.append(
            "Discussion policy: after recording work, report it to the team "
            "(speak or direct_message) before the next silent work turn."
        )
    if discussion.silent_work_turn_requires_discussion:
        lines.append(
            f"Discussion policy: after {discussion.silent_work_turns} consecutive "
            "work-only turns your next action must be a discussion action "
            f"(speak/direct_message/share_note). Your current silent streak: {silent_streak}."
        )
    if discussion.conflicts_require_targeted_speak:
        lines.append(
            "Discussion policy: resolve a disagreement with a targeted message to "
            "the teammate concerned, not by silently overwriting their draft."
        )
    if policy.communication_limited:
        lines.append(
            "Communication budget (card): "
            f"{communication.status_for(agent)}; max "
            f"{communication.max_message_chars} chars per message. Counted actions: "
            f"{', '.join(sorted(policy.counted_message_actions()))}."
        )
    if policy.structured_deliberation:
        lines.append(
            "Structured deliberation (card): use propose to open a numbered claim, "
            "challenge/provide_evidence to test it, revise to update your own, and "
            f"decide (decision maker: {policy.decision_maker}) to close it. The team "
            f"must record at least {policy.min_challenges} challenge(s) before the "
            "answer sheet may be submitted. challenge/provide_evidence/revise/decide "
            "need an existing proposal id; open proposals now: "
            + (", ".join(open_proposals) if open_proposals else "none (use propose first)")
            + "."
        )
    if programming and policy.workstation_lease:
        holder = (
            f"currently held by {lease_holder}" if lease_holder else "currently free"
        )
        lines.append(
            "Workstation lease (card): one shared keyboard for the entire team. Whoever "
            f"last ran or submitted code holds it for {LEASE_TURNS} turns across all "
            f"problems; others may analyse or review. Shared keyboard: {holder}."
        )
    if programming and policy.run_judging_latency_turns:
        lines.append(
            f"Judging latency (card): a verdict arrives {policy.run_judging_latency_turns} "
            "turn(s) after submit_code; you cannot resubmit that problem meanwhile."
            + (" A verdict is pending on the active problem." if pending_verdict else "")
        )
    if programming:
        lines.append(
            "Repair budget (card): after an official rejection, "
            f"{policy.repair_budget_after_rejected_run} further executions without a "
            "better sample verdict lower the problem's priority; move on and revisit."
        )
    role = role_line(card, agent, team_size)
    if role:
        lines.append(role)
    return "\n".join(lines)


def card_block(card: RuleCard, team_size: int) -> str:
    return f"CONTEST RULE CARD (agent view)\n{_card_text(card, team_size)}"


def parse_coach_summary(
    response: str,
    manifest: ContestManifest,
    *,
    team_size: int,
) -> dict[str, Any]:
    """Legacy summary parser; not used by the turn-0-only OTC engine."""
    stripped = response.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:] if lines and lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    parsed: Any = None
    start, end = stripped.find("{"), stripped.rfind("}")
    candidates = [stripped]
    if 0 <= start < end:
        candidates.append(stripped[start : end + 1])
    # Models writing TeX inside JSON strings produce invalid escapes such as
    # "\(" or "\sin"; doubling the stray backslashes keeps the object readable.
    candidates.extend(
        re.sub(r'\\(?![\\/"bfnrtu])', r"\\\\", candidate) for candidate in list(candidates)
    )
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            break
        parsed = None
    if parsed is None:
        # Truncated or otherwise unreadable object: salvage the summary text.
        match = re.search(r'"summary"\s*:\s*"((?:[^"\\]|\\.)*)', stripped)
        if match:
            stripped = match.group(1).replace("\\n", "\n").replace('\\"', '"')
    known = {task.task_id for task in manifest.tasks}
    suffixes = {task.task_id.rsplit(":", 1)[-1]: task.task_id for task in manifest.tasks}
    agents = [f"Agent_{index}" for index in range(1, team_size + 1)]

    def ids(values: Any) -> list[str]:
        out: list[str] = []
        for value in values if isinstance(values, list) else []:
            raw = str(value)
            task_id = raw if raw in known else suffixes.get(raw)
            if task_id and task_id not in out:
                out.append(task_id)
        return out

    if not isinstance(parsed, dict):
        return {
            "summary": stripped,
            "work_assignments": {agent: [] for agent in agents},
            "task_order": [],
            "watch_points": [],
        }
    work_raw = parsed.get("work_assignments")
    return {
        "summary": str(parsed.get("summary") or stripped),
        "work_assignments": {
            agent: ids(work_raw.get(agent) if isinstance(work_raw, dict) else [])
            for agent in agents
        },
        "task_order": ids(parsed.get("task_order")),
        "watch_points": [
            str(item) for item in parsed.get("watch_points") or []
        ]
        if isinstance(parsed.get("watch_points"), list)
        else [],
    }


__all__ = [
    "BRIEF_EVENT",
    "COACH_AGENT",
    "LEASE_TURNS",
    "OPENING_EVENT",
    "THINK_EVENT",
    "card_block",
    "challenge_count",
    "coach_brief_prompts",
    "coach_event",
    "coach_opening_prompts",
    "communication_budget",
    "deliberation_ledger",
    "parse_coach_summary",
    "private_think_ledger",
    "protocol_text",
    "repair_budget_exhausted",
    "reported_after_last_work",
    "silent_work_streak",
    "submission_pending",
    "think_system_prompt",
    "workstation_holder",
]
