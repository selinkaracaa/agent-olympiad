"""Give every rule-card role real duties instead of the generated boilerplate.

The draft generator gave 171 role slots the same three sentences, so a geometry
specialist and a forensics specialist read identical instructions and the roster
cost tokens without producing any division of labour. This script writes duties
derived from the role's title and the contest protocol, and leaves hand-written
duties alone.

Usage:
    python collectors/write_role_duties.py --dry-run
    python collectors/write_role_duties.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RULES = REPO / "data" / "rules"
sys.path.insert(0, str(REPO / "src"))

from rules import (  # noqa: E402
    iter_rule_card_ids,
    load_rule_card_payload,
    write_rule_card_payload,
)

BOILERPLATE = {
    (
        "Contribute according to your specialty.",
        "Respect contest resource limits.",
        "Help keep the shared answer/artifact coherent.",
    ),
    (
        "Coordinate the team and maintain the shared deliverable.",
        "Submit only after completeness and rule checks.",
        "Refuse forbidden tools and outside help.",
    ),
}

# Matched against the role title in order, so put specific keywords first.
DUTY_BANK: list[tuple[str, list[str]]] = [
    ("captain and synthesizer", [
        "Assign unsolved problems and keep the team from crowding one question.",
        "Hold the shared answer sheet and keep it consistent with the discussion.",
    ]),
    ("captain and batch submitter", [
        "Decide when the current batch is good enough to commit.",
        "Keep a running list of which problems are answered and which are open.",
    ]),
    ("captain / oralist", [
        "Own the spoken case: opening, structure, and closing.",
        "Absorb teammates' research into one line of argument rather than a list.",
    ]),
    ("captain / editor", [
        "Own the deliverable's structure and cut material that does not earn points.",
        "Resolve disagreements between analysts before they reach the final text.",
    ]),
    ("captain", [
        "Direct who answers and stop teammates from talking over each other.",
        "Give the team's official answer once the group has settled.",
    ]),
    ("team lead", [
        "Split challenges across the team and rebalance when someone stalls.",
        "Track partial findings so nothing discovered is lost.",
    ]),
    ("driver", [
        "Type the code and keep the single workstation productive.",
        "Refuse to start coding until the navigator's approach is clear.",
    ]),
    ("navigator", [
        "Design the algorithm and justify its complexity before code is written.",
        "Watch the driver's code for deviations from the agreed approach.",
    ]),
    ("tester", [
        "Invent edge cases, degenerate inputs, and overflow risks before submitting.",
        "Reproduce failures precisely so the fix targets the real cause.",
    ]),
    ("language reference reader", [
        "Answer library and syntax questions from permitted references only.",
        "Flag when a language feature is not in the official environment.",
    ]),
    ("algebra", [
        "Lead algebra, functions, equations, and inequality problems.",
        "Recheck each simplification before its answer enters the sheet.",
    ]),
    ("geometry", [
        "Lead geometry, trigonometry, and diagram-based reasoning.",
        "State any assumption a text-only diagram forces you to make.",
    ]),
    ("combinatorics", [
        "Lead counting, probability, and expected-value problems.",
        "Give exact fractions in lowest terms unless the problem says otherwise.",
    ]),
    ("number theory", [
        "Lead modular arithmetic, divisibility, and integer constructions.",
        "Check integer answers for off-by-one and sign mistakes.",
    ]),
    ("web / crypto", [
        "Lead web and cryptography challenges and report what the service reveals.",
        "Record every endpoint, parameter, and key you recover.",
    ]),
    ("pwn / reverse", [
        "Lead binary exploitation and reverse engineering work.",
        "Explain the vulnerability before claiming a working exploit.",
    ]),
    ("forensics", [
        "Lead forensics, steganography, and artefact recovery.",
        "Say which tool produced each finding so others can reproduce it.",
    ]),
    ("note-taker", [
        "Keep the shared notes current so no teammate repeats finished work.",
        "Consolidate recovered flags in the exact required format.",
    ]),
    ("backup operator", [
        "Pick up whichever challenge is stalled and try a different angle.",
        "Verify a teammate's flag before it is submitted.",
    ]),
    ("backup solver", [
        "Take the problems nobody has claimed rather than duplicating work.",
        "Say early when a problem is beyond the remaining time.",
    ]),
    ("fast solver", [
        "Clear the easy problems in the current batch quickly and accurately.",
        "Hand off anything that needs deep work instead of stalling the batch.",
    ]),
    ("strategy lead", [
        "Decide which problems are worth attempting for the points available.",
        "Call the trade-off between accuracy and speed for each batch.",
    ]),
    ("problem splitter", [
        "Partition the problem set so no two teammates duplicate work.",
        "Reassign problems as soon as someone finishes early.",
    ]),
    ("writeup checker", [
        "Check that each written answer actually answers the question asked.",
        "Enforce the required answer format before submission.",
    ]),
    ("completeness checker", [
        "Scan for unanswered problems before the team submits.",
        "Confirm every required part of the deliverable is present.",
    ]),
    ("verifier", [
        "Challenge weak arguments and demand an independent check.",
        "Reject an answer rather than let an unverified one be submitted.",
    ]),
    ("quant", [
        "Build the numbers: valuation, models, and sensitivity checks.",
        "State assumptions explicitly and show which results depend on them.",
    ]),
    ("analyst", [
        "Gather the evidence the recommendation rests on.",
        "Separate what the sources say from what the team infers.",
    ]),
    ("research lead", [
        "Decide which questions the research must answer and in what order.",
        "Kill lines of inquiry that will not change the recommendation.",
    ]),
    ("slide / report designer", [
        "Turn analysis into a structure a judge can follow in one pass.",
        "Cut slides and sections that do not carry an argument.",
    ]),
    ("researcher", [
        "Find and cite the authorities the argument depends on.",
        "Bring counter-authority to the team before a judge does.",
    ]),
    ("writer", [
        "Draft the assigned section in full prose, not notes.",
        "Keep the section within its word or time budget.",
    ]),
    ("opponent prep", [
        "Argue the other side hard enough to expose weak reasoning.",
        "Prepare answers to the strongest objection the team will face.",
    ]),
    ("judge-question specialist", [
        "Anticipate judge questions and prepare short, direct answers.",
        "Flag any claim the team cannot defend under questioning.",
    ]),
    ("experiment lead", [
        "Decide the procedure and the order of measurements.",
        "State the setup precisely enough for another team to repeat it.",
    ]),
    ("data recorder", [
        "Record every measurement with units and stated uncertainty.",
        "Never adjust a recorded value to fit an expectation.",
    ]),
    ("analysis / calculations", [
        "Turn recorded data into the required quantities, showing the work.",
        "Carry uncertainty through the calculation instead of dropping it.",
    ]),
    ("planner / editor", [
        "Run the planning stage and fix the outline before writing starts.",
        "Edit for the rubric during the peer-edit stage, not for taste.",
    ]),
    ("history specialist", [
        "Answer history and civilisation questions from memory alone.",
        "Say when you are unsure instead of guessing over a teammate.",
    ]),
    ("geography / arts", [
        "Answer geography, art, and literature questions from memory alone.",
        "Say when you are unsure instead of guessing over a teammate.",
    ]),
    ("science / misc", [
        "Answer science and miscellaneous questions from memory alone.",
        "Say when you are unsure instead of guessing over a teammate.",
    ]),
    ("primary solver", [
        "Produce the first full attempt at the problem.",
        "Show the reasoning so a teammate can check it.",
    ]),
    ("secondary solver", [
        "Attack the problem from a different angle than the primary solver.",
        "Compare results and surface the disagreement early.",
    ]),
    ("scribe", [
        "Keep the shared workspace readable and current.",
        "Write answers in the required format as they are settled.",
    ]),
    ("specialist", [
        "Take the part of the task that matches your stated specialty.",
        "Check a teammate's work once your own part is done.",
    ]),
]

PROTOCOL_DEFAULT = {
    "cyber_defense_proxy": [
        "Defend your assigned services and report what you changed.",
        "Keep services available while you harden them.",
    ],
    "robotics_rules_proxy": [
        "Own your part of the robot design, program, or run strategy.",
        "Check every choice against the season's scoring table.",
    ],
    "creative_performance_proxy": [
        "Contribute original team work only; no outside assistance.",
        "Tie your contribution to a scored element of the problem.",
    ],
    "event_packet_proxy": [
        "Work the event assigned to you with only the aids that event allows.",
        "Answer on the official sheet in the order the packet asks for.",
    ],
}

FALLBACK = [
    "Take the part of the task that matches your role and finish it.",
    "Check a teammate's work once your own part is done.",
]

SUBMITTER_DUTY = "Submit only after the format and rule checks pass."


def duties_for(title: str, protocol: str, may_submit: bool) -> list[str]:
    lowered = title.lower()
    duties: list[str] | None = None
    for keyword, bank in DUTY_BANK:
        if keyword in lowered:
            duties = list(bank)
            break
    if duties is None:
        duties = list(PROTOCOL_DEFAULT.get(protocol, FALLBACK))
    if may_submit:
        duties.append(SUBMITTER_DUTY)
    return duties


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--all", action="store_true", help="rewrite hand-written duties too"
    )
    args = parser.parse_args()

    changed_cards = 0
    changed_roles = 0
    for competition_id in iter_rule_card_ids(RULES):
        card = load_rule_card_payload(
            competition_id, rules_root=RULES, required=True
        )
        protocol = card.get("protocol") or ""
        touched = False
        for role in card.get("agent_roles") or []:
            current = tuple(role.get("duties") or ())
            if current and current not in BOILERPLATE and not args.all:
                continue
            duties = duties_for(role.get("title", ""), protocol, bool(role.get("may_submit")))
            if list(current) == duties:
                continue
            role["duties"] = duties
            touched = True
            changed_roles += 1
        if not touched:
            continue
        changed_cards += 1
        print(f"{card['competition_id']}: rewrote duties for {len(card['agent_roles'])} roles")
        if not args.dry_run:
            write_rule_card_payload(
                competition_id,
                card,
                rules_root=RULES,
            )

    print(
        f"\n{changed_roles} roles in {changed_cards} cards"
        + (" (dry run)" if args.dry_run else "")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
