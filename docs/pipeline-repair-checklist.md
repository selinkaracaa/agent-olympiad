# Original six pipeline findings: repair ledger

This tracks the original audit, not an expanding list of unrelated cleanup.
Status is scoped to those findings; it does not claim the repository has no bugs.

| # | Original finding | Resolution | Verification |
|---|---|---|---|
| 1 | Skip/resume accepted insufficiently identified output | CLI and batches resolve an expected run identity; incompatible/legacy artifacts fail closed; exit zero alone is insufficient | `test_contest_run_identity.py`; `test_batch_summary.py` |
| 2 | CLI settings were ignored or recorded differently from execution | Resolve output cap, review/final-review, rules mode/root/strict before providers; reject conflicting options. Retired `--skip-existing-roots` now errors before writes rather than silently doing nothing | `test_contest_settings.py` |
| 3 | OTC and Open Table Coach diverged into duplicate implementations | Only canonical `otc` uses the latest rule-card implementation; former variant names are aliases; old per-problem implementation removed | `test_otc_migration.py`; `test_otc_rulecard.py` |
| 4 | Monolithic runner mixed prompts, gating, transport, state, and finalization | Config/actions already extracted; lifecycle is now an instance with small ordered phases, isolated per-seat state, and separate prompt/policy/lifecycle modules. Facade retains compatibility imports | `test_contest_engine_replay.py` (12 pre-refactor replay fingerprints plus dependency/phase guards); runner/programming/OTC regressions |
| 5 | ICPC batch depended on a historical script under `results/` | Fresh and resumed jobs both use `src/run_competition_batch.py`; historical trace files are not execution dependencies | `test_contest_run_identity.py` |
| 6 | Wholly unsupported grading reported `graded=True` | `graded` requires all tasks to be evaluable; partial/unavailable tasks do not enter score denominators | `test_contest_protocol_regressions.py`; adapter grading tests |

All six findings are addressed. Batch-summary provenance was a follow-through
on item 1: it now revalidates only jobs verified by the current invocation and
excludes pending/failed/unmatched artifacts.

The codebase-design skill guided item 4: preserve the caller interface, put the
mutable state behind a single run interface, and separate per-seat phase state.
The replay fixtures were captured before that restructuring and must not be
updated merely to accommodate a refactor.

No historical experiment outputs or checkpoints were rewritten, and verification
uses mocked providers/judges rather than launching paid experiments.
