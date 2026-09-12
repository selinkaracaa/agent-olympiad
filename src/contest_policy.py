"""Baseline action gating, task routing, and opening-plan normalization."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any

import otc_runtime
from contest_actions import _is_answer_sheet_contest, _next_task, _task_complete, _task_has_independent_approval, _contest_complete
from contest_manifest import ContestManifest
from contest_memory import ContestMemory
from contest_session import ContestSession, TaskState, TaskUnit
from rulecard_policy import MESSAGE_ACTION_NAMES, WORKSTATION_ACTION_NAMES
from strategy import StrategicPolicy
from tool_registry import ACTION_REGISTRY, DELIBERATION_ACTION_NAMES, DESK_READONLY_ACTION_NAMES, LEADER_ACTION_NAMES, MEMORY_ACTION_NAMES, ActionSpec, resolve_actions

from contest_config import ContestRunConfig


from contest_prompts import (
    _needs_programming_source,
    _pending_review_queue,
)

def _resolved_actions(
    manifest: ContestManifest,
    config: ContestRunConfig | None = None,
) -> frozenset[ActionSpec]:
    """Baseline-level action surface; per-turn gating lives in _actions_for_agent."""
    specs: set[ActionSpec] = set()
    handlers = set(ACTION_REGISTRY)
    for task in manifest.tasks:
        benchmark = task.benchmark
        declared = set(benchmark.get("available_capabilities") or ())
        assets = benchmark.get("assets") or []
        if any("lab" in str(asset).lower() for asset in assets):
            declared.add("read_lab_equipment")
        if any("star" in str(asset).lower() for asset in assets):
            declared.add("read_star_chart")
        requirements = dict(benchmark.get("tool_requirements") or {})
        specs.update(
            resolve_actions(
                competition=manifest.competition_id,
                task_type=task.task_type,
                benchmark_requirements=requirements,
                declared_capabilities=declared,
                registered_handlers=handlers,
                runtime="session",
            )
        )
    if config is not None and config.otc_policy is not None:
        # Card-declared competition-specific bundle on top of the common set.
        if config.otc_policy.structured_deliberation:
            specs.update(ACTION_REGISTRY[name] for name in DELIBERATION_ACTION_NAMES)
        if "submit_code" not in config.otc_policy.allowed_actions:
            specs.discard(ACTION_REGISTRY["submit_code"])
    if _is_answer_sheet_contest(manifest):
        submit = ACTION_REGISTRY["submit"]
        specs.discard(submit)
        specs.discard(ACTION_REGISTRY["request_review"])
        specs.add(
            replace(
                submit,
                description=(
                    "Submit the complete current answer sheet once and end the contest."
                ),
                arguments=(),
            )
        )
    if manifest.metadata.get("artifact_contract"):
        # Artifact delivery exposes collaboration actions; external research/lab
        # tools need their own adapter and must not silently claim availability.
        specs = {spec for spec in specs if spec.pack in {"common", "desk", "memory", "deliberation"}
                 or spec.name in {"review_answer", "request_review", "direct_message"}}
    if config is not None:
        specs = _trim_to_baseline(specs, config)
    return frozenset(specs)


def _trim_to_baseline(
    specs: set[ActionSpec],
    config: ContestRunConfig,
) -> set[ActionSpec]:
    """Drop the optional action bundles a baseline does not include."""
    features = config.features
    hidden: set[str] = set()
    if features.basic_open_table:
        hidden |= DELIBERATION_ACTION_NAMES | {"review_answer", "request_review"}
    if not features.memory_actions:
        hidden |= MEMORY_ACTION_NAMES
    if not features.desk_actions:
        hidden |= DESK_READONLY_ACTION_NAMES
    if not features.private_channel or config.team_size < 2:
        hidden.add("direct_message")
    if not features.leader_submits:
        hidden |= LEADER_ACTION_NAMES
    if features.coach == "card":
        # Discussion and independent review coexist; Coach never assigns tasks.
        hidden |= {"assign_problem"}
    return {spec for spec in specs if spec.name not in hidden}


def _card_submission_blocks(
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    memory: ContestMemory | None,
    *,
    answer_sheet_contest: bool,
) -> set[str]:
    """Hand-in actions the rule card withholds from this agent right now."""
    policy = config.otc_policy
    if policy is None:
        return set()
    hidden: set[str] = set()
    if not policy.may_submit(agent):
        hidden |= {"submit", "submit_code", "finish_contest"}
    # Actions that end the whole contest wait for the card's minimum length
    # and, under structured deliberation, for the required challenges.
    ending = {"finish_contest"} | ({"submit"} if answer_sheet_contest else set())
    if session.budget.turns_used < policy.min_turns:
        hidden |= ending
    if (
        policy.structured_deliberation
        and memory is not None
        and otc_runtime.challenge_count(memory) < policy.min_challenges
    ):
        hidden |= ending
    return hidden


def _card_gate(
    available: frozenset[ActionSpec],
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    memory: ContestMemory | None,
    *,
    answer_sheet_contest: bool,
) -> frozenset[ActionSpec]:
    """Apply the rule card's per-turn restrictions (``otc`` baseline only)."""
    policy = config.otc_policy
    if policy is None or memory is None:
        return available
    names = {spec.name for spec in available}
    hidden = _card_submission_blocks(
        session, config, agent, memory, answer_sheet_contest=answer_sheet_contest
    )
    if policy.structured_deliberation and not policy.may_decide(agent):
        hidden.add("decide")
    open_proposals: tuple[str, ...] = ()
    if policy.structured_deliberation:
        open_proposals = tuple(
            otc_runtime.deliberation_ledger(memory).report()["open_proposals"]
        )
        if not open_proposals:
            # Nothing to challenge, support, revise or decide yet: offering
            # these only produces "unknown proposal" errors.
            hidden |= DELIBERATION_ACTION_NAMES - {"propose"}
    active = session.active_task
    current_turn = session.budget.turns_used
    if active is not None and active.kind == "programming":
        if policy.workstation_lease:
            holder = otc_runtime.workstation_holder(
                memory, active.task_id, current_turn=current_turn
            )
            if holder is not None and holder != agent:
                hidden |= WORKSTATION_ACTION_NAMES
        if otc_runtime.submission_pending(
            active,
            current_turn=current_turn,
            latency_turns=policy.run_judging_latency_turns,
        ):
            hidden |= {"submit_code", "execute_code"}
    discussion = policy.discussion
    if (
        discussion.silent_work_turn_requires_discussion
        and otc_runtime.silent_work_streak(memory, agent) >= discussion.silent_work_turns
        and names & MESSAGE_ACTION_NAMES
    ):
        hidden |= {
            "work",
            "execute_code",
            "submit_code",
            "submit",
            "select_problem",
            "skip_problem",
            "finish_contest",
        }
    gated = set(spec for spec in available if spec.name not in hidden)
    if open_proposals:
        # Pin proposal_id to the proposals that are actually open.
        for spec in list(gated):
            if spec.name in DELIBERATION_ACTION_NAMES and spec.name != "propose":
                gated.discard(spec)
                gated.add(
                    replace(
                        spec,
                        arguments=tuple(
                            replace(argument, enum=open_proposals)
                            if argument.name == "proposal_id"
                            else argument
                            for argument in spec.arguments
                        ),
                    )
                )
    work_spec = next((spec for spec in gated if spec.name == "work"), None)
    if work_spec is not None:
        # The card allows exactly one action per turn, so switching problems
        # and recording work must be a single move: work(problem_id=...).
        # Pin the registry's optional problem_id to the problems still open.
        switchable = tuple(task.task_id for task in session.tasks if not task.locked)
        if switchable:
            gated.discard(work_spec)
            gated.add(
                replace(
                    work_spec,
                    description=(
                        "Record durable work for the team on your current problem, "
                        "or pass problem_id to switch to another problem and record "
                        "the work there in the same turn."
                    ),
                    arguments=tuple(
                        replace(
                            argument,
                            description=(
                                "Optional: the problem this work belongs to. "
                                "Omit to keep working on your current problem."
                            ),
                            required=False,
                            enum=switchable,
                        )
                        if argument.name == "problem_id"
                        else argument
                        for argument in work_spec.arguments
                    ),
                )
            )
    return frozenset(gated)


