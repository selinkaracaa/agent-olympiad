# Environment — `history_olympiad`

## Roster

```json
{
  "active_min": 1,
  "active_default": 3,
  "active_max": 4,
  "range_basis": "mixed_or_unresolved",
  "official_roster_note": "The 2025 World Championship uses teams of two or three, with one allowed to play if teammates are absent; historical benchmark rows still record four and require edition review.",
  "collaboration": "No verbal or written conferral is allowed while a tossup is being read; official bonus and third-quarter category phases permit team conferral."
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
  "paper_pencil": "blank_paper_only",
  "provided_materials_only": true
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "rules_edition": "2025_world_championship",
  "required_selectors": [
    "rules_edition",
    "division"
  ],
  "official_quarters": [
    {
      "quarter": 1,
      "format": "10_tossups_or_8_for_intermediate_elementary",
      "points_each": 10
    },
    {
      "quarter": 2,
      "format": "8_tossups_with_non_bounceback_bonus",
      "points_each": 10
    },
    {
      "quarter": 3,
      "format": "category_round",
      "seconds_per_team": 60,
      "conferral": true
    },
    {
      "quarter": 4,
      "format": "8_progressive_tossups",
      "point_values": [
        30,
        20,
        10
      ]
    }
  ]
}
```

## Deliverable

```json
{
  "answer_format": "Return numbered answers for the exposed questions and identify the quarter or phase; do not claim a live buzz, opponent outcome, or moderator ruling.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "history_bowl_session"
  ],
  "official_deliverable": "live_four_quarter_buzzer_match_responses",
  "official_mime_types": [
    "application/x-live-buzzer-match"
  ]
}
```
