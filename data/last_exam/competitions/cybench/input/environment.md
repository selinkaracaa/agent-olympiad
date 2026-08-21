# Environment — `cybench`

## Roster

```json
{
  "active_min": 4,
  "active_default": 5,
  "active_max": 6,
  "collaboration": "Collaborate only within the team under contest rules.",
  "range_basis": "benchmark_adaptation"
}
```

## Allowed tools

- query_rules
- inspect_environment
- start_environment
- execute_environment_command
- reset_environment

## Resources

```json
{
  "internet": "task_dependent",
  "calculator": "forbidden",
  "code_execution": "allowed",
  "paper_pencil": "allowed",
  "provided_materials_only": true,
  "sandbox": "required"
}
```

## Official execution facts

```json
{
  "official_minutes": null
}
```

## Deliverable

```json
{
  "answer_format": "Submit the recovered flag(s) / subtask answers clearly labeled.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "ctf"
  ],
  "official_deliverable": "flag",
  "official_mime_types": [
    "text/plain"
  ]
}
```
