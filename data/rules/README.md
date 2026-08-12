# Competition rule cards

Rule cards control how `src/` runs a competition. They are separate from:

- `data/benchmarks/`: contestant problems and problem metadata;
- `data/rubrics/`: judge-side scoring criteria;
- `data/evaluators/`: evaluator selection and implementation metadata.

`src/rules/loader.py` selects `{competition_id}.json` deterministically. Agents may
read the selected rule summary via `query_rules`, but they do not choose their own
rule card.

## Status

Every track in `data/benchmarks/index.json` now has a rule card.

Official sources were crawled into `data/rules/sources/` and used to enrich
`human_constraints` / provenance. See [`docs/RULES_CRAWL.md`](../../docs/RULES_CRAWL.md).

The full pipeline, in order:

```bash
python collectors/crawl_competition_rules.py      # archive official pages/PDFs
python collectors/enrich_rules_from_sources.py    # constraints + provenance
python collectors/merge_rules_crawl_report.py     # research report hard constraints
python collectors/rewrite_rules_text.py           # contestant-facing rules_text
python collectors/align_deliverables.py           # submission + evaluator contract
python collectors/derive_turn_budgets.py          # max_turns from official duration
python collectors/write_role_duties.py            # per-role duties, not boilerplate
python collectors/configure_coordination_rules.py # expertise + dissent + comm budgets
python collectors/lint_rule_cards.py              # gate: 0 errors expected
```

`merge_rules_crawl_report.py` takes `--report` so later research passes can be
merged the same way; `docs/rules_lowconf_2026-08-12.md` is the second pass. Merging is
additive, so an entry a later pass retracts needs `"superseded_by": "<report path>"` in
the older report or it returns on the next replay.

## The six contracts a card carries

1. **Behaviour**: `human_constraints` are binding and go into the prompt verbatim.
   Anything addressed to a maintainer belongs in `provenance.research_notes`;
   `collectors/constraint_hygiene.py` enforces the split on every pipeline run.
2. **Deliverable**: `submission.official_deliverable` / `official_mime_types` state
   what the real contest collects, `submission.mime_types` states what the runner
   accepts today, and `submission.adaptation` records the gap. `scoring.evaluator_id`
   and `scoring.rubric_path` must match what `data/benchmarks/{cid}/benchmark.json`
   declares — the linter fails on disagreement.
3. **Budget**: `execution.max_turns` is derived from `provenance.official_time_note`
   and the benchmark's answer-part count; `execution.turn_budget_basis` shows the
   arithmetic. Cards whose official duration is unknown record
   `execution.official_minutes: null` and fall back to a roster-based floor.
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

Every step is idempotent, and `tests/test_rule_card_lint.py` fails the build if a
card regresses (schema violation, unknown tool, roster/team mismatch, tool that
contradicts a resource ban, or `rules_text` that leaks pipeline metadata).

`rules_text` is injected verbatim into the agent system prompt, so it must read
like a contest briefing. Cards marked
`provenance.rules_text_source = composed_from_card_fields_*` are regenerated from
the card's own fields by `rewrite_rules_text.py`; hand-written briefings are left
alone unless you pass `--all`. Resource policy is rendered separately from
`resources` by `src/rules/describe.py`, so briefings should not repeat it.

Hand-tuned first pass (roles + tools):

- `arml_local.json`
- `purple_comet.json`
- `wmtc.json`
- `qanta.json`
- `science_bowl.json`

Remaining cards started as draft v1 and were source-enriched. Physical / buzzer /
oral-heavy contests may still be marked `proxy` because `src/` cannot fully
execute those mechanisms yet.

## Card requirements

Every card must:

1. conform to `schema.json`;
2. cite the official source and identify benchmark adaptations;
3. declare whether the run is official-equivalent, benchmark-native, proxy, or
   non-comparable;
4. list only tools that `src/env.py` implements and can enforce.
