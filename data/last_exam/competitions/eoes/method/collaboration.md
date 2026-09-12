# Method — `eoes`

How this benchmark's agents are asked to work. Projected from `data/rules/eoes/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Collaborate only within the team under contest rules.
- Banned during the contest: internet access and running code. Permitted: calculators. Conditional: physical lab equipment is not available in this simulation. Paper and pencil are always available. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Separate provided observations from derived calculations and never invent an instrument reading, specimen state, safety check, or physical manipulation that the task does not expose.
- Reconcile units, tables, graphs, uncertainty, and conclusions into the single practical report required by the selected task.
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
    "mode": "unlimited"
  }
}
```

## Simulation

```json
{
  "max_turns": 24,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 11 (3 teammates x 2 turns + 1 answer parts + 4 for synthesis)",
  "physical_observation_adapter": "required_but_unavailable"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The task represents a practical or laboratory event through the available interface.",
    "The source-recorded active team has 3 members.",
    "Source-recorded competition rule: Physical instruments may be proxied; do not invent unavailable readings.",
    "Source-recorded competition rule: Official home page: each country sends two teams of three; two experimental assignments spanning biology/chemistry/physics skills.",
    "Source-recorded competition rule: Age: may only turn 17 during the EOES year (never older than 17).",
    "Physical instruments may be proxied; do not invent unavailable readings.",
    "Official home page: each country sends two teams of three; two experimental assignments spanning biology/chemistry/physics skills.",
    "Age: may only turn 17 during the EOES year (never older than 17)."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access and running code. Permitted: calculators. Conditional: physical lab equipment is not available in this simulation. Paper and pencil are always available. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: Use organizer-style calculator / lab constraints; no internet.",
    "Use organizer-style calculator / lab constraints; no internet.",
    "Do not claim tools, internet, or materials that the rule card forbids."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: Team experimental science practical packet.",
    "Source-recorded competition rule: Emphasis on team division of labor; ~4 hours per assignment described on home page.",
    "Team experimental science practical packet.",
    "Emphasis on team division of labor; ~4 hours per assignment described on home page.",
    "You must behave like a human teammate under official contest rules."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit a lab-style report: data, calculations, tables/graphs description, and conclusions.",
    "Official deliverable: lab report.",
    "Do not look up answer keys or hidden solutions."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per problem_or_question in gold_or_judge mode, but the repository evaluator is deferred; do not invent a completed score."
  ],
  "runtime_limitations": [
    "Runtime limitation: Wet-lab / instrument practicals are non-comparable to PDF reading agents without a lab proxy.",
    "Runtime limitation: Rules PDF content not fully retrieved here."
  ]
}
```
