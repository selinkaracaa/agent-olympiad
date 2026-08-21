# Environment — `hmmt_guts`

## Roster

```json
{
  "active_min": 6,
  "active_default": 8,
  "active_max": 8,
  "roster_max": 8,
  "range_basis": "mixed_or_unresolved",
  "official_roster_note": "Official November Guts teams are 4–6 high-school students; official February Guts teams are 6–8. This card keeps active_min 6, active_default 8, and active_max 8, with season_variants nov.team_size 6 and feb.team_size 8. Select season from the benchmark row; do not treat a November row as an eight-person February team, and do not invent teammates beyond the selected-season roster.",
  "collaboration": "All members of the selected-season Guts roster work together on the current released set; only teammates may discuss the problems."
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
  "paper_pencil": "allowed",
  "provided_materials_only": true,
  "books_and_notes": "forbidden",
  "computational_aids": "forbidden",
  "drawing_aids": "forbidden",
  "personal_electronic_devices": "forbidden",
  "outside_communication": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": 80,
  "required_selectors": [
    "season"
  ],
  "season_variants": {
    "feb": {
      "team_size": 8,
      "batch_size": 4,
      "official_minutes": 80
    },
    "nov": {
      "team_size": 6,
      "batch_size": 3,
      "official_minutes": 80
    }
  },
  "progressive_batch_release": "specified_only",
  "batch_finality": "specified_only",
  "live_scoreboard": "official_during_contest_specified_not_enforced",
  "appeals": "specified_only",
  "sweepstakes_scope": "guts_component_only"
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
    "guts_round"
  ],
  "official_deliverable": "answer_sheet",
  "official_mime_types": [
    "text/plain"
  ]
}
```
