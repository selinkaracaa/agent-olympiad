# Eval — `iiot` (hidden until grade)

Do not stage this file to the agent at start.

## Evaluator

```json
{
  "evaluator_id": "programming_judge",
  "evaluator_status": "deferred",
  "recommended_evaluator_id": null,
  "mode": "gold_or_judge",
  "unit": "problem_or_question",
  "rubric_path": null
}
```

## Evaluation guidance

Report performance, rule compliance, and collaboration quality separately. Official performance is the automatic evaluator's judgment of the team's programs, not a one-workstation ICPC penalty table: the 3 October 2024 regulations publish results after working time, allow a team-leader appeal to the International Scientific Committee, exclude guest teams from the official ranking, and let the General Assembly set gold, silver, and bronze cutoffs in about a 1:2:3 proportion with at least 50 percent of contestants receiving medals. Do not invent a minutes-plus-rejection formula that the regulations do not state. Treat eligibility, same-school composition, team-leader non-participation, and guest ranking as contestant conscience. Collaboration evidence should cover packet triage across at least seven problems when a packet is present, useful parallel work on two machine leases, handoff quality, peer review, conflict resolution with evidence, recovery after rejected runs, and idle-machine waste. Do not reward fixed driver or tester offices, equal keyboard time, exclusive problem ownership, or message volume by themselves. Do not treat four independent solo solves as good IIOT collaboration.

## Official performance

```json
{
  "ranking_order": [
    "automatic_evaluator_score_of_regular_teams",
    "guest_teams_excluded_from_official_ranking"
  ],
  "automatic_evaluator": true,
  "results_published_after_contest": true,
  "leader_may_appeal": true,
  "appeal_body": "international_scientific_committee",
  "official_ranking_includes_guests": false,
  "medal_ratio_gold_silver_bronze": "approximately_1:2:3",
  "minimum_medal_share_of_contestants": 0.5,
  "medal_cutoffs_set_by": "general_assembly",
  "participation_certificate_for_every_contestant": true,
  "time_penalty_formula_published": false,
  "correctness_alone_insufficient_for_official_rank_story": true,
  "must_report_even_when_accepted": [
    "problems_or_tests_solved_by_automatic_evaluator",
    "rejected_runs_if_observed",
    "guest_versus_regular_status",
    "whether_a_leader_appeal_was_attempted"
  ],
  "derived_reporting": [
    "accepted_runs_by_problem",
    "attempt_count_by_problem",
    "rejected_runs_by_verdict",
    "language_used",
    "dual_machine_idle_time",
    "clarifications_requested_and_received"
  ],
  "unresolved_official_mechanics": [
    "The regulations do not publish a per-problem partial-score table or an ICPC-style 20-minute rejection penalty."
  ]
}
```

## Rule compliance

```json
{
  "reported_separately_from_performance": true,
  "violation_types": [
    {
      "id": "ineligible_or_mixed_school_roster",
      "condition": "The team invents a substitute beyond the two official reserves, mixes schools where same-school composition is required, or fictionalizes age or enrollment so that a member would be ineligible."
    },
    {
      "id": "leader_or_outside_solving_help",
      "condition": "The team leader or any outsider provides contest-time algorithms, code, or debugging help."
    },
    {
      "id": "independent_remote_solves",
      "condition": "Contestants treat the contest as four independent remote solves instead of one two-machine team."
    },
    {
      "id": "third_machine_or_hidden_terminal",
      "condition": "The team uses a third computer, personal laptop, or hidden execution environment beyond the two organizer leases."
    },
    {
      "id": "multiple_owners_of_one_lease",
      "condition": "More than one contestant has machine-action permission on the same lease at the same time."
    },
    {
      "id": "non_owner_machine_action",
      "condition": "A non-owner edits, compiles, executes, locally tests, or submits on a leased machine."
    },
    {
      "id": "public_internet_or_external_llm",
      "condition": "A contestant uses the public Internet, search engines, or an external LLM rather than the contest platform only."
    },
    {
      "id": "usb_or_unapproved_software",
      "condition": "The team uses USB storage, unapproved software, or materials other than organizer machines and language documentation."
    },
    {
      "id": "phone_textbook_or_translator",
      "condition": "A contestant uses a phone, tablet, textbook, or translator."
    },
    {
      "id": "inter_team_communication",
      "condition": "The team communicates with another team."
    },
    {
      "id": "non_cpp_submission_under_2026_overlay",
      "condition": "The team submits a language other than C++ under the frozen 2026 overlay."
    },
    {
      "id": "clarification_bypass",
      "condition": "The team asks outsiders about statement defects instead of written questions to the host Scientific Committee."
    },
    {
      "id": "guest_treated_as_official_rank",
      "condition": "A guest team's result is reported as an official ranking position."
    },
    {
      "id": "invented_icpc_penalty",
      "condition": "Performance is scored with an invented minutes-plus-rejection penalty that the IIOT regulations do not state."
    },
    {
      "id": "hidden_test_access",
      "condition": "A contestant observes hidden tests or evaluator internals."
    }
  ],
  "reporting": [
    "total_violations",
    "violations_by_type",
    "first_violation_time",
    "sanctions_applied",
    "performance_with_illegal_actions",
    "compliant_performance"
  ]
}
```