def _actions_for_agent(
    actions: frozenset[ActionSpec],
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    *,
    answer_sheet_contest: bool = False,
    review_targets: list[dict[str, str]] | None = None,
    reported_version_hashes: set[str] | None = None,
    work_task_ids: set[str] | None = None,
    review_task_ids: set[str] | None = None,
    answer_sheet_submit_ready: bool = False,
    required_answer_task_ids: set[str] | None = None,
    programming_source_required: bool = False,
    memory: ContestMemory | None = None,
) -> frozenset[ActionSpec]:
    """Per-turn, per-agent gating on top of the baseline action surface."""
    if programming_source_required and config.otc_policy is not None:
        # A source gate must not demand a machine action forbidden by the lease.
        legal = _card_gate(actions, session, config, agent, memory,
                           answer_sheet_contest=answer_sheet_contest)
        programming_source_required = any(spec.name == "execute_code" for spec in legal)
    base = _actions_for_agent_base(
        actions,
        session,
        config,
        agent,
        answer_sheet_contest=answer_sheet_contest,
        review_targets=review_targets,
        reported_version_hashes=reported_version_hashes,
        work_task_ids=work_task_ids,
        review_task_ids=review_task_ids,
        answer_sheet_submit_ready=answer_sheet_submit_ready,
        required_answer_task_ids=required_answer_task_ids,
        programming_source_required=programming_source_required,
        card_blocks_submit="submit"
        in _card_submission_blocks(
            session, config, agent, memory, answer_sheet_contest=answer_sheet_contest
        ),
    )
    return _card_gate(
        base, session, config, agent, memory, answer_sheet_contest=answer_sheet_contest
    )


