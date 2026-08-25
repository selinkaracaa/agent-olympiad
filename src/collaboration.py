import json
from dataclasses import dataclass, field
from typing import Callable, Literal

from actions import apply_agent_response, build_action_instructions, extract_final_answer_from_text, parse_agent_response
from contest_budget import resolve_contest_budget
from env import TurnLimitExceededError
from rules import agent_view, load_rule_card
from rules.describe import describe_resources
from rules.models import AgentRole

SchemaName = Literal[
    "round_table",
    "centralized",
    "decentralized",
    "single_agent",
    "open_table_coach",
]
QueryFn = Callable[[str, str], str]


@dataclass
class CollabConfig:
    """Collaboration budgets and schema knobs.

    Turns = time constraint (contest clock). Each turn, each eligible agent may
    make at most one LLM call (or choose to sleep), except single_agent which
    may use up to `solo_calls_per_turn` calls per turn to match team API budget.
    API calls = cost constraint across the whole run.
    """

    max_turns: int | None = None
    max_api_calls: int | None = None
    max_output_tokens_per_call: int | None = None
    max_total_tokens: int | None = None
    # Backward-compatible aliases used by older callers / smoke tests.
    rounds: int | None = None
    decentralized_events: int | None = None
    synthesize: bool = True
    progress: Callable[[str], None] | None = None
    # Equal-resource solo baseline: calls allowed per turn (= team size by default).
    solo_calls_per_turn: int | None = None

    def resolved_max_turns(self, competition_id: str) -> int:
        if self.rounds is not None:
            return self.rounds
        if self.decentralized_events is not None:
            return self.decentralized_events
        if self.max_turns is not None:
            return self.max_turns
        return resolve_contest_budget(competition_id).max_turns


def _apply_budget_config(env, config: CollabConfig) -> None:
    budget = resolve_contest_budget(
        env.competition_id,
        max_turns=config.resolved_max_turns(env.competition_id),
        max_api_calls=config.max_api_calls,
        max_output_tokens_per_call=config.max_output_tokens_per_call,
        max_total_tokens=config.max_total_tokens,
    )
    env.budget = budget
    env.max_turns = budget.max_turns
    env.max_api_calls = budget.max_api_calls
    env.max_output_tokens_per_call = budget.max_output_tokens_per_call
    env.max_total_tokens = budget.max_total_tokens


def _roster(env) -> list[AgentRole]:
    if getattr(env, "rule_card", None) is not None:
        return env.rule_card.roster(env.team_size)
    return [
        AgentRole(
            name=f"Agent_{index + 1}",
            title="captain and synthesizer" if index == 0 else "team specialist",
            duties=(),
            may_submit=index == 0,
        )
        for index in range(env.team_size)
    ]


def _role_lookup(env, agent_name: str) -> AgentRole:
    return next(
        (role for role in _roster(env) if role.name == agent_name),
        AgentRole(agent_name, agent_name, (), False),
    )


def _format_constraints(constraints: list[str]) -> str:
    return "\n".join(f"- {item}" for item in constraints) or "(none listed)"


