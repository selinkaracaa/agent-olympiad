# Environment — `ethics_bowl_nhseb`

## Roster

```json
{
  "active_min": 3,
  "active_default": 5,
  "active_max": 5,
  "roster_max": 7,
  "range_basis": "source_record",
  "official_roster_note": "A team has three to seven students; no more than five are seated in a match.",
  "collaboration": "Only the seated members participate in a match; they may confer in the designated periods, while the non-presenting team remains silent during the other team's speaking period."
}
```

## Allowed tools

- query_rules

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "forbidden",
  "code_execution": "forbidden",
  "paper_pencil": "organizer_provided_scratch_paper_only",
  "provided_materials_only": true,
  "personal_timer": "non_networked_non_storage_reference_only"
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "rules_edition": "2025-2026",
  "required_selectors": [
    "competition_scope",
    "match_mode"
  ],
  "selector_default": {
    "competition_scope": "regional",
    "match_mode": "in_person"
  },
  "official_phases": [
    {
      "phase": "presentation_conferral",
      "minutes": 2
    },
    {
      "phase": "presentation",
      "minutes_by_scope": {
        "regional": 5,
        "divisional_or_national": 6
      }
    },
    {
      "phase": "commentary_conferral",
      "minutes": 2
    },
    {
      "phase": "commentary",
      "minutes": 3
    },
    {
      "phase": "response_conferral",
      "minutes": 2
    },
    {
      "phase": "response",
      "minutes": 3
    },
    {
      "phase": "judge_questions",
      "minutes": 10
    }
  ],
  "second_case_role_reversal": "specified_only"
}
```

## Deliverable

```json
{
  "answer_format": "Provide the presentation, opposing-team commentary, response to commentary, and answers to judges as distinct labeled sections.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "ethics_case_set"
  ],
  "official_deliverable": "live_oral_match_performance",
  "official_mime_types": [
    "audio/x-live-speech"
  ]
}
```
