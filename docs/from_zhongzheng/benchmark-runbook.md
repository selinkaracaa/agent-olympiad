<!-- markdownlint-disable MD060 -->

# Benchmark runbook

This is the operational guide for protocol `contest_session_v6`. Commands use
PowerShell from the repository root.

## 1. Prerequisites

- Python environment with `requirements.txt` installed.
- Provider credentials in `.env` or the process environment.
- Docker available for isolated programming sample execution.
- VJudge/Kattis credentials and local gateway for remote ICPC runs.

Typical setup:

```powershell
cd e:\agent_olympiad\agent-team-features-main
..\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill the provider and judge credentials required by the intended run. Do not
commit `.env`.

Basic checks:

```powershell
python src\run_competition_batch.py --help
$env:PYTHONPATH = "src;tests;scripts"
python -m unittest discover -s tests -q
```

## 2. Choose the current execution path

For new experiments always provide:

```text
--contest-manifest <manifest.json>
--system-variant <single_agent|decentralized|centralized|otc>
```

Do not use `--schema open_table_coach`; that is the retired per-problem stack.

Canonical baseline names:

- `single_agent`
- `decentralized`
- `centralized`
- `otc`

Legacy names still parse but should not appear in new scripts.

## 3. Inspect or create a manifest

Existing manifests are under:

```text
data\contest_manifests\
data\contest_manifests\generated\
```

Minimal form:

```json
{
  "session_id": "example_2026",
  "competition_id": "arml_local",
  "problem_ids": ["arml_local_2012"],
  "split_parts": true,
  "question_ids": ["1", "2", "3"]
}
```

Rules:

- every `problem_id` must exist in
  `data/benchmarks/<competition>/benchmark.json`;
- preserve official contest grouping where metadata permits;
- use `split_parts` only when one packet contains separately graded numbered
  parts;
- never put answer keys or solution text into prompt overrides.

Generate structured-gold manifests without running the complete suite:

```powershell
python -c "import sys; sys.path.insert(0,'scripts'); from run_otc_gold_suite import write_manifests; print(len(write_manifests(['mystery_hunt'])))"
```

Current natural grouping:

- Science Bowl: official parent packet;
- QANTA: year + tournament;
- Mystery Hunt: year;
- ARML packet competitions: one published round, split into questions.

## 4. Run one contest

### 4.1 OTC

```powershell
python -u src\run_competition_batch.py `
  --live `
  --provider perplexity `
  --model openai/gpt-5.4-mini `
  --contest-manifest data\contest_manifests\arml_local_2010.json `
  --system-variant otc `
  --action-calling auto `
  --output results\arml_local_2010_otc_v6
```

For OTC:

- the rule card defaults to enforced;
- roster and contest clock default from the competition/card;
- a missing required card fails closed;
- one blind Coach call occurs before contest time;
- the card may add private think calls, memory, deliberation, message budgets,
  workstation lease, or judge latency.

### 4.2 Decentralized baseline

```powershell
python -u src\run_competition_batch.py `
  --live `
  --provider perplexity `
  --model openai/gpt-5.4-mini `
  --contest-manifest data\contest_manifests\arml_local_2010.json `
  --system-variant decentralized `
  --action-calling auto `
  --team-size 6 `
  --output results\arml_local_2010_decentralized_v6
```

`vanilla_team` is only an alias for `decentralized`.

### 4.3 Centralized and single-agent

Change only:

```text
--system-variant centralized
```

or:

```text
--system-variant single_agent --team-size 1
```

In centralized runs, `Agent_1` plans first, may reassign workers, and alone can
submit.

## 5. Run a matched comparison

A valid baseline comparison holds constant:

- manifest and ordered task set;
- provider, model, temperature, and output-token limit;
- team size, except the inherently one-seat `single_agent`;
- contest clock, turn limit, simulated minutes;
- API-call and shared token ceilings;
- action transport;
- judge settings;
- starting seat;
- programming deadline policy.

Only `--system-variant` should change.

Use explicit budgets when exact matching matters:

```powershell
$common = @(
  "--live",
  "--provider", "perplexity",
  "--model", "openai/gpt-5.4-mini",
  "--contest-manifest", "data\contest_manifests\arml_local_2010.json",
  "--action-calling", "native",
  "--team-size", "6",
  "--max-turns", "9",
  "--max-api-calls", "109",
  "--max-total-tokens", "220000",
  "--start-seat", "0"
)

python -u src\run_competition_batch.py @common `
  --system-variant otc --output results\pair\arml_2010_otc

python -u src\run_competition_batch.py @common `
  --system-variant decentralized --output results\pair\arml_2010_decentralized
```

The same ceiling does not imply the same consumption. OTC normally spends calls
on Coach/private think/review; decentralized may finish below the ceiling.

## 6. Structured-gold batches

Run generated manifests for selected competitions:

```powershell
python -u scripts\run_otc_gold_suite.py `
  --competitions arml_local `
  --system-variant otc `
  --output results\gold_v6_otc
```

Matched decentralized batch:

```powershell
python -u scripts\run_otc_gold_suite.py `
  --competitions arml_local `
  --system-variant decentralized `
  --team-size 6 `
  --output results\gold_v6_decentralized