def _system_prompt(env, role: str) -> str:
    meta = env.get_metadata()
    card = getattr(env, "rule_card", None)
    rule = meta.get("rule") or {}
    assigned = _role_lookup(env, role)
    structured = (rule.get("deliberation") or {}).get("mode") == "structured"
    tools = build_action_instructions(
        env.get_available_tools(), structured_deliberation=structured
    )
    specialties = ""
    if card is not None and assigned.rule_expertise:
        lines = []
        for category in assigned.rule_expertise:
            lines.append(f"{category.replace('_', ' ').title()}:")
            lines.extend(f"- {item}" for item in card.rule_sections.get(category, []))
        specialties = (
            "\n=== YOUR RULE SPECIALTY ===\n"
            "Every teammate can consult the complete rules. You are primarily "
            "responsible for tracking and communicating these sections:\n"
            + "\n".join(lines)
            + "\n"
        )
    resources = describe_resources(rule.get("resources") or {}) if rule else ""
    communication = ""
    if (rule.get("communication") or {}).get("mode") == "limited":
        policy = rule["communication"]
        communication = (
            "\n=== LIMITED COMMUNICATION BUDGET ===\n"
            f"Team limit: {policy['team_message_budget']} messages; your limit: "
            f"{policy['per_agent_message_budget']}; maximum "
            f"{policy['max_message_chars']} characters each. Use write_private_notes "
            "for private analysis without consuming communication budget.\n"
        )
    return (
        f"You are {assigned.name}, title: {assigned.title}.\n"
        f"You are a contestant on a {meta['competition_id']} team of {meta['team_size']} agents.\n"
        f"Problem: {meta.get('title') or meta['problem_id']} ({meta.get('year', 'n/a')})\n"
        f"Allowed tools: {meta['allowed_tools'] or 'none'}\n\n"
        f"Resource rules: {resources}\n"
        f"Competition rule profile: {rule.get('profile')} ({rule.get('protocol')}).\n"
        f"Official/adapted rules summary: {rule.get('rules_text', '')}\n\n"
        "=== HUMAN CONTEST RULES (BINDING) ===\n"
        f"{_format_constraints(rule.get('human_constraints') or [])}\n\n"
        "=== AGENT COLLABORATION RULES ===\n"
        f"{_format_constraints(rule.get('agent_constraints') or [])}\n"
        f"{specialties}{communication}\n"
        "=== YOUR ROLE DUTIES ===\n"
        f"{_format_constraints(list(assigned.duties))}\n"
        f"May submit final answer: {'yes' if assigned.may_submit else 'no — advise only'}\n\n"
        f"{tools}"
    )


def _coach_system_prompt(env, *, precontest: bool) -> str:
    meta = env.get_metadata()
    phase = "pre-contest preparation" if precontest else "the opening team discussion"
    return (
        f"You are Coach for a {meta['competition_id']} team during {phase}.\n"
        "You are an adviser, not a contestant. You may only broadcast advice or sleep; "
        "you may not use tools, edit the scratchpad, or submit an answer.\n\n"
        "Respond with plain text (broadcast as speech), or:\n"
        "ACTION: speak | PAYLOAD: <advice>\n"
        "ACTION: sleep | PAYLOAD: <short reason>"
    )


def _agent_visible_rules(env) -> str:
    card = load_rule_card(env.competition_id, required=False)
    if card is None:
        meta = env.get_metadata()
        payload = {
            "competition_id": meta["competition_id"],
            "team_size": meta["team_size"],
            "allowed_tools": meta["allowed_tools"],
        }
    else:
        view = agent_view(card, team_size=env.team_size)
        keys = (
            "competition_id",
            "protocol",
            "rules_text",
            "human_constraints",
            "agent_constraints",
            "resources",
            "allowed_tools",
            "information_policy",
            "communication",
            "simulation",
            "agent_roles",
        )
        payload = {key: view[key] for key in keys}
    return json.dumps(payload, ensure_ascii=False, indent=2)


def _discussion_history(env) -> str:
    if not env.chat_history:
        return "(no messages yet)"
    lines = []
    for entry in env.chat_history:
        lines.append(f"[{entry['sender']}]: {entry['message']}")
    return "\n".join(lines)


def _agent_user_prompt(env, agent_name: str, schema_note: str, extra: str = "") -> str:
    state = env.get_state()
    scratchpad = state["shared_workspace"].get("scratchpad") or "(empty)"
    private_notes = env.get_private_notes(agent_name) or "(empty)"
    return f"""=== SCHEMA ===
{schema_note}

=== PROBLEM ===
{state['problem_statement']}

=== TEAM DISCUSSION ===
{_discussion_history(env)}

=== SHARED SCRATCHPAD ===
{scratchpad}

=== YOUR PRIVATE NOTES ===
{private_notes}

=== YOUR TURN ===
You are {agent_name}.
Turn budget (time): {state['turn_status']}
API budget (cost): {state['api_call_status']}
Token budget (team output): {state['token_status']} (cap {state['output_token_cap_per_call']} tokens/call)
Communication budget: {env.communication.status_for(agent_name)}
Submitted: {state['submitted']}
{extra}
You may act once this turn, or:
ACTION: sleep | PAYLOAD: <short reason>
What is your contribution?"""