def _actions_for_agent_base(
    actions: frozenset[ActionSpec],
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    *,
    answer_sheet_contest: bool = False,
    review_targets: list[dict[str, str]] | None = None,
    reported_version_hashes: set[str] | None = None,
    work_task_ids: set[str] | None = None,
    review_task_ids: set[str] | None = None,
    answer_sheet_submit_ready: bool = False,
    required_answer_task_ids: set[str] | None = None,
    programming_source_required: bool = False,
    card_blocks_submit: bool = False,
) -> frozenset[ActionSpec]:
    available = _trim_to_baseline(set(actions), config)
    review_enabled = config.review_required or (
        config.final_review_required and review_targets is not None
    )
    teammates = tuple(
        f"Agent_{index}"
        for index in range(1, config.team_size + 1)
        if f"Agent_{index}" != agent
    )
    direct_message = next(
        (spec for spec in available if spec.name == "direct_message"),
        None,
    )
    if direct_message is not None:
        by_name = {argument.name: argument for argument in direct_message.arguments}
        available.discard(direct_message)
        available.add(
            replace(
                direct_message,
                arguments=(
                    replace(by_name["recipients"], enum=teammates),
                    by_name["content"],
                ),
            )
        )
    # Desk actions that take a problem id get the concrete task list so the
    # model cannot invent identifiers.
    task_ids = tuple(task.task_id for task in session.tasks)
    for name in ("inspect_problem", "triage_problem", "remember", "recall"):
        spec = next((spec for spec in available if spec.name == name), None)
        if spec is None:
            continue
        available.discard(spec)
        available.add(
            replace(
                spec,
                arguments=tuple(
                    replace(argument, enum=task_ids)
                    if argument.name == "problem_id"
                    else argument
                    for argument in spec.arguments
                ),
            )
        )
    leader = config.leader
    if leader is not None:
        assign_spec = next(
            (spec for spec in available if spec.name == "assign_problem"), None
        )
        if assign_spec is not None:
            available.discard(assign_spec)
            if agent == leader and teammates:
                by_name = {arg.name: arg for arg in assign_spec.arguments}
                available.add(
                    replace(
                        assign_spec,
                        arguments=(
                            replace(by_name["agent"], enum=teammates),
                            replace(by_name["problem_ids"], enum=task_ids),
                            by_name["reason"],
                        ),
                    )
                )
        if config.features.leader_submits and agent != leader:
            # Workers draft and report; only the leader hands anything in.
            for name in ("submit", "submit_code", "finish_contest"):
                available = {spec for spec in available if spec.name != name}
    if not review_enabled:
        # Without the review workflow, keeping review actions visible created
        # an accidental rewrite/review loop on one task.
        available.discard(ACTION_REGISTRY["request_review"])
        available.discard(ACTION_REGISTRY["review_answer"])
    if not _contest_complete(session):
        # The handler rejects finish_contest until every task holds a valid
        # submission, so exposing it earlier only burns a turn (both variants).
        available.discard(ACTION_REGISTRY["finish_contest"])
    if answer_sheet_contest:
        available = {
            spec for spec in available if spec.name != "finish_contest"
        }
        missing_drafts = any(
            not task.versions
            for task in session.tasks
            if required_answer_task_ids is None or task.task_id in required_answer_task_ids
        )
        unapproved = config.review_required and any(
            task.versions and not _task_has_independent_approval(task)
            for task in session.tasks
            if required_answer_task_ids is None or task.task_id in required_answer_task_ids
        )
        if missing_drafts or unapproved or card_blocks_submit or (
            config.final_review_required and not answer_sheet_submit_ready
        ):
            available = {
                spec for spec in available if spec.name != "submit"
            }
        elif any(spec.name == "submit" for spec in available):
            # Sheet complete: the submitter's only remaining move is to hand it
            # in. Workers under a leader keep their ordinary desk instead.
            return frozenset(
                spec for spec in available if spec.name == "submit"
            )
    if work_task_ids is not None:
        active = session.active_task
        select_spec = ACTION_REGISTRY["select_problem"]
        available.discard(select_spec)
        # The scheduler already points the shared cursor at the agent's task, so
        # re-selecting the active problem would only burn a turn.
        selectable = tuple(
            task.task_id
            for task in session.tasks
            if task.task_id in work_task_ids
            and not task.locked
            and (active is None or task.task_id != active.task_id)
        )
        if selectable:
            problem_argument = select_spec.arguments[0]
            available.add(
                replace(
                    select_spec,
                    description=(
                        "Switch to a different problem allowed by your coach "
                        "assignment. The active task is already selected."
                    ),
                    arguments=(replace(problem_argument, enum=selectable),),
                )
            )
        if active is None or active.task_id not in work_task_ids:
            unavailable = {
                "work",
                "request_review",
                "skip_problem",
                "submit_code",
            }
            available = {
                spec
                for spec in available
                if spec.name not in unavailable and spec.pack == "common"
            }
        elif _task_has_independent_approval(active):
            available.discard(ACTION_REGISTRY["work"])
    actions = frozenset(available)

    if review_enabled and (
        review_targets is not None
        or answer_sheet_contest
        or any(task.kind == "programming" for task in session.tasks)
    ):
        available = set(actions)
        review_spec = next(
            (spec for spec in available if spec.name == "review_answer"),
            None,
        )
        if review_spec is not None:
            available.discard(review_spec)
            targets = (
                review_targets
                if review_targets is not None
                else _pending_review_queue(
                    session,
                    reviewer=agent,
                    reported_version_hashes=reported_version_hashes,
                    allowed_task_ids=review_task_ids,
                )
            )
            if targets:
                by_name = {argument.name: argument for argument in review_spec.arguments}
                available.add(
                    replace(
                        review_spec,
                        description=(
                            "Independently review one currently eligible non-author "
                            "answer version from the shared queue."
                        ),
                        arguments=(
                            replace(
                                by_name["problem_id"],
                                enum=tuple(row["problem_id"] for row in targets),
                            ),
                            replace(
                                by_name["version_hash"],
                                enum=tuple(row["version_hash"] for row in targets),
                            ),
                            by_name["decision"],
                            by_name["content"],
                        ),
                    )
                )
        actions = frozenset(available)
    if answer_sheet_contest:
        return actions
    active = session.active_task
    if active is None or active.kind != "programming":
        return actions
    if not config.review_required:
        if config.features.leader_submits and agent == config.leader:
            # The leader hands in whatever source the team has frozen on the
            # active task; it never pastes code into the submission itself.
            available = set(actions)
            submit_spec = ACTION_REGISTRY["submit_code"]
            available.discard(submit_spec)
            if active.versions and not active.locked:
                available.add(
                    replace(
                        submit_spec,
                        description=(
                            "Submit the active problem's latest recorded source "
                            "version to the remote judge for an official verdict."
                        ),
                        arguments=(),
                    )
                )
            actions = frozenset(available)
        return actions

    available = set(actions)
    latest = active.versions[-1] if active.versions else None
    has_evidence = bool(latest and latest.evidence_refs)
    # In reviewed programming sessions, work is a note, not a source setter.
    # execute_code is the explicit path for creating/revising candidate source.
    work_spec = ACTION_REGISTRY["work"]
    if work_spec in available:
        available.remove(work_spec)
        available.add(replace(work_spec, description=(
            "Record programming analysis notes without replacing candidate source. "
            "Use execute_code for complete source; use speak to report sample AC."
        )))
    # OTC requires approval; review-only ablations retain their existing semantics.
    has_approval = has_evidence and (
        session.has_independent_approval() if config.otc_policy is not None
        else session.has_independent_review()
    )
    latest_attempt = next(
        (
            submission
            for submission in reversed(active.submissions)
            if latest and submission.version_hash == latest.version_hash
        ),
        None,
    )
    attempt_blocks_submit = bool(
        latest_attempt
        and (
            latest_attempt.valid
            or latest_attempt.turn == session.budget.turns_used
        )
    )

    if not has_approval or attempt_blocks_submit:
        available.discard(ACTION_REGISTRY["submit_code"])
    else:
        submit_spec = ACTION_REGISTRY["submit_code"]
        available.discard(submit_spec)
        available.add(
            replace(
                submit_spec,
                description=(
                    "Submit the exact frozen, sample-AC, independently reviewed "
                    "source version to the remote judge for an official verdict."
                ),
                arguments=(),
            )
        )
    # Authors report successful local runs with speak. Reviewers use
    # review_answer directly from the shared queue.
    available.discard(ACTION_REGISTRY["request_review"])
    if (
        programming_source_required
        and _needs_programming_source(active)
        and (work_task_ids is None or active.task_id in work_task_ids)
        and ACTION_REGISTRY["execute_code"] in available
    ):
        # Only the programming implementation/repair stage is artifact-gated.
        # Reporting, independent review and submission retain their own tools.
        return frozenset({ACTION_REGISTRY["execute_code"]})
    return frozenset(available)


