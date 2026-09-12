# Method — `ieo_business_case`

How this benchmark's agents are asked to work. Projected from `data/rules/ieo_business_case/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Collaborate only within the team under contest rules.
- Permitted: internet access, calculators and running code. Paper and pencil are always available.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Keep sourced evidence, analysis, recommendations, and presentation claims distinct, then reconcile them into one internally consistent artifact.
- Do not cite a source, experiment, market action, or judge interaction unless it was actually available and observed in the task environment.
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
    "team_message_budget": 12,
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
    "Competition model: The team researches, authors, and defends a judged artifact.",
    "The source-recorded active team may have 3 to 5 members; the runner default is 5.",
    "Source-recorded competition rule: Contrast: Economics/Finance individual exams ban smartphones/electronics; permitted instruments listed ≤1 month ahead (not the Business Case tools regime).",
    "Contrast: Economics/Finance individual exams ban smartphones/electronics; permitted instruments listed ≤1 month ahead (not the Business Case tools regime)."
  ],
  "timeline": [
    "Source-recorded timing: The regulations establish preparation and presentation days but not one exact continuous 1,440-minute official clock.",
    "Source-recorded competition rule: Do not modify the submission after the lock/deadline.",
    "Source-recorded competition rule: Business Case lasts two days: preparation day + presentation day; presentations must be English slide-supported oral talks.",
    "Source-recorded competition rule: All teams submit slides by Steering Committee deadline before Opening Ceremony; no slide changes afterward.",
    "Source-recorded competition rule: Business Case contributes 50 final points (raw then Z-normalized); group stage then Finals for group winners; criterion scores use median of judges.",
    "Do not modify the submission after the lock/deadline.",
    "Business Case lasts two days: preparation day + presentation day; presentations must be English slide-supported oral talks.",
    "All teams submit slides by Steering Committee deadline before Opening Ceremony; no slide changes afterward.",
    "Business Case contributes 50 final points (raw then Z-normalized); group stage then Finals for group winners; criterion scores use median of judges.",
    "Preparation and presentation span two days.",
    "Slides must be submitted by the Steering Committee deadline and cannot be changed afterward."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Permitted: internet access, calculators and running code. Paper and pencil are always available.",
    "Source-recorded competition rule: Online and offline research materials and ordinary software are allowed.",
    "Online and offline research materials and ordinary software are allowed.",
    "Do not claim tools, internet, or materials that the rule card forbids.",
    "Online and offline research materials and ordinary software are allowed during preparation.",
    "Contacting anyone outside the team for help is prohibited."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: No contact with anyone outside the team during the case window.",
    "Source-recorded competition rule: Team size: ≤5 contestants (+1–2 leaders).",
    "Source-recorded competition rule: Business Case is a team competition; communication only with IEO officials and teammates (no outsiders).",
    "No contact with anyone outside the team during the case window.",
    "Team size: ≤5 contestants (+1–2 leaders).",
    "Business Case is a team competition; communication only with IEO officials and teammates (no outsiders).",
    "You must behave like a human teammate under official contest rules."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: No contact with anyone outside the team during the case window.",
    "Source-recorded competition rule: During preparation: any online and offline materials allowed; contacting other people for help is prohibited.",
    "No contact with anyone outside the team during the case window.",
    "During preparation: any online and offline materials allowed; contacting other people for help is prohibited.",
    "Use evidence responsibly and do not obtain hidden solutions or outside authorship."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit a structured report or slide outline covering analysis, recommendation, and evidence.",
    "Official deliverable: slide deck.",
    "Benchmark adaptation: Official entries are slide files; the runner submits the deck as structured text.",
    "Source-recorded competition rule: Deliver a slide deck / strategic report suitable for oral presentation.",
    "Source-recorded competition rule: Do not modify the submission after the lock/deadline.",
    "Source-recorded competition rule: Business Case lasts two days: preparation day + presentation day; presentations must be English slide-supported oral talks.",
    "Source-recorded competition rule: All teams submit slides by Steering Committee deadline before Opening Ceremony; no slide changes afterward.",
    "Deliver a slide deck / strategic report suitable for oral presentation.",
    "Do not modify the submission after the lock/deadline.",
    "Business Case lasts two days: preparation day + presentation day; presentations must be English slide-supported oral talks.",
    "All teams submit slides by Steering Committee deadline before Opening Ceremony; no slide changes afterward.",
    "Do not look up answer keys or hidden solutions.",
    "Deliver an English, slide-supported oral business-case presentation."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is evaluated per artifact in rubric mode by slide_deck_v1; repository evaluator status is ready.",
    "Source-recorded competition rule: Business Case contributes 50 final points (raw then Z-normalized); group stage then Finals for group winners; criterion scores use median of judges.",
    "Business Case contributes 50 final points (raw then Z-normalized); group stage then Finals for group winners; criterion scores use median of judges.",
    "Business Case contributes 50 final points; criterion scores use the median of judges."
  ],
  "runtime_limitations": [
    "Runtime limitation: Oral Q&A with live judge panels and slide-lock social dynamics are weak under text-only multi-agent simulation.",
    "Runtime limitation: Case partner / host-specific scoring guide is not universal across years."
  ]
}
```