def _count_numbered_parts(text: str) -> int:
    import re
    return len(re.findall(r"(?:^|\n)\s*\d+\s*[\.\)]", text))


def _synthesis_system_prompt(env, synthesizer: str) -> str:
    meta = env.get_metadata()
    return (
        f"You are {synthesizer}, writing the team's official final answer sheet for "
        f"{meta['competition_id']} ({meta.get('year', 'n/a')}).\n"
        "Output ONLY the numbered answer sheet. No ACTION lines, no commentary."
    )


def _final_answer_instructions(env) -> str:
    task_type = env.problem_data.get("task_type", "")
    total_pts = env.problem_data.get("total_points")
    if task_type in {"team_contest", "team_power", "team_practical"}:
        points_line = f" ({int(total_pts)} points total)" if total_pts else ""
        return f"""Write the team's COMPLETE final answer sheet{points_line}.

CRITICAL:
- Include EVERY numbered problem from the problem statement (1. through 10.).
- Format exactly:
1. [answer]
2. [answer]
...
10. [answer]
- Compile the best answers from the full discussion and scratchpad above.
- Output plain text only (no ACTION: lines)."""
    return "Synthesize the team's complete final answer as plain text."


def _submit_synthesis_response(env, synthesizer: str, response: str) -> int:
    """Submit synthesis output; prefer full response over truncated ACTION payloads."""
    text = response.strip()
    if not text:
        return 0

    for action_type, payload in parse_agent_response(response):
        if action_type == "submit_final":
            text = payload.strip()
            break

    parts = _count_numbered_parts(text)
    if parts < 3:
        stripped = response.strip()
        if _count_numbered_parts(stripped) > parts:
            text = stripped
            parts = _count_numbered_parts(text)

    env.execute_action(synthesizer, "submit_final", text)
    return parts


def _synthesis_prompt(env, schema_note: str) -> str:
    state = env.get_state()
    instructions = _final_answer_instructions(env)
    return f"""=== SCHEMA ===
{schema_note}

=== PROBLEM ===
{state['problem_statement']}

=== FULL TEAM DISCUSSION ===
{_discussion_history(env)}

=== SHARED SCRATCHPAD ===
{state['shared_workspace'].get('scratchpad') or '(empty)'}

=== FINAL TEAM ANSWER ===
{instructions}"""


def _budgeted_query(env, query_llm_fn: QueryFn, config: CollabConfig) -> QueryFn:
    """Wrap the LLM callback so every call counts toward cost + token budgets."""
    _apply_budget_config(env, config)

    def call(system: str, user: str) -> str:
        if env.token_budget_exhausted():
            raise TurnLimitExceededError(
                f"Token budget reached ({env.max_total_tokens}) for {env.problem_id}"
            )
        env.record_api_call()
        response = query_llm_fn(system, user)
        return env.apply_output_token_budget(response)

    return call


def _should_stop(env) -> bool:
    return env.submitted or env.api_budget_exhausted() or env.token_budget_exhausted()


def _run_agent_once(
    env,
    query: QueryFn,
    agent: str,
    schema_note: str,
    extra: str,
    *,
    submitters: set[str] | None = None,
    allowed_actions: set[str] | None = None,
    system_prompt: str | None = None,
    progress: Callable[[str], None] | None = None,
) -> None:
    if _should_stop(env):
        return
    if progress:
        progress(f"Turn {env.current_turn}/{env.max_turns} — {agent} thinking...")
    try:
        response = query(
            system_prompt or _system_prompt(env, agent),
            _agent_user_prompt(env, agent, schema_note, extra=extra),
        )
    except TurnLimitExceededError:
        if progress:
            progress("API/turn budget exhausted — stopping agent calls.")
        return
    apply_agent_response(
        env,
        agent,
        response,
        submitters=submitters,
        allowed_actions=allowed_actions,
    )


