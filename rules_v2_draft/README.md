# Agent Olympiad rules v2 draft

This folder is an isolated, review-only prototype. It does not modify or replace
`data/rules`, `src`, collectors, benchmark rows, or the current evaluator registry.

The draft turns the recommendations from the 2026-08-16 audit into an executable
design with one deep module interface:

```python
repository = RuleRepository.open("rules_v2_draft")
report = repository.validate()
resolved = repository.resolve(task_metadata)
```

Callers provide task metadata. The module hides ruleset selection, JSON Schema
validation, semantic checks, source-hash verification, team-size handling, and
roster expansion. Tests exercise the same interface that a future runtime adapter
would use.

## What is included

```text
rules_v2_draft/
  catalog.json                  ruleset selection by task metadata
  migration_matrix.json         recommended next action for all 37 tracks
  schemas/                      strict Draft 2020-12 schemas
  rules_v2/                     resolver, roster generator, and validator
  rulesets/                     nine corrected rulesets for eight tracks
  tools/validate.py             validation and current-row migration audit
  tools/demo.py                 resolver and roster examples
  tests/test_rules_v2.py        interface-level tests
  REPORT.md                     verification results and review decisions
```

The example rulesets cover the highest-value problems found in the current store:

- `hmmt_guts`: separate February/eight-person and November/six-person rulesets;
- `ichto`: one 4–6 person national team, with external Opponent/Reviewer teams;
- `iiot`: two contest-machine slots rather than contradictory single-workstation text;
- `wharton_investment`: correct 4–6 roster and explicit AI-authorship conflict;
- `wsc_writing`: all three teammates write one complete response;
- `purple_comet` and `fyziklani`: explicit non-comparability caused by AI bans;
- `debatebench`: four private two-speaker coalitions instead of one team of eight.

## Design decisions

### Ruleset selection is task-aware

`catalog.json` selects by explicit metadata such as `season`. Matching uses the
most-specific selector and rejects equal-specificity ambiguity. A future migration
should add `ruleset_id` directly to benchmark rows so historical rules do not drift
when a competition changes its format.

### Machine policy is canonical

`resource_policy` stores one structured decision for Internet, code, calculators,
AI, devices, or shared capacity. Contestant prose should eventually be rendered
from these fields instead of independently edited strings.

### Constraints are traceable

Every official constraint has an ID, source reference, and enforcement status.
Archived source files carry SHA-256 hashes. Benchmark adaptations are labeled and
may remain unsourced because they are project design choices rather than external
facts.

### Unsupported mechanisms cannot claim equivalence

The semantic validator rejects `official_equivalent` whenever a required state is
missing, a comparability dimension is adapted, or a waiver/unsupported mechanism
exists. AI prohibitions are treated as participant-identity conflicts, not merely
as unavailable external tools.

### Variable rosters generate safely

Cards define required roles plus an optional fill role. The resolver generates a
valid roster at every declared size. This removes the current fixed-role failure
for six-person HMMT November rows and also supports Wharton, Purple Comet, and
Fyziklání ranges.

### Adversaries use coalitions

`multi_coalition` rulesets declare private groups explicitly. The BP example gives
each pair its own private channel while treating speeches as public chamber state.
IChTo instead resolves one national team and leaves official opposing teams outside
that roster.

## Run the draft

From this folder:

```powershell
python tools\validate.py
python tools\validate.py --check-current-benchmarks
python tools\demo.py
python -m unittest discover -s tests -v
```

The only current-row migration failure expected by this draft is IChTo: all nine
existing rows say `team_size=3`, while the sourced rules require 4–6. The draft
does not silently coerce those rows; it reports that the benchmark metadata must
be corrected.

## Not implemented here

This is deliberately not a second production runtime. It does not yet provide:

- shared-machine leases for ICPC or IIOT;
- progressive batch state for HMMT or Fyziklání;
- buzzer, oral-performance, physical-lab, robot, or live-market environments;
- missing production evaluators;
- migrated v2 cards for the remaining 29 tracks.

Those changes should happen only after the v2 fields and conservative profile
policy are reviewed.
