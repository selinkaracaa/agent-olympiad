# Environment — `science_olympiad`

## Roster

```json
{
  "active_min": 1,
  "active_default": 15,
  "active_max": 15,
  "collaboration": "Only the participants authorized by the selected season, division, and event rules may collaborate on that event.",
  "range_basis": "benchmark_adaptation",
  "roster_max": 15,
  "official_roster_note": "Fifteen is a tournament roster cap, not the active participant count for one event."
}
```

## Allowed tools

- query_rules
- read_official_materials

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "event_dependent_not_exposed_by_default",
  "code_execution": "forbidden",
  "paper_pencil": "allowed",
  "provided_materials_only": true
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "required_selectors": [
    "season",
    "division",
    "event"
  ],
  "event_rules": "not_selected",
  "event_corrections": "not_selected",
  "event_score_sheet": "not_selected"
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
    "science_olympiad_event"
  ],
  "official_deliverable": "event_answer_sheet",
  "official_mime_types": [
    "text/plain"
  ]
}
```