def _leader_plan_prompts(
    manifest: ContestManifest,
    config: ContestRunConfig,
) -> tuple[str, str]:
    tasks = [
        {
            "problem_id": task.task_id,
            "type": task.task_type,
            "programming": task.programming,
            "prompt": task.prompt,
        }
        for task in manifest.tasks
    ]
    role = (
        f"You are {config.leader}, the team leader, and you stay in the contest "
        "afterwards. Produce a structured opening plan for your teammates. You "
        "may assign one problem per agent, several agents to one problem, or the "
        "whole team to one problem; you may work on any problem yourself and you "
        "alone submit. You can change assignments later with assign_problem. "
    )
    plan_title = "OPENING LEADER PLAN"
    system = (
        role
        + "Base the choice on the actual "
        "task set, team size, rules, and budget. Do not solve the problems and do not "
        "call contestant actions. Respect the declared task family: never prescribe "
        "source code, stdin/stdout, sample execution, or code review for a "
        "non-programming family. Return only one JSON object with this schema: "
        '{"summary":"...",'
        '"work_assignments":{"Agent_1":["exact problem_id"]},'
        '"review_assignments":{"Agent_1":["exact problem_id"]},'
        '"task_order":["exact problem_id"],'
        '"switch_conditions":["..."],"final_check":["..."]}.'
    )
    user = (
        f"{plan_title}\nCompetition: {manifest.competition_id}\n"
        f"Task family: {manifest.task_family}\n"
        "Competition format: "
        f"{manifest.metadata.get('competition_description') or 'No additional format description.'}\n"
        f"Team size: {config.team_size}\n"
        f"Budget: turns={config.max_turns}, api_calls={config.max_api_calls}, "
        f"tokens={config.max_tokens}, minutes={config.max_simulated_minutes}\n"
        f"Rules: {config.rule_guidance or 'No additional rule-card guidance.'}\n"
        "Assign every listed task to at least one worker and at least one reviewer. "
        "A task may appear under multiple workers for group collaboration. "
        "Use only the exact Agent_N names and exact problem_id strings shown here. "
        "Work assignments will be enforced by the runtime and copied into each "
        "agent's private memory.\n"
        f"Tasks:\n{json.dumps(tasks, ensure_ascii=False)}"
    )
    return system, user


