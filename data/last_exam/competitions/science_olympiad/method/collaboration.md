# Method — `science_olympiad`

How this benchmark's agents are asked to work. Projected from `data/rules/science_olympiad/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Only the participants authorized by the selected season, division, and event rules may collaborate on that event.
- Banned during the contest: internet access and running code. Conditional: calculator permission is event-dependent and not exposed by default. Paper and pencil are always available. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Apply only the rules for the selected season, division, and event; a tournament roster rule does not authorize every roster member to collaborate on one event.
- Do not treat the 15-person tournament roster as the active team for one event; require the event's season, division, event rules, corrections, and score sheet before claiming official equivalence.
- Only designated submitters may make the shared submission: Agent_1.
- Use only the official mechanisms that the current task actually exposes; do not claim physical, oral, live-opponent, judge, or environment actions that were not observed.

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
  "max_turns": 35,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 35 (15 teammates x 2 turns + 1 answer parts + 4 for synthesis)",
  "selector_enforcement": "missing_from_current_rows"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The task represents one event packet from a broader multi-event competition.",
    "Benchmark adaptation: the runner permits 1 to 15 active agents and defaults to 15; official roster note: Fifteen is a tournament roster cap, not the active participant count for one event.",
    "Source-recorded competition rule: The Division B or C tournament roster may contain up to fifteen students, but this does not make all fifteen active participants in one event.",
    "Source-recorded competition rule: Official event corrections and clarifications modify the corresponding event rules and must be applied with the selected season packet.",
    "Source-recorded competition rule: No unrestricted web search is allowed unless the selected event rules explicitly authorize it."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "Source-recorded competition rule: Season, division, and event must be selected before active participants, time, tools, references, deliverable, and scoring can be treated as official."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access and running code. Conditional: calculator permission is event-dependent and not exposed by default. Paper and pencil are always available. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: Only the references, calculators, devices, build materials, and safety equipment authorized by the selected event rules may be used."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Only the participants authorized by the selected season, division, and event rules may collaborate on that event."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit the team's final answers in numbered order, using exact values when required.",
    "Official deliverable: event answer sheet."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per problem_or_question in gold_or_judge mode, but the repository evaluator is deferred_event_rules_not_selected; do not invent a completed score.",
    "Source-recorded competition rule: The event score sheet or rubric, not a generic Science Olympiad formula, determines official performance."
  ],
  "runtime_limitations": [
    "Runtime limitation: Without the locked Rules Manual, event-level tool lists cannot be asserted.",
    "Runtime limitation: 15-person multi-event tournament ≠ one exam packet.",
    "Runtime limitation: The current row lacks season, division, and event selectors and therefore cannot select a binding event rulebook.",
    "Runtime limitation: The runner cannot reproduce event-dependent laboratory apparatus, constructed devices, impound, safety inspection, or physical performance."
  ]
}
```
