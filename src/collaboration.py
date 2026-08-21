from dataclasses import dataclass
from typing import Callable, Literal

from actions import apply_agent_response, build_action_instructions, parse_agent_response
from rules.describe import describe_resources
from rules.models import AgentRole

SchemaName = Literal["round_table", "centralized", "decentralized"]
QueryFn = Callable[[str, str], str]


@dataclass
class CollabConfig:
  rounds: int = 2
  decentralized_events: int = 3
  synthesize: bool = True
  progress: Callable[[str], None] | None = None


def _roster(env) -> list[AgentRole]:
    if getattr(env, "rule_card", None) is not None:
        return env.rule_card.roster(env.team_size)
    return [
        AgentRole(
            name=f"Agent_{index + 1}",
            title=(
                "captain and synthesizer"
                if index == 0
                else "primary solver"
                if index == 1
                else "independent verifier"
                if index == 2
                else "specialist and completeness checker"
            ),
            duties=(),
            may_submit=index == 0,
        )
        for index in range(env.team_size)
    ]


def _submitters(env) -> set[str]:
    return {role.name for role in _roster(env) if role.may_submit} or {"Agent_1"}


def _role_lookup(env, agent_name: str) -> AgentRole:
    for role in _roster(env):
        if role.name == agent_name:
            return role
    return AgentRole(name=agent_name, title=agent_name, duties=(), may_submit=False)


def _format_constraints(constraints: list[str]) -> str:
    if not constraints:
        return "(no additional human constraints listed)"
    return "\n".join(f"- {item}" for item in constraints)


def _format_duties(role: AgentRole) -> str:
    if not role.duties:
        return "- Contribute useful work and respect team process."
    return "\n".join(f"- {item}" for item in role.duties)


def _format_roster(env) -> str:
    return "\n".join(
        f"- {role.name}: {role.title}"
        + (" [may submit]" if role.may_submit else "")
        for role in _roster(env)
    )


def _deliverable_line(deliverable: dict) -> str:
    name = str(deliverable.get("official_deliverable") or "").strip()
    if not name:
        return ""
    return f"Official deliverable: {name.replace('_', ' ')}\n"


def _can_access(env, agent_name: str, category: str) -> bool:
    card = env.rule_card
    if card is None or card.information_policy.get("mode") == "shared":
        return True
    if (
        card.information_policy.get("mode") == "role_specialized"
        and category == "contest_rules"
    ):
        return True
    return card.role_can_access(agent_name, category)