```

Run each competition separately when matching its official/card roster; the
card defaults differ across competitions. Without an explicit
`--team-size`, the batch helper uses the OTC card default for OTC and three
seats for non-OTC baselines. A mixed-competition decentralized command is
therefore not automatically roster-matched.

Useful options:

- `--limit N`: smoke-test the first N generated sessions;
- `--team-size N`: explicit override; OTC validates the card range;
- the same output root resumes/skips only identity-matching sessions.

Start with `--limit 1` before a paid sweep.

## 7. ICPC full-contest pairs

### 7.1 Start the local gateway

```powershell
python -u src\vjudge_gateway.py serve --port 8787
```

Health check:

```powershell
python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8787/v1/health').read().decode())"
```

### 7.2 Run all configured World Finals pairs

```powershell
python -u scripts\run_all_icpc_full_pairs.py `
  --output-root results\icpc_full_pairs_v6 `
  --start-year 2012 `
  --end-year 2025
```

The scheduler:

- groups all remote-ready problems by World Finals year;
- creates one full-contest manifest per year;
- runs `otc` and `decentralized`;
- checks gateway health before each job;
- validates run identity before skip/resume;
- writes `batch_status.json`, per-job logs, and run directories.

It enables programming deadline submission. Read that flag in the result before
interpreting remote attempts.

To omit separately verified years:

```powershell
python -u scripts\run_all_icpc_full_pairs.py `
  --output-root results\icpc_full_pairs_v6 `
  --skip-year 2012
```

## 8. Resume and output safety

For a direct interrupted run:

```powershell
python src\run_competition_batch.py <same arguments> `
  --resume `
  --output <same-directory>
```

Resume succeeds only when the fingerprint matches. It rejects:

- changed source under `src/`;
- changed manifest/task content;
- changed rule card;
- changed model, baseline, budgets, judges, transport, or generation settings;
- mismatched protocol/action versions;
- corrupt or legacy artifacts without a valid identity.

Use a new output directory for any changed experiment.

## 9. Read the results

### 9.1 `run_config.json`

Read this first. It contains resolved settings and the run fingerprint.

### 9.2 `contest_checkpoint.json`

Intermediate resumable state:

- serialized `ContestSession`;
- full `ContestMemory`;
- protocol/action versions and identity.

### 9.3 `contest_session.json`

Final source of truth:

- `run`, `config`, baseline features, rule-card record;
- tasks, versions, reviews, submissions, and final state;
- complete visibility-tagged event archive;
- budget and timing;
- action transport log;
- diagnostics and protocol-specific counters;
- grade and evaluation coverage;
- Communication, Planning, CS, AAR, and AB.

### 9.4 Batch files

Depending on the scheduler:

- `summary.tsv`;
- `manifest_index.json`;
- `batch_status.json`;
- `completed_metrics.tsv`;
- per-job logs.

Batch summaries are provenance checked. A stale file in an output directory is
not automatically counted as a current completion.

## 10. Common controls

| Flag | Meaning |
|---|---|
| `--live` | Use the real model provider; omit for mock/offline paths |
| `--provider` / `--model` | Contestant model |
| `--max-output-tokens` | Per-call generation limit |
| `--max-turns` | Override derived contest rounds, hard-capped by resolver |
| `--max-api-calls` | Shared model-call ceiling |
| `--max-total-tokens` | Shared output-token ceiling |
| `--max-simulated-minutes` | Simulated contest clock ceiling |
| `--start-seat` | Rotate first acting seat |
| `--action-calling` | `auto`, `native`, `emulated`, or compatibility `prompt-json` |
| `--judge-task` | Run registered task judge |
| `--judge-collab` | Compute Communication/Planning/CS |
| `--judge-cce` | Add optional causal action-graph judge |
| `--programming-deadline-submit` | Submit eligible recorded programming candidates at deadline |
| `--resume` | Reuse only an identity-matching output |

For OTC, do not override review or rule mode in normal benchmark runs. Such
overrides are ablations and must be labeled as ablations.

## 11. Troubleshooting

### No actions or immediate configuration failure

- Confirm the manifest ids exist in the benchmark.
- Confirm OTC has `data/rules/<competition>/collaboration.json`.
- Check team-size range in the card.
- Inspect `rules_status.json` and `run_config.json`.

### Run will not resume

Read the compatibility error. Do not bypass it. Source/config/card changes
require a fresh output directory.

### ICPC produces PENDING or no official verdict

- probe `/v1/health`;
- confirm VJudge/Kattis credentials;
- inspect gateway logs;
- check whether the card's judging-latency round has elapsed;
- distinguish `SAMPLE_WA/RE` from a remote submission;
- inspect workstation lease and pending-verdict events.

### API calls look larger than turns

One turn contains several seats. OTC can also add private think calls and a
turn-0 Coach call. Emulated tool corrections add calls to
`budget.api_calls_used`. Post-run LLM judges create additional provider calls,
but they are outside that contest budget field.

### A run completed but has no usable score

Check `grade.evaluation_coverage` and per-task status. Completion and grade
availability are separate.

### Generated session counts look too high

Do not interpret benchmark row count as contest count. Regenerate manifests
with `run_otc_gold_suite.py`; question-level Science Bowl, QANTA, and Mystery
Hunt rows are grouped into natural sessions.

## 12. Before publishing numbers

Verify:

1. both variants have matching run identities except baseline-specific fields;
2. protocol/action versions are current and equal;
3. task and rule-card hashes match;
4. no session is `blocked`, `invalid`, `pending`, or ungraded unintentionally;
5. remote verdicts are valid and not only local sample results;
6. session count means contest sessions, not agents or raw benchmark rows;
7. cost columns report API calls and output tokens separately from turns;
8. historical results are labeled with their original protocol.
