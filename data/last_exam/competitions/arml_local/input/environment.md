# Environment — `arml_local`

## Roster

```json
{
  "active_min": 6,
  "active_default": 6,
  "active_max": 6,
  "roster_max": 6,
  "range_basis": "source_record",
  "official_roster_note": "ARML Local is open to middle schools, high schools, and homeschool groups. Each school or group may field one or more teams of six students.",
  "collaboration": "The entire six-person team works the Team Round together and files one shared short-answer sheet."
}
```

## Allowed tools

- query_rules

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "forbidden",
  "electronic_devices": "forbidden",
  "books_notes": "forbidden",
  "paper_pencil": "allowed",
  "provided_materials_only": true,
  "outside_communication": "forbidden"
}
```

## Official execution facts

```json
{
  "wall_clock_note": "Official ARML Local team round is about 45 minutes; max_turns is a safety budget.",
  "official_minutes": 45,
  "session_track": "team_round_only"
}
```

## Deliverable

```json
{
  "answer_format": "Numbered team answer sheet:\n1. [answer]\n2. [answer]\n...\n10. [answer]\nUse exact values when the problem asks for them.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "team_contest"
  ],
  "official_deliverable": "answer_sheet",
  "official_mime_types": [
    "text/plain"
  ]
}
```
