# Eval — `wro` (hidden until grade)

Do not stage this file to the agent at start.

## Evaluator

```json
{
  "evaluator_id": null,
  "evaluator_status": "deferred_physical_game_and_selectors",
  "recommended_evaluator_id": null,
  "mode": "selected_game_score_then_time",
  "unit": "robot_attempt",
  "rubric_path": null
}
```

## Evaluation guidance

Official scoring mechanics: The judge scores the field state when the robot attempt ends and records elapsed time in full seconds. A disqualified attempt receives the worst possible score and 120 seconds. Exact points, number of ranked runs, and tie resolution come from the selected game and national tournament format; Appendix D examples are not binding rules. Unresolved official evaluation state: Age-group mission scoring, national tournament mode, number of runs, Q&A additions, and tie breakers are not selected. Task performance: evaluate the inspected robot program and scored field attempt per robot_attempt in selected_game_score_then_time mode and enforce this answer contract: Submit the program and a structured design/run analysis; label simulated or hypothetical behavior and do not report an unobserved physical score. Repository status: the evaluator is deferred_physical_game_and_selectors. Do not invent a completed benchmark grade or claim evaluator readiness. Rule compliance: report prohibited tools, outside assistance, hidden-answer access, unauthorized submission, and competition-specific violations separately from task performance. Collaboration quality: assess allocation, evidence exchange, verification, handoffs, recovery, replanning, and communication efficiency without rewarding fixed roles, equal airtime, or message volume by themselves. Fidelity: identify official mechanisms that the current runner does not reproduce; never treat a proxy action as proof that a physical, oral, live-opponent, judge, or mutable-environment event occurred.

## Official performance

```json
{
  "source_status": "source_enriched_v1",
  "source_review_status": "primary_rules_partial_or_variant_selector_required",
  "mechanics_completeness": "general_attempt_rules_only_game_scoring_unresolved",
  "mode": "selected_game_score_then_time",
  "unit": "robot_attempt",
  "criteria": [
    "Repository evaluation status: Task performance is specified per robot_attempt in selected_game_score_then_time mode, but the repository evaluator is deferred_physical_game_and_selectors; do not invent a completed score.",
    "Source-recorded competition rule: At the end of an attempt the judge scores the observed field state, records full seconds, and the team signs the score sheet; after sign-off no further complaint is allowed.",
    "Source-recorded competition rule: A disqualified attempt receives the worst possible score and the maximum time of 120 seconds."
  ],
  "mechanics": [
    "The judge scores the field state when the robot attempt ends and records elapsed time in full seconds.",
    "A disqualified attempt receives the worst possible score and 120 seconds.",
    "Exact points, number of ranked runs, and tie resolution come from the selected game and national tournament format; Appendix D examples are not binding rules."
  ],
  "tie_breakers": [],
  "source_refs": [
    "2026 RoboMission General Rules pp. 13-16; non-binding examples begin p. 19"
  ],
  "unresolved": [
    "Age-group mission scoring, national tournament mode, number of runs, Q&A additions, and tie breakers are not selected."
  ],
  "repository_evaluator_id": null,
  "repository_evaluator_status": "deferred_physical_game_and_selectors"
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
      "id": "coach_authorship",
      "condition": "A coach or other adult builds, codes, or programs the robot for the team."
    },
    {
      "id": "field_or_robot_touch",
      "condition": "A team member touches the robot or mission objects during the run outside an allowed condition."
    },
    {
      "id": "unselected_ruleset_claim",
      "condition": "A score or ranking is claimed without the selected game, national rules, and Q&A snapshot."
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
  "evaluator_status": "deferred_physical_game_and_selectors",
  "official_environment_fully_reproduced": false,
  "official_wall_clock_enforced": false,
  "declared_unavailable_mechanisms": [
    "robot_environment",
    "inspection_quarantine_and_field_state"
  ],
  "proxy_limitations": [
    "Physical robot construction, sensors, and table runs are outside software-agent fidelity.",
    "Always pair General Rules with the year’s Game PDF + Q&A.",
    "The runner has no physical robot, inspection, quarantine, randomized field, judge, score sheet, or national tournament state.",
    "The selected age-group game document, jurisdiction rules, and Q&A snapshot are absent, so exact mission score and ranking are deferred."
  ],
  "required_selectors": [
    "season",
    "category",
    "age_group",
    "jurisdiction",
    "game_document",
    "q_and_a_snapshot"
  ],
  "submission_adaptation": "The runner accepts program text and analysis but cannot accept or score a physical robot attempt."
}
```

## Submission adaptation

```json
{
  "max_count": 1,
  "adaptation": "The runner accepts program text and analysis but cannot accept or score a physical robot attempt."
}
```