def _strip_coach_response(response: str) -> str:
    marker = "ACTION: speak | PAYLOAD:"
    stripped = response.strip()
    if stripped.lower().startswith(marker.lower()):
        stripped = stripped[len(marker) :].strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
    return stripped


def _normalize_task_ids(
    values: Any,
    manifest: ContestManifest,
) -> list[str]:
    known = {task.task_id for task in manifest.tasks}
    suffixes = {
        task.task_id.rsplit(":", 1)[-1]: task.task_id
        for task in manifest.tasks
    }
    normalized: list[str] = []
    for value in values if isinstance(values, list) else []:
        raw = str(value)
        task_id = raw if raw in known else suffixes.get(raw)
        if task_id and task_id not in normalized:
            normalized.append(task_id)
    return normalized


def _default_coach_plan(
    manifest: ContestManifest,
    config: ContestRunConfig,
    *,
    summary: str,
) -> dict[str, Any]:
    agents = [f"Agent_{index}" for index in range(1, config.team_size + 1)]
    scored = [task.task_id for task in manifest.tasks]
    work = {agent: [] for agent in agents}
    review = {agent: [] for agent in agents}
    for index, task_id in enumerate(scored):
        work[agents[index % len(agents)]].append(task_id)
        reviewer_index = (index + 1) % len(agents) if len(agents) > 1 else index
        review[agents[reviewer_index]].append(task_id)
        if len(agents) > 1:
            review[agents[(reviewer_index + 1) % len(agents)]].append(task_id)
    return {
        "summary": summary or "Round-robin fallback allocation.",
        "work_assignments": work,
        "review_assignments": review,
        "task_order": scored,
        "switch_conditions": ["Move on after the latest draft is independently approved."],
        "final_check": ["Audit every latest version before final submission."],
    }


