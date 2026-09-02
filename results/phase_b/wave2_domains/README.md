# Wave 2 — non-math domains

Same Phase B slice as math wave: **4 teams × 4 schemas = 16 cells per contest**.

| Contest | Domain | Problem | Grader |
|---|---|---|---|
| `ieo_business_case` | Economics | `ieo_business_case_2021` | slide deck rubric |
| `iol_team` | Linguistics | `iol_team_2005` | rubric LLM |
| `ioaa_group` | Astronomy | `ioaa_group_2025` | rubric LLM (+ partial gold) |
| `icpc` | Programming | `icpc_wf_2012_bottles` | sample judge |

**Cells:** 4 × 16 = **64**

## Run (Sean enforced — primary)

```bash
set -a && source .env && set +a

# Recommended: auto-resume + prevent Mac sleep + kill stalled cells
python3 scripts/watch_phase_b.py \
  --matrix results/phase_b/wave2_domains_enforced/phase_b_matrix.json \
  --stall-minutes 90 \
  -- \
  --suite wave2 --rules-mode enforced \
  --schemas single_agent,centralized,round_table,decentralized \
  --output results/phase_b/wave2_domains_enforced
```

One-shot daemon (no auto-restart):

```bash
python3 scripts/daemon_phase_b.py \
  --suite wave2 \
  --rules-mode enforced \
  --schemas single_agent,centralized,round_table,decentralized \
  --output results/phase_b/wave2_domains_enforced \
  --resume results/phase_b/wave2_domains_enforced/phase_b_matrix.json
```

## Meeting report

```bash
python3 scripts/summarize_phase_b_matrix.py \
  --markdown results/phase_b/wave2_domains_enforced/meeting_summary.md \
  results/phase_b/wave2_domains_enforced/phase_b_matrix.json
```

## Run (rules off — baseline comparison only)

```bash
python3 scripts/daemon_phase_b.py \
  --suite wave2 \
  --schemas single_agent,centralized,round_table,decentralized \
  --output results/phase_b/wave2_domains
```

## Monitor

```bash
tail -f results/phase_b/wave2_domains/phase_b_matrix.json  # after first cell
python3 -c "import json; d=json.load(open('results/phase_b/wave2_domains/phase_b_matrix.json')); print(d['ok'], '/', len(d['results']))"
```

## Resume

```bash
python3 src/run_phase_b_matrix.py --live --suite wave2 \
  --schemas single_agent,centralized,round_table,decentralized \
  --output results/phase_b/wave2_domains \
  --resume results/phase_b/wave2_domains/phase_b_matrix.json
```

## Notes

- `ijso_practical` is deferred: benchmark entries are placeholders (no problem text).
- Prefer `iol_team_2005` over `iol_team_2003` (2003 lacks problem description).
- Hypothesis: multi-agent helps more here than on ARML short-answer math.

## Benchmark design (Sean-style, wave 2)

| Layer | Math (Sean) | Economics / wave 2 (new) |
|---|---|---|
| Enforced comms | `max_message_chars`, message budgets | Same (from rule card) |
| Private reasoning | `open_table_coach` + `write_private_notes` | Same when `--rules-mode enforced` |
| Domain protocol | ARML team sheet reconciliation | **IEO two-phase schedule** (`simulation.phases`) |

**IEO phases** (enforced only): turns 1–20 = prep day (`web_search` ok, no `submit_final`); turns 21–30 = slide lock (no new research, submit allowed). Declared in `data/rules/ieo_business_case/collaboration.json`, enforced in `src/rules/phases.py`.
