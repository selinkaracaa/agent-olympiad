# Eval — `odyssey_of_the_mind` (hidden until grade)

Do not stage this file to the agent at start.

## Evaluator

```json
{
  "evaluator_id": null,
  "evaluator_status": "deferred",
  "recommended_evaluator_id": null,
  "mode": "rubric",
  "unit": "artifact",
  "rubric_path": null
}
```

## Evaluation guidance

Task performance: evaluate the long term performance per artifact in rubric mode and enforce this answer contract: Submit the complete team deliverable requested by the problem statement. Repository status: the evaluator is deferred. Do not invent a completed benchmark grade or claim evaluator readiness. Rule compliance: report prohibited tools, outside assistance, hidden-answer access, unauthorized submission, and competition-specific violations separately from task performance. Collaboration quality: assess allocation, evidence exchange, verification, handoffs, recovery, replanning, and communication efficiency without rewarding fixed roles, equal airtime, or message volume by themselves. Fidelity: identify official mechanisms that the current runner does not reproduce; never treat a proxy action as proof that a physical, oral, live-opponent, judge, or mutable-environment event occurred.

## Official performance

```json
{
  "source_status": "hand_written_fallback_v1",
  "source_review_status": "material_official_fields_remain_unverified",
  "mechanics_completeness": "not_fully_encoded",
  "mode": "rubric",
  "unit": "artifact",
  "criteria": [
    "Repository evaluation status: Task performance is specified per artifact in rubric mode, but the repository evaluator is deferred; do not invent a completed score."
  ],
  "mechanics": [],
  "tie_breakers": [],
  "source_refs": [],
  "unresolved": [],
  "repository_evaluator_id": null,
  "repository_evaluator_status": "deferred"
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
  "evaluator_status": "deferred",
  "official_environment_fully_reproduced": false,
  "official_wall_clock_enforced": false,
  "declared_unavailable_mechanisms": [
    "physical_performance_environment",
    "outside_assistance_provenance"
  ],
  "proxy_limitations": [
    "Physical props, vehicles, structures, and live Spontaneous cannot be PDF-synopses-evaluated as equivalent.",
    "Outside-assistance edge cases need the full Program Guide sections."
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
