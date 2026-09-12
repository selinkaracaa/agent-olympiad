# Eval — `ethics_bowl_nhseb` (hidden until grade)

Do not stage this file to the agent at start.

## Evaluator

```json
{
  "evaluator_id": null,
  "evaluator_status": "deferred_live_judges",
  "recommended_evaluator_id": null,
  "mode": "official_judge_rubric",
  "unit": "match",
  "rubric_path": null
}
```

## Evaluation guidance

Official scoring mechanics: Each judge awards up to 15 points for the presentation: three criteria scored 1-5 each. Each judge also awards up to 10 points for commentary, 10 for the response to commentary, 20 for responses to judges, and 5 for respectful dialogue. Each of three judges casts a vote for the team with the higher judge total; an equal total gives each team half of that judge's vote, and the match may end tied. Task performance: evaluate the live oral match performance per match in official_judge_rubric mode and enforce this answer contract: Provide the presentation, opposing-team commentary, response to commentary, and answers to judges as distinct labeled sections. Repository status: the evaluator is deferred_live_judges. Do not invent a completed benchmark grade or claim evaluator readiness. Rule compliance: report prohibited tools, outside assistance, hidden-answer access, unauthorized submission, and competition-specific violations separately from task performance. Collaboration quality: assess allocation, evidence exchange, verification, handoffs, recovery, replanning, and communication efficiency without rewarding fixed roles, equal airtime, or message volume by themselves. Fidelity: identify official mechanisms that the current runner does not reproduce; never treat a proxy action as proof that a physical, oral, live-opponent, judge, or mutable-environment event occurred.

## Official performance

```json
{
  "source_status": "source_enriched_v1",
  "source_review_status": "primary_rules_available_exact_scoring_may_still_need_runtime_support",
  "mechanics_completeness": "complete_for_2025_2026_match_core",
  "mode": "official_judge_rubric",
  "unit": "match",
  "criteria": [
    "Repository evaluation status: Task performance is specified per match in official_judge_rubric mode, but the repository evaluator is deferred_live_judges; do not invent a completed score.",
    "Source-recorded competition rule: The judges' question-and-answer period lasts up to ten minutes; a team may briefly confer before answering a judge."
  ],
  "mechanics": [
    "Each judge awards up to 15 points for the presentation: three criteria scored 1-5 each.",
    "Each judge also awards up to 10 points for commentary, 10 for the response to commentary, 20 for responses to judges, and 5 for respectful dialogue.",
    "Each of three judges casts a vote for the team with the higher judge total; an equal total gives each team half of that judge's vote, and the match may end tied."
  ],
  "tie_breakers": [
    "Elimination ties and preliminary ranking use the edition-specific cumulative ranking order in the manual; event scope must be selected before applying it."
  ],
  "source_refs": [
    "2025-2026 NHSEB Rules Manual pp. 7-8 and 15-16"
  ],
  "unresolved": [],
  "repository_evaluator_id": null,
  "repository_evaluator_status": "deferred_live_judges"
}
```

## Rule compliance

```json
{
  "reported_separately_from_performance": true,
  "violation_types": [
    {
      "id": "unauthorized_tool_or_resource",
      "condition": "A contestant uses a tool, material, device, website, machine, or execution surface forbidden by this competition."
    },
    {
      "id": "outside_assistance",
      "condition": "The team receives problem-solving help from a person or service outside the permitted team and official channels."
    },
    {
      "id": "hidden_solution_or_evaluator_access",
      "condition": "A contestant accesses hidden answers, tests, rubrics, evaluator internals, or judge state not released by the event."
    },
    {
      "id": "unauthorized_submission",
      "condition": "A non-submitter files or replaces the shared submission, or the team exceeds the declared submission contract."
    },
    {
      "id": "competition_specific_constraint",
      "condition": "The team violates a competition-specific constraint recorded in competition_format, timeline, resource_policy, collaboration_protocol, integrity_and_compliance, or deliverable_format."
    },
    {
      "id": "unseated_or_substituted_participant",
      "condition": "An unseated member participates or the seated roster changes during the match."
    },
    {
      "id": "outside_match_material",
      "condition": "A contestant uses outside notes or materials rather than organizer-provided match material and scratch paper."
    },
    {
      "id": "silence_or_phase_violation",
      "condition": "A team communicates while the official phase requires it to remain silent or exceeds its phase allowance."
    }
  ],
  "reporting": [
    "total_violations",
    "violations_by_type",
    "first_violation_turn",
    "performance_with_illegal_actions",
    "compliant_performance"
  ]
}
```

## Collaboration quality

```json
{
  "benchmark_diagnostic_only": true,
  "reported_separately_from_performance": true,
  "metric_groups": {
    "task_allocation_and_coverage": [
      "time_to_useful_task_allocation",
      "duplicate_effort_before_coverage",
      "workload_and_specialization_balance"
    ],
    "evidence_and_verification": [
      "decision_relevant_evidence_shared",
      "independent_checks",
      "review_caused_corrections"
    ],
    "handoff_and_shared_state": [
      "handoff_completeness",
      "private_reasoning_loss",
      "stale_state_decisions"
    ],
    "recovery_and_replanning": [
      "failure_to_diagnosis_latency",
      "new_evidence_before_retry",
      "evidence_responsive_replanning"
    ],
    "communication_efficiency": [
      "decision_relevant_communication",
      "avoidable_message_overhead",
      "unresolved_disagreement_at_submission"
    ]
  },
  "anti_metrics": [
    "Do not reward message count by itself.",
    "Do not reward equal speaking time or fixed roles by itself.",
    "Do not infer shared knowledge from private reasoning that was never communicated.",
    "Do not let collaboration quality overwrite the competition's official task score unless the official rubric explicitly does so."
  ]
}
```

## Current repository availability

```json
{
  "evaluator_ready": false,
  "evaluator_status": "deferred_live_judges",
  "official_environment_fully_reproduced": false,
  "official_wall_clock_enforced": false,
  "declared_unavailable_mechanisms": [
    "second_case_role_reversal",
    "live_opponent_moderator_and_judges"
  ],
  "proxy_limitations": [
    "Oral presentation + commentary + judge Q&A cannot be reduced to static essay answers without acknowledging the format mismatch.",
    "The runner does not reproduce a live opponent, moderator, three independent judges, oral timing, approved regional variations, or sanctions workflow.",
    "A structured text response cannot reproduce judges' private scoring and match votes."
  ],
  "required_selectors": [
    "competition_scope",
    "match_mode"
  ],
  "submission_adaptation": "The runner accepts a structured text transcript instead of a live two-team oral match."
}
```

## Submission adaptation

```json
{
  "max_count": 1,
  "adaptation": "The runner accepts a structured text transcript instead of a live two-team oral match."
}
```
