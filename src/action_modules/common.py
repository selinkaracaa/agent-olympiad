"""Common action definitions; role and workflow extensions remain policy-gated."""

# Every setting gets this core. Role/phase/state legality is checked at dispatch.
CORE_ACTION_NAMES = frozenset({
    "speak", "work", "rest", "select_problem", "skip_problem",
    "inspect_problem", "triage_problem", "check_budget", "query_rules", "submit",
})

from functools import partial
from .contracts import (ArgumentSpec, make_action, _TEXT, _REASON, _PROBLEM_ID,
                        _RECIPIENTS, _OPTIONAL_PROBLEM_ID, _PROPOSAL_ID)

_action = partial(make_action, module="common")

SPECS = (
    _action(
        "select_problem",
        "Select (claim) a contest problem to work on.",
        (_PROBLEM_ID,),
        visibility="contest",
    ),
    _action("speak", "Broadcast a message to the team.", (_TEXT,)),
    _action(
        "direct_message",
        "Send a private message to one teammate or a named sub-group of teammates.",
        (_RECIPIENTS, _TEXT),
        visibility="private",
        # Text form: ``Agent_2, Agent_3 | message``.
        text_payload=("recipients", "content"),
    ),
    _action(
        "work",
        (
            "Record durable work for the team: a candidate answer or draft for "
            "one problem. Pass problem_id to record against a specific problem "
            "(and make it your current one); without it the work goes to your "
            "current problem. For short-answer tasks, keep reasoning above a "
            "separate final line: Final answer: <value>. Never substitute a "
            "different problem\'s answer for this problem."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        # Text form: ``[<problem_id> |] <content>``.
        text_payload=("problem_id", "content"),
    ),
    _action(
        "inspect_problem",
        (
            "Read one problem's statement plus its complete answer-version, "
            "review, and submission history without changing the team's "
            "active problem. Without problem_id it shows your current problem "
            "(or the whole board / latest code history where that applies). "
            "Self-verification context only; it never counts as an "
            "independent review."
        ),
        (
            _OPTIONAL_PROBLEM_ID,
            ArgumentSpec(
                "focus",
                description="Optional aspect to re-check, such as edge cases.",
                required=False,
            ),
        ),
        visibility="private",
        text_payload=("problem_id", "focus"),
    ),
    _action(
        "triage_problem",
        (
            "Set the team's working priority for one problem, or mark it "
            "hopeless. Hopeless problems stay on the sheet and their latest "
            "draft is still submitted at the deadline."
        ),
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "priority",
                description="Team priority for this problem.",
                enum=("high", "normal", "low", "hopeless"),
            ),
            _REASON,
        ),
        visibility="team",
        text_payload=("problem_id", "priority", "reason"),
    ),
    _action(
        "assign_problem",
        (
            "Leader only: replace one teammate's enforced work list with the "
            "given problems. The teammate is scheduled onto the first listed "
            "problem from the next round."
        ),
        (
            ArgumentSpec(
                "agent",
                description="Exact teammate name to reassign.",
            ),
            ArgumentSpec(
                "problem_ids",
                type="array",
                items="string",
                description="Problems this teammate may work on, in order.",
            ),
            _REASON,
        ),
        visibility="team",
        text_payload=("agent", "problem_ids", "reason"),
    ),
    _action(
        "request_review",
        "Ask a teammate to review the current active problem; this does not approve it.",
        (
            _TEXT,
            ArgumentSpec(
                "reviewer",
                description="Optional teammate name.",
                required=False,
            ),
        ),
        text_payload=("content", "reviewer"),
    ),
    _action(
        "review_answer",
        (
            "Independently review another agent's current answer version. "
            "Pass version_hash to pin the exact version you read (shown by "
            "inspect_problem); without it the review applies to the version "
            "currently recorded."
        ),
        (
            _PROBLEM_ID,
            ArgumentSpec(
                "version_hash",
                description="Current answer version being reviewed; defaults to the latest.",
                required=False,
            ),
            ArgumentSpec(
                "decision",
                description="Review outcome.",
                enum=("approve", "reject"),
            ),
            ArgumentSpec("content", description="Review findings and evidence."),
        ),
        text_payload=("problem_id", "version_hash", "decision", "content"),
    ),
    _action(
        "submit",
        "Submit a final answer for evaluation.",
        (ArgumentSpec("answer", description="Complete final answer."),),
        visibility="team",
        submission_attempts=1,
        evaluator=True,
        evaluator_name="task_evaluator",
        submission=True,
    ),
    _action(
        "skip_problem",
        "Skip (release) the current problem.",
        (_REASON,),
        visibility="contest",
    ),
    _action(
        "finish_contest",
        (
            "Finish only after every task has a valid submission and required "
            "final review. Answer-sheet contests end through submit instead."
        ),
        (_REASON,),
        visibility="contest",
        terminal=True,
    ),
    _action("rest", "Pass the current turn.", (_REASON,), visibility="private"),
    _action(
        "check_budget",
        (
            "Show turns, API calls, tokens, contest clock, penalties, and which "
            "problems still have nothing recorded."
        ),
        (),
        visibility="private",
    ),
    _action(
        "query_rules",
        "Show the contest rules and rule card as visible to your role.",
        (),
        visibility="private",
    ),
    _action(
        "propose",
        (
            "Open a numbered proposal (a candidate answer, approach, or split of "
            "work) for the team to challenge, support, or decide on."
        ),
        (_TEXT, _OPTIONAL_PROBLEM_ID),
        pack="deliberation",
    ),
    _action(
        "challenge",
        "Raise a concrete objection to an open proposal you did not author.",
        (_PROPOSAL_ID, _TEXT),
        pack="deliberation",
        text_payload=("proposal_id", "content"),
    ),
    _action(
        "provide_evidence",
        "Attach a check, derivation, or counterexample to an open proposal.",
        (_PROPOSAL_ID, _TEXT),
        pack="deliberation",
        text_payload=("proposal_id", "content"),
    ),
    _action(
        "revise",
        "Author only: replace the current claim of your open proposal.",
        (_PROPOSAL_ID, _TEXT),
        pack="deliberation",
        text_payload=("proposal_id", "content"),
    ),
    _action(
        "decide",
        "Decision maker only: accept, reject, or defer an open proposal.",
        (
            _PROPOSAL_ID,
            ArgumentSpec(
                "outcome",
                description="Decision on the proposal.",
                enum=("accept", "reject", "defer"),
            ),
            ArgumentSpec("reason", description="Why the team decides this way."),
        ),
        pack="deliberation",
        text_payload=("proposal_id", "outcome", "reason"),
    ),

    _action(
        "use_calculator",
        "Evaluate a mathematical expression.",
        (ArgumentSpec("expression", description="Arithmetic expression."),),
        visibility="private",
        pack="math",
        tool_calls=1,
        is_tool=True,
    ),
    _action(
        "execute_code",
        (
            "Execute code in the contest sandbox. For programming tasks the same "
            "source is also run on the official sample input and compared with "
            "the expected output; only a sample AC counts as local run evidence."
        ),
        (
            ArgumentSpec("code", description="Source code to execute."),
            ArgumentSpec(
                "language",
                description="Runtime language; defaults to Python.",
                required=False,
            ),
        ),
        visibility="private",
        pack="programming",
        tool_calls=1,
        is_tool=True,
    ),
    _action(
        "web_search",
        "Search permitted web resources.",
        (ArgumentSpec("query", description="Search query."),),
        visibility="private",
        pack="research",
        tool_calls=1,
        is_tool=True,
    ),
    _action(
        "render_pdf",
        "Render complete source to PDF and page previews. Artifact contests also record "
        "this as the current candidate for independent review; other contests return a preview only. "
        "Use plain text for documents; HTML slide source only when the delivery contract requires it.",
        (ArgumentSpec("content", description="Complete document or slide source to render."),),
        visibility="private", pack="artifacts", is_tool=True, tool_calls=1,
    ),
)
