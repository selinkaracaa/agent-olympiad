# Method — `vis_moot`

How this benchmark's agents are asked to work. Projected from `data/rules/vis_moot/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Collaborate only within the team under contest rules.
- Banned during the contest: calculators and running code. Permitted: internet access. Paper and pencil are always available.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Observe the competition's phase order: confer only in an authorized conferral period, designate the current speaker, and stop when the modeled phase ends.
- Keep the team's presentation, opponent commentary, response, and judge-question answers distinct so each can be evaluated under its own official criterion.
- Only designated submitters may make the shared submission: Agent_1.
- Use only the official mechanisms that the current task actually exposes; do not claim physical, oral, live-opponent, judge, or environment actions that were not observed.

## Information / deliberation / communication

```json
{
  "information_policy": {
    "mode": "role_specialized",
    "shared": [
      "problem",
      "contest_rules",
      "team_discussion",
      "scratchpad"
    ],
    "coordination_requirement": "All teammates may consult the complete public contest rules. Private reasoning becomes shared state only when communicated; assigned rule expertise creates tracking responsibility, not exclusive access."
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
    "team_message_budget": 10,
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
  "max_turns": 24,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 15 (5 teammates x 2 turns + 1 answer parts + 4 for synthesis)"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team prepares a case, presents it, and responds to judges or opponents.",
    "Mixed or unresolved rulesets: the runner permits 2 to 5 active agents and defaults to 5.",
    "Source-recorded competition rule: Prepare arbitration memorials from the Vis problem packet.",
    "Source-recorded competition rule: Facts limited to Problem + clarifications + necessary logical extensions / publicly available true facts; inventing facts is unethical and sanctioned.",
    "Source-recorded competition rule: Use current-year Rules Booklet (rules change annually).",
    "Prepare arbitration memorials from the Vis problem packet.",
    "Facts limited to Problem + clarifications + necessary logical extensions / publicly available true facts; inventing facts is unethical and sanctioned.",
    "Use current-year Rules Booklet (rules change annually)."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "Source-recorded competition rule: Oral hearings in Vienna (and/or Vis East Hong Kong as separate moot); registration fee and participation expectations after claimant memo.",
    "Oral hearings in Vienna (and/or Vis East Hong Kong as separate moot); registration fee and participation expectations after claimant memo."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: calculators and running code. Permitted: internet access. Paper and pencil are always available.",
    "Do not claim tools, internet, or materials that the rule card forbids."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: Team: ≥2 students from one institution; no maximum team size (31st Rules §31).",
    "Source-recorded competition rule: Memoranda: searchable PDF, single file, typically ≤1 MB upload limit; deadlines via team account (claimant then respondent).",
    "Team: ≥2 students from one institution; no maximum team size (31st Rules §31).",
    "Memoranda: searchable PDF, single file, typically ≤1 MB upload limit; deadlines via team account (claimant then respondent).",
    "You must behave like a human teammate under official contest rules."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: Legal research is allowed; outside drafting help is not.",
    "Legal research is allowed; outside drafting help is not."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit the written memorial/case analysis and a concise oral outline.",
    "Official deliverable: written memorandum.",
    "Benchmark adaptation: Official memoranda are filed as PDF; the runner submits the memorandum text.",
    "Source-recorded competition rule: Write for both advocacy and oral defense.",
    "Source-recorded competition rule: Parts: memorandum for claimant, memorandum for respondent, oral hearings.",
    "Source-recorded competition rule: Oral hearings in Vienna (and/or Vis East Hong Kong as separate moot); registration fee and participation expectations after claimant memo.",
    "Write for both advocacy and oral defense.",
    "Parts: memorandum for claimant, memorandum for respondent, oral hearings.",
    "Oral hearings in Vienna (and/or Vis East Hong Kong as separate moot); registration fee and participation expectations after claimant memo.",
    "Do not look up answer keys or hidden solutions."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per artifact in rubric mode, but the repository evaluator is unassigned; do not invent a completed score."
  ],
  "runtime_limitations": [
    "Runtime limitation: Index team_size 5 is a modeling choice, not a Vis maximum.",
    "Runtime limitation: Oral arbitration advocacy and multi-month prep dwarfs single-session agent runs.",
    "Runtime limitation: 31st Rules PDF retrieved; prefer the Rules Booklet for the exact Vis year under evaluation."
  ]
}
```
