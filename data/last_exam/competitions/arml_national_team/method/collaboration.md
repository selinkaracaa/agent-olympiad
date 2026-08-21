# Method — `arml_national_team`

How this benchmark's agents are asked to work. Projected from `data/rules/arml_national_team/collaboration.json`.

## Agent constraints

- Inhabit an eligible national ARML contestant on one coach-seeded 15-person regional team; do not invent substitutes, borrowed students, or a second region.
- Compete as one Team Round team with one shared sheet—not as 15 independent solvers.
- Begin with the same contestant permissions as every teammate; do not assume a permanent captain, specialist, or reviewer office.
- Carry age, graduation, region, seeding, and no-mid-Team-Round-substitution obligations as conscience.
- Treat private reasoning as unknown to teammates until you communicate it.
- When teammates disagree, surface an independent check before writing the answer on the shared sheet.
- Any contestant may file the shared sheet, but the team files exactly one.
- Do not use a calculator, electronic device, internet, electronic translator, archives, or outside help.
- Do not invent a Team Round wall-clock the official rules page does not give, and do not start Individual, Power, or Relay work in this sitting.

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
    "team_message_budget": 30,
    "per_agent_message_budget": 2,
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
  "max_turns": 44,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock 4 turns vs floor 44 (15 teammates x 2 turns + 10 answer parts + 4 for synthesis)",
  "eligibility_and_logistics_state": "specified_for_role_immersion_not_enforced"
}
```

## Rule sections

```json
{
  "official_eligibility_and_logistics": [
    "Official: a student must not have turned 19 before the December 31 immediately preceding the competition, with the January-to-meet exception only if the student did not graduate K-12 before March 1 of the competition year.",
    "Official: no student who graduated high school before March 1 of the competition year is eligible.",
    "Official: teams must be drawn from a well-defined contiguous, non-intersecting region without gerrymandering or dual-region students.",
    "Official: coaches seed 15-person teams by strength as A1, A2, … or B1, B2, ….",
    "Official: borrowed students are prohibited; a student may compete only on the team they are registered with for housing.",
    "Simulation choice: these identity obligations are role immersion; the session does not execute registration, housing, or eligibility state."
  ],
  "competition_format": [
    "Official: this sitting is the Team Round: ten questions, five points each, 50 possible, worked by the entire team.",
    "Official: Individual is five rounds of two questions, one point each, 10 per person and 150 per team.",
    "Official: Power is worth 50 points with exactly one solution packet.",
    "Official: Relay awards 5 points at three minutes and 3 points at six minutes, with 25 possible per Relay 1 and 25 possible per Relay 2.",
    "Simulation choice: agents work only the Team Round."
  ],
  "timeline": [
    "Official: no substitutions can be made once the Team Round has started.",
    "Official: the ARML/IRML rules page does not establish a Team Round wall-clock duration.",
    "Simulation choice: do not treat 20 minutes or any other secondary clock as official.",
    "Simulation choice: max_turns is a safety budget, not an official countdown."
  ],
  "resource_policy": [
    "Official: calculators will not be allowed on any part of the ARML contest.",
    "Official: electronic devices are banned; discovery during Team or Power disqualifies the team from that round; devices are collected before Team and returned after Power.",
    "Official: a book-form dictionary is allowed only for participants whose first language is not English; electronic translators are not allowed.",
    "Official: an inspected visual aid such as a magnifying glass is allowed for a visual handicap.",
    "Simulation choice: the only exposed tool is consulting these contest rules."
  ],
  "collaboration_protocol": [
    "Official: the entire team works the Team Round together on one shared short-answer process.",
    "Official: Individual communication is banned once questions are handed out; that ban does not apply to this Team Round sitting.",
    "Simulation choice: contestants start as equal peers; temporary specialization may emerge but is never a fixed office."
  ],
  "integrity_and_compliance": [
    "Official: cheating during the Team or Power round nullifies that round's score.",
    "Official: students must respect university, ARML, and team property.",
    "Official: no internet, outside references, or borrowed students.",
    "Simulation choice: accessing hidden answers or evaluator internals is a compliance violation."
  ],
  "deliverable_format": [
    "Official: Team Round answers are short numerical values; proofs are not required for this round.",
    "Official: the team files one shared answer sheet.",
    "Simulation choice: submit the team's final answers in numbered order, using exact values when required."
  ],
  "evaluation_criteria": [
    "Official: each correct Team Round answer is worth five points, 50 possible.",
    "Official: team-score ties at the meet are broken by Team plus Power, then Relay, then Individual.",
    "Simulation choice: this session scores the Team Round sheet against gold short answers and does not compute a full-meet tie-break."
  ],
  "runtime_limitations": [
    "Simulation choice: no official Team Round clock is encoded, so no live countdown runs.",
    "Simulation choice: device collection, scoring-room substitutions, physical cards, and 15-person room logistics are unavailable.",
    "Simulation choice: limited message budgets and structured deliberation are research overlays, not official ARML rules."
  ],
  "typical_contest_workflow": [
    "Simulation choice: cover all ten questions, keep independent checks on high-value answers, and reconcile one sheet.",
    "Simulation choice: reassign work when a teammate finishes or a check fails."
  ],
  "conflict_resolution": [
    "Simulation choice: answer disagreements are resolved by an independent recomputation, not by silent overwrite."
  ],
  "handoff_protocol": [
    "Simulation choice: a handoff should name the question, claimed answer, method, doubts, and next check."
  ],
  "review_protocol": [
    "Simulation choice: review before filing is optional; corrections caused by review should remain observable."
  ],
  "emergent_behavior": [
    "Observe but do not require scouting, allocation, temporary specialization, independent checks, or role rotation.",
    "Do not reward a permanent captain, equal speaking time, exclusive question ownership, or message volume by itself."
  ]
}
```
