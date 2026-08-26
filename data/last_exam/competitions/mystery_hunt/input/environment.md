# Environment — `mystery_hunt`

## Roster

```json
{
  "active_min": 8,
  "active_default": 12,
  "active_max": 12,
  "collaboration": "The configured agents may freely coordinate inside their benchmark team; they may not obtain answers from another competing team.",
  "range_basis": "benchmark_adaptation",
  "official_roster_note": "The 2026 FAQ states no official team-size recommendation; 8-12 is only the runner's configured range."
}
```

## Allowed tools

- query_rules
- execute_code
- web_search

## Resources

```json
{
  "internet": "allowed",
  "calculator": "forbidden",
  "code_execution": "allowed",
  "paper_pencil": "allowed",
  "provided_materials_only": false,
  "external_teams": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "rules_edition": "2026"
}
```

## Deliverable

```json
{
  "answer_format": "Submit the team's final answers in numbered order, using exact values when required.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "puzzle"
  ],
  "official_deliverable": "puzzle_answer",
  "official_mime_types": [
    "text/plain"
  ]
}
```