def _run_synthesis(
    env,
    query_llm_fn: QueryFn,
    schema_note: str,
    synthesizer: str,
    *,
    submitters: set[str] | None = None,
    progress: Callable[[str], None] | None = None,
) -> None:
    if env.submitted:
        return

    def _log(msg: str) -> None:
        if progress:
            progress(msg)

    best_answer = ""
    best_parts = 0

    for attempt in range(2):
        if env.api_budget_exhausted() or env.token_budget_exhausted():
            _log("Budget exhausted — skipping further synthesis attempts.")
            break
        _log(f"{synthesizer} synthesizing final answer (attempt {attempt + 1})...")
        system = _synthesis_system_prompt(env, synthesizer)
        user = _synthesis_prompt(env, schema_note)
        if attempt > 0:
            user += (
                "\n\nREMINDER: Your previous submission was incomplete. "
                "You MUST include ALL numbered problems (1. through 10.)."
            )
        try:
            response = query_llm_fn(system, user)
        except TurnLimitExceededError:
            _log("API budget exhausted during synthesis.")
            break
        if env.submitted:
            env.workspace["final_answer"] = ""
            env.submitted = False
            env.submitted_by = None

        parts = _submit_synthesis_response(env, synthesizer, response)
        answer = env.workspace.get("final_answer", "")
        if parts > best_parts:
            best_parts = parts
            best_answer = answer

        if parts >= 5:
            break
        _log(f"  submission has only {parts} numbered parts — retrying synthesis")

    if best_answer and not env.submitted:
        env.execute_action(synthesizer, "submit_final", best_answer)
    elif best_answer and _count_numbered_parts(env.workspace.get("final_answer", "")) < best_parts:
        env.workspace["final_answer"] = best_answer
        env.submitted = True
        env.submitted_by = synthesizer