def _normalize_coach_plan(
    response: str,
    manifest: ContestManifest,
    config: ContestRunConfig,
) -> dict[str, Any]:
    stripped = _strip_coach_response(response)
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        try:
            parsed = json.loads(stripped[start : end + 1])
        except (json.JSONDecodeError, ValueError):
            return _default_coach_plan(manifest, config, summary=stripped)
    if not isinstance(parsed, dict):
        return _default_coach_plan(manifest, config, summary=stripped)

    agents = [f"Agent_{index}" for index in range(1, config.team_size + 1)]
    work_raw = parsed.get("work_assignments")
    review_raw = parsed.get("review_assignments")
    work = {
        agent: _normalize_task_ids(
            work_raw.get(agent, []) if isinstance(work_raw, dict) else [],
            manifest,
        )
        for agent in agents
    }
    review = {
        agent: _normalize_task_ids(
            review_raw.get(agent, []) if isinstance(review_raw, dict) else [],
            manifest,
        )
        for agent in agents
    }
    scored = [task.task_id for task in manifest.tasks]
    for index, task_id in enumerate(scored):
        if not any(task_id in assignments for assignments in work.values()):
            work[agents[index % len(agents)]].append(task_id)
        if not any(task_id in assignments for assignments in review.values()):
            reviewer_index = (index + 1) % len(agents) if len(agents) > 1 else index
            review[agents[reviewer_index]].append(task_id)
        assigned_reviewers = [
            agent for agent in agents if task_id in review[agent]
        ]
        if len(agents) > 1 and len(assigned_reviewers) < 2:
            backup = next(agent for agent in agents if agent not in assigned_reviewers)
            review[backup].append(task_id)
    switch_conditions = parsed.get("switch_conditions")
    final_check = parsed.get("final_check")
    return {
        "summary": str(parsed.get("summary") or "Coach allocation"),
        "work_assignments": work,
        "review_assignments": review,
        "task_order": _normalize_task_ids(parsed.get("task_order"), manifest)
        or scored,
        "switch_conditions": [
            str(item) for item in switch_conditions
        ]
        if isinstance(switch_conditions, list)
        else [],
        "final_check": [str(item) for item in final_check]
        if isinstance(final_check, list)
        else [],
    }


