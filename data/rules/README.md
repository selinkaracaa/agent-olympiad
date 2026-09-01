# Competition rule cards

Rule cards control how `src/` runs a competition. They are separate from:

- `data/benchmarks/`: contestant problems and problem metadata;
- `data/rubrics/`: judge-side scoring criteria;
- `data/evaluators/`: evaluator selection and implementation metadata.

`src/rules/loader.py` selects a competition deterministically. Every production
rule card is stored under its competition ID using three canonical files:

```text
data/rules/{competition_id}/
  competition.json   # official/public contest input
  collaboration.json # method, including simulation.max_turns
  evaluation.json    # hidden judge/eval configuration
```

`src/rules/storage.py` composes those components into one `RuleCard`. It retains
legacy `{competition_id}.json` support for compatibility, while rejecting missing
components, misplaced/duplicate fields, and simultaneous flat and bundled
representations. `data/rules/schema.json` and the linter validate the assembled
card. Agents may read the selected rule summary via `query_rules`, but they do not
choose their own rule card.

## Status

Every track in `data/benchmarks/index.json` has a three-component rule-card
bundle. The 36 non-ICPC bundles also carry the same content contract as ICPC:
explicit contestant constraints, agent operations, labeled official/adapted
rule sections, and four separate evaluation layers (`official_performance`,
`rule_compliance`, `collaboration_quality`, and
`current_repository_availability`).

The 2026-08-17 source audit is recorded in every non-ICPC card as
`provenance.source_review`. Its A-D coverage grade is a source-coverage status,
not a claim that the runner reproduces the competition. A structurally complete
card may therefore still be `proxy` or `non_comparable`, have null official
values, require a season/division/event selector, or retain a deferred evaluator.
See [`docs/rule_card_icpc_standard_gap_audit_2026-08-17.md`](../../docs/rule_card_icpc_standard_gap_audit_2026-08-17.md).

Source-audited corrections now include APPE's maximum of six active participants,
NHSEB's 3-7 roster and maximum five seated, the 2025 History Bowl four-quarter
rules and no incorrect-answer deductions, Mystery Hunt's lack of an official
8-12 cap, IOAI Team Challenge default-deny web policy, event-specific Science
Olympiad selectors, 2026 WRO RoboMission scope, and removal of unsupported exact
ARML/IEO/IIOT/IJSO/IOAA durations. Variable-size cards resolve rosters at their
declared minimum, default, and maximum sizes.

When deterministic grading is appropriate but benchmark rows do not yet declare
an evaluator, `scoring.recommended_evaluator_id` records the intended evaluator
without falsely marking the integration ready. The linter continues to warn until
the benchmark metadata and evaluator are migrated together.

Official sources were crawled into `data/rules/sources/` and used to enrich
`human_constraints` / provenance. See [`docs/RULES_CRAWL.md`](../../docs/RULES_CRAWL.md).

The full pipeline, in order:

```bash
python collectors/crawl_competition_rules.py      # archive official pages/PDFs
python collectors/enrich_rules_from_sources.py    # constraints + provenance
python collectors/merge_rules_crawl_report.py     # research report hard constraints
python collectors/rewrite_rules_text.py           # contestant-facing rules_text
python collectors/align_deliverables.py           # submission + evaluator contract
python collectors/write_role_duties.py            # per-role duties, not boilerplate
python collectors/configure_coordination_rules.py # expertise + dissent + comm budgets
python collectors/apply_source_review_corrections.py # reviewed facts + explicit unknowns
python collectors/derive_turn_budgets.py           # max_turns from reviewed duration
python collectors/standardize_rule_card_content.py # ICPC-level content contract
python collectors/lint_rule_cards.py              # gate: 0 errors expected
```

`merge_rules_crawl_report.py` takes `--report` so later research passes can be
merged the same way; `docs/rules_lowconf_2026-08-12.md` is the second pass. Merging is
additive, so an entry a later pass retracts needs `"superseded_by": "<report path>"` in
the older report or it returns on the next replay.

## Three rule layers and six runtime contracts

The three files separate distinct kinds of rules:

1. **Competition rules** define what the contest permits and requires: roster,
   official clocks, tools, resources, official `human_constraints`, public
   deliverable, and fidelity/provenance.
2. **Collaboration rules** define `agent_constraints`, roles, information
   sharing, deliberation, communication, and `simulation` (runner method such as
   `max_turns` and pending-run latency).
