# OTC pipeline

Run from any directory with Bash, PowerShell, or CMD. Default scope is every
session in the 44-track benchmark catalog, OTC, gpt-5.4-mini, official card
budgets. Runs are serial. There is no pilot limit unless explicitly requested.

```bash
bash scripts/run_pipeline.sh all --output results/otc_pipeline_20260911
bash scripts/run_pipeline.sh report --output results/otc_pipeline_20260911
```

```powershell
scripts/run_pipeline.ps1 -Stage all -Output results/otc_pipeline_20260911
scripts/run_pipeline.ps1 -Stage report -Output results/otc_pipeline_20260911
```

CMD: `scripts\run_pipeline.cmd -Stage all -Output results/otc_pipeline_20260911`.
Set `PIPELINE_PYTHON` to override the Python interpreter.

Stages: `register` creates the complete registry and per-session manifests;
`run` executes that registry with identity-checked native resume and the artifact
runner's own resume checks; `report` reads saved results; `all` performs all stages.
Optional `--competitions arml_local,icpc` narrows execution without removing other
tracks from the registry. CLI `--limit N` is an explicit pilot only.

Outputs: `registry.json` includes all tracks and blocked input/adapter requirements;
`batch_status.json` records statuses and running commands; `logs/` has one log per
job; `runs/` retains native and artifact outputs; `summary.tsv` extracts scores
from the embedded grade/metrics fields, including blank rows for pending or
blocked sessions. Registered does not mean runnable or graded. External/live
environment tracks require dedicated adapters; no text-only stand-in is executed.
Artifact routes require a local task PDF and configured rubric. Native runs require
complete deterministic grading or a verified ICPC mapping and healthy Docker/gateway.

Reuse the same output root to resume compatible runs. Changed manifests or code
identities require a new output root. `pipeline.lock` prevents duplicate supervisors
in the same output root; after an abrupt kill verify the recorded PID is gone before
removing that one lock. Different roots must not share concurrent remote judging.

Deadline submission preserves available public task drafts; its selected version
and waived review gate are recorded in the contest events. Scoring and artifact
validation remain separate from submission eligibility.
