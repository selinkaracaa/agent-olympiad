# Environment — `arml_national_team`

## Roster

```json
{
  "active_min": 15,
  "active_default": 15,
  "active_max": 15,
  "roster_max": 15,
  "range_basis": "source_record",
  "official_roster_note": "A national ARML/IRML team consists of 15 members. Coaches seed teams by strength as A1, A2, … or B1, B2, …. Teams may compete with fewer than 15; no substitutions are allowed once the Team Round has started.",
  "collaboration": "The entire team works the Team Round together and files one shared short-answer sheet."
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
  "electronic_devices": "forbidden",
  "paper_pencil": "allowed",
  "paper_dictionary": "non_native_english_speakers_book_form_only",
  "electronic_translators": "forbidden",
  "provided_materials_only": true,
  "outside_communication": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "session_track": "team_round_only"
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
    "team_contest"
  ],
  "official_deliverable": "answer_sheet",
  "official_mime_types": [
    "text/plain"
  ]
}
```
