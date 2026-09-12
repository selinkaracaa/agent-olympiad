# Method — `ichto`

How this benchmark's agents are asked to work. Projected from `data/rules/ichto/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Collaborate within one national team. Reporter, Opponent, Reviewer, and Observer are assignments held by different teams in a fight, not teammate roles.
- Banned during the contest: internet access and running code. Permitted: calculators. Conditional: presentation devices are limited to one laptop or tablet showing a single slideshow. Paper and pencil are always available.
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
    "mode": "unlimited"
  }
}
```

## Simulation

```json
{
  "max_turns": 24,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 13 (4 teammates x 2 turns + 1 answer parts + 4 for synthesis)"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team prepares a case, presents it, and responds to judges or opponents.",
    "The source-recorded active team may have 4 to 6 members; the runner default is 4.",
    "Source-recorded competition rule: Do not fabricate experimental results not supported by materials.",
    "Source-recorded competition rule: Teams of 4 to 6 high-school students representing one country; the working language is English.",
    "Source-recorded competition rule: The Reporter may open only a single slideshow file and no other files or windows.",
    "Do not fabricate experimental results not supported by materials.",
    "Teams of 4 to 6 high-school students representing one country; the working language is English.",
    "The Reporter may open only a single slideshow file and no other files or windows."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "Source-recorded competition rule: In each round your team acts as Reporter, Opponent, Reviewer, or (in four-team sections) Observer, and roles rotate every round until every team has held every role.",
    "Source-recorded competition rule: The Captain nominates which single team member serves as Reporter, Opponent, or Reviewer for a round, and only that person speaks for the team.",
    "Source-recorded competition rule: Keep to the round clock: report 8 minutes, opposition 5, reporter's response 4, academic discussion 5, review 3, jury questions 5, general discussion 5; all monologues are strictly monologues.",
    "Source-recorded competition rule: Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Source-recorded competition rule: Once you begin an active role you may not communicate with your team until the round ends, except during a time-out.",
    "Source-recorded competition rule: A Captain may call one 60-second time-out per stage, only before the jury's questions and only between parts of the round or during the reporter-opponent discussion.",
    "Source-recorded competition rule: Your team may reject two challenges per round for free; from the third rejection onward the round's Reporter points are multiplied by 0.8, 0.7, 0.6, 0.5, or 0.4.",
    "Source-recorded competition rule: Strategic refusals are limited to one per stage and two across all semi-final stages; all other refusals are tactical and apply only to the current round.",
    "Source-recorded competition rule: In the general discussion each active team may ask exactly one question before observers, jury, and audience may ask.",
    "In each round your team acts as Reporter, Opponent, Reviewer, or (in four-team sections) Observer, and roles rotate every round until every team has held every role.",
    "The Captain nominates which single team member serves as Reporter, Opponent, or Reviewer for a round, and only that person speaks for the team.",
    "Keep to the round clock: report 8 minutes, opposition 5, reporter's response 4, academic discussion 5, review 3, jury questions 5, general discussion 5; all monologues are strictly monologues.",
    "Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Once you begin an active role you may not communicate with your team until the round ends, except during a time-out.",
    "A Captain may call one 60-second time-out per stage, only before the jury's questions and only between parts of the round or during the reporter-opponent discussion.",
    "Your team may reject two challenges per round for free; from the third rejection onward the round's Reporter points are multiplied by 0.8, 0.7, 0.6, 0.5, or 0.4.",
    "Strategic refusals are limited to one per stage and two across all semi-final stages; all other refusals are tactical and apply only to the current round.",
    "In the general discussion each active team may ask exactly one question before observers, jury, and audience may ask."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access and running code. Permitted: calculators. Conditional: presentation devices are limited to one laptop or tablet showing a single slideshow. Paper and pencil are always available.",
    "Source-recorded competition rule: Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Do not claim tools, internet, or materials that the rule card forbids.",
    "Banned during the contest: internet access and running code. Permitted: calculators and one presentation device restricted to a single slideshow. Paper and pencil are available."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate within one national team. Reporter, Opponent, Reviewer, and Observer are assignments held by different teams in a fight, not teammate roles.",
    "Source-recorded competition rule: Cite reasoning clearly; be ready for opponent and jury questioning.",
    "Source-recorded competition rule: In each round your team acts as Reporter, Opponent, Reviewer, or (in four-team sections) Observer, and roles rotate every round until every team has held every role.",
    "Source-recorded competition rule: The Captain nominates which single team member serves as Reporter, Opponent, or Reviewer for a round, and only that person speaks for the team.",
    "Source-recorded competition rule: Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Source-recorded competition rule: Once you begin an active role you may not communicate with your team until the round ends, except during a time-out.",
    "Source-recorded competition rule: A Captain may call one 60-second time-out per stage, only before the jury's questions and only between parts of the round or during the reporter-opponent discussion.",
    "Source-recorded competition rule: Take each of Reporter, Opponent, and Reviewer at most once during the semi-finals; extra roles are scored at half technical points.",
    "Source-recorded competition rule: Your team may reject two challenges per round for free; from the third rejection onward the round's Reporter points are multiplied by 0.8, 0.7, 0.6, 0.5, or 0.4.",
    "Source-recorded competition rule: In the general discussion each active team may ask exactly one question before observers, jury, and audience may ask.",
    "Cite reasoning clearly; be ready for opponent and jury questioning.",
    "In each round your team acts as Reporter, Opponent, Reviewer, or (in four-team sections) Observer, and roles rotate every round until every team has held every role.",
    "The Captain nominates which single team member serves as Reporter, Opponent, or Reviewer for a round, and only that person speaks for the team.",
    "Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Once you begin an active role you may not communicate with your team until the round ends, except during a time-out.",
    "A Captain may call one 60-second time-out per stage, only before the jury's questions and only between parts of the round or during the reporter-opponent discussion.",
    "Take each of Reporter, Opponent, and Reviewer at most once during the semi-finals; extra roles are scored at half technical points.",
    "Your team may reject two challenges per round for free; from the third rejection onward the round's Reporter points are multiplied by 0.8, 0.7, 0.6, 0.5, or 0.4.",
    "In the general discussion each active team may ask exactly one question before observers, jury, and audience may ask.",
    "You must behave like a human teammate under official contest rules."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: Cite reasoning clearly; be ready for opponent and jury questioning.",
    "Source-recorded competition rule: Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning.",
    "Cite reasoning clearly; be ready for opponent and jury questioning.",
    "Use no electronic devices except calculators and one laptop or tablet per team for slides; using the Internet is strictly prohibited and costs 30% of the round's technical points after a warning."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit a written chemistry report plus a concise opposition-preparation and jury-question outline. This is a text proxy for the live multi-team fight.",
    "Official deliverable: oral report and opposition.",
    "Source-recorded competition rule: Prepare chemistry tournament reports/arguments for presentation and opposition.",
    "Source-recorded competition rule: Official problems page publishes annual problem sets for a chemistry tournament (oral fight / reporting style historically).",
    "Source-recorded competition rule: Keep to the round clock: report 8 minutes, opposition 5, reporter's response 4, academic discussion 5, review 3, jury questions 5, general discussion 5; all monologues are strictly monologues.",
    "Prepare chemistry tournament reports/arguments for presentation and opposition.",
    "Official problems page publishes annual problem sets for a chemistry tournament (oral fight / reporting style historically).",
    "Keep to the round clock: report 8 minutes, opposition 5, reporter's response 4, academic discussion 5, review 3, jury questions 5, general discussion 5; all monologues are strictly monologues.",
    "Do not look up answer keys or hidden solutions.",
    "Submit the written memorial/case analysis and a concise oral outline."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per artifact in rubric mode, but the repository evaluator is deferred; do not invent a completed score."
  ],
  "runtime_limitations": [
    "Runtime limitation: The event is a live oral debate with jury scorecards; monologue timing, oratory, and slide quality carry real marks that text-only simulation cannot reproduce.",
    "Runtime limitation: Grades are given by at least five human jurors with the highest and lowest discarded, which no gold-answer or single-judge proxy reproduces.",
    "Runtime limitation: Cross-team dynamics (challenge selection, strategic refusals, section grouping by rank) require three or four competing teams running simultaneously."
  ]
}
```