def _system_prompt(env, agent_name: str) -> str:
    meta = env.get_metadata()
    role = _role_lookup(env, agent_name)
    rule = meta.get("rule") or {}
    structured_deliberation = (
        (rule.get("deliberation") or {}).get("mode") == "structured"
    )
    limited_communication = (
        (rule.get("communication") or {}).get("mode") == "limited"
    )
    tools = build_action_instructions(
        env.get_available_tools(),
        structured_deliberation=structured_deliberation,
    )
    constraints = rule.get("human_constraints") or []
    agent_constraints = rule.get("agent_constraints") or []
    answer_format = rule.get("answer_format") or ""
    resources = rule.get("resources") or {}
    rule_header = ""
    sees_rules = _can_access(env, agent_name, "contest_rules")
    if rule and sees_rules:
        rule_header = (
            f"Competition rule profile: {rule['profile']} ({rule['protocol']}).\n"
            f"Official/adapted rules summary: {rule['rules_text']}\n"
        )
    elif rule:
        rule_header = (
            "Private information boundary: the full contest-rules packet is not "
            "included in your briefing. Ask a teammate to communicate constraints "
            "that affect your work.\n"
        )
    resource_prose = describe_resources(resources) if resources else ""
    resource_line = f"Resource rules: {resource_prose}\n" if resource_prose else ""
    answer_line = (
        f"Required answer format:\n{answer_format}\n"
        if answer_format and sees_rules
        else ""
    )
    deliverable_line = (
        _deliverable_line(rule.get("deliverable") or {}) if sees_rules else ""
    )
    visible_constraints = constraints if sees_rules else []
    rules_heading = (
        "HUMAN CONTEST RULES (BINDING)"
        if sees_rules
        else "CONTEST RULES AVAILABLE TO YOU"
    )
    deliberation_guidance = ""
    if structured_deliberation:
        deliberation_guidance = (
            "\n=== DISAGREEMENT PROTOCOL ===\n"
            "Do not bury substantive disagreement in generic chat. Open a proposal, "
            "challenge it with reasons, attach evidence, revise when warranted, and "
            "leave the designated submitter a traceable decision. Prefer evidence "
            "over role authority or vote count.\n"
        )
    specialty_guidance = ""
    if role.rule_expertise and env.rule_card is not None:
        specialty_lines = []
        for category in role.rule_expertise:
            rules = env.rule_card.rule_sections.get(category) or []
            specialty_lines.append(f"{category.replace('_', ' ').title()}:")
            specialty_lines.extend(f"- {item}" for item in rules)
        specialty_guidance = (
            "\n=== YOUR RULE SPECIALTY ===\n"
            "Every teammate can consult the complete rules. You are primarily "
            "responsible for tracking and communicating these sections:\n"
            + "\n".join(specialty_lines)
            + "\n"
        )
    communication_guidance = ""
    if limited_communication:
        policy = rule["communication"]
        communication_guidance = (
            "\n=== LIMITED COMMUNICATION BUDGET ===\n"
            f"The team may send {policy['team_message_budget']} counted messages; "
            f"you may send at most {policy['per_agent_message_budget']}. "
            f"Each message is capped at {policy['max_message_chars']} characters. "
            "Broadcast only information that changes another teammate's work. Use "
            "write_private_notes for independent analysis; private notes are visible "
            "only to you and cost no communication budget.\n"
        )
    return (
        f"You are {role.name}, title: {role.title}.\n"
        f"You must behave like a human contestant on a {meta['competition_id']} team "
        f"of {meta['team_size']}.\n"
        f"Problem: {meta.get('title') or meta['problem_id']} ({meta.get('year', 'n/a')})\n"
        f"Allowed tools: {meta['allowed_tools'] or 'none'}\n"
        f"{resource_line}"
        f"{deliverable_line}"
        f"{rule_header}\n"
        f"=== {rules_heading} ===\n"
        f"{_format_constraints(visible_constraints)}\n"
        f"\n=== AGENT COLLABORATION RULES ===\n"
        f"{_format_constraints(agent_constraints)}\n"
        f"{specialty_guidance}\n"
        f"{communication_guidance}\n"
        f"{deliberation_guidance}\n"
        f"=== YOUR ROLE DUTIES ===\n"
        f"{_format_duties(role)}\n"
        f"May submit final answer: {'yes' if role.may_submit else 'no — advise only'}\n\n"
        f"=== TEAM ROSTER ===\n"
        f"{_format_roster(env)}\n\n"
        f"{answer_line}\n"
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
    role = _role_lookup(env, agent_name)
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
You are {role.name} ({role.title}).
Turn budget: {state['turn_status']}
Communication budget: {env.communication.status_for(agent_name)}
Submitted: {state['submitted']}
Obey the binding human contest rules and your role duties.
{extra}
What is your contribution?"""


def _count_numbered_parts(text: str) -> int:
    import re
    return len(re.findall(r"(?:^|\n)\s*\d+\s*[\.\)]", text))


def _synthesis_system_prompt(env, synthesizer: str) -> str:
    meta = env.get_metadata()
    rule = meta.get("rule") or {}
    answer_format = rule.get("answer_format") or (
        "Output ONLY the numbered answer sheet. No ACTION lines, no commentary."
    )
    constraints = (
        rule.get("human_constraints") or []
        if _can_access(env, synthesizer, "contest_rules")
        else []
    )
    agent_constraints = rule.get("agent_constraints") or []
    return (
        f"You are {synthesizer}, writing the team's official final answer for "
        f"{meta['competition_id']} ({meta.get('year', 'n/a')}).\n"
        f"Binding constraints:\n{_format_constraints(constraints)}\n\n"
        f"Agent collaboration rules:\n"
        f"{_format_constraints(agent_constraints)}\n\n"
        f"Answer format:\n{answer_format}\n"
        "Output only the final answer content. No ACTION lines."
    )


def _final_answer_instructions(env) -> str:
    rule = (env.get_metadata().get("rule") or {})
    if rule.get("answer_format"):
        return (
            "Write the team's COMPLETE final answer using this format:\n"
            f"{rule['answer_format']}\n"
            "Compile the best answers from the discussion and scratchpad."
        )
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

=== DELIBERATION LEDGER ===
{state['deliberation']}

=== COMMUNICATION BUDGET REPORT ===
{state['communication']}

=== FINAL TEAM ANSWER ===
{instructions}"""


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
    scoring_mode = ""
    if getattr(env, "rule_card", None) is not None:
        from rules.views import grader_view

        scoring_mode = (grader_view(env.rule_card).get("scoring") or {}).get("mode")
    target_parts = 5 if scoring_mode != "gold" or env.problem_data.get("task_type") in {
        "team_contest",
        "team_power",
        "team_practical",
        "guts_round",
    } else 1

    for attempt in range(2):
        _log(f"{synthesizer} synthesizing final answer (attempt {attempt + 1})...")
        system = _synthesis_system_prompt(env, synthesizer)
        user = _synthesis_prompt(env, schema_note)
        if attempt > 0 and target_parts >= 5:
            user += (
                "\n\nREMINDER: Your previous submission was incomplete. "
                "You MUST include ALL numbered problems."
            )
        response = query_llm_fn(system, user)
        if env.submitted:
            env.workspace["final_answer"] = ""
            env.submitted = False
            env.submitted_by = None

        parts = _submit_synthesis_response(env, synthesizer, response)
        answer = env.workspace.get("final_answer", "")
        if parts > best_parts:
            best_parts = parts
            best_answer = answer

        if parts >= target_parts:
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
    Schema A: Round Table — every agent sees the full conversation, takes turns.
    """
    config = config or CollabConfig()
    schema_note = "Round Table: all agents see full history; strict turn order."
    roster = _roster(env)
    submitters = _submitters(env)

    for _round in range(config.rounds):
        for role in roster:
            if env.submitted:
                break
            if config.progress:
                config.progress(
                    f"Round {_round + 1}/{config.rounds} — {role.name} ({role.title}) thinking..."
                )
            system = _system_prompt(env, role.name)
            user = _agent_user_prompt(
                env,
                role.name,
                schema_note,
                extra=f"Round {_round + 1} of {config.rounds}.",
            )
            response = query_llm_fn(system, user)
            apply_agent_response(env, role.name, response, submitters=submitters)

    if config.synthesize:
        _run_synthesis(
            env,
            query_llm_fn,
            schema_note,
            next(role.name for role in roster if role.may_submit),
            submitters=submitters,
            progress=config.progress,
        )

    return _result(env, "round_table")


def run_centralized(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema B: Centralized — coordinator delegates, aggregates, and submits.
    """
    config = config or CollabConfig()
    roster = _roster(env)
    leader = next((role for role in roster if role.may_submit), roster[0])
    workers = [role for role in roster if role.name != leader.name]
    schema_note = (
        f"Centralized: {leader.name} ({leader.title}) delegates; "
        "only the designated submitter finalizes the answer."
    )

    state = env.get_state()
    system = _system_prompt(env, leader.name)
    worker_names = ", ".join(role.name for role in workers) or "(no workers)"
    user = (
        f"=== PROBLEM ===\n{state['problem_statement']}\n\n"
        f"You are the team coordinator ({leader.title}). Assign sub-tasks to {worker_names}. "
        "Output your delegation plan."
    )
    if config.progress:
        config.progress(f"{leader.name} planning delegation...")
    plan = query_llm_fn(system, user)
    env.execute_action(leader.name, "speak", f"Delegation plan: {plan}")

    for peer in workers:
        if env.submitted:
            break
        if config.progress:
            config.progress(f"{peer.name} ({peer.title}) working on assigned slice...")
        system = _system_prompt(env, peer.name)
        user = _agent_user_prompt(
            env,
            peer.name,
            schema_note,
            extra=f"Leader's plan:\n{plan}\n\nComplete your assigned slice. You may use allowed tools.",
        )
        response = query_llm_fn(system, user)
        apply_agent_response(env, peer.name, response, submitters=set())

    if config.synthesize and not env.submitted:
        _run_synthesis(
            env,
            query_llm_fn,
            schema_note,
            leader.name,
            submitters={leader.name},
            progress=config.progress,
        )

    return _result(env, "centralized")


def run_decentralized(env, query_llm_fn: QueryFn, config: CollabConfig | None = None) -> dict:
    """
    Schema C: Decentralized — agents work independently, coordinate via shared state.
    """
    config = config or CollabConfig()
    schema_note = "Decentralized: no leader; peers update scratchpad/tools directly."
    roster = _roster(env)
    submitters = _submitters(env)

    for _event in range(config.decentralized_events):
        for role in roster:
            if env.submitted:
                break
            if config.progress:
                config.progress(
                    f"Event {_event + 1}/{config.decentralized_events} — "
                    f"{role.name} ({role.title}) thinking..."
                )
            system = _system_prompt(env, role.name)
            user = _agent_user_prompt(
                env,
                role.name,
                schema_note,
                extra="Coordinate directly with peers. No manager.",
            )
            response = query_llm_fn(system, user)
            apply_agent_response(env, role.name, response, submitters=submitters)

    if config.synthesize and not env.submitted:
        synthesizer = next(role.name for role in roster if role.may_submit)
        _run_synthesis(
            env,
            query_llm_fn,
            schema_note,
            synthesizer,
            submitters=submitters,
            progress=config.progress,
        )

    return _result(env, "decentralized")


def _result(env, schema: str) -> dict:
    meta = env.get_metadata()
    evaluation = None
    if getattr(env, "rule_card", None) is not None:
        from rules.views import grader_view

        evaluation = {
            "scoring": grader_view(env.rule_card).get("scoring") or {},
        }
    return {
        "schema": schema,
        "problem_id": env.problem_id,
        "competition_id": env.competition_id,
        "submitted": env.submitted,
        "submitted_by": env.submitted_by,
        "turns_used": env.current_turn,
        "chat_messages": len(env.chat_history),
        "final_answer": env.workspace.get("final_answer", ""),
        "grade": env.grade_submission(),
        "deliberation": env.deliberation.report(),
        "communication": env.communication.report(),
        "rule": meta.get("rule"),
        "evaluation": evaluation,
        "roster": meta.get("rule", {}).get("agent_roles") if meta.get("rule") else [
            {"name": role.name, "title": role.title, "may_submit": role.may_submit}
            for role in _roster(env)
        ],
    }


SCHEMAS: dict[SchemaName, Callable] = {
    "round_table": run_round_table,
    "centralized": run_centralized,
    "decentralized": run_decentralized,
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
