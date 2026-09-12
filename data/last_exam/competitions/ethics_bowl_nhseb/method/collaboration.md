# Method — `ethics_bowl_nhseb`

How this benchmark's agents are asked to work. Projected from `data/rules/ethics_bowl_nhseb/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Only the seated members participate in a match; they may confer in the designated periods, while the non-presenting team remains silent during the other team's speaking period.
- Banned during the contest: internet access, calculators and running code. Conditional: paper and pencil is organizer provided scratch paper only and personal timer is non networked non storage reference only. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Observe the competition's phase order: confer only in an authorized conferral period, designate the current speaker, and stop when the modeled phase ends.
- Keep the team's presentation, opponent commentary, response, and judge-question answers distinct so each can be evaluated under its own official criterion.
- For the 2025-2026 NHSEB ruleset, use only the seated team for a match, make no mid-match substitution, and keep the non-presenting team silent during the other team's conferral and response periods.
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
    "max_message_chars": 1000,
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
  "turn_budget_basis": "official clock n/a turns vs floor 15 (5 teammates x 2 turns + 1 answer parts + 4 for synthesis)",
  "live_opponent_moderator_and_judges": "unavailable"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team prepares a case, presents it, and responds to judges or opponents.",
    "The source-recorded active team may have 3 to 5 members; the runner default is 5; official roster note: A team has three to seven students; no more than five are seated in a match.",
    "Source-recorded competition rule: The two teams reverse roles for the second half of the match and a new case and question are used.",
    "Source-recorded competition rule: Regional rule variations require NHSEB approval and must be communicated to participating teams."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "Source-recorded competition rule: Seated participants are selected before the match opens, and substitution is not allowed during a match.",
    "Source-recorded competition rule: A team timer may not store data or connect to the internet, may not time the opposing team, and is subordinate to the moderator's official time.",
    "Source-recorded competition rule: The judges' question-and-answer period lasts up to ten minutes; a team may briefly confer before answering a judge."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access, calculators and running code. Conditional: paper and pencil is organizer provided scratch paper only and personal timer is non networked non storage reference only. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: Organizer-provided scratch paper may be used, but outside notes and materials are prohibited and all match materials are collected afterward.",
    "Source-recorded competition rule: A team timer may not store data or connect to the internet, may not time the opposing team, and is subordinate to the moderator's official time."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Only the seated members participate in a match; they may confer in the designated periods, while the non-presenting team remains silent during the other team's speaking period.",
    "Source-recorded competition rule: A registered team has at least three and at most seven students, with no more than five seated for one match.",
    "Source-recorded competition rule: A team timer may not store data or connect to the internet, may not time the opposing team, and is subordinate to the moderator's official time.",
    "Source-recorded competition rule: The presenting team has two minutes to confer, followed by five minutes at a regional event or six minutes at a divisional playoff or National Championship.",
    "Source-recorded competition rule: The opposing team has two minutes to confer and three minutes to comment; the presenting team then has two minutes to confer and three minutes to respond.",
    "Source-recorded competition rule: The judges' question-and-answer period lasts up to ten minutes; a team may briefly confer before answering a judge.",
    "Source-recorded competition rule: When one team speaks, the other team must remain silent, although it may quietly take notes where the rules permit."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: Organizer-provided scratch paper may be used, but outside notes and materials are prohibited and all match materials are collected afterward."
  ],
  "deliverable_format": [
    "Runner answer contract: Provide the presentation, opposing-team commentary, response to commentary, and answers to judges as distinct labeled sections.",
    "Official deliverable: live oral match performance.",
    "Benchmark adaptation: The runner accepts a structured text transcript instead of a live two-team oral match.",
    "Source-recorded competition rule: The judges' question-and-answer period lasts up to ten minutes; a team may briefly confer before answering a judge."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per match in official_judge_rubric mode, but the repository evaluator is deferred_live_judges; do not invent a completed score.",
    "Source-recorded competition rule: The judges' question-and-answer period lasts up to ten minutes; a team may briefly confer before answering a judge."
  ],
  "runtime_limitations": [
    "Runtime limitation: Oral presentation + commentary + judge Q&A cannot be reduced to static essay answers without acknowledging the format mismatch.",
    "Runtime limitation: The runner does not reproduce a live opponent, moderator, three independent judges, oral timing, approved regional variations, or sanctions workflow.",
    "Runtime limitation: A structured text response cannot reproduce judges' private scoring and match votes."
  ]
}
```
