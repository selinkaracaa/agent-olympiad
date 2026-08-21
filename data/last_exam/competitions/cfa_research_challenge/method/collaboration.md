# Method — `cfa_research_challenge`

How this benchmark's agents are asked to work. Projected from `data/rules/cfa_research_challenge/collaboration.json`.

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
  "turn_budget_basis": "official clock n/a turns vs floor 13 (4 teammates x 2 turns + 1 answer parts + 4 for synthesis)"
}
```

## Rule sections

```json
{
  "competition_format": [
    "Competition model: The team researches, authors, and defends a judged artifact.",
    "The source-recorded active team may have 3 to 5 members; the runner default is 4.",
    "Source-recorded competition rule: Use only publicly available information.",
    "Source-recorded competition rule: Support recommendations with evidence and valuation reasoning.",
    "Use only publicly available information.",
    "Support recommendations with evidence and valuation reasoning."
  ],
  "timeline": [
    "Benchmark adaptation: no official numeric duration is encoded in the available primary-source record; simulation.max_turns is only a runner safety budget.",
    "Source-recorded competition rule: May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
    "May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
    "Track local kickoff, written-report, and presentation deadlines.",
    "Faculty and mentor assistance is subject to timed caps."
  ],
  "resource_policy": [
    "Source-recorded resource policy: Permitted: internet access, calculators and running code. Paper and pencil are always available.",
    "Do not claim tools, internet, or materials that the rule card forbids.",
    "Research must use publicly available information only.",
    "AI use requires responsible disclosure and may not replace the team’s own analysis."
  ],
  "collaboration_protocol": [
    "Source-recorded collaboration rule: Collaborate only within the team under contest rules.",
    "Source-recorded competition rule: Team: 3–5 students at local kickoff; no alternates; undergrad/grad mix allowed.",
    "Source-recorded competition rule: Only team members may research the subject company; publicly available information only.",
    "Team: 3–5 students at local kickoff; no alternates; undergrad/grad mix allowed.",
    "Only team members may research the subject company; publicly available information only.",
    "You must behave like a human teammate under official contest rules."
  ],
  "integrity_and_compliance": [
    "Benchmark safety rule: do not use hidden solutions, evaluator internals, unauthorized outside assistance, or resources forbidden by this competition.",
    "Source-recorded competition rule: Advisor/mentor guidance is limited; outsiders must not write the report.",
    "Source-recorded competition rule: May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
    "Source-recorded competition rule: AI allowed only with reflective/responsible disclosure (Appendix B); misrepresenting AI output as own analysis prohibited.",
    "Source-recorded competition rule: Plagiarism ban; cite sources; IP/copyright obligations on third-party materials.",
    "Advisor/mentor guidance is limited; outsiders must not write the report.",
    "May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
    "AI allowed only with reflective/responsible disclosure (Appendix B); misrepresenting AI output as own analysis prohibited.",
    "Plagiarism ban; cite sources; IP/copyright obligations on third-party materials.",
    "Only team members may research the company; outsiders may advise only within official limits.",
    "Cite sources, avoid plagiarism, and respect third-party copyright."
  ],
  "deliverable_format": [
    "Runner answer contract: Submit a structured report or slide outline covering analysis, recommendation, and evidence.",
    "Official deliverable: research report and deck.",
    "Benchmark adaptation: Official entries are a written report plus a deck; the runner submits both as text.",
    "Source-recorded competition rule: Produce an equity research report / presentation artifact.",
    "Source-recorded competition rule: Advisor/mentor guidance is limited; outsiders must not write the report.",
    "Source-recorded competition rule: May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
    "Source-recorded competition rule: Deliverables: written equity research report + oral presentation to judges; local scoring often 50% written / 50% presentation.",
    "Produce an equity research report / presentation artifact.",
    "Advisor/mentor guidance is limited; outsiders must not write the report.",
    "May use faculty advisor + industry mentor within timed caps (faculty ≤10h advisory before written report; mentor time capped in Rule 3.4); may not enlist other professionals to do the analysis.",
    "Deliverables: written equity research report + oral presentation to judges; local scoring often 50% written / 50% presentation.",
    "Do not look up answer keys or hidden solutions.",
    "Produce a written equity-research report and an oral presentation to judges."
  ],
  "evaluation_criteria": [
    "Repository evaluation status: Task performance is specified per artifact in rubric mode, but the repository evaluator is unassigned; do not invent a completed score.",
    "Local scoring commonly balances the written report and presentation equally.",
    "Recommendations need evidence and defensible valuation reasoning."
  ],
  "runtime_limitations": [
    "Runtime limitation: Paid terminals (Bloomberg etc.) and company info sessions are not freely replicable.",
    "Runtime limitation: Mentor hour caps and oral defense Q&A are hard to simulate honestly."
  ]
}
```
