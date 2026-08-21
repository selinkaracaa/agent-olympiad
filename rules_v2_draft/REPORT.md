# Rules v2 draft verification report

Date: 2026-08-16

## Outcome

The isolated draft is internally valid and executable.

- 9 rulesets for 8 representative tracks
- 37/37 current tracks covered by `migration_matrix.json`
- 0 schema, semantic, catalog, provenance, hash, or migration-matrix errors
- 11/11 interface-level tests passed
- 45/45 current HMMT rows resolve with the correct six- or eight-person roster
- 228 current rows checked across the eight example tracks
- 219 resolve without data migration
- 9 IChTo rows are deliberately rejected because current metadata says three
  teammates while the sourced official range is four through six

## Checks performed

The validator currently checks:

1. full JSON Schema Draft 2020-12 conformance;
2. unique catalog IDs and paths, safe local paths, and selector ambiguity;
3. catalog/file competition, ruleset, and selector agreement;
4. team range arithmetic and roster generation at minimum/default/maximum sizes;
5. unique roles, submitter availability, and complete coalition membership;
6. official constraint citations and valid source references;
7. archived source existence and SHA-256 integrity;
8. obvious prose-versus-resource contradictions;
9. evaluator/status and rubric-path consistency;
10. conservative comparability/profile semantics;
11. exact 37-track coverage in the migration matrix.

## Review decisions requested before adoption

1. Confirm the conservative rule: an explicit ban on generative AI makes an
   LLM-agent run `non_comparable`, even when the problem answers are objectively
   gradable.
2. Decide whether adversarial formats should run all coalitions together or score
   one cooperative team against scripted opponents.
3. Approve adding `ruleset_id` and normalized selectors such as season, division,
   event, and edition to benchmark rows.
4. Approve required/fill roster templates instead of fixed `Agent_1`…`Agent_N`
   records.
5. Decide whether the nine IChTo rows should be migrated to a four-person default
   or redefined as a three-team fight abstraction with a different competition ID.
6. Choose the first production evaluator wave. The recommended first wave is
   deterministic gold/flag scoring before oral, physical, robot, and long-horizon
   artifact evaluation.

## Reproduction

```powershell
cd E:\agent_olympiad\agent-olympiad\rules_v2_draft
python tools\validate.py --check-current-benchmarks
python -m unittest discover -s tests -v
```
