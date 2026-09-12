"""Agent-visible prompts and read-only review projections."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from contest_actions import _is_answer_sheet_contest, _local_run_reports, _sample_reports, _task_has_independent_approval
from contest_manifest import ContestManifest, TaskFamily
from contest_memory import ContestMemory
from contest_session import ContestSession, TaskUnit
from tool_registry import DESK_ACTION_NAMES, ActionSpec, render_action_instructions

from contest_config import ContestRunConfig


def _task_rows(session: ContestSession) -> list[dict[str, Any]]:
    return [
        {
            "task_id": task.task_id,
            "state": task.state.value,
            "attempts": len(task.submissions),
            "locked": task.locked,
            "has_draft": bool(task.versions),
            "versions": len(task.versions),
            "latest_author": task.versions[-1].author if task.versions else None,
            "independent_approval": _task_has_independent_approval(task),
            "valid_submission": task.latest_valid_submission is not None,
            "priority": task.priority,
            "hopeless": task.hopeless,
            "triaged_by": task.triaged_by,
        }
        for task in session.tasks
    ]


def _needs_programming_source(task: TaskUnit) -> bool:
    """True for initial implementation and local/official failure repair."""
    if task.kind != "programming" or task.locked:
        return False
    if not task.versions:
        return True
    latest = task.versions[-1]
    return not latest.evidence_refs or any(
        submission.valid and submission.version_hash == latest.version_hash
        for submission in task.submissions
    )


def _programming_gate_guidance(
    session: ContestSession,
    config: ContestRunConfig,
    agent: str,
    reported_version_hashes: set[str] | None = None,
    sample_reports: dict[str, dict[str, Any]] | None = None,
) -> str:
    active = session.active_task
    if (
        not config.review_required
        or active is None
        or active.kind != "programming"
    ):
        return ""

    latest = active.versions[-1] if active.versions else None
    latest_attempt = next(
        (
            submission
            for submission in reversed(active.submissions)
            if latest and submission.version_hash == latest.version_hash
        ),
        None,
    )
    remote_failure = _remote_failure_guidance(active, config)
    sample_failure = _sample_failure_text(
        (sample_reports or {}).get(latest.version_hash) if latest else None
    )
    if latest is None:
        next_step = (
            "Call execute_code with the complete candidate source. work stores "
            "analysis notes only. This creates your first source version: write "
            "the solver in the code argument now, rather than waiting for a "
            "pre-existing program. execute_code feeds the official sample input to "
            "your program and compares the output; only a sample AC counts as "
            "local run evidence."
        )
    elif latest_attempt and latest_attempt.valid:
        next_step = (
            f"The latest frozen version received {latest_attempt.verdict}. "
            "Use execute_code with revised complete source to create a new version."
        )
    elif latest_attempt and latest_attempt.turn == session.budget.turns_used:
        next_step = (
            "A remote submission of this version already failed this round. "
            "Analyze the failure or wait until the next round before retrying."
        )
    elif not latest.evidence_refs:
        next_step = (
            (
                f"The latest version failed the official samples. {sample_failure} "
                "Fix the code and call execute_code again with the complete revised "
                "source; review and submission stay locked until the samples pass."
            )
            if sample_failure
            else (
                "Call execute_code with the exact complete latest source; it must "
                "pass the official sample cases. work and verify do not count as "
                "local run/test evidence."
            )
        )
    elif any(
        not review.stale
        and review.version_hash == latest.version_hash
        and review.decision == "reject"
        for review in active.reviews
    ):
        next_step = (
            "A reviewer rejected this sample-AC version. Do not request another "
            "review of unchanged code. Either (a) fix the named defect and call "
            "execute_code with the new complete source, or (b) if you believe the "
            "code is right, call submit_code with no arguments now: the remote judge "
            "is the final oracle and a WA/TLE verdict costs only a time penalty, "
            "while never submitting scores zero."
        ) if config.otc_policy is None else (
            "A reviewer rejected this version. Fix the defect, execute the revised "
            "source, and obtain independent approval again. Submission is blocked."
        )
    elif latest.version_hash not in (reported_version_hashes or set()):
        if latest.author == agent:
            next_step = (
                "Call speak to report the sample-AC local run and ask a different "
                "agent to review this exact version."
            )
            if remote_failure:
                next_step += (
                    " Because the previous version failed remotely, this speak must "
                    "contain a one-line diagnosis: what was wrong before and what "
                    "changed in this version. The version does not enter the review "
                    "queue until you speak."
                )
        else:
            next_step = "Wait for the author to report the successful local run with speak."
    elif not session.has_independent_review():
        next_step = (
            "Wait for a different agent to review this exact reported version."
            if latest.author == agent
            else (
                "Read the full source and the sample report listed under YOUR "
                "ELIGIBLE PENDING REVIEWS, then call review_answer on this exact "
                "evidence-backed version. Approve if the algorithm, edge cases, and "
                "complexity look sound; reject only with a concrete defect or a "
                "specific failing input. Remember the remote judge decides "
                "correctness; the samples already pass."
            )
        )
    else:
        next_step = (
            "Call submit_code with no source argument; it submits the exact frozen "
            "latest version to the remote judge."
        )
    guidance = f"PROGRAMMING GATE — NEXT REQUIRED: {next_step}\n"
    if remote_failure:
        guidance += f"{remote_failure}\n"
    return guidance + "\n"


def _shared_review_history(
    session: ContestSession,
    *,
    max_versions_per_task: int | None = None,
    max_content_chars: int | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build shared review history grouped by task and immutable answer version."""
    history: dict[str, list[dict[str, Any]]] = {}
    for task in session.tasks:
        versions = (
            task.versions[-max_versions_per_task:]
            if max_versions_per_task is not None
            else task.versions
        )
        rows = []
        for version in versions:
            content = version.content
            if max_content_chars is not None and len(content) > max_content_chars:
                content = content[:max_content_chars] + "…"
            rows.append(
                {
                    "version_hash": version.version_hash,
                    "parent_hash": version.parent_hash,
                    "author": version.author,
                    "answer": content,
                    "current": bool(
                        task.versions
                        and version.version_hash == task.versions[-1].version_hash
                    ),
                    "reviews": [
                        {
                            "reviewer": review.reviewer,
                            "decision": review.decision,
                            "body": review.body,
                            "stale": review.stale,
                        }
                        for review in task.reviews
                        if review.version_hash == version.version_hash
                    ],
                }
            )
        if rows:
            history[task.task_id] = rows
    return history


