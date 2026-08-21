# Method — `ccdc`

How this benchmark's agents are asked to work. Projected from `data/rules/ccdc/collaboration.json`.

## Agent constraints

- Apply this competition's own roster, timing, tool, collaboration, submission, and scoring rules; do not import rules from another contest.
- Collaborate only within the team under contest rules.
- Banned during the contest: internet access and calculators. Conditional: running code requires the mutable network environment. Paper and pencil are always available. Work only from the materials provided with the problem.
- Treat private reasoning and notes as unknown to teammates until you communicate the decision-relevant content.
- Do not access hidden solutions, answer keys, evaluator internals, or unauthorized outside problem-solving help.
- Track services, incidents, injects, and authorized changes separately; do not claim network state, red-team activity, or service availability that the runner does not expose.
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
  "max_turns": 24,
  "scheduler": "src_collaboration_draft",
  "turn_budget_basis": "official clock n/a turns vs floor 21 (8 teammates x 2 turns + 1 answer parts + 4 for synthesis)"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The task represents a live cyber-defense event through a partial environment.",
    "Mixed or unresolved rulesets: the runner permits 8 to 8 active agents and defaults to 8.",
    "Live injects and full range VMs are not fully available; mark proxy limits."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Banned during the contest: internet access and calculators. Conditional: running code requires the mutable network environment. Paper and pencil are always available. Work only from the materials provided with the problem.",
    "Source-recorded competition rule: Live cyber-defense competition: teams operate and defend networked systems under injects; not a paper contest.",
    "Source-recorded competition rule: Use only Internet resources that are free and available to every team; no fee-gated or membership-gated content, no private staging areas, FTP sites, email accounts, network storage, or shared drives, and no Google Docs or Drive unless competition officials provide it.",
    "Source-recorded competition rule: Printed reference materials such as books, magazines, and checklists are permitted; personal computers, laptops, tablets, phones, wireless devices, and removable or electronic media are not, unless pre-authorized.",
    "Source-recorded competition rule: Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
    "Live cyber-defense competition: teams operate and defend networked systems under injects; not a paper contest.",
    "Use only Internet resources that are free and available to every team; no fee-gated or membership-gated content, no private staging areas, FTP sites, email accounts, network storage, or shared drives, and no Google Docs or Drive unless competition officials provide it.",
    "Printed reference materials such as books, magazines, and checklists are permitted; personal computers, laptops, tablets, phones, wireless devices, and removable or electronic media are not, unless pre-authorized.",
    "Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
    "Do not claim tools, internet, or materials that the rule card forbids.",
    "Banned during the contest: internet access, calculators and running code. Paper and pencil are always available. Work only from the materials provided with the problem."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: Your institution submits a roster of up to 12 competitors, and the competition team is at most 8 of them, of whom at most 2 may be graduate students.",
    "Source-recorded competition rule: Designate a Team Captain as the liaison to the White Team, and keep a captain or identified liaison in the competition space at all times during competition hours.",
    "Source-recorded competition rule: Compete with no outside assistance from any non-team member, including your own faculty representative, from the start of the event to the end, overnight hours included.",
    "Source-recorded competition rule: Use only Internet resources that are free and available to every team; no fee-gated or membership-gated content, no private staging areas, FTP sites, email accounts, network storage, or shared drives, and no Google Docs or Drive unless competition officials provide it.",
    "Source-recorded competition rule: You may use team-written scripts and tools only if they were published on a public, non-university site at least 3 months earlier, declared and frozen with officials, and approved in advance.",
    "Source-recorded competition rule: Team-written tools must not reach resources outside the competition environment beyond simple DNS lookups, and must not deliberately break expected system functionality.",
    "Source-recorded competition rule: Examine only your own systems; any offensive activity against a system outside your assigned network, including another team's, is immediate disqualification.",
    "Source-recorded competition rule: Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
    "Source-recorded competition rule: Do not migrate or containerize a scored service unless an inject or local rule allows it, and accept that any defensive action which breaks the scoring engine is your team's own loss.",
    "Source-recorded competition rule: You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
    "Source-recorded competition rule: Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.",
    "Your institution submits a roster of up to 12 competitors, and the competition team is at most 8 of them, of whom at most 2 may be graduate students.",
    "Designate a Team Captain as the liaison to the White Team, and keep a captain or identified liaison in the competition space at all times during competition hours.",
    "Compete with no outside assistance from any non-team member, including your own faculty representative, from the start of the event to the end, overnight hours included.",
    "Use only Internet resources that are free and available to every team; no fee-gated or membership-gated content, no private staging areas, FTP sites, email accounts, network storage, or shared drives, and no Google Docs or Drive unless competition officials provide it.",
    "You may use team-written scripts and tools only if they were published on a public, non-university site at least 3 months earlier, declared and frozen with officials, and approved in advance.",
    "Team-written tools must not reach resources outside the competition environment beyond simple DNS lookups, and must not deliberately break expected system functionality.",
    "Examine only your own systems; any offensive activity against a system outside your assigned network, including another team's, is immediate disqualification.",
    "Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
    "Do not migrate or containerize a scored service unless an inject or local rule allows it, and accept that any defensive action which breaks the scoring engine is your team's own loss.",
    "You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
    "Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.",
    "You must behave like a human teammate under official contest rules.",
    "Cyber defense scenario brief / team packet only in this dataset.",
    "Benchmark materials are Team Packets / Wildcard scenario briefs only — live VMs/injects excluded by collection strategy."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: Do not attack systems outside the authorized scenario environment.",
    "Source-recorded competition rule: Compete with no outside assistance from any non-team member, including your own faculty representative, from the start of the event to the end, overnight hours included.",
    "Source-recorded competition rule: Team-written tools must not reach resources outside the competition environment beyond simple DNS lookups, and must not deliberately break expected system functionality.",
    "Source-recorded competition rule: Examine only your own systems; any offensive activity against a system outside your assigned network, including another team's, is immediate disqualification.",
    "Source-recorded competition rule: Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
    "Source-recorded competition rule: You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
    "Source-recorded competition rule: Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.",
    "Do not attack systems outside the authorized scenario environment.",
    "Compete with no outside assistance from any non-team member, including your own faculty representative, from the start of the event to the end, overnight hours included.",
    "Team-written tools must not reach resources outside the competition environment beyond simple DNS lookups, and must not deliberately break expected system functionality.",
    "Examine only your own systems; any offensive activity against a system outside your assigned network, including another team's, is immediate disqualification.",
    "Grant Operations and White Team members access to your systems immediately when they ask, and do not modify hardware, open equipment cases, or connect unauthorized devices.",
    "You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
    "Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit the team's final answers in numbered order, using exact values when required.",
    "Official deliverable: defended services and reports.",
    "Source-recorded competition rule: Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.",
    "Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.",
    "Do not look up answer keys or hidden solutions."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per problem_or_question in gold_or_judge mode, but the repository evaluator is deferred; do not invent a completed score.",
    "Source-recorded competition rule: You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
    "Source-recorded competition rule: Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing.",
    "You gain points for keeping required services up, preventing unauthorized access, and completing business injects, and lose them for SLA violations, using recovery services, and successful Red Team penetrations; no running score is shown during play.",
    "Submit written incident reports for Red Team activity you detect — a thorough report with source and destination addresses, timeline, impact, and remediation can reduce that incident's penalty, while vague ones earn nothing."
  ],
  "runtime_limitations": [
    "Runtime limitation: The contest is a live multi-day defense of real infrastructure against an active human Red Team; no static text environment reproduces adversarial pressure or service uptime scoring.",
    "Runtime limitation: Injects arrive on an unannounced schedule from an Orange/White Team simulating business customers.",
    "Runtime limitation: The three-month public-publication requirement for team tooling is an out-of-band preparation constraint that cannot be enforced inside a run."
  ]
}
```
