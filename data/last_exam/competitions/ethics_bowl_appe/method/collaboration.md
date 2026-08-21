# Method — `ethics_bowl_appe`

How this benchmark's agents are asked to work. Projected from `data/rules/ethics_bowl_appe/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- The seated participants may confer only in the designated phase; multiple members may contribute orally, but only one person speaks at a time.
- Banned during the contest: internet access, calculators and running code. Conditional: paper and pencil is scratch paper only after official start and personal timer is non networked non storage reference only. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Observe the competition's phase order: confer only in an authorized conferral period, designate the current speaker, and stop when the modeled phase ends.
- Keep the team's presentation, opponent commentary, response, and judge-question answers distinct so each can be evaluated under its own official criterion.
- For the 2025 APPE national ruleset, treat response, commentary, commentary response, and judge questioning as separate hard-stop phases and allow only one speaker at a time.
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
  "live_opponent_and_judges": "unavailable"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team prepares a case, presents it, and responds to judges or opponents.",
    "The source-recorded active team may have 1 to 6 members; the runner default is 5; official roster note: The 2025 national rules allow a team of any roster size, but no more than six members may actively participate in a match.",
    "Source-recorded competition rule: Teams may be any roster size, but no more than six members may actively participate in a match.",
    "Source-recorded competition rule: The match winner is determined by judges' sheet outcomes, not by simply summing both teams' raw points."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "Source-recorded competition rule: Once participants are seated and ready, no substitution is allowed for the remainder of the round after the case is announced.",
    "Source-recorded competition rule: Books and pre-existing notes are prohibited during the match; organizer-provided case material and scratch paper may be used after the official timer starts.",
    "Source-recorded competition rule: The presenting team receives two minutes to confer and up to ten minutes to respond, with a hard stop at time.",
    "Source-recorded competition rule: After one minute of conferral, the opposing team has up to five minutes to comment, and only one of its members may speak at a time.",
    "Source-recorded competition rule: The presenting team then receives one minute to confer and up to five minutes to reply to the commentary, with one speaker at a time.",
    "Source-recorded competition rule: Judges receive up to ten minutes for questions; team members may briefly huddle before answering and different members may answer different judges.",
    "Source-recorded competition rule: After the first case, the teams reverse presenting and commenting roles for a second case."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access, calculators and running code. Conditional: paper and pencil is scratch paper only after official start and personal timer is non networked non storage reference only. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: Books and pre-existing notes are prohibited during the match; organizer-provided case material and scratch paper may be used after the official timer starts.",
    "Source-recorded competition rule: A personal timer is only a reference: it may not connect to the internet or store data, and the moderator's timer is official."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: The seated participants may confer only in the designated phase; multiple members may contribute orally, but only one person speaks at a time.",
    "Source-recorded competition rule: The presenting team receives two minutes to confer and up to ten minutes to respond, with a hard stop at time.",
    "Source-recorded competition rule: After one minute of conferral, the opposing team has up to five minutes to comment, and only one of its members may speak at a time.",
    "Source-recorded competition rule: The presenting team then receives one minute to confer and up to five minutes to reply to the commentary, with one speaker at a time.",
    "Source-recorded competition rule: Judges receive up to ten minutes for questions; team members may briefly huddle before answering and different members may answer different judges."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: Books and pre-existing notes are prohibited during the match; organizer-provided case material and scratch paper may be used after the official timer starts."
  ],
  "deliverable_format": [
    "Runner answer contract: Provide the case response, opposing-team commentary, commentary reply, and judge-question answers as distinct labeled sections exposed by the task.",
    "Official deliverable: live oral match performance.",
    "Benchmark adaptation: The runner accepts a structured text transcript instead of a live two-team oral match.",
    "Source-recorded competition rule: Judges receive up to ten minutes for questions; team members may briefly huddle before answering and different members may answer different judges."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per match in official_judge_rubric mode, but the repository evaluator is deferred_live_judges; do not invent a completed score."
  ],
  "runtime_limitations": [
    "Runtime limitation: Live oral ethics debate / commentary rounds are rubric-oral; transcript-only proxies lose timing and interruption norms.",
    "Runtime limitation: Need the Rules PDF click-through for bans on notes/devices if any.",
    "Runtime limitation: The runner does not reproduce a live opposing team, moderator, three-judge panel, role reversal, oral hard stops, or judge questions.",
    "Runtime limitation: A text transcript is a benchmark adaptation of the official oral match performance."
  ]
}
```
