# Contest run identity and reuse

The contest-session CLI and the ICPC full-pairs / gold-suite schedulers share
one configuration resolver and one reuse check. This applies to
`run_competition_batch.py --contest-manifest ...`; the legacy per-problem
runner is unchanged. The ARML / Science Bowl batch reuses the gold-suite launch
function, so it receives the same checks.

Before starting model calls, a new run writes `run_config.json`, containing
resolved settings and a SHA-256 fingerprint. The same identity is embedded in
every `contest_checkpoint.json` and the final `contest_session.json`.

The fingerprint covers canonical baseline and effective review settings, team
size, budgets, starting seat, deadline policy, model/provider, generation
parameters, action transport, enabled judges, loaded rule-card content, the
ordered manifest with its resolved task/benchmark content, protocol/action
versions, and all Python source files under `src/`. Task and full rule-card
contents are stored as hashes; agent-visible rule guidance is also recorded
as part of the effective prompt settings. API credentials, output paths, timestamps and variant
alias spelling are excluded.

Source matching is intentionally conservative: even a change to another Python
module under `src/` requires a fresh output directory. The fingerprint is not
a complete environment snapshot: remote provider/OJ state, installed packages,
and external asset files referenced by benchmark paths are not pinned by it.

With `--resume`, an exactly matching final result is skipped, and a matching
checkpoint is continued. A completed run can have unavailable grading; execution
completion does not imply that its score is usable. A matching existing result
or checkpoint without `--resume` is rejected to prevent accidental overwrites.

The two schedulers automatically make the same skip/resume decision. A process
exit code of zero alone is insufficient to mark a batch job complete.

Legacy files without an identity, mismatched settings, corrupt identities and
inconsistent protocol/action versions are rejected with a diagnostic. Existing
session results and checkpoints are retained. Do not add fingerprints to old
artifacts by hand: the settings used to produce them cannot be established from
their names. Choose a fresh output directory for a new experiment instead.

## Batch summary provenance

Gold-suite and ARML / Science Bowl batches share `contest_batch_summary.py`.
Only jobs verified as `ok` or `skipped_complete` by this invocation are eligible
for scores. The exporter revalidates the expected identity and final envelope,
then reads metrics from that same validated snapshot.

Unvisited jobs are `pending`, even if older result files exist. Failed or blocked
jobs have blank scores; changed/corrupt final artifacts are `invalid` with a
reason. A verified completion with unavailable grading remains `ungraded`, not
an execution failure. `batch_status` and `run_fingerprint` expose that distinction
and provenance in the TSV. Both entry points update the summary before stopping
on a blocked job, so stale scores cannot survive an early exit.

Summary replacement is atomic. Existing session/checkpoint files are read-only
during export. Direct callers must pass this invocation's `run_results` (including
the expected `run_identity`); no results supplied means all rows stay pending.

## Effective contest settings

`--max-output-tokens` now resolves in this order: explicit CLI override, contest
registry (`icpc`/`iiot`: 4096), then the common 8192 default. The resolved limit
is passed to generation and action callers and recorded in the identity and
result. Legacy per-problem runs retain their 8192 default.

`--no-require-review` disables both ordinary review and final review by default.
`--require-final-review` / `--no-require-final-review` independently override
the final audit. The effective ordinary-review setting is reflected in
`baseline.review_workflow`; both effective gates are recorded explicitly.
The rule-card `otc` baseline rejects enabled review gates because its action
surface does not implement that workflow.

For contest-session runs, `--rules-mode` defaults to `enforced` for `otc` and
`off` for other baselines. `--rules-root` selects the actual card directory.
`prompt_only` injects the selected card's agent-visible view, with evaluation
fields hidden, without enforcing its roster or enabling Coach behavior.
`enforced` is supported only by `otc`; requesting it for another baseline is
an explicit configuration error. Likewise, `otc` cannot silently become an
`off` or `prompt_only` run. Rule-root/strict flags with mode `off` are rejected.

When a requested card is absent, non-strict CLI runs write `rules_status.json`
with `rules_baseline_unavailable` and make no model calls or contest result.
`--rules-strict` instead raises a configuration error before any output writes.
Batch schedulers treat an unavailable card as blocked. Existing recorded runs
are not replaced with an unavailable-condition report.
