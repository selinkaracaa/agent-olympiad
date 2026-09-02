# Enforced-rules matrix (Sean method)

**Command:** `--rules-mode enforced` with the same 4×4 Phase B slice.

| Setting | Value |
|---|---|
| Contests | ARML Local, ARML National Team, Purple Comet HS |
| Teams | gpt, claude, gemini, hetero |
| Schemas | single_agent, centralized, round_table, decentralized |
| Cells | **48** (3 × 16) |

## Monitor

```bash
tail -f results/phase_b/enforced_matrix/run.log
python3 -c "import json; d=json.load(open('results/phase_b/enforced_matrix/phase_b_matrix.json')); print(len(d['results']), 'ok', d.get('ok'))"
```

## Resume if interrupted

```bash
export PERPLEXITY_API_KEY=...
python3 src/run_phase_b_matrix.py --live --rules-mode enforced \
  --competitions arml_local,arml_national_team,purple_comet \
  --schemas single_agent,centralized,round_table,decentralized \
  --output results/phase_b/enforced_matrix \
  --resume results/phase_b/enforced_matrix/phase_b_matrix.json
```

## Compare to rules-off matrix

Old results: `results/phase_b/full_matrix/phase_b_matrix.json` (`rules_mode: off`)

Pilot comparison (1 cell): `results/rules_enforced_compare/comparison.md`