def _card_task_claimed_this_turn(
    memory: ContestMemory, task_id: str, *, agent: str, turn: int
) -> bool:
    """Whether another seat is already on ``task_id`` (this turn or the last)."""
    for event in reversed(memory.archival_snapshot()["events"]):
        if event["turn"] < turn - 1:
            return False
        if (
            event.get("task_id") == task_id
            and event["actor"] != agent
            and event["actor"].startswith("Agent_")
            and event["kind"] != "think"
        ):
            return True
    return False


def _card_task_settled(task: TaskUnit) -> bool:
    """Whether the ``otc`` focus scheduler should move a seat past ``task``."""
    if task.kind == "programming":
        return _task_complete(task)
    return bool(task.versions)


def _card_focus_task(
    session: ContestSession,
    memory: ContestMemory,
    agent: str,
    personal_assignment: dict[str, Any] | None,
    strategic_policy: StrategicPolicy,
) -> TaskUnit | None:
    """The problem this seat is on under the ``otc`` baseline.

    Preference order: the agent's own latest ``select_problem`` (its choice
    stands until it switches), then the coach's advisory list, then whatever
    the scheduler would pick next.
    """
    chosen: str | None = None
    own_recent: str | None = None
    for event in reversed(memory.archival_snapshot()["events"]):
        if event["actor"] != agent:
            continue
        if own_recent is None and event.get("task_id") and event["kind"] != "think":
            own_recent = str(event["task_id"])
        if event["kind"] == "select_problem":
            payload = event["payload"] if isinstance(event["payload"], dict) else {}
            chosen = str(payload.get("problem_id") or "") or None
            break
        if event["kind"] == "skip_problem":
            break
    by_id = {task.task_id: task for task in session.tasks}
    if chosen is not None:
        task = by_id.get(chosen)
        if task is not None and not task.locked and task.state is not TaskState.BLOCKED:
            return task
    assigned: list[TaskUnit] = []
    if personal_assignment is not None:
        for task_id in personal_assignment.get("work_tasks", []):
            task = by_id.get(str(task_id))
            if task is not None and not task.locked and not task.hopeless:
                assigned.append(task)
        # The coach's suggestions are worked in order; an answer-sheet problem
        # that already holds a draft is settled for scheduling purposes (the
        # seat can still come back to it explicitly via work(problem_id=...)).
        # A programming problem stays in focus until it is accepted.
        for task in assigned:
            if not _card_task_settled(task):
                return task
    unseen = _next_task(session, strategic_policy)
    if (
        unseen is not None
        and not _card_task_settled(unseen)
        and not _card_task_claimed_this_turn(memory, unseen.task_id, agent=agent, turn=session.budget.turns_used)
    ):
        # One idle seat picks up the blank problem; the rest go back to
        # verifying their own drafts instead of piling onto the same task.
        return unseen
    if assigned:
        return assigned[-1]
    # No suggestion left: keep verifying the seat's own last problem rather
    # than following the shared cursor onto a teammate's.
    if own_recent is not None:
        recent = by_id.get(own_recent)
        if recent is not None and not recent.locked and recent.state is not TaskState.BLOCKED:
            return recent
    active = session.active_task
    if active is not None and not active.locked:
        return active
    return unseen


