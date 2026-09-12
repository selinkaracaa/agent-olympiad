# Vallina OTC: basic Open Table Coach + rule card

Canonical baseline: `vallina_otc` (user-requested spelling). `vanilla_otc` is an
alias. Existing `vanilla` / `vanilla_team` still mean `decentralized`.
The full `otc` preset and its mandatory review contract remain unchanged.

## Experimental contract

| Mechanism | vallina_otc | otc |
| --- | --- | --- |
| Single blind turn-0 Coach | Yes | Yes |
| Contest rule card, roster and submission permissions | Yes | Yes |
| Communication/resource limits and programming isolation | Yes | Yes |
| Current-turn private thinking call | Yes | Yes |
| Public conversation and current drafts | Yes | Yes |
| Explicit memory tools and retrieval | No | Yes |
| Historical private-thought reinjection | No | Yes |
| Direct private messages | No | Yes |
| Mandatory peer approval | No | Yes |
| Structured proposals/challenges/decisions | No | Card-dependent |
| Enforced strategic discussion after work | No | Card-dependent |
| PDF validation and the separate final judge | Same implementation | Same implementation |

Voluntary checking happens through ordinary public discussion. Basic OTC is
not stateless: current drafts, bounded ordinary conversation, tool errors,
scores and resource state remain visible. Its backend event log is still kept
for audit, replay, rule enforcement and checkpoints; this is not the explicit
agent memory/retrieval treatment. Private thinking is logged for audit, but
only the current turn's latest thought is shown to its subsequent action call.

The original rule card is validated and fingerprinted unchanged. A pure runtime
overlay removes enhanced strategic requirements and exposes the effective basic
collaboration profile in Coach/contestant prompts. It does not rewrite official
card files or relax roster, submission-role, communication or workstation rules.

For artifact tasks, work must still produce a valid rendered candidate. Submit
freezes the current candidate PDF; the judge scores that PDF with no post-hoc
editor. Basic OTC does not require a teammate approval. Failed rendering or no
candidate still means no graded artifact. This does not repair pre-existing
renderer, dataset, or rubric limitations.

## Usage

```powershell
# Native contest, one shared engine
..\.venv\Scripts\python.exe src/run_competition_batch.py --live --contest-manifest data/contest_manifests/arml_local_2009.json --system-variant vallina_otc --provider perplexity --model openai/gpt-5.4 --output results/arml_2009_vallina_otc

# Artifact preflight only: no paid calls
..\.venv\Scripts\python.exe src/run_otc_artifact.py --competition wsc_writing --task-pdf results/wsc_writing_gq_001_otc_pilot/input/task.pdf --system-variant vallina_otc --output results/wsc_vallina_otc --prepare-only
```

Both CLIs record the resolved baseline in run identity. Cross-baseline resume
must fail. Use fresh output directories for comparisons and match the task,
model, judge, roster, card, turn budget, call budget and scoring scope. Token
budgets are engine output-token accounting, not a total input-plus-output cost
cap; record provider usage separately.

This is a bundled ablation of enhanced collaboration, not a memory-only ablation.
A score difference cannot be attributed to memory alone. No paid basic-OTC run
or improvement claim is part of this implementation change.

## Existing experiments

Pre-change Python sources and rule cards were preserved at
`E:/agent_olympiad/run_source_snapshots/pre_vallina_otc_20260910`, with a source
hash manifest. Existing processes are not restarted or relabeled. If an old run
needs recovery, restore/use its matching source environment; do not bypass the
run-identity check to resume it with this changed code.
