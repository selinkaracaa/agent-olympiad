# Environment — `pumac_power`

## Roster

```json
{
  "active_min": 8,
  "active_default": 8,
  "active_max": 8,
  "roster_max": 8,
  "range_basis": "source_record",
  "official_roster_note": "A full PUMaC team is exactly eight high-school students. Power-Only teams are also exactly eight; individuals may not apply to Power-Only. Members must be under 20 before the contest date and must not have been enrolled full-time in a post-secondary institution before that date.",
  "collaboration": "All eight students on the team may collaborate freely on the Power Round; no one outside those eight may help."
}
```

## Allowed tools

- query_rules

## Resources

```json
{
  "internet": "forbidden_unless_year_packet_explicitly_allows",
  "calculator": "year_packet_dependent_not_exposed_by_default",
  "code_execution": "year_packet_dependent_not_exposed_by_default",
  "paper_pencil": "allowed",
  "provided_materials_only": true,
  "outside_resources": "forbidden_unless_test_says_otherwise",
  "books": "forbidden_unless_test_says_otherwise",
  "people_outside_the_eight": "forbidden"
}
```

## Official execution facts

```json
{
  "official_minutes": null,
  "week_long_workflow": "official_not_reproduced_by_turn_budget",
  "packet_instructions_control": "official_packet_overrides_card_on_conflict",
  "computational_aids": "year_packet_dependent_default_deny"
}
```

## Deliverable

```json
{
  "answer_format": "Submit a numbered proof packet with a complete justification for every claimed result, explicit references to earlier parts, and the required anonymous page labels.",
  "shared": true,
  "mime_types": [
    "text/plain"
  ],
  "task_types": [
    "proof_packet"
  ],
  "official_deliverable": "proof_packet",
  "official_mime_types": [
    "text/plain"
  ]
}
```