def _scheduled_agent_task(
    session: ContestSession,
    *,
    agent: str,
    work_task_ids: list[str],
    review_task_ids: set[str],
    reported_version_hashes: set[str],
) -> TaskUnit | None:
    def schedulable(task: TaskUnit) -> bool:
        return not task.locked and (
            task.state is not TaskState.BLOCKED
            or session.budget.turns_used >= (task.blocked_until_turn or 0)
        )

    # Live triage (triage_problem) outranks the Coach's frozen task_order:
    # stable sort keeps the Coach order inside each priority band and pushes
    # hopeless tasks to the end without dropping them.
    work_task_ids = sorted(
        work_task_ids, key=lambda task_id: session.task(task_id).priority_rank
    )

    # A sample-AC candidate must finish its review/submission pipeline before
    # reviewers or authors are sent back to untouched assignments. Otherwise
    # the shared active-task cursor rotates away from ready code and can consume
    # the entire contest without a remote submission.
    pending_reviews = _pending_review_queue(
        session,
        reviewer=agent,
        reported_version_hashes=reported_version_hashes,
        allowed_task_ids=review_task_ids,
    )
    for row in pending_reviews:
        task = session.task(row["problem_id"])
        if task.kind == "programming" and schedulable(task):
            return task

    for task_id in work_task_ids:
        task = session.task(task_id)
        if not schedulable(task) or task.kind != "programming" or not task.versions:
            continue
        latest = task.versions[-1]
        if (latest.evidence_refs and latest.author == agent
                and latest.version_hash not in reported_version_hashes):
            return task
        latest_submitted = any(
            submission.version_hash == latest.version_hash
            for submission in task.submissions
        )
        if (
            latest.evidence_refs
            and _task_has_independent_review(task)
            and not latest_submitted
        ):
            return task

    # Programming failures and untouched tasks share the same rotation order.
    # An untouched task must not indefinitely suppress repairs of an earlier WA.
    # For other families this remains the original initial-draft pass.
    for task_id in work_task_ids:
        task = session.task(task_id)
        if schedulable(task) and (not task.versions or _needs_programming_source(task)):
            return task

    # Preserve initial parallel drafting, then route review-only assignments
    # for every family. The active cursor determines the full problem context.
    for row in pending_reviews:
        task = session.task(row["problem_id"])
        if schedulable(task):
            return task

    for task_id in work_task_ids:
        task = session.task(task_id)
        if not schedulable(task):
            continue
        latest = task.versions[-1]
        rejected = any(
            not review.stale
            and review.version_hash == latest.version_hash
            and review.decision == "reject"
            for review in task.reviews
        )
        if rejected:
            return task
        if task.kind == "programming" and not task.locked:
            return task
        if not _task_has_independent_approval(task) and latest.author != agent:
            return task
    return None


def _task_has_independent_review(task: TaskUnit) -> bool:
    if not task.versions:
        return False
    version = task.versions[-1]
    return any(
        not review.stale
        and review.version_hash == version.version_hash
        and review.reviewer != version.author
        for review in task.reviews
    )


def _rejected_version_count(task: TaskUnit) -> int:
    """Count distinct candidate versions rejected by another agent."""
    return len(
        {
            review.version_hash
            for review in task.reviews
            if review.decision == "reject"
        }
    )
