# Environment — `debatebench`

## Roster

```json
{
  "active_min": 8,
  "active_default": 8,
  "active_max": 8,
  "collaboration": "Eight participants form four private two-speaker coalitions. Each speaker may prepare only with their partner; cross-coalition sharing is forbidden.",
  "range_basis": "mixed_or_unresolved"
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
  "provided_materials_only": true
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "coalition_privacy": "specified_only",
  "coalitions": [
    {
      "id": "opening_government",
      "members": [
        "Agent_1",
        "Agent_2"
      ]
    },
    {
      "id": "opening_opposition",
      "members": [
        "Agent_3",
        "Agent_4"
      ]
    },
    {
      "id": "closing_government",
      "members": [
        "Agent_5",
        "Agent_6"
      ]
    },
    {
      "id": "closing_opposition",
      "members": [
        "Agent_7",
        "Agent_8"
      ]
    }
  ]
}
```

## Deliverable

```json
{
  "answer_format": "Submit eight labeled speeches in official order: PM, LO, DPM, DLO, MG, MO, GW, OW. Preserve coalition privacy and identify POIs separately.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "bp_debate_transcript"
  ],
  "official_deliverable": "oral_speech",
  "official_mime_types": [
    "text/plain"
  ]
}
```