def run_round_table(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema A: Round Table — every agent sees the full conversation.
    Each turn: agents act in order; each agent ≤ 1 LLM call (or sleep).
    """
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    schema_note = (
        "Round Table: all agents see full history; strict order within each turn. "
        "At most one LLM call per agent per turn (or sleep)."
    )
    agents = [f"Agent_{i + 1}" for i in range(env.team_size)]

    while not _should_stop(env):
        if not env.can_begin_turn():
            break
        turn = env.begin_turn()
        for agent in agents:
            _run_agent_once(
                env,
                query,
                agent,
                schema_note,
                extra=f"Collaboration turn {turn} of {env.max_turns}.",
                progress=config.progress,
            )
            if _should_stop(env):
                break

    if config.synthesize:
        _run_synthesis(env, query, schema_note, "Agent_1", progress=config.progress)

    return _result(env, "round_table")


def run_open_table_coach(
    env,
    query_llm_fn: QueryFn,
    config: CollabConfig | None = None,
) -> dict:
    """Coach prepares the team, joins one open-table turn, then exits."""
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    rules_text = _agent_visible_rules(env)
    schema_note = (
        "Open Table + Coach: Coach provides a rule-grounded preparation brief and "
        "joins only the opening discussion. After that, contestants collaborate "
        "through full shared history without Coach."
    )
    agents = [f"Agent_{i + 1}" for i in range(env.team_size)]
    coach_actions = {"speak", "sleep"}

    # Turn 1 is charged to the common clock and budget, but Coach cannot see the problem.
    if not _should_stop(env) and env.can_begin_turn():
        turn = env.begin_turn()
        if config.progress:
            config.progress(f"Turn {turn}/{env.max_turns} — Coach preparing team...")
        precontest_prompt = f"""=== PUBLIC CONTEST AND COLLABORATION RULES ===
{rules_text}

=== TEAM RESOURCE ENVELOPE ===
Team size: {env.team_size} contestants
Total turns: {env.max_turns}

Prepare a concise strategy for time allocation, task ordering, communication, and
cross-checking. Do not discuss or infer the unseen problem."""
        try:
            response = query(
                _coach_system_prompt(env, precontest=True),
                precontest_prompt,
            )
        except TurnLimitExceededError:
            response = ""
        if response:
            apply_agent_response(
                env,
                "Coach",
                response,
                submitters=set(),
                allowed_actions=coach_actions,
            )

    # Turn 2 is the only problem-aware turn that includes Coach.
    if not _should_stop(env) and env.can_begin_turn():
        turn = env.begin_turn()
        for agent in agents:
            _run_agent_once(
                env,
                query,
                agent,
                schema_note,
                extra=(
                    f"Opening open-table turn {turn} of {env.max_turns}. "
                    "Review the problem, propose assignments and priorities, and "
                    "respond to the Coach's preparation brief.\n\n"
                    f"PUBLIC CONTEST AND COLLABORATION RULES:\n{rules_text}"
                ),
                progress=config.progress,
            )
            if _should_stop(env):
                break
        if not _should_stop(env):
            _run_agent_once(
                env,
                query,
                "Coach",
                schema_note,
                extra=(
                    "This is your final participation. Summarize the contestants' "
                    "opening discussion into actionable priorities and time checkpoints. "
                    "After this message you leave the team.\n\n"
                    f"PUBLIC CONTEST AND COLLABORATION RULES:\n{rules_text}"
                ),
                submitters=set(),
                allowed_actions=coach_actions,
                system_prompt=_coach_system_prompt(env, precontest=False),
                progress=config.progress,
            )

    # Every remaining contest turn belongs only to the contestants.
    while not _should_stop(env):
        if not env.can_begin_turn():
            break
        turn = env.begin_turn()
        for agent in agents:
            _run_agent_once(
                env,
                query,
                agent,
                schema_note,
                extra=(
                    f"Contestant-only collaboration turn {turn} of {env.max_turns}. "
                    "Use the opening plan, shared discussion, and contest rules. "
                    "Coach has exited and cannot participate.\n\n"
                    f"PUBLIC CONTEST AND COLLABORATION RULES:\n{rules_text}"
                ),
                progress=config.progress,
            )
            if _should_stop(env):
                break

    if config.synthesize and not env.submitted:
        _run_synthesis(env, query, schema_note, agents[0], progress=config.progress)

    return _result(env, "open_table_coach")


def run_centralized(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema B: Centralized — coordinator delegates, aggregates, and submits.
    Turn 1: leader plans. Later turns: workers each get ≤ 1 call (or sleep).
    """
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    schema_note = (
        "Centralized: Group_Leader delegates; only leader submits final answer. "
        "At most one LLM call per agent per turn (or sleep)."
    )
    leader = "Group_Leader"
    workers = [f"Agent_{i + 1}" for i in range(1, env.team_size)]

    plan = ""
    while not _should_stop(env):
        if not env.can_begin_turn():
            break
        turn = env.begin_turn()
        if turn == 1:
            if config.progress:
                config.progress(f"Turn {turn}/{env.max_turns} — Group_Leader planning...")
            state = env.get_state()
            system = _system_prompt(env, leader)
            user = (
                f"=== PROBLEM ===\n{state['problem_statement']}\n\n"
                "You are the Group Leader. Assign sub-tasks to Agent_2 .. "
                f"Agent_{env.team_size}. Output your delegation plan."
            )
            try:
                plan = query(system, user)
            except TurnLimitExceededError:
                break
            env.execute_action(leader, "speak", f"Delegation plan: {plan}")
            continue

        for peer in workers:
            _run_agent_once(
                env,
                query,
                peer,
                schema_note,
                extra=(
                    f"Leader's plan:\n{plan}\n\n"
                    f"Collaboration turn {turn} of {env.max_turns}. "
                    "Complete your assigned slice. You may use allowed tools or sleep."
                ),
                submitters=set(),
                progress=config.progress,
            )
            if _should_stop(env):
                break

    if config.synthesize and not env.submitted:
        _run_synthesis(
            env,
            query,
            schema_note,
            leader,
            submitters={"Group_Leader"},
            progress=config.progress,
        )

    return _result(env, "centralized")


def run_decentralized(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema C: Decentralized — agents work independently, coordinate via shared state.
    Each turn: every agent ≤ 1 LLM call (or sleep).
    """
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    schema_note = (
        "Decentralized: no leader; peers update scratchpad/tools directly. "
        "At most one LLM call per agent per turn (or sleep)."
    )
    agents = [f"Agent_{i + 1}" for i in range(env.team_size)]

    while not _should_stop(env):
        if not env.can_begin_turn():
            break
        turn = env.begin_turn()
        for agent in agents:
            _run_agent_once(
                env,
                query,
                agent,
                schema_note,
                extra=(
                    f"Collaboration turn {turn} of {env.max_turns}. "
                    "Coordinate directly with peers. No manager. Or sleep."
                ),
                progress=config.progress,
            )
            if _should_stop(env):
                break

    if config.synthesize and not env.submitted:
        _run_synthesis(env, query, schema_note, agents[0], progress=config.progress)

    return _result(env, "decentralized")


def run_single_agent(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """Baseline: one agent, same wall-clock turns, equal total API budget.

    Per turn the solo agent may make up to `team_size` LLM calls (or sleep),
    matching the multi-agent per-turn call budget.
    """
    config = config or CollabConfig()
    natural_team = env.team_size
    calls_per_turn = config.solo_calls_per_turn or max(1, natural_team)
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    schema_note = (
        "Single-agent baseline: you alone have the full team resource budget. "
        f"Each turn you may take up to {calls_per_turn} actions/calls "
        f"(equal to a {natural_team}-agent team's per-turn budget), or sleep."
    )
    agent = "Solo"

    while not _should_stop(env):
        if not env.can_begin_turn():
            break
        turn = env.begin_turn()
        for slot in range(1, calls_per_turn + 1):
            if _should_stop(env):
                break
            extra = (
                f"Collaboration turn {turn} of {env.max_turns}, "
                f"solo slot {slot}/{calls_per_turn}. "
                "Solve the full contest packet and submit when ready."
            )
            _run_agent_once(
                env,
                query,
                agent,
                schema_note,
                extra=extra,
                progress=config.progress,
            )
            if env.action_log and env.action_log[-1].get("action") == "sleep":
                break

    if config.synthesize and not env.submitted:
        _run_synthesis(env, query, schema_note, agent, progress=config.progress)

    result = _result(env, "single_agent")
    result["solo_calls_per_turn"] = calls_per_turn
    result["natural_team_size"] = natural_team
    return result


def _result(env, schema: str) -> dict:
    meta = env.get_metadata()
    evaluation = None
    if getattr(env, "rule_card", None) is not None:
        from rules.views import grader_view

        evaluation = {"scoring": grader_view(env.rule_card).get("scoring") or {}}
    return {
        "schema": schema,
        "problem_id": env.problem_id,
        "competition_id": env.competition_id,
        "submitted": env.submitted,
        "submitted_by": env.submitted_by,
        "turns_used": env.current_turn,
        "max_turns": env.max_turns,
        "api_calls": env.api_calls,
        "max_api_calls": env.max_api_calls,
        "tokens_used": env.tokens_used,
        "max_total_tokens": env.max_total_tokens,
        "max_output_tokens_per_call": env.max_output_tokens_per_call,
        "action_count": env.action_count,
        "chat_messages": len(env.chat_history),
        "final_answer": env.workspace.get("final_answer", ""),
        "grade": env.grade_submission(),
        "deliberation": env.deliberation.report(),
        "communication": env.communication.report(),
        "rule": meta.get("rule"),
        "evaluation": evaluation,
        "roster": (
            meta.get("rule", {}).get("agent_roles")
            if meta.get("rule")
            else [
                {
                    "name": role.name,
                    "title": role.title,
                    "may_submit": role.may_submit,
                }
                for role in _roster(env)
            ]
        ),
    }


SCHEMAS: dict[SchemaName, Callable] = {
    "round_table": run_round_table,
    "centralized": run_centralized,
    "decentralized": run_decentralized,
    "single_agent": run_single_agent,
    "open_table_coach": run_open_table_coach,
}


def run_collaboration(
    schema: SchemaName,
    env,
    query_llm_fn: QueryFn,
    config: CollabConfig | None = None,
) -> dict:
    if schema not in SCHEMAS:
        raise ValueError(f"Unknown schema '{schema}'. Choose from: {list(SCHEMAS)}")
    return SCHEMAS[schema](env, query_llm_fn, config)
