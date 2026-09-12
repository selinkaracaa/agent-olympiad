# Method — `history_olympiad`

How this benchmark's agents are asked to work. Projected from `data/rules/history_olympiad/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- No verbal or written conferral is allowed while a tossup is being read; official bonus and third-quarter category phases permit team conferral.
- Banned during the contest: internet access, calculators and running code. Conditional: paper and pencil is blank paper only. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Follow phase-specific buzzer, recognition, speaker, and conferral rules; do not communicate an answer during a phase in which teammate consultation is forbidden.
- Maintain the current quarter, eligibility-to-answer state, score state, and committed responses without inventing opponent or moderator actions.
- During tossups, teammates may not confer verbally or in writing and only the contestant who buzzed may answer; conferral is allowed only in the official bonus and category-round phases.
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
  "max_turns": 24,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 13 (4 teammates x 2 turns + 1 answer parts + 4 for synthesis)",
  "selector_enforcement": "missing_from_historical_rows",
  "buzzer_opponents_and_moderator": "unavailable"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The task represents a buzzer round or match packet.",
    "Mixed or unresolved rulesets: the runner permits 1 to 4 active agents and defaults to 3; source boundary: The 2025 World Championship uses teams of two or three, with one allowed to play if teammates are absent; historical benchmark rows still record four and require edition review."
  ],
  "timeline": [
    "Source-recorded timing: Bowl round / packet timing.",
    "Source-recorded competition rule: A contestant must buzz before answering a tossup, and only the contestant who buzzed may give the answer.",
    "Source-recorded competition rule: Second-quarter bonuses allow conferral, are worth ten points, and do not bounce back after an incorrect answer.",
    "Source-recorded competition rule: The third-quarter category round gives each team sixty seconds, permits conferral, allows passes without return, and may award a twenty-point sweep bonus."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access, calculators and running code. Conditional: paper and pencil is blank paper only. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: No pre-existing resources are allowed; a writing utensil and blank paper may be used to take notes where the phase permits."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: No verbal or written conferral is allowed while a tossup is being read; official bonus and third-quarter category phases permit team conferral.",
    "Source-recorded competition rule: Under the 2025 World Championship rules, a team plays with two or three students; one student may still compete if teammates are absent.",
    "Source-recorded competition rule: Incorrect responses never deduct points, although an incorrect tossup response makes that team ineligible to buzz again on that question.",
    "Source-recorded competition rule: Teammates may not confer verbally or in writing during tossups, and no notes may be written while a tossup is being read.",
    "Source-recorded competition rule: The third-quarter category round gives each team sixty seconds, permits conferral, allows passes without return, and may award a twenty-point sweep bonus.",
    "Source-recorded competition rule: A tied first or second place is broken by zero-point tossup questions until one team answers correctly."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition."
  ],
  "deliverable_format": [
    "Runner answer contract: Return numbered answers for the exposed questions and identify the quarter or phase; do not claim a live buzz, opponent outcome, or moderator ruling.",
    "Official deliverable: live four quarter buzzer match responses.",
    "Benchmark adaptation: The runner grades a text packet or session without live buzzer, opponent, moderator, or protest state.",
    "Source-recorded competition rule: A contestant must buzz before answering a tossup, and only the contestant who buzzed may give the answer.",
    "Source-recorded competition rule: A contestant who buzzes has three seconds to begin an answer, subject to the moderator's non-protestable timing judgment.",
    "Source-recorded competition rule: Second-quarter bonuses allow conferral, are worth ten points, and do not bounce back after an incorrect answer.",
    "Source-recorded competition rule: Fourth-quarter tossups are worth thirty, twenty, or ten points depending on where the answer is given."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per session in edition_specific_match_score mode, but the repository evaluator is deferred_ruleset_and_match_engine; do not invent a completed score.",
    "Source-recorded competition rule: The third-quarter category round gives each team sixty seconds, permits conferral, allows passes without return, and may award a twenty-point sweep bonus.",
    "Source-recorded competition rule: A tied first or second place is broken by zero-point tossup questions until one team answers correctly."
  ],
  "runtime_limitations": [
    "Runtime limitation: Buzzer interrupt timing and neg penalties are central and hard to simulate from static packets.",
    "Runtime limitation: Bee vs Bowl formats differ — benchmark excludes Bee/MS per collection notes.",
    "Runtime limitation: Historical benchmark packets do not declare the governing rules edition, so the 2025 roster and gameplay rules cannot be silently applied to every row.",
    "Runtime limitation: The runner lacks live opponents, buzzer lockout, moderator answer acceptance, phase clocks, protests, bouncebacks, and category selection state."
  ]
}
```
