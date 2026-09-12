# Environment — `icpc`

## Roster

```json
{
  "active_min": 3,
  "active_default": 3,
  "active_max": 3,
  "collaboration": "Three contestants may collaborate with one another throughout the contest while sharing one workstation.",
  "coach_role": "administrative_contact_only_not_a_contestant",
  "coach_during_contest": "no_problem_solving_help",
  "co_location": "three_contestants_share_one_on_site_team_workstation",
  "official_roster_note": "The World Finals team is the same three contestants who qualified; reserves are not allowed. Eligibility, coach certification, visas, attendance, and host logistics are official contestant identity rules included for role immersion and are not runtime-enforced state machines. Season-specific regional eligibility lines (age, enrollment year, regional-season counts) must be read from the current Regional Rules and are not frozen as permanent dates in this card."
}
```

## Allowed tools

- query_rules
- execute_code

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "forbidden",
  "code_execution": "shared_workstation_only",
  "paper_pencil": "allowed",
  "unapproved_materials": "forbidden",
  "shared_workstation": true,
  "shared_workstation_count": 1,
  "extra_computers": "forbidden",
  "personal_electronic_devices": "forbidden",
  "root_access": "forbidden",
  "approved_printed_materials": "allowed",
  "team_reference_document": "up_to_25_single_sided_letter_or_a4_pages",
  "natural_language_dictionary": "one_unannotated_copy_per_contestant",
  "ide_internal_ai_tools": "disabled",
  "removable_storage": "forbidden",
  "external_llms_and_search_engines": "forbidden",
  "outside_communication": "forbidden",
  "other_teams_code_or_materials": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": 300,
  "multi_problem_packet": "unavailable",
  "official_packet_size_note": "Recent World Championships have posed ten or more problems; exact count is an event parameter.",
  "problem_language": "English",
  "official_contest_communications_language": "English",
  "contestant_to_official_interpreter": "allowed_team_identified",
  "allowed_languages": [
    "C",
    "C++",
    "Java",
    "Kotlin",
    "Python3"
  ],
  "program_io_model": "stdin_to_stdout",
  "problems_independent": true,
  "live_scoreboard": "official_during_contest",
  "live_scoreboard_contents": "teams ordered by current rank with performance statistics; same-rank alphabetical",
  "scoreboard_freeze": "accepted_notifications_may_suspend_rejected_continue",
  "clarification_channel": "unavailable"
}
```

## Deliverable

```json
{
  "answer_format": "Submit a complete stdin/stdout program in an allowed World Finals language (C, C++, Java, Kotlin, or Python 3) through the programming judge. Only an Accepted run solves a problem.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "algorithmic_programming"
  ],
  "official_deliverable": "source_code",
  "official_languages": [
    "C",
    "C++",
    "Java",
    "Kotlin",
    "Python3"
  ],
  "official_mime_types": [
    "text/x-csrc",
    "text/x-c++src",
    "text/x-java",
    "text/x-kotlin",
    "text/x-python"
  ],
  "io_model": "stdin_stdout"
}
```
