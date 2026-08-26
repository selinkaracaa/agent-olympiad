# Method — `mystery_hunt`

How this benchmark's agents are asked to work. Projected from `data/rules/mystery_hunt/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- The configured agents may freely coordinate inside their benchmark team; they may not obtain answers from another competing team.
- Banned during the contest: calculators and help from other teams. Permitted: internet access and running code. Paper and pencil are always available.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Track which material is currently released, which answers are provisional, and which answers are already committed; do not use or claim access to unreleased stages.
- Record dependencies between ordinary puzzles, metas, and final objectives so that handoffs preserve the state needed by later solvers.
- Treat the configured 8-12-agent roster as a benchmark adaptation, not an official MIT Mystery Hunt team-size limit.
- Separate task-level answer checking from full-hunt hint, interaction, meta, runaround, and coin-finding state that the current benchmark does not reproduce.
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
    "mode": "unstructured",
    "min_challenges": 0,
    "evaluation_dimensions": [
      "evidence_responsiveness",
      "decision_traceability"
    ]
  },
  "communication": {
    "mode": "unlimited"
  }
}
```

## Simulation

```json
{
  "max_turns": 29,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 29 (12 teammates x 2 turns + 1 answer parts + 4 for synthesis)",
  "full_hunt_unlock_state": "unavailable",
  "hint_and_interaction_state": "unavailable",
  "runaround_and_coin_state": "unavailable"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team works through material released in stages and commits answers under the event sequence.",
    "Benchmark adaptation: the runner permits 8 to 12 active agents and defaults to 12; official roster note: The 2026 FAQ states no official team-size recommendation; 8-12 is only the runner's configured range."
  ],
  "timeline": [
    "Source-recorded timing: Open-ended hunt timing; this row is one puzzle."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: calculators and help from other teams. Permitted: internet access and running code. Paper and pencil are always available.",
    "Source-recorded competition rule: Teams may coordinate internally and use ordinary solving tools and internet resources unless the current hunt or puzzle states a narrower rule."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: The configured agents may freely coordinate inside their benchmark team; they may not obtain answers from another competing team.",
    "Source-recorded competition rule: The MIT Mystery Hunt does not publish an official team-size recommendation or an 8-12 person maximum.",
    "Source-recorded competition rule: A team must not ask another competing team for puzzle answers."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit the team's final answers in numbered order, using exact values when required.",
    "Official deliverable: puzzle answer.",
    "Source-recorded competition rule: Answers must be submitted in the canonical answer form accepted by the current hunt's answer mechanism.",
    "Source-recorded competition rule: The 2026 winner must satisfy the hunt's MIT-student eligibility requirement and is expected to write the following year's hunt."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per problem_or_question in gold mode, but the repository evaluator is deferred_benchmark_metadata_missing; do not invent a completed score.",
    "Source-recorded competition rule: Answers must be submitted in the canonical answer form accepted by the current hunt's answer mechanism.",
    "Source-recorded competition rule: Remote participation does not reproduce every in-person interaction, and the in-person runaround is required to win the 2026 hunt."
  ],
  "runtime_limitations": [
    "Runtime limitation: Index team_size 12 is a modeling stub vs real 30–100+ teams.",
    "Runtime limitation: Physical runarounds, interactions, and meta structure are out of scope for isolated puzzle rows.",
    "Runtime limitation: Unrestricted web/tools make 'fair human comparison' poorly defined for LLM agents.",
    "Runtime limitation: The configured 8-12-agent range is a benchmark capacity choice, not an official roster limit.",
    "Runtime limitation: Question-level rows omit full-hunt unlocking, metas, hints, interactions, rate limits, runaround, and coin verification."
  ]
}
```