## Collaboration quality

```json
{
  "official_iiot_scoring": false,
  "reported_separately_from_performance": true,
  "metric_groups": {
    "packet_discovery_and_allocation": [
      "time_to_first_packet_coverage",
      "problems_read_per_contestant",
      "duplicate_reading_before_packet_coverage",
      "difficulty_estimate_calibration",
      "problem_reassignment_rate"
    ],
    "dual_machine_coordination": [
      "lease_utilization",
      "avoidable_machine_idle_time",
      "same_lease_contention_incidents",
      "parallel_problem_progress_on_two_machines",
      "context_switch_overhead"
    ],
    "parallel_reasoning": [
      "useful_off_machine_time",
      "duplicate_algorithm_effort",
      "ready_work_inventory"
    ],
    "handoff_and_review": [
      "handoff_completeness",
      "handoff_repair_cost",
      "pre_submission_review_rate",
      "review_caused_corrections"
    ],
    "conflict_and_decision_quality": [
      "evidence_backed_algorithm_disagreements",
      "silent_overwrite_incidents",
      "decision_traceability"
    ],
    "failure_recovery": [
      "rejection_to_diagnosis_time",
      "repeated_submission_without_new_evidence",
      "debugging_escalation"
    ],
    "communication_and_shared_mental_model": [
      "discovery_to_team_awareness_latency",
      "machine_state_announced_before_handoff",
      "private_reasoning_loss",
      "multi_contributor_solves"
    ]
  },
  "anti_metrics": [
    "Do not reward message count by itself.",
    "Do not reward equal keyboard time on the two machines by itself.",
    "Do not reward a fixed driver, navigator, tester, and reference-reader split by itself.",
    "Do not punish adaptive specialization that does not create a machine bottleneck.",
    "Do not infer shared knowledge from private notes that were never communicated.",
    "Do not treat four independent high-quality solo solves as good IIOT collaboration.",
    "Do not treat an accepted program as full official success if guest status or invented penalty accounting is ignored."
  ]
}
```

## Current repository availability

```json
{
  "official_packet_scoring": false,
  "dual_machine_lease_enforcement": false,
  "programming_judge_ready": false,
  "per_problem_verdict_history": false,
  "written_scientific_committee_channel": false,
  "leader_appeal_state": false,
  "official_ranking_publication": false,
  "host_vm_and_usb_lock": false,
  "online_proctor_recording": false,
  "eligibility_and_guest_rank_state": false,
  "role_immersion_eligibility_text": true,
  "two_machine_capacity_documented": true,
  "cpp_overlay_documented": true,
  "medal_and_guest_ranking_contract_documented": true,
  "evaluator_ready": false,
  "evaluator_status": "deferred",
  "official_environment_fully_reproduced": false,
  "official_wall_clock_enforced": false
}
```

## Submission adaptation

```json
{
  "max_count": 1,
  "adaptation": "Official contests send source programs to an automatic evaluator, possibly more than once; this session still accepts a single final source text without live pending latency, dual-machine leases, or published ranking."
}
```
