# Environment — `iiot`

## Roster

```json
{
  "active_min": 4,
  "active_default": 4,
  "active_max": 4,
  "roster_max": 6,
  "collaboration": "Four contestants collaborate throughout the contest while sharing two organizer-provided computers; the team leader coordinates but is not a contestant.",
  "range_basis": "source_record",
  "official_roster_note": "The official team is four contestants plus two reserves for replacement if needed. One team leader coordinates and registers the team and is not a contestant during the contest. Eligibility, same-school or same-institution/region composition, national qualification, visas, host lodging, and ceremonies are official identity and logistics rules included for role immersion and are not runtime-enforced state machines."
}
```

## Allowed tools

- query_rules
- execute_code

## Resources

```json
{
  "internet": "judge_only_or_forbidden",
  "calculator": "forbidden",
  "code_execution": "organizer_machines_only",
  "paper_pencil": "allowed",
  "provided_materials_only": true,
  "contest_machine_capacity": 2,
  "machine_lease_enforcement": "specified_only",
  "organizer_computers_and_software_only": true,
  "personal_mouse_keyboard": "allowed_if_host_scientific_committee_approves",
  "usb_ports": "disabled",
  "personal_electronic_devices": "forbidden",
  "textbooks_and_translators": "forbidden",
  "language_documentation": "organizer_provided_allowed",
  "external_llms_and_search_engines": "forbidden",
  "outside_communication": "forbidden",
  "other_teams_code_or_materials": "forbidden",
  "inter_team_communication": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "evaluated_edition": "international_final_regulations_2024_10_03_plus_2026_online_cpp_two_computer_overlay",
  "edition_duration_note": "The International Final lasts 4 hours; execution.official_minutes stays null because this card does not encode that duration as the runtime clock.",
  "exclusive_machine_lease": "two_specified_only",
  "shared_machine_count": 2,
  "multi_problem_packet": "unavailable",
  "official_packet_size_note": "The International Final involves solving at least seven problems; the exact count is an event parameter.",
  "problem_language": "English",
  "official_contest_communications_language": "English",
  "allowed_languages_regulations": [
    "C",
    "C++",
    "Pascal"
  ],
  "allowed_languages_evaluated_overlay": [
    "C++"
  ],
  "problems_independent": true,
  "clarification_channel": "written_questions_to_host_scientific_committee_initial_period_specified_not_enforced",
  "automatic_evaluator": "specified_deferred",
  "leader_appeal": "specified_not_enforced"
}
```

## Deliverable

```json
{
  "answer_format": "Submit source code or the required program output for the programming judge.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "algorithmic_programming"
  ],
  "official_deliverable": "source_code",
  "official_mime_types": [
    "text/x-c++src",
    "text/x-python"
  ]
}
```
