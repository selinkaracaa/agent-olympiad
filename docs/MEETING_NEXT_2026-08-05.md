# Meeting follow-ups — updated 2026-08-21

See full notes: [`docs/MEETING_2026-08-21.md`](MEETING_2026-08-21.md)

## Reality gaps — status

1. **Wall-clock proxy** — DONE (MVP): duration→turns + `simulated_minutes`
2. **Live search + anti-cheat** — DONE (MVP): DuckDuckGo + leak block; lab/star fixtures when present
3. **ICPC sample judge + 20-min WA** — DONE (MVP): Kattis samples; secret tests deferred
4. **More gold contests** — DONE (MVP): ARML Local/National Team + Purple Comet HS 2018–2024

## Next experiment

Gold suite (not all 20): single-agent baseline + round_table / centralized / decentralized,
then homogeneous / heterogeneous models.

```bash
python3 collectors/fetch_icpc_samples.py --limit 20
python3 src/run_competition_batch.py --live --schema centralized \
  --competitions arml_local,arml_national_team,purple_comet,icpc
```

## Still open

- DomJudge / secret ICPC tests; C++/Java; shared-computer lock
- HMMT / Fyziklani curated shorts
- Single-agent equal-budget baseline wiring
- ≥5 collaboration baselines; hetero model teams
