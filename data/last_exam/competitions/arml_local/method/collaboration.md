# Method — `arml_local`

How this benchmark's agents are asked to work. Projected from `data/rules/arml_local/collaboration.json`.

## Agent constraints

- Inhabit an eligible ARML Local contestant on one fixed six-person school or homeschool team; do not invent a seventh teammate, a borrowed student, or a mid-round substitute.
- Compete as six teammates on one Team Round sheet—not as six independent solvers.
- Begin with the same contestant permissions as every teammate; do not assume a permanent captain, specialist, or reviewer office.
- Treat private reasoning as unknown to teammates until you communicate it.
- When teammates disagree on an answer, surface the conflict with an independent check before writing it on the shared sheet.
- Any contestant may file the shared sheet, but the team files exactly one.
- Do not use a calculator, electronic device, internet, books, notes, archives, or outside help.
- Do not start Individual or Relay work in this sitting.

## Information / deliberation / communication

```json
{
  "information_policy": {
    "mode": "shared",
    "shared": [
      "problem",
      "contest_rules",
      "team_discussion",
      "scratchpad"
    ],
    "coordination_requirement": "Contestants receive equal baseline information access, but private reasoning is not silently copied between them; they must communicate discoveries needed by teammates."
  },
  "deliberation": {
    "mode": "structured",
    "min_challenges": 1,
    "decision_maker": "submitter",
    "evaluation_dimensions": [
      "evidence_responsiveness",
      "revision_after_challenge",
      "decision_traceability",
      "authority_bias",
      "majority_bias"
    ]
  },
  "communication": {
    "mode": "limited",
    "team_message_budget": 18,
    "per_agent_message_budget": 3,
    "max_message_chars": 1200,
    "counted_actions": [
      "speak",
      "write_scratchpad",
      "propose",
      "challenge",
      "provide_evidence",
      "revise",
      "decide"
    ]
  }
}
```

## Simulation

```json
{
  "max_turns": 26,
  "scheduler": "round_table_or_centralized",
  "turn_budget_basis": "official clock 9 turns vs floor 26 (6 teammates x 2 turns + 10 answer parts + 4 for synthesis)",
  "eligibility_and_logistics_state": "specified_for_role_immersion_not_enforced"
}
```

## Rule sections

```json
{
  "official_eligibility_and_logistics": [
    "Official: ARML Local is open to all middle schools, high schools, and homeschool groups.",
    "Official: each school may field one or more teams of six students.",
    "Official: coaches or local contest coordinators grade papers the day of the contest and submit team scores.",
    "Simulation choice: eligibility, multi-team school identity, and score-submission logistics are carried as contestant conscience; the session does not execute registration or grading-portal state."
  ],
  "competition_format": [
    "Official: this sitting is the Team Round: a set of 15 short-answer questions worked together by the entire team.",
    "Official: the same Local meet also has Individual and Relay rounds with a structure similar to the national meet.",
    "Simulation choice: agents work only the Team Round; they must not pretend to run Individual or Relay."
  ],
  "timeline": [
    "Official: the Team Round is 45 minutes.",
    "Official: Individual is five pairs at 10 minutes per pair.",
    "Official: Relay is three rounds of 6, 8, and 10 minutes.",
    "Official: the Local contest can be completed in about 2.5 hours, allowing for breaks.",
    "Simulation choice: max_turns is a safety budget approximating the 45-minute Team Round, not a live countdown clock."
  ],
  "resource_policy": [
    "Official: calculators are not allowed on any ARML part.",
    "Official: phones, computers, internet, books, and notes are forbidden; paper and pencil are allowed.",
    "Official: work only from the materials provided with the problem.",
    "Simulation choice: the only exposed tool is consulting these contest rules."
  ],
  "collaboration_protocol": [
    "Official: the entire six-person team works the Team Round together and produces one shared short-answer sheet.",
    "Simulation choice: contestants start as equal peers; temporary specialization may emerge but is never a fixed office.",
    "Simulation choice: private notes are not team knowledge until communicated."
  ],
  "integrity_and_compliance": [
    "Official: do not look up contest archives, answer keys, or outside problem-solving help.",
    "Official: electronic devices and calculators are banned.",
    "Simulation choice: accessing hidden answers or evaluator internals is a compliance violation."
  ],
  "deliverable_format": [
    "Official: submit one shared short-answer sheet; answers are usually exact values.",
    "Official: the Team Round contains 15 questions.",
    "Simulation choice: current tasks serialize 10 numbered answer parts: 1. [answer] through 10. [answer]."
  ],
  "evaluation_criteria": [
    "Official: coaches and local coordinators grade the papers and submit team scores.",
    "Official: the Local page does not publish a numeric point value per Team Round question.",
    "Simulation choice: this session scores the submitted numbered answers against gold short answers."
  ],
  "runtime_limitations": [
    "Simulation choice: the 45-minute hard stop, physical papers, live proctors, and coach score submission are not enforced.",
    "Simulation choice: Individual, Relay, nationwide compilation, and prize fulfillment are unavailable.",
    "Simulation choice: limited message budgets and structured deliberation are research overlays, not official ARML Local rules."
  ],
  "typical_contest_workflow": [
    "Simulation choice: read the sheet, split remaining questions, and keep at least one independent check on high-risk answers.",
    "Simulation choice: reconcile one numbered sheet before anyone files it."
  ],
  "conflict_resolution": [
    "Simulation choice: answer disagreements are resolved by an independent recomputation or written reason, not by silent overwrite of the shared sheet."
  ],
  "handoff_protocol": [
    "Simulation choice: a handoff should name the question, the claimed answer, the method, remaining doubts, and the next check."
  ],
  "review_protocol": [
    "Simulation choice: review before filing is optional rather than mandatory; corrections caused by review should remain observable."
  ],
  "emergent_behavior": [
    "Observe but do not require scouting, allocation, temporary specialization, independent checks, or role rotation.",
    "Do not reward a permanent captain, equal speaking time, exclusive question ownership, or message volume by itself."
  ]
}
```
