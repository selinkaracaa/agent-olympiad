# Environment — `wro`

## Roster

```json
{
  "active_min": 2,
  "active_default": 3,
  "active_max": 3,
  "collaboration": "The two or three student members design, build, and program the robot; a coach may guide learning but may not build or program it for the team.",
  "range_basis": "source_record",
  "official_roster_note": "A 2026 RoboMission team consists of two or three students and is guided by a coach."
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
    "category",
    "age_group",
    "jurisdiction",
    "game_document",
    "q_and_a_snapshot"
  ],
  "rules_edition": "2026_robomission_general",
  "robot_attempt_seconds": 120
}
```

## Deliverable

```json
{
  "answer_format": "Submit the program and a structured design/run analysis; label simulated or hypothetical behavior and do not report an unobserved physical score.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "robotics_mission",
    "robotics_project"
  ],
  "official_deliverable": "inspected_robot_program_and_scored_field_attempt",
  "official_mime_types": [
    "application/x-physical-robot-attempt"
  ]
}
```
