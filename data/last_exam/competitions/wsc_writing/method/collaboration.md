# Method — `wsc_writing`

How this benchmark's agents are asked to work. Projected from `data/rules/wsc_writing/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Collaborate only within the team under contest rules.
- Banned during the contest: internet access, calculators, running code and personal electronics. Paper and pencil are always available. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Respect the event's shared-planning, private-writing, and review stages; do not transfer text or edits across a stage boundary unless that stage permits it.
- Do not reveal one writer's private drafting state to another writer during the individual-writing stage unless the selected event rules explicitly reopen collaboration.
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
    "team_message_budget": 8,
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
  "turn_budget_basis": "official clock n/a turns vs floor 11 (3 teammates x 2 turns + 1 answer parts + 4 for synthesis)"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team plans together, writes under the event's individual-work stage, and completes the permitted review stage.",
    "The source-recorded active team has 3 members.",
    "Source-recorded competition rule: Each of the three teammates answers a different prompt.",
    "Source-recorded competition rule: Responses may use a form appropriate to the prompt, including creative pieces, persuasive arguments, poems, or essays.",
    "Each of the three teammates answers a different prompt.",
    "Responses may use a form appropriate to the prompt, including creative pieces, persuasive arguments, poems, or essays."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "The event runs in team-preparation, individual-writing, and final peer-review stages.",
    "No official numeric stage schedule is encoded from the available primary sources."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access, calculators, running code and personal electronics. Paper and pencil are always available. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: Write the response with pen or pencil.",
    "Write the response with pen or pencil.",
    "No electronic devices; treat the writing as handwritten."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: The team receives three to four prompts drawn from the six World Scholar's Cup subject areas.",
    "Source-recorded competition rule: The team answers exactly three prompts.",
    "The team receives three to four prompts drawn from the six World Scholar's Cup subject areas.",
    "The team answers exactly three prompts.",
    "Prepare with teammates without devices before individual writing begins.",
    "Each teammate writes independently, then teammates review one another's work at the end."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit three written responses, one per teammate, with each response answering a different prompt.",
    "Official deliverable: written essay.",
    "Source-recorded competition rule: First prepare with teammates without using devices, then write independently, then review one another's work at the end.",
    "Source-recorded competition rule: Write the response with pen or pencil.",
    "First prepare with teammates without using devices, then write independently, then review one another's work at the end.",
    "Write the response with pen or pencil.",
    "Submit three essays or the staged portfolio required by the prompt."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is evaluated per artifact in rubric mode by rubric_llm_v1; repository evaluator status is ready."
  ],
  "runtime_limitations": [
    "Runtime limitation: Neither the fetched official events page nor the official rubric PDF states a numeric stage schedule.",
    "Runtime limitation: The rubric PDF contains evaluation questions only; it does not establish a rule that peer editors may not finish an incomplete response."
  ]
}
```
