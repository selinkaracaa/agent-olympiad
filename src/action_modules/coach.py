"""Optional blind, once-per-session pre-contest Coach lifecycle.

Coach is not a contestant-callable tool. It never sees task statements, assigns
problems, or acts after the contest starts. Audit storage remains always on.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from contest_manifest import ContestManifest
    from contest_memory import ContestMemory
    from contest_session import ContestSession
    from rulecard_policy import OpenTablePolicy
    from rules.models import RuleCard

SPECS = ()
COACH_AGENT = "Coach"
BRIEF_EVENT = "precontest_coach_guidance"


@dataclass(frozen=True)
class CoachBrief:
    guidance: str = ""
    budget_exhausted: bool = False
    created: bool = False


def _card_text(card: RuleCard, team_size: int) -> str:
    from rules.views import agent_view
    return json.dumps(agent_view(card, team_size=team_size), ensure_ascii=False)


def coach_brief_prompts(
    card: RuleCard,
    policy: OpenTablePolicy,
    manifest: ContestManifest,
    *,
    team_size: int,
    max_turns: int,
    max_api_calls: int | None,
    memory_enabled: bool = True,
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
        f"Optional memory module: {'enabled' if memory_enabled else 'disabled'}. "
        "Normal shared drafts and conversation are available in either case. "
        "Recommend remember/recall/share_note only when the memory module is enabled.\n"
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


def prepare_brief(
    *, enabled: bool, card: RuleCard | None, policy: OpenTablePolicy | None,
    manifest: ContestManifest, session: ContestSession, memory: ContestMemory,
    team_size: int, max_turns: int, max_api_calls: int | None,
    query: Callable[[str, str], str], charge_tokens: Callable[[str], bool],
    memory_enabled: bool = True,
) -> CoachBrief:
    """Restore an existing brief or create one at turn zero within shared budget."""
    if not enabled:
        return CoachBrief()
    if card is None or policy is None:
        raise ValueError("Coach requires an enforced competition rule card")
    existing = next((event for event in reversed(memory.view(COACH_AGENT))
                     if event.kind == BRIEF_EVENT and event.actor == COACH_AGENT), None)
    if existing is not None:
        return CoachBrief(guidance=str(existing.payload.get("guidance") or ""))
    if session.budget.turns_used != 0:
        raise ValueError("Coach cannot be introduced after the contest has started")
    from contest_session import BudgetExceededError
    from rulecard_policy import clip_text
    try:
        session.consume_budget(api_calls=1)
    except BudgetExceededError:
        return CoachBrief(budget_exhausted=True)
    system, user = coach_brief_prompts(
        card, policy, manifest, team_size=team_size,
        max_turns=max_turns, max_api_calls=max_api_calls,
        memory_enabled=memory_enabled,
    )
    response = query(system, user)
    exhausted = not charge_tokens(response)
    guidance, _ = clip_text(response.strip(), policy.char_limit("work"))
    memory.append(
        task_id=None, question_id=None, actor=COACH_AGENT, visibility="public",
        kind=BRIEF_EVENT, payload={
            "guidance": guidance, "plan": None, "author": COACH_AGENT,
            "stage": "precontest_brief",
        }, turn=session.budget.turns_used,
    )
    return CoachBrief(guidance, exhausted, True)
