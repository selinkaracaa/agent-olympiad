# Eval — `mystery_hunt` (hidden until grade)

Do not stage this file to the agent at start.

## Evaluator

```json
{
  "evaluator_id": null,
  "evaluator_status": "deferred_benchmark_metadata_missing",
  "recommended_evaluator_id": "gold_answer_v1",
  "mode": "gold",
  "unit": "problem_or_question",
  "rubric_path": null
}
```

## Evaluation guidance

Official scoring mechanics: A task-level answer is accepted only when it matches the current puzzle's answer mechanism; this is not equivalent to winning the full hunt. Unresolved official evaluation state: Full-hunt progression, hint costs, interactions, final runaround, and coin-finding depend on the annual hunt implementation. Task performance: evaluate the puzzle answer per problem_or_question in gold mode and enforce this answer contract: Submit the team's final answers in numbered order, using exact values when required. Repository status: the evaluator is deferred_benchmark_metadata_missing. Do not invent a completed benchmark grade or claim evaluator readiness. Rule compliance: report prohibited tools, outside assistance, hidden-answer access, unauthorized submission, and competition-specific violations separately from task performance. Collaboration quality: assess allocation, evidence exchange, verification, handoffs, recovery, replanning, and communication efficiency without rewarding fixed roles, equal airtime, or message volume by themselves. Fidelity: identify official mechanisms that the current runner does not reproduce; never treat a proxy action as proof that a physical, oral, live-opponent, judge, or mutable-environment event occurred.

## Official performance

```json
{
  "source_status": "source_enriched_v1",
  "source_review_status": "primary_rules_partial_or_variant_selector_required",
  "mechanics_completeness": "annual_rules_and_full_hunt_state_not_encoded",
  "mode": "gold",
  "unit": "problem_or_question",
  "criteria": [
    "Repository evaluation status: Task performance is specified per problem_or_question in gold mode, but the repository evaluator is deferred_benchmark_metadata_missing; do not invent a completed score.",
    "Source-recorded competition rule: Answers must be submitted in the canonical answer form accepted by the current hunt's answer mechanism.",
    "Source-recorded competition rule: Remote participation does not reproduce every in-person interaction, and the in-person runaround is required to win the 2026 hunt."
  ],
  "mechanics": [
    "A task-level answer is accepted only when it matches the current puzzle's answer mechanism; this is not equivalent to winning the full hunt."
  ],
  "tie_breakers": [],
  "source_refs": [
    "MIT Mystery Hunt 2026 FAQ and official archive"
  ],
  "unresolved": [
    "Full-hunt progression, hint costs, interactions, final runaround, and coin-finding depend on the annual hunt implementation."
  ],
  "repository_evaluator_id": null,
  "repository_evaluator_status": "deferred_benchmark_metadata_missing"
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
  "evaluator_status": "deferred_benchmark_metadata_missing",
  "official_environment_fully_reproduced": false,
  "official_wall_clock_enforced": false,
  "declared_unavailable_mechanisms": [
    "full_hunt_unlock_state",
    "hint_and_interaction_state",
    "runaround_and_coin_state"
  ],
  "proxy_limitations": [
    "Index team_size 12 is a modeling stub vs real 30–100+ teams.",
    "Physical runarounds, interactions, and meta structure are out of scope for isolated puzzle rows.",
    "Unrestricted web/tools make 'fair human comparison' poorly defined for LLM agents.",
    "The configured 8-12-agent range is a benchmark capacity choice, not an official roster limit.",
    "Question-level rows omit full-hunt unlocking, metas, hints, interactions, rate limits, runaround, and coin verification."
  ],
  "required_selectors": [],
  "submission_adaptation": null
}
```

## Submission adaptation

```json
{
  "max_count": 1
}
```