3. **Evaluation rules** are hidden until grade: evaluator/rubric pointers,
   official-performance reporting, compliance, collaboration diagnostics, and
   runner adaptations. Judge-side rubric content remains in `data/rubrics/`.

Together those layers carry six runtime contracts:

1. **Behaviour**: `human_constraints` are binding and go into the prompt verbatim.
   Anything addressed to a maintainer belongs in `provenance.research_notes`;
   `collectors/constraint_hygiene.py` enforces the split on every pipeline run.
2. **Deliverable**: `submission.official_deliverable` / `official_mime_types` state
   what the real contest collects, `submission.mime_types` states what the runner
   accepts today, and `submission.adaptation` records the gap. `scoring.evaluator_id`
   and `scoring.rubric_path` must match what `data/benchmarks/{cid}/benchmark.json`
   declares — the linter fails on disagreement.
3. **Budget**: `simulation.max_turns` is derived from
   `provenance.official_time_note` and the benchmark's answer-part count;
   `simulation.turn_budget_basis` shows the arithmetic. Cards whose official
   duration is unknown record `execution.official_minutes: null` and fall back
   to a roster-based floor. Agents never receive evaluator IDs, rubric paths,
   gold pointers, or `evaluation_guidance`.
4. **Information**: opt-in cards set `information_policy.mode` to
   `role_specialized`. Every teammate can consult the complete contestant rules,
   while `rule_sections` and each role's `rule_expertise` assign primary
   responsibility: planners track timing and workflow, modelers track tool/data
   limits, researchers track sources and integrity, and writers track format and
   judging priorities. Prompts and `query_rules` repeat the responsible role's
   sections so the team knows whom to ask without making basic compliance
   information artificially secret. Judge-only gold answers and raw rubric files
   remain unavailable.
5. **Deliberation**: collaboration-heavy cards may set
   `deliberation.mode = structured`. Agents then record `propose`, `challenge`,
   `provide_evidence`, `revise`, and `decide` actions against proposal IDs.
   Challenges and evidence are broadcast to the team but also retained in a
   machine-readable ledger, allowing evaluation of evidence responsiveness,
   traceable decisions, authority bias, and majority bias. Only proposal authors
   may revise; only designated submitters may decide.
6. **Communication**: high-pressure team cards may set
   `communication.mode = limited`, with team-wide and per-agent message budgets
   plus a per-message character cap. Broadcasts, shared-scratchpad writes, and
   structured deliberation consume the budget. `write_private_notes` lets an
   agent continue independent work without broadcasting or spending a message;
   those notes appear only in that agent's later prompts. Usage and rejected
   messages are included in the run result for coordination-efficiency analysis.

The coordination overlay is curated per mechanism rather than applied as one
bundle: 30 tracks use role-specialized rule ownership, 25 use structured
deliberation, and 19 use a limited communication budget. Buzzer phases,
continuous real-time collaboration, long-term creative work, and cards whose
rosters combine opposing teams are not given a flat message budget when that
would distort the source competition. Every enabled mechanism is recorded as a
benchmark adaptation rather than an official contest constraint.

The source-correction and content-standard passes are idempotent. The linter and
`tests/test_rule_card_lint.py` fail the build if a card regresses through a schema
violation, missing source-review state, incomplete citation metadata, unknown
tool, roster/team mismatch, tool/resource contradiction, or pipeline text in the
contest briefing. Unclassified authority, unfrozen edition, missing source
locator, and unassigned evaluator remain visible warnings rather than invented
facts.

`rules_text` is injected verbatim into the agent system prompt, so it must read
like a contest briefing. Cards marked
`provenance.rules_text_source = composed_from_card_fields_*` are regenerated from
the card's own fields by `rewrite_rules_text.py`; hand-written briefings are left
alone unless you pass `--all`. Resource policy is rendered separately from
`resources` by `src/rules/describe.py`, so briefings should not repeat it.

Physical, buzzer, oral, market, network, long-horizon, and robotics contests may
remain `proxy` or `non_comparable` because a complete text card does not create
the missing live environment, opponent, judge, apparatus, or state machine.

## Card requirements

Every card must:

1. conform to `schema.json`;
2. cite the official source and identify benchmark adaptations;
3. declare whether the run is official-equivalent, benchmark-native, proxy, or
   non-comparable;
4. list only tools that `src/env.py` implements and can enforce.
