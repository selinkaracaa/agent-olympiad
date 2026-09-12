# Environment — `ioai_team`

## Roster

```json
{
  "active_min": 4,
  "active_default": 4,
  "active_max": 4,
  "collaboration": "Collaborate only within the team under contest rules.",
  "range_basis": "source_record"
}
```

## Allowed tools

- query_rules
- execute_code

## Resources

```json
{
  "internet": "translation_site_only_unless_team_task_guide_allows_more",
  "calculator": "forbidden",
  "code_execution": "task_specific_environment_only",
  "paper_pencil": "allowed",
  "provided_materials_only": true
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "rules_edition": "2026_version_4",
  "required_selectors": [
    "team_challenge_round",
    "task_guide_version"
  ],
  "team_challenge_environment": "specified_by_separate_task_guide"
}
```

## Deliverable

```json
{
  "answer_format": "Submit a structured report or slide outline covering analysis, recommendation, and evidence.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "team_challenge"
  ],
  "official_deliverable": "code_and_predictions",
  "official_mime_types": [
    "text/x-python",
    "text/plain"
  ]
}
```
