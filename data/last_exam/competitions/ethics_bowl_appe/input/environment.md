# Environment — `ethics_bowl_appe`

## Roster

```json
{
  "active_min": 1,
  "active_default": 5,
  "active_max": 6,
  "range_basis": "source_record",
  "official_roster_note": "The 2025 national rules allow a team of any roster size, but no more than six members may actively participate in a match.",
  "collaboration": "The seated participants may confer only in the designated phase; multiple members may contribute orally, but only one person speaks at a time."
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
  "paper_pencil": "scratch_paper_only_after_official_start",
  "provided_materials_only": true,
  "personal_timer": "non_networked_non_storage_reference_only"
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "rules_edition": "2025_national",
  "required_selectors": [
    "competition_scope"
  ],
  "selector_default": {
    "competition_scope": "national"
  },
  "official_phases": [
    {
      "phase": "presenting_team_conferral",
      "minutes": 2
    },
    {
      "phase": "presenting_team_response",
      "minutes": 10,
      "hard_stop": true
    },
    {
      "phase": "opposing_team_conferral",
      "minutes": 1
    },
    {
      "phase": "opposing_team_commentary",
      "minutes": 5,
      "hard_stop": true
    },
    {
      "phase": "presenting_team_reply_conferral",
      "minutes": 1
    },
    {
      "phase": "presenting_team_reply",
      "minutes": 5,
      "hard_stop": true
    },
    {
      "phase": "judge_questioning",
      "minutes": 10,
      "hard_stop": true
    }
  ],
  "second_case_role_reversal": "specified_only"
}
```

## Deliverable

```json
{
  "answer_format": "Provide the case response, opposing-team commentary, commentary reply, and judge-question answers as distinct labeled sections exposed by the task.",
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
