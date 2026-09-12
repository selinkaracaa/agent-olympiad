# Environment — `ioaa_group`

## Roster

```json
{
  "active_min": 5,
  "active_default": 5,
  "active_max": 5,
  "collaboration": "Equal contestants assigned to one international group team collaborate on the host-designed task and produce one shared answer.",
  "range_basis": "mixed_or_unresolved",
  "official_roster_note": "Statute 13 requires at least five students from different countries, randomized when possible. Exact size is host-year specific; the 2023 packet used five-person asteroid teams. This card models five active contestants and does not freeze five as a universal official maximum."
}
```

## Allowed tools

- query_rules
- use_calculator
- read_star_chart

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "allowed",
  "personal_calculator": "forbidden",
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
    "host_year"
  ],
  "host_year_packet": "required",
  "edition_example_note": "The 2023 Group Competition packet is an edition example only: random 5-person asteroid teams; sealed envelopes opened on START; 90-minute maximum; shortest total time after task-specific time penalties; organizer-provided calculator, office supplies, geometrical instruments, paper, and constants table. Those values are not a current universal official clock, roster, or scoring rule."
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
  "official_deliverable": "worked_answers",
  "official_mime_types": [
    "text/plain"
  ]
}
```
