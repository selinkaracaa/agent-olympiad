import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Callable, Literal

from actions import apply_agent_response, build_action_instructions, extract_final_answer_from_text, parse_agent_response
from contest_budget import resolve_contest_budget
from env import TurnLimitExceededError
from memory import MemoryStore
from rules import AgentRole, RulesMode, agent_view
from rules.describe import describe_resources

SchemaName = Literal[
    "round_table",
    "centralized",
    "decentralized",
    "single_agent",
    "open_table_coach",
    "debate",
    "self_consistency",
    "memory_solo",
    "subagent",
    "liveoi_best_of_8",
]
QueryFn = Callable[[str, str], str]
JudgeFn = Callable[[str], float]


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
    sample_count: int = 5
    memory_bound: int = 8
    debate_rounds: int = 2
    self_consistency_tie_behavior: Literal["first", "lexicographic"] = "first"
    deterministic_judge: JudgeFn | None = None

    def resolved_max_turns(self, competition_id: str) -> int:
        if self.rounds is not None:
            return self.rounds
        if self.decentralized_events is not None:
            return self.decentralized_events
        if self.max_turns is not None:
            return self.max_turns
        return resolve_contest_budget(competition_id).max_turns


def _apply_budget_config(env, config: CollabConfig) -> None:
    configured_turns = (
        config.rounds
        if config.rounds is not None
        else config.decentralized_events
        if config.decentralized_events is not None
        else config.max_turns
        if config.max_turns is not None
        else env.max_turns
    )
    budget = resolve_contest_budget(
        env.competition_id,
        max_turns=configured_turns,
        max_api_calls=(
            config.max_api_calls
            if config.max_api_calls is not None
            else env.max_api_calls
        ),
        max_output_tokens_per_call=(
            config.max_output_tokens_per_call
            if config.max_output_tokens_per_call is not None
            else env.max_output_tokens_per_call
        ),
        max_total_tokens=(
            config.max_total_tokens
            if config.max_total_tokens is not None
            else env.max_total_tokens
        ),
    )
    env.budget = budget
    env.max_turns = budget.max_turns
    env.max_api_calls = budget.max_api_calls
    env.max_output_tokens_per_call = budget.max_output_tokens_per_call
    env.max_total_tokens = budget.max_total_tokens
    env.record_budget_snapshot("budget_configured")


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


def _format_constraints(values: list[str]) -> str:
    return "\n".join(f"- {value}" for value in values) or "(none listed)"


