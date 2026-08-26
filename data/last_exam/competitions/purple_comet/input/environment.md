# Environment — `purple_comet`

## Roster

```json
{
  "active_min": 1,
  "active_default": 6,
  "active_max": 6,
  "roster_max": 6,
  "collaboration": "One to six teammates may work together from the same or different locations and share one team answer form; an adult supervisor aged 21 or older is required and is not a contestant.",
  "range_basis": "source_record",
  "official_roster_note": "A team may have as few as one and as many as six students. An adult supervisor aged 21 or older must register the team, start the clock, and monitor rule-following, and must not help solve problems, supply definitions, or enter answers except where judges grant a disability accommodation. Competitive-category age, grade, and school-size rules, and the 244-hour window, are official identity and logistics obligations included for role immersion and are not runtime-enforced state machines."
}
```

## Allowed tools

- query_rules
- use_calculator

## Resources

```json
{
  "internet": "forbidden_for_solution_search",
  "calculator": "allowed",
  "computer_algebra": "allowed_for_calculation_only",
  "ai_tools": "forbidden",
  "solution_method_search": "forbidden",
  "paper_pencil": "allowed",
  "local_books_and_notes": "allowed",
  "generative_ai": "forbidden",
  "outside_help": "forbidden",
  "remote_teammate_communication": "allowed"
}
```

## Official execution facts

```json
{
  "wall_clock_note": "HS usually 90 minutes / MS 60 minutes; max_turns is a safety budget.",
  "official_minutes": 90,
  "division_variants": {
    "MS": {
      "problem_count": 20,
      "official_minutes": 60
    },
    "HS": {
      "problem_count": 30,
      "official_minutes": 90
    }
  },
  "competition_window_hours": 244,
  "supervisor_starts_clock": true,
  "answer_form": "web_form_last_submission_per_problem_counts",
  "partial_submissions_accumulate": true
}
```

## Deliverable

```json
{
  "answer_format": "Ordered non-negative integers, one per problem:\n1. N\n2. N\n...\nUse the contest's required integer encoding (for example m+n).",
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
