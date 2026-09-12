# Method — `jessup`

How this benchmark's agents are asked to work. Projected from `data/rules/jessup/collaboration.json`.

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
    "The source-recorded active team may have 2 to 5 members; the runner default is 5.",
    "Source-recorded competition rule: Legal research on public sources and provided databases is allowed.",
    "Source-recorded competition rule: FAQ confirms max five contributors over the competition year.",
    "Legal research on public sources and provided databases is allowed.",
    "FAQ confirms max five contributors over the competition year."
  ],
  "timeline": [
    "Source-recorded timing: Multi-month memorial preparation plus oral rounds.",
    "Source-recorded competition rule: Memorials: Applicant + Respondent; hard submission deadline (disqualification if missing both by schedule time); formatting/content rules in Rule 5.",
    "Memorials: Applicant + Respondent; hard submission deadline (disqualification if missing both by schedule time); formatting/content rules in Rule 5.",
    "Multi-month memorial preparation plus oral rounds."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: calculators and running code. Permitted: internet access. Paper and pencil are always available.",
    "Do not claim tools, internet, or materials that the rule card forbids."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: No outside coaching that writes the memorial for the team.",
    "Source-recorded competition rule: Team: 2–5 Team Members; only Team Members may contribute substantive work product.",
    "Source-recorded competition rule: Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
    "Source-recorded competition rule: No other-team assistance (notes, memorials, practice moots against competitors, etc.).",
    "No outside coaching that writes the memorial for the team.",
    "Team: 2–5 Team Members; only Team Members may contribute substantive work product.",
    "Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
    "No other-team assistance (notes, memorials, practice moots against competitors, etc.).",
    "You must behave like a human teammate under official contest rules."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: No outside coaching that writes the memorial for the team.",
    "Source-recorded competition rule: Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
    "Source-recorded competition rule: No other-team assistance (notes, memorials, practice moots against competitors, etc.).",
    "No outside coaching that writes the memorial for the team.",
    "Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
    "No other-team assistance (notes, memorials, practice moots against competitors, etc.)."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit the written memorial/case analysis and a concise oral outline.",
    "Official deliverable: written memorial.",
    "Benchmark adaptation: Official memorials are filed as PDF; the runner submits the memorial text.",
    "Source-recorded competition rule: Prepare Applicant and Respondent written memorials plus oral outlines.",
    "Source-recorded competition rule: Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
    "Source-recorded competition rule: Memorials: Applicant + Respondent; hard submission deadline (disqualification if missing both by schedule time); formatting/content rules in Rule 5.",
    "Source-recorded competition rule: Season roughly Compromis in September → memorials ~January → oral Qualifying/International rounds.",
    "Prepare Applicant and Respondent written memorials plus oral outlines.",
    "Outside assistance tightly limited: research/write/edit of Memorials and oral arguments must be exclusive Team Member work; Advisors limited to general advice (research methods, writing/advocacy technique) not drafting arguments.",
    "Memorials: Applicant + Respondent; hard submission deadline (disqualification if missing both by schedule time); formatting/content rules in Rule 5.",
    "Season roughly Compromis in September → memorials ~January → oral Qualifying/International rounds.",
    "Do not look up answer keys or hidden solutions."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is evaluated per artifact in rubric mode by rubric_llm_v1; repository evaluator status is ready.",
    "Source-recorded competition rule: Arguments must withstand judge questioning.",
    "Arguments must withstand judge questioning."
  ],
  "runtime_limitations": [
    "Runtime limitation: Months-long research + proprietary legal databases (ILSA-provided) are not free-web equivalent.",
    "Runtime limitation: Oral courtroom advocacy and anonymity rules are out of scope for written-memorial-only agent evals.",
    "Runtime limitation: AI policy: not a blanket ban in the sections reviewed; still subordinate to exclusive Team Member work-product rule — do not invent a permission."
  ]
}
```