def _system_prompt(env, role: str) -> str:
    meta = env.get_metadata()
    task_type = str(env.problem_data.get("task_type") or "")
    programming_contest = task_type in {"algorithmic_programming", "programming"} or (
        (env.problem_data.get("evaluation") or {}).get("evaluator_id")
        == "programming_judge"
    )
    tools = build_action_instructions(
        env.get_available_tools(),
        programming_contest=programming_contest,
        structured_deliberation=bool(
            env.rules_mode is RulesMode.ENFORCED
            and env.rule_card
            and env.rule_card.deliberation.get("mode") == "structured"
        ),
        private_notes=env.rules_mode is RulesMode.ENFORCED,
    )
    if env.rule_card is not None:
        card = env.rule_card
        visible = agent_view(card, team_size=env.team_size)
        assigned = _role_lookup(env, role)
        expertise = []
        for category in assigned.rule_expertise:
            expertise.append(f"{category.replace('_', ' ').title()}:")
            expertise.extend(f"- {item}" for item in card.rule_sections.get(category, []))
        resources = describe_resources(visible["resources"])
        return (
            f"You are {assigned.name}, title: {assigned.title}.\n"
            f"You are a contestant on a {meta['competition_id']} team of "
            f"{meta['team_size']} agents.\n"
            f"Problem: {meta.get('title') or meta['problem_id']} "
            f"({meta.get('year', 'n/a')})\n"
            f"Runtime tools: {meta['allowed_tools'] or 'none'}\n\n"
            f"Competition rule profile: {card.profile} ({card.protocol}).\n"
            f"{card.rules_text}\n\n"
            "=== CONTESTANT-VISIBLE COMPETITION RULES ===\n"
            f"{_format_constraints(list(card.human_constraints))}\n"
            f"{resources}\n\n"
            "=== COLLABORATION AND RESOURCE RULES ===\n"
            f"{_format_constraints(list(card.agent_constraints))}\n"
            f"Declared tools: {list(card.allowed_tools) or 'none'}\n"
            f"Communication policy: {card.communication}\n"
            f"Deliberation policy: {card.deliberation}\n\n"
            "=== YOUR ROLE DUTIES ===\n"
            f"{_format_constraints(list(assigned.duties))}\n"
            f"May submit final answer: {'yes' if assigned.may_submit else 'no'}\n"
            + (
                "\n=== YOUR RULE EXPERTISE ===\n" + "\n".join(expertise) + "\n"
                if expertise
                else ""
            )
            + f"\n{tools}"
        )
    return (
        f"You are {role} on a {meta['competition_id']} team of {meta['team_size']} agents.\n"
        f"Problem: {meta.get('title') or meta['problem_id']} ({meta.get('year', 'n/a')})\n"
        f"Allowed tools: {meta['allowed_tools'] or 'none'}\n\n"
        f"{tools}"
    )


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
    private_notes = (
        env.get_private_notes(agent_name) or "(empty)"
        if env.rules_mode is RulesMode.ENFORCED
        else None
    )
    observations = env.consume_agent_observations(agent_name)
    private_result = ""
    if observations:
        heading = (
            "=== YOUR LAST TOOL RESULT ==="
            if len(observations) == 1
            else "=== YOUR LAST TOOL RESULTS ==="
        )
        rendered = "\n\n".join(
            f"Turn {item['turn']} | action={item['action']} | "
            f"visibility={item['visibility']}\n{item['result']}"
            for item in observations
        )
        private_result = f"{heading}\n{rendered}\n\n"
    private_section = (
        f"=== YOUR PRIVATE NOTES ===\n{private_notes}\n\n"
        if private_notes is not None
        else ""
    )
    return f"""{private_result}=== SCHEMA ===
{schema_note}

=== PROBLEM ===
{state['problem_statement']}

=== TEAM DISCUSSION ===
{_discussion_history(env)}

=== SHARED SCRATCHPAD ===
{scratchpad}

{private_section}\
=== YOUR TURN ===
You are {agent_name}.
Turn budget (time): {state['turn_status']}
API budget (cost): {state['api_call_status']}
Token budget (team output): {state['token_status']} (cap {state['output_token_cap_per_call']} tokens/call)
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
    progress: Callable[[str], None] | None = None,
) -> None:
    if _should_stop(env):
        return
    if progress:
        progress(f"Turn {env.current_turn}/{env.max_turns} — {agent} thinking...")
    try:
        response = query(
            _system_prompt(env, agent),
            _agent_user_prompt(env, agent, schema_note, extra=extra),
        )
    except TurnLimitExceededError:
        if progress:
            progress("API/turn budget exhausted — stopping agent calls.")
        return
    apply_agent_response(env, agent, response, submitters=submitters)


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
    agents = [role.name for role in _roster(env)]

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
        submitters = {role.name for role in _roster(env) if role.may_submit}
        _run_synthesis(
            env,
            query,
            schema_note,
            next(iter(submitters), agents[0]),
            submitters=submitters,
            progress=config.progress,
        )

    return _result(env, "round_table")


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
    roster = _roster(env)
    leader_role = next((role for role in roster if role.may_submit), roster[0])
    leader = leader_role.name if env.rule_card is not None else "Group_Leader"
    workers = [role.name for role in roster if role.name != leader]

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
                f"You are the coordinator. Assign sub-tasks to {workers}. "
                "Output your delegation plan."
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
            submitters={leader},
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
    agents = [role.name for role in _roster(env)]

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
        submitters = {role.name for role in _roster(env) if role.may_submit}
        _run_synthesis(
            env,
            query,
            schema_note,
            next(iter(submitters), agents[0]),
            submitters=submitters,
            progress=config.progress,
        )

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


def _isolated_prompt(
    env,
    agent_name: str,
    instruction: str,
    extra: str = "",
) -> tuple[str, str]:
    """Build a prompt without team history, scratchpad, or other candidates."""
    system = _system_prompt(env, agent_name)
    user = (
        f"=== PROBLEM ===\n{env._problem_statement()}\n\n"
        f"=== ASSIGNMENT ===\n{instruction}"
    )
    if extra:
        user += f"\n\n{extra}"
    return system, user


def _numbered_answers(text: str) -> dict[int, str]:
    matches = list(re.finditer(r"(?m)^\s*(\d+)\s*[\.\)]\s*(.+?)\s*$", text))
    return {int(match.group(1)): match.group(2).strip() for match in matches}


def aggregate_numbered_answers(
    candidates: list[str],
    *,
    tie_behavior: Literal["first", "lexicographic"] = "first",
) -> str:
    parsed = [_numbered_answers(candidate) for candidate in candidates]
    part_numbers = sorted({number for answer in parsed for number in answer})
    rows: list[str] = []
    for number in part_numbers:
        values = [answer[number] for answer in parsed if number in answer]
        counts = Counter(values)
        best_count = max(counts.values())
        tied = [value for value, count in counts.items() if count == best_count]
        selected = min(tied) if tie_behavior == "lexicographic" else next(
            value for value in values if value in tied
        )
        rows.append(f"{number}. {selected}")
    if rows:
        return "\n".join(rows)
    if not candidates:
        return ""
    counts = Counter(candidate.strip() for candidate in candidates)
    best_count = max(counts.values())
    tied = [value for value, count in counts.items() if count == best_count]
    return min(tied) if tie_behavior == "lexicographic" else next(
        candidate.strip() for candidate in candidates if candidate.strip() in tied
    )


def run_self_consistency(
    env, query_llm_fn: QueryFn, config: CollabConfig | None = None
) -> dict:
    """Generate isolated candidates and aggregate numbered answers deterministically."""
    config = config or CollabConfig()
    if config.sample_count < 1:
        raise ValueError("sample_count must be positive")
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    env.begin_turn()
    candidates: list[str] = []
    for index in range(config.sample_count):
        if _should_stop(env):
            break
        system, user = _isolated_prompt(
            env,
            "Solo",
            "Independently solve the complete task. Return a numbered answer sheet.",
            f"Independent sample {index + 1}/{config.sample_count}.",
        )
        candidates.append(query(system, user))
    final = aggregate_numbered_answers(
        candidates,
        tie_behavior=config.self_consistency_tie_behavior,
    )
    if final:
        env.execute_action("Solo", "submit_final", final)
    result = _result(env, "self_consistency")
    result.update({"candidates": candidates, "aggregation": "per_part_majority"})
    return result


def run_memory_solo(
    env, query_llm_fn: QueryFn, config: CollabConfig | None = None
) -> dict:
    """Solo baseline with bounded private memory and no shared team state."""
    config = config or CollabConfig()
    if config.memory_bound < 1:
        raise ValueError("memory_bound must be positive")
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    memory = MemoryStore(["Solo"])
    candidates: list[str] = []
    while not _should_stop(env) and env.can_begin_turn():
        turn = env.begin_turn()
        recalled = memory.recall("Solo", scope="private", top_k=config.memory_bound)
        system, user = _isolated_prompt(
            env,
            "Solo",
            "Solve alone and refine a complete answer using only your bounded notes.",
            f"Turn {turn}. YOUR PERSISTENT NOTES:\n{memory.render(recalled)}",
        )
        try:
            response = query(system, user)
        except TurnLimitExceededError:
            break
        candidates.append(response)
        memory.add("Solo", response, turn=turn)
    final = candidates[-1].strip() if candidates else ""
    if final:
        env.execute_action("Solo", "submit_final", final)
    snapshot = memory.snapshot()
    snapshot["private"]["Solo"] = snapshot["private"]["Solo"][-config.memory_bound :]
    result = _result(env, "memory_solo")
    result.update(
        {
            "memory": snapshot,
            "memory_bound": config.memory_bound,
            "candidates": candidates,
        }
    )
    return result


def run_subagent(
    env, query_llm_fn: QueryFn, config: CollabConfig | None = None
) -> dict:
    """Fixed orchestrator with stateless, mutually invisible workers."""
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    env.begin_turn()
    orchestrator = "Orchestrator"
    system, user = _isolated_prompt(
        env,
        orchestrator,
        f"Decompose the task into exactly {env.team_size} independent assignments.",
    )
    plan = query(system, user)
    assignments = _numbered_answers(plan)
    worker_outputs: list[dict[str, str]] = []
    for index in range(1, env.team_size + 1):
        if _should_stop(env):
            break
        worker = f"Worker_{index}"
        assignment = assignments.get(index, f"Solve slice {index} of {env.team_size}.")
        system, user = _isolated_prompt(
            env,
            worker,
            "Solve only the assigned slice. You cannot see or contact other workers.",
            f"ORCHESTRATOR ASSIGNMENT:\n{assignment}",
        )
        try:
            output = query(system, user)
        except TurnLimitExceededError:
            break
        worker_outputs.append(
            {"worker": worker, "assignment": assignment, "output": output}
        )
    final = ""
    if not _should_stop(env):
        context = "\n\n".join(
            f"{item['worker']} ({item['assignment']}):\n{item['output']}"
            for item in worker_outputs
        )
        system, user = _isolated_prompt(
            env,
            orchestrator,
            "Aggregate the worker returns into the complete final answer only.",
            f"DECOMPOSITION:\n{plan}\n\nWORKER RETURNS:\n{context}",
        )
        final = query(system, user)
        env.execute_action(orchestrator, "submit_final", final)
    result = _result(env, "subagent")
    result.update(
        {
            "decomposition": plan,
            "worker_outputs": worker_outputs,
            "worker_isolation": True,
        }
    )
    return result


def run_debate(
    env, query_llm_fn: QueryFn, config: CollabConfig | None = None
) -> dict:
    """Independent proposals followed by challenge, revision, and decision."""
    config = config or CollabConfig()
    if config.debate_rounds < 1:
        raise ValueError("debate_rounds must be positive")
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    agents = [f"Agent_{index + 1}" for index in range(env.team_size)]
    events: list[dict[str, Any]] = []
    proposals: dict[str, str] = {}
    env.begin_turn()
    for index, agent in enumerate(agents, start=1):
        system, user = _isolated_prompt(
            env,
            agent,
            "Produce an independent substantive solution proposal.",
        )
        proposals[f"P{index}"] = query(system, user)
        events.append({"phase": "propose", "agent": agent, "proposal_id": f"P{index}"})
    for round_index in range(config.debate_rounds):
        if _should_stop(env):
            break
        if env.can_begin_turn():
            env.begin_turn()
        for index, agent in enumerate(agents):
            target = f"P{(index + round_index + 1) % len(agents) + 1}"
            system, user = _isolated_prompt(
                env,
                agent,
                f"Challenge {target} with concise evidence.",
                f"PROPOSAL:\n{proposals[target]}",
            )
            query(system, user)
            events.append({"phase": "challenge", "agent": agent, "proposal_id": target})
        for index, agent in enumerate(agents, start=1):
            proposal_id = f"P{index}"
            system, user = _isolated_prompt(
                env,
                agent,
                f"Revise your proposal {proposal_id} after the challenge round.",
                f"ORIGINAL:\n{proposals[proposal_id]}",
            )
            proposals[proposal_id] = query(system, user)
            events.append(
                {"phase": "revise", "agent": agent, "proposal_id": proposal_id}
            )
    for proposal_id in proposals:
        events.append(
            {"phase": "decide", "agent": agents[0], "proposal_id": proposal_id}
        )
    if not _should_stop(env):
        rendered = "\n\n".join(
            f"{proposal_id}: {proposal}" for proposal_id, proposal in proposals.items()
        )
        system, user = _isolated_prompt(
            env,
            agents[0],
            "Synthesize the decided proposals into the final answer only.",
            rendered,
        )
        env.execute_action(agents[0], "submit_final", query(system, user))
    counts = Counter(event["phase"] for event in events)
    result = _result(env, "debate")
    result.update(
        {
            "debate": {"counts": dict(counts), "proposals": proposals},
            "structured_events": events,
            "synthesizer": agents[0],
        }
    )
    return result


def run_liveoi_best_of_8(
    env, query_llm_fn: QueryFn, config: CollabConfig | None = None
) -> dict:
    """Generate eight isolated candidates and select only with an explicit judge."""
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    query = _budgeted_query(env, query_llm_fn, config)
    env.begin_turn()
    candidates: list[str] = []
    for index in range(8):
        if _should_stop(env):
            break
        system, user = _isolated_prompt(
            env,
            "Solo",
            "Independently produce one complete final answer or source file.",
            f"Candidate {index + 1}/8.",
        )
        candidates.append(query(system, user))
    scores: list[float] | None = None
    selected_index: int | None = None
    if config.deterministic_judge is not None and candidates:
        scores = [float(config.deterministic_judge(item)) for item in candidates]
        selected_index = max(
            range(len(candidates)),
            key=lambda index: (scores[index], -index),
        )
        env.execute_action("Solo", "submit_final", candidates[selected_index])
    result = _result(env, "liveoi_best_of_8")
    result.update(
        {
            "candidates": candidates,
            "selection_available": selected_index is not None,
            "selected_index": selected_index,
            "judge_scores": scores,
        }
    )
    return result


def run_open_table_coach(
    env, query_llm_fn: QueryFn, config: CollabConfig | None = None
) -> dict:
    """Round table with one non-submitting coach message before competition turns."""
    config = config or CollabConfig()
    _apply_budget_config(env, config)
    if not env.api_budget_exhausted():
        env.record_api_call()
        advice = env.apply_output_token_budget(
            query_llm_fn(
                "You are a non-competing coach. Give concise strategic advice only.",
                f"Problem:\n{env._problem_statement()}",
            )
        )
        env.execute_action("Coach", "speak", advice)
    result = run_round_table(env, query_llm_fn, config)
    result["schema"] = "open_table_coach"
    result["coach_advice"] = advice if "advice" in locals() else ""
    return result


def _result(env, schema: str) -> dict:
    fallback_roster = [
        {
            "name": f"Agent_{index + 1}",
            "title": "captain and synthesizer" if index == 0 else "team specialist",
            "may_submit": index == 0,
        }
        for index in range(env.team_size)
    ]
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
        "roster": (
            [
                {
                    "name": role.name,
                    "title": role.title,
                    "may_submit": role.may_submit,
                }
                for role in _roster(env)
            ]
            if env.rule_card is not None
            else fallback_roster
        ),
        **env.rules_metadata(),
    }


SCHEMAS: dict[SchemaName, Callable] = {
    "round_table": run_round_table,
    "centralized": run_centralized,
    "decentralized": run_decentralized,
    "single_agent": run_single_agent,
    "open_table_coach": run_open_table_coach,
    "debate": run_debate,
    "self_consistency": run_self_consistency,
    "memory_solo": run_memory_solo,
    "subagent": run_subagent,
    "liveoi_best_of_8": run_liveoi_best_of_8,
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
