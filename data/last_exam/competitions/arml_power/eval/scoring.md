# Eval — `arml_power` (hidden until grade)

Do not stage this file to the agent at start.

## Evaluator

```json
{
  "evaluator_id": "rubric_llm_v1",
  "evaluator_status": "ready",
  "recommended_evaluator_id": null,
  "mode": "gold",
  "unit": "problem_or_question",
  "rubric_path": "data/rubrics/team_power_proof_40_v1.json"
}
```

## Evaluation guidance

Report packet quality, rule compliance, and collaboration separately. Do not claim a complete current Power Contest administrivia score: the Rules page is Under Construction. Where national Power constraints are the only published Power rules, treat the work as a 50-point one-packet proof with lowest-score extras. Score justification depth; do not accept bare answers as a complete packet. Treat invented clocks, rosters, and aid exceptions as compliance failures. Collaboration evidence should cover part allocation, proof review, and one-packet synthesis. Do not reward fixed roles or message volume.

## Official performance

```json
{
  "track_identity": "mixed_national_power_rules_vs_standalone_power_contest",
  "standalone_power_contest_scoring": "not_established_rules_page_under_construction",
  "national_power_points_possible_if_applied": 50,
  "packets_allowed_if_national_rule_applied": 1,
  "extra_packet_rule_if_national_rule_applied": "all_packets_scored_lowest_kept",
  "computational_aid_exceptions": "none_published_default_deny",
  "official_minutes": null,
  "correctness_alone_insufficient": true,
  "must_not_invent": [
    "sixty_minute_clock",
    "official_standalone_roster",
    "computational_aid_exception",
    "complete_administrivia_packet"
  ],
  "must_report": [
    "justification_completeness",
    "extra_packet_count",
    "invented_administrivia_claims"
  ]
}
```

## Rule compliance

```json
{
  "reported_separately_from_performance": true,
  "violation_types": [
    {
      "id": "invented_clock_roster_or_aid_exception",
      "condition": "The team treats a 60-minute clock, a published standalone roster, or a computational-aid exception as official."
    },
    {
      "id": "claiming_complete_power_contest_administrivia",
      "condition": "The team claims to be following a complete current Power Contest administrivia packet that this card does not encode."
    },
    {
      "id": "calculator_or_electronic_device",
      "condition": "A contestant uses a calculator, phone, computer, or other electronic device."
    },
    {
      "id": "multiple_solution_packets",
      "condition": "The team files more than one solution packet."
    },
    {
      "id": "missing_required_justification",
      "condition": "The packet gives bare answers where the verbs require work or proof."
    },
    {
      "id": "outside_assistance",
      "condition": "The team receives problem-solving help from anyone outside the team."
    },
    {
      "id": "hidden_solution",
      "condition": "A contestant accesses hidden solutions, rubrics, or evaluator internals."
    }
  ],
  "reporting": [
    "total_violations",
    "violations_by_type",
    "first_violation_turn",
    "sanctions_applied",
    "performance_with_illegal_actions",
    "compliant_performance"
  ]
}
```

## Collaboration quality

```json
{
  "official_arml_scoring": false,
  "reported_separately_from_performance": true,
  "metric_groups": {
    "part_allocation_and_coverage": [
      "time_to_useful_part_allocation",
      "duplicate_proof_effort",
      "abandoned_part_recovery"
    ],
    "proof_development": [
      "justification_depth_matched_to_verb",
      "independent_proof_checks",
      "review_caused_corrections"
    ],
    "packet_synthesis": [
      "single_packet_consistency",
      "handoff_completeness",
      "private_reasoning_loss"
    ],
    "conflict_and_decision_quality": [
      "evidence_backed_proof_disagreements",
      "silent_overwrite_incidents",
      "decision_traceability"
    ],
    "communication_and_shared_mental_model": [
      "discovery_to_team_awareness_latency",
      "decision_relevant_communication",
      "unresolved_disagreement_at_submission"
    ]
  },
  "anti_metrics": [
    "Do not reward message count by itself.",
    "Do not reward a fixed scribe or equal speaking time by itself.",
    "Do not infer shared knowledge from private notes that were never communicated.",
    "Do not treat independent solo writeups as good Power collaboration.",
    "Do not treat a list of bare answers as a complete Power packet.",
    "Do not score invented Power Contest administrivia as official performance."
  ]
}
```

## Current repository availability

```json
{
  "evaluator_ready": true,
  "evaluator_status": "ready",
  "official_environment_fully_reproduced": false,
  "official_wall_clock_enforced": false,
  "official_minutes_encoded": false,
  "rubric_llm_proof_proxy": true,
  "standalone_power_contest_administrivia": false,
  "official_standalone_roster": false,
  "official_standalone_clock": false,
  "computational_aid_exception_published": false,
  "multiple_packet_lowest_score_enforced": false,
  "handwriting_fidelity": false,
  "role_immersion_unresolved_status_text": true,
  "limited_communication_overlay": true,
  "structured_deliberation_overlay": true,
  "submission_adaptation": null
}
```

## Submission adaptation

```json
{
  "max_count": 1
}
```
