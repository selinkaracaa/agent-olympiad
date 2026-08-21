# Environment — `ccdc`

## Roster

```json
{
  "active_min": 8,
  "active_default": 8,
  "active_max": 8,
  "collaboration": "Collaborate only within the team under contest rules.",
  "range_basis": "mixed_or_unresolved"
}
```

## Allowed tools

- query_rules
- inspect_environment

## Resources

```json
{
  "internet": "forbidden",
  "calculator": "forbidden",
  "code_execution": "requires_mutable_network_environment",
  "paper_pencil": "allowed",
  "provided_materials_only": true
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "mutable_network_environment": "unavailable",
  "red_team_actions": "unavailable",
  "inject_lifecycle": "specified_only",
  "service_score_state": "unavailable"
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
    "cyber_defense_scenario",
    "wildcard_material"
  ],
  "official_deliverable": "defended_services_and_reports",
  "official_mime_types": [
    "text/plain"
  ]
}
```