def _pending_review_queue(
    session: ContestSession,
    *,
    reviewer: str,
    reported_version_hashes: set[str] | None = None,
    allowed_task_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    reported = reported_version_hashes or set()
    return [
        {
            "problem_id": task.task_id,
            "version_hash": task.versions[-1].version_hash,
            "author": task.versions[-1].author,
        }
        for task in session.tasks
        if task.versions
        and (allowed_task_ids is None or task.task_id in allowed_task_ids)
        and task.versions[-1].author != reviewer
        and (
            task.kind != "programming"
            or task.versions[-1].version_hash in reported
        )
        and not _task_has_independent_approval(task)
        and not any(
            not review.stale
            and review.version_hash == task.versions[-1].version_hash
            and review.decision == "reject"
            for review in task.reviews
        )
    ]


def _reported_version_hashes(memory: ContestMemory) -> set[str]:
    return set(_local_run_reports(memory))


def _sample_failure_text(report: dict[str, Any] | None) -> str:
    if not report:
        return ""
    verdict = report.get("sample_verdict")
    if verdict is None or str(verdict).upper() == "AC":
        return ""
    failed = [
        case
        for case in report.get("sample_cases") or []
        if str(case.get("verdict")) != "AC"
    ]
    parts = [str(report.get("sample_summary") or f"Sample judge: {verdict}.")]
    for case in failed[:3]:
        line = f"sample case {case.get('name')} -> {case.get('verdict')}"
        if case.get("detail"):
            line += f" ({case['detail']})"
        if case.get("expected") is not None:
            line += f"; expected: {json.dumps(case.get('expected'), ensure_ascii=False)}"
        if case.get("actual") is not None:
            line += f"; got: {json.dumps(case.get('actual'), ensure_ascii=False)}"
        parts.append(line)
    return " ".join(parts)


_VERDICT_CHECKLISTS = {
    "WA": (
        "WA checklist: re-read the output format (case labels, spacing, line "
        "breaks, exact wording), floating-point precision and rounding, edge cases "
        "(zero/empty input, minimum and maximum bounds, ties), integer overflow or "
        "off-by-one in loops, and every branch the samples never exercise. Build "
        "an extra adversarial test and run it with execute_code."
    ),
    "TLE": (
        "TLE checklist: compute the asymptotic complexity against the maximum "
        "input size, replace per-query rescans with precomputation or better data "
        "structures, read all input with sys.stdin.buffer and write with one join, "
        "and avoid Python-level loops over 10^7 or more operations."
    ),
    "RE": (
        "RE checklist: index and recursion bounds, division by zero, exhausted "
        "input reads, memory blow-ups, and unhandled parsing of blank lines."
    ),
    "MLE": (
        "MLE checklist: avoid materializing full input copies or dense tables; "
        "stream input and prefer arrays over lists of objects."
    ),
}


def _remote_failure_guidance(
    active: TaskUnit,
    config: ContestRunConfig,
) -> str:
    """Describe the latest valid non-AC remote verdict with a concrete checklist."""
    attempt = next(
        (submission for submission in reversed(active.submissions) if submission.valid),
        None,
    )
    if attempt is None or attempt.verdict.upper() == "AC":
        return ""
    verdict = attempt.verdict.upper()
    valid_attempts = sum(submission.valid for submission in active.submissions)
    remaining = max(0, config.consecutive_non_ac_limit - active.consecutive_non_ac)
    checklist = _VERDICT_CHECKLISTS.get(
        verdict,
        "Re-derive the algorithm from the statement and test the boundaries.",
    )
    return (
        f"REMOTE VERDICT {verdict} on attempt {valid_attempts}; "
        f"{remaining} more non-AC attempt(s) before this task is forced into cooldown. "
        "The judge gives no failing case, so reason from the statement. "
        f"{checklist} The same source hash cannot be resubmitted; the revised "
        "version must pass the official samples again, be reported with speak, and "
        "be independently re-reviewed."
    )


def _system_prompt(
    config: ContestRunConfig,
    agent: str,
    actions: frozenset[ActionSpec],
    *,
    native_actions: bool = False,
    answer_sheet_contest: bool = False,
    task_family: TaskFamily = "general",
    coach_guidance: str = "",
    card_protocol: str = "",
    card_block: str = "",
    opening_summary: str = "",
) -> str:
    if native_actions:
        base = (
            f"You are {agent}, one contestant in a {config.team_size}-agent team.\n"
            "You decide which provided function best advances the contest. "
            "Choose exactly one function and call it once. "
            "Do not emit a text answer instead of the function call."
        )
    else:
        base = (
            f"You are {agent}, one contestant in a {config.team_size}-agent team.\n"
            "Return exactly one JSON object with keys action and arguments. "
            "Do not include Markdown or a second action.\n"
            f"{render_action_instructions(actions)}"
        )
    if any(spec.name in DESK_ACTION_NAMES for spec in actions):
        base += (
            "\nDESK TOOLS: inspect_problem reads any problem's statement and full "
            "version/review/submission history without moving the team's active "
            "problem; use it to check another problem or to self-verify before you "
            "act. remember stores a private note (intermediate result, dead end, "
            "reminder) that survives outside the visible transcript; recall searches "
            "your notes and shared notes; share_note publishes one note to the team. "
            "work is only for a candidate answer, never for notes. triage_problem "
            "sets the team priority of a problem (high/normal/low/hopeless) so the "
            "scheduler reorders remaining work; hopeless problems stay on the sheet "
            "and their latest draft is still submitted at the deadline. Desk tools "
            "consume a turn like any other action, so do not loop on them."
        )
    features = config.features
    if features.coach == "none" and not features.structured_context:
        if config.rule_guidance:
            return base + f"\nCONTEST RULES\n{config.rule_guidance}"
        return base
    reviewed_programming = task_family == "programming" and config.review_required
    if features.coach == "leader":
        leader = config.leader
        if agent == leader:
            strategic = base + (
                f"\nLEADER PROTOCOL: You are {leader}, the team leader. Your opening "
                "plan is enforced: each teammate may only work on the problems in "
                "their work list, and you may change a list at any time with "
                "assign_problem. You may work on any problem yourself. Only you can "
                "submit: teammates draft and report, you check the latest version of "
                "each problem and hand it in. Re-plan when a problem stalls, when a "
                "teammate finishes early, or when the budget is running out. "
            )
        else:
            strategic = base + (
                f"\nLEADER PROTOCOL: {leader} is the team leader. Work only on the "
                "problems in your enforced work list, report results with speak, and "
                f"raise blockers or handoffs with direct_message to {leader}. You "
                "cannot submit; the leader hands in the team's latest version of each "
                "problem, so make sure your best answer is the latest recorded draft. "
            )
        strategic += (
            "The active task is a shared team cursor, not an ownership lock: select "
            "the problem you are assigned before acting on it. Preserve teammates' "
            "drafts and do not overwrite a sound version without a concrete correction. "
        )
    elif features.coach == "card":
        strategic = base + "\n" + card_protocol + (
            "\nThe active task is a shared team cursor, not an ownership lock: select "
            "the problem you intend to act on. Preserve teammates' drafts and do not "
            "overwrite a sound version without a concrete correction. "
        )
        if features.private_channel and config.team_size > 1:
            strategic += (
                "Use direct_message for a private question, handoff, or correction to "
                "specific teammates; use speak when the whole team should know. "
            )
    else:
        # Explicit feature ablations can exercise review/memory without a Coach.
        strategic = base
    if features.private_channel and config.team_size > 1:
        strategic += (
            "Use direct_message for a private handoff; use speak for the whole team. "
        )
    strategic += (
        "Use work for programming analysis notes; execute_code records source. "
        if reviewed_programming
        else "Use work only to create a substantive candidate solution or final answer, "
             "never a status update, request for missing work, TODO, or placeholder. "
    )
    if config.review_required:
        strategic += (
            "A different agent uses "
            "review_answer with the exact problem_id and version_hash to approve or "
            "reject it. After repeated failed submissions, move to another unsolved "
            "problem and revisit later. "
            "Inspect task status before acting: prefer review over another rewrite when "
            "a teammate's candidate is ready."
        )
    else:
        strategic += (
            "After repeated failed submissions, move to another unsolved problem and "
            "revisit later. Inspect task status before acting so you do not redo a "
            "teammate's finished work."
        )
    if answer_sheet_contest and config.otc_policy is not None and config.review_required:
        strategic += (
            "\nOTC ANSWER-SHEET PROTOCOL: work records a complete answer with its "
            "derivation. Every new version enters the shared independent review queue. "
            "Use review_answer on another author\'s exact current version; approve only "
            "a complete, checkable answer. Rejection blocks submission and changing "
            "the answer invalidates old reviews. There is no frozen Coach allocation. "
            "After all scored answers are independently approved and card discussion "
            "requirements are met, call submit once to hand in the sheet. Deadline "
            "collection includes only approved current versions. "
            + ("A separate final review is also required. " if config.final_review_required
               else "No redundant contest-wide final-review round is required. ")
        )
    elif answer_sheet_contest and config.review_required:
        strategic += (
            "\nANSWER-SHEET COACH PROTOCOL: Never submit an individual problem. "
            "Use work only when you have a complete candidate response for the active "
            "problem: include the explicit final answer and enough derivation to audit "
            "it. Never save setup notes, TODOs, uncertainty, or placeholders as a "
            "candidate answer; use speak to discuss those or move to another assigned "
            "problem. Follow the opening coach's frozen allocation when selecting "
            "problems. Every new candidate automatically enters the shared review "
            "queue. A reviewer must reject any candidate lacking an explicit final "
            "answer or containing unresolved uncertainty; approve only a complete, "
            "checkable answer. After every problem has a "
            "reviewed draft, perform the contest-wide FINAL REVIEW. Only after that "
            "review is complete, call submit once with no arguments to atomically "
            "hand in the whole answer sheet and end the contest. Never call "
            "finish_contest."
        )
    elif answer_sheet_contest:
        strategic += (
            "\nANSWER-SHEET PROTOCOL: Never submit an individual problem. Use work "
            "only when you have a complete candidate response for the active problem "
            "with an explicit final answer. Never save setup notes, TODOs, or "
            "placeholders as a candidate answer. "
            + (
                f"Once every problem has a draft, {config.leader} calls submit once "
                "with no arguments to hand in the whole sheet and end the contest; "
                "nobody else can submit. "
                if features.leader_submits
                else "Once every problem has a draft, call submit once with no "
                "arguments to hand in the whole sheet and end the contest. "
            )
            + "Never call finish_contest."
        )
    elif task_family == "programming" and not config.review_required:
        strategic += (
            "\nPROGRAMMING WORKFLOW: An author calls execute_code with the complete "
            "candidate source that reads stdin and writes stdout; the system runs it "
            "on the official samples and reports expected versus actual output. Fix "
            "the code and re-run until the samples pass, then report with speak. "
            + (
                f"Only {config.leader} submits: after a sample-AC report, the leader "
                "selects that problem and calls submit_code with no arguments to send "
                "the latest recorded source to the remote judge. "
                if features.leader_submits
                else "When the samples pass, call submit_code to send the source to "
                "the remote judge. "
            )
            + "A WA/TLE costs a time penalty, but a sample-AC version that is never "
            "submitted scores zero. Select another unsolved problem after a valid "
            "submission."
        )
    elif task_family == "programming":
        strategic += (
            "\nMANDATORY PROGRAMMING WORKFLOW: (1) An author calls execute_code "
            "with the complete candidate source that reads stdin and writes stdout. "
            "Write the first solver directly in that call; lack of existing source "
            "is not a reason to rest. Do not replace an algorithm with a placeholder "
            "or a hardcoded sample harness when repairing it. "
            "The system runs it on the official sample input and compares the "
            "output; only a sample AC counts as local run evidence, and a sample "
            "failure reports the expected versus actual output so you can fix it. "
            "(2) Only after the samples pass, the author calls speak to report the "
            "sample result (and, after a remote WA/TLE, a one-line diagnosis of what "
            "changed) and asks for review. (3) A different agent reads the FULL "
            "source and sample report shown in YOUR ELIGIBLE PENDING REVIEWS and "
            "calls review_answer on that exact version, approving when the "
            "algorithm, edge cases, and complexity look sound; reject only with a "
            "concrete defect or a specific failing input, never for lack of a formal "
            "proof. Never approve code you have not read in full. "
            "(4) After the independent review, call submit_code with no arguments; "
            "the system re-checks the samples and then submits the frozen reviewed "
            "source to the remote judge. Never rewrite or paste source into "
            "submit_code. The remote judge is the final oracle: a WA/TLE costs a "
            "time penalty, but a sample-AC version that is never submitted scores "
            "zero. If review_answer rejects a version, the author either fixes the "
            "named defect and re-runs execute_code, or submits anyway when the "
            "objection is speculative; never request another review of unchanged "
            "code. After WA/TLE, follow the verdict checklist in the PROGRAMMING "
            "GATE, revise, and repeat all four steps. Select another unsolved "
            "problem after a valid submission. Never call finish_contest while any "
            "task lacks a valid submission or required final approval."
        )
        if config.otc_policy is not None:
            strategic = strategic.replace(
                "If review_answer rejects a version, the author either fixes the "
                "named defect and re-runs execute_code, or submits anyway when the "
                "objection is speculative; never request another review of unchanged "
                "code.",
                "If review_answer rejects a version, fix the defect, re-run "
                "execute_code and obtain approval of the new version. Rejection "
                "is a veto, including at the deadline.",
            ).replace("(4) After the independent review,",
                      "(4) After independent approval of the current version,")
    elif task_family == "mathematics":
        strategic += (
            "\nMATHEMATICS WORKFLOW: This is a mathematics contest, not a programming "
            "task. Never ask for source code, stdin/stdout, executable candidates, or "
            "sample-run evidence. Read the numbered problems in the active prompt and "
            "solve as many as possible. Use work only for an actual candidate answer "
            "sheet containing explicit numbered final answers, with compact derivations "
            "where useful for review. Preserve already-solved entries when revising the "
            "sheet. Use the calculator when available for arithmetic checks. Reviewers "
            "check the mathematics and answer numbering, not code. Submit the best "
            "available answer sheet before the deadline even when some entries remain "
            "blank or unreviewed."
        )
    elif task_family == "short_answer":
        strategic += (
            "\nSHORT-ANSWER WORKFLOW: This is not a programming task. Answer the "
            "questions directly and concisely. For a packet, use work for a numbered "
            "answer sheet such as `Q1: answer`; for one question, give its explicit "
            "final answer. Never save a status update or ask for source code. Reviewers "
            "check factual correctness, aliases, and alignment between question numbers "
            "and answers. Submit the most complete answer set available by the deadline."
        )
    elif task_family == "puzzle":
        strategic += (
            "\nPUZZLE WORKFLOW: This is a puzzle whose deliverable is a final answer "
            "word or phrase, not source code. Infer the puzzle mechanism from the "
            "provided prompt and assets, share concrete deductions with the team, and "
            "use work only when recording a plausible final answer with its supporting "
            "reasoning. Never store a status-only draft. Review extraction, spelling, "
            "and answer format before submission."
        )
    else:
        strategic += (
            "\nGENERAL NON-PROGRAMMING WORKFLOW: Solve the task directly. Use work only "
            "for a substantive candidate response with an explicit final answer. Never "
            "ask for executable source or stdin/stdout unless the active task explicitly "
            "states that programming is required."
        )
    if coach_guidance:
        title = (
            "OPENING LEADER PLAN" if features.coach == "leader"
            else "PRE-CONTEST COACH BRIEF"
        )
        strategic += f"\n{title}\n{coach_guidance}"
    if opening_summary:
        strategic += f"\nCOACH OPENING SUMMARY (after the opening turn; the coach has left)\n{opening_summary}"
    if card_block:
        strategic += f"\n{card_block}"
    elif config.rule_guidance:
        strategic += f"\nCONTEST RULES\n{config.rule_guidance}"
    return strategic


def _user_prompt(
    manifest: ContestManifest,
    session: ContestSession,
    memory: ContestMemory,
    config: ContestRunConfig,
    agent: str,
    *,
    final_review_phase: bool = False,
    personal_assignment: dict[str, Any] | None = None,
    programming_source_required: bool = False,
    think_ledger: list[dict[str, Any]] | None = None,
) -> str:
    active = session.active_task
    policy = config.otc_policy
    allowed_reviews = (
        set(personal_assignment.get("review_tasks", []))
        if personal_assignment
        else None
    )
    task_by_id = {task.task_id: task for task in manifest.tasks}
    active_text = (
        f"ACTIVE TASK {active.task_id}\n"
        "(This task is already selected for you; act on it directly instead of "
        f"calling select_problem again.)\n{task_by_id[active.task_id].prompt}"
        if active is not None
        else "NO ACTIVE TASK. Select one unfinished problem."
    )
    status = json.dumps(_task_rows(session), ensure_ascii=False)
    shared_reviews = json.dumps(
        _shared_review_history(
            session,
            max_versions_per_task=5,
            max_content_chars=800,
        ),
        ensure_ascii=False,
    )
    local_run_reports = _local_run_reports(memory)
    sample_reports = _sample_reports(memory)
    pending_rows = _pending_review_queue(
        session,
        reviewer=agent,
        reported_version_hashes=set(local_run_reports),
        allowed_task_ids=allowed_reviews,
    )
    if final_review_phase and active is not None and active.versions:
        version = active.versions[-1]
        if version.author != agent and (allowed_reviews is None or active.task_id in allowed_reviews):
            if not any(row["problem_id"] == active.task_id for row in pending_rows):
                pending_rows.append({"problem_id": active.task_id, "version_hash": version.version_hash, "author": version.author})
    session_task_by_id = {task.task_id: task for task in session.tasks}
    for row in pending_rows:
        task = session_task_by_id[row["problem_id"]]
        version = next(
            (
                candidate
                for candidate in reversed(task.versions)
                if candidate.version_hash == row["version_hash"]
            ),
            None,
        )
        if version is None:
            continue
        row["prompt"] = task_by_id[task.task_id].prompt
        row["answer"] = version.content
        if task.kind == "programming":
            # Reviewers approve the exact frozen source, so show all of it.
            row["source"] = version.content
            row["sample_report"] = sample_reports.get(version.version_hash)
            row["author_report"] = local_run_reports.get(version.version_hash)
    pending_reviews = json.dumps(pending_rows, ensure_ascii=False)
    budget = json.dumps(
        {
            **asdict(session.budget),
            "blank_tasks": [task.task_id for task in session.tasks if not task.versions],
        },
        ensure_ascii=False,
    )
    if policy is not None and active is not None and not config.features.basic_open_table:
        # Projection sizes come from the card's memory_entries block.
        entries = policy.memory_entries
        context: Any = memory.strategic_projection(
            viewer=agent,
            current_task_id=active.task_id,
            max_current_events=entries.shared_work,
            max_direct_messages=entries.group_messages,
            max_team_messages=entries.public_messages,
            max_chars=max(6000, 300 * (entries.shared_work + entries.public_messages)),
        )
    elif config.features.structured_context and active is not None:
        context = memory.strategic_projection(
            viewer=agent,
            current_task_id=active.task_id,
            max_chars=6000,
        )
    else:
        visible = memory.view(agent)
        if config.features.basic_open_table:
            visible = [event for event in visible if event.kind not in {'think', 'note', 'note_shared'}]
        context = [
            {
                "turn": event.turn,
                "actor": event.actor,
                "kind": event.kind,
                "payload": event.payload,
            }
            for event in visible[-12:]
        ]
    phase = (
        "FINAL REVIEW PHASE: Audit the active task's latest draft answer. "
        "Call review_answer with its exact problem_id and version_hash. Approve with "
        "concise evidence if correct; reject and explain the defect if wrong.\n\n"
        if final_review_phase
        else ""
    )
    submission_rule = ""
    if _is_answer_sheet_contest(manifest):
        if config.final_review_required:
            submission_rule = (
                "ANSWER-SHEET RULE: work edits per-problem drafts. Do not submit "
                "individual problems. The active problem is shared state, not exclusive "
                "ownership; follow the coach's allocation when selecting which problem "
                "to work on or review. After every draft and the full-sheet review are "
                "complete, call submit once with no arguments; that atomically hands in "
                "the whole sheet and ends the contest. Never use finish_contest.\n\n"
            )
        elif config.features.leader_submits:
            submission_rule = (
                "ANSWER-SHEET RULE: work edits per-problem drafts. Do not submit "
                f"individual problems. Only {config.leader} can call submit (once, "
                "with no arguments) to hand in the whole current answer sheet and end "
                "the contest. Never use finish_contest.\n\n"
            )
        else:
            submission_rule = (
                "ANSWER-SHEET RULE: work edits per-problem drafts. Do not submit "
                "individual problems. Call submit once with no arguments to hand in "
                "the whole current answer sheet and end the contest. Never use "
                "finish_contest.\n\n"
            )
    personal_block = (
        (
            "COACH OPENING SUGGESTION FOR YOU (advice, not a lock)\n"
            if policy is not None
            else "YOUR ENFORCED PERSONAL COACH MEMORY\n"
        )
        + f"{json.dumps(personal_assignment, ensure_ascii=False)}\n\n"
        if personal_assignment is not None
        else ""
    )
    think_block = (
        "YOUR PRIVATE THINK LEDGER (newest last; nobody else sees this)\n"
        f"{json.dumps(think_ledger, ensure_ascii=False)}\n\n"
        if think_ledger
        else ""
    )
    if config.features.basic_open_table:
        think_block = think_block.replace('YOUR PRIVATE THINK LEDGER (newest last; nobody else sees this)',
                                          'CURRENT PRIVATE THOUGHT (this turn only)')
    source_block = ""
    if (config.review_required
            and active is not None and active.kind == "programming" and active.versions):
        latest = active.versions[-1]
        source_block = (
            "ACTIVE PROGRAMMING SOURCE (complete, not a preview; repair this version)\n"
            + json.dumps({
                "version_hash": latest.version_hash,
                "author": latest.author,
                "source": latest.content,
                "sample_report": sample_reports.get(latest.version_hash),
                "reviews": [asdict(review) for review in active.reviews
                            if review.version_hash == latest.version_hash and not review.stale],
                "latest_official_submission": (
                    asdict(active.latest_valid_submission) if active.latest_valid_submission else None
                ),
            }, ensure_ascii=False) + "\n\n"
        )
    source_requirement = (
        "SOURCE ACTION REQUIRED: The analysis/rest allowance for this programming "
        "task has been used. Call execute_code now with a complete best-effort "
        "solver reading stdin and writing stdout. Implement or repair the actual "
        "algorithm; do not send an empty/TODO program or a hardcoded sample harness.\n\n"
        if programming_source_required else ""
    )
    review_block = (
        "SHARED ANSWER REVIEW HISTORY (answer previews are truncated to 800 chars; "
        "the complete, untruncated source of every version you may review is given "
        f"under YOUR ELIGIBLE PENDING REVIEWS)\n{shared_reviews}\n\n"
        f"YOUR ELIGIBLE PENDING REVIEWS\n{pending_reviews}\n\n"
    )
    if config.features.basic_open_table:
        drafts = [{"problem_id": task.task_id, "content": task.versions[-1].content,
                   "author": task.versions[-1].author} for task in session.tasks if task.versions]
        review_block = 'CURRENT SHARED DRAFTS\n' + json.dumps(drafts, ensure_ascii=False) + '\n\n'
    return (
        f"CONTEST {manifest.session_id}\n"
        f"TASK FAMILY {manifest.task_family}\n"
        "COMPETITION FORMAT "
        f"{manifest.metadata.get('competition_description') or 'No additional format description.'}\n"
        f"TASK STATUS {status}\n"
        f"BUDGET {budget}\n\n"
        "DEADLINE POLICY: When the session ends, the environment automatically "
        "hands in pending non-programming drafts for both team variants. Missing "
        "answers remain blank. You may use your last action to improve a draft.\n\n"
        f"{personal_block}"
        f"{think_block}"
        f"{submission_rule}"
        f"{phase}"
        f"{_programming_gate_guidance(session, config, agent, set(local_run_reports), sample_reports)}"
        f"{active_text}\n\n"
        f"{source_requirement}{source_block}"
        f"{review_block}"
        f"{'VISIBLE CONVERSATION' if config.features.basic_open_table else 'VISIBLE MEMORY'}\n{json.dumps(context, ensure_ascii=False)}"
    )
