# Meeting follow-ups — 2026-08-05

Priorities:

1. **Turn budget in collaboration** — DONE  
   - Turn = time; each agent ≤ 1 LLM call/turn or `sleep`  
   - API calls = cost (`--max-api-calls`)  
   - Token caps = per-call + team-wide (`src/contest_budget.py`)  
   - Per-competition defaults: 50 turns; ICPC/IIOT 4K output/call placeholder  
   - Keep all three schemas as baselines

2. **Run baseline table** — next (live)  
   ```bash
   export PERPLEXITY_API_KEY=pplx-...
   python3 src/run_smoke_batch.py --live --rounds 2   # all 20 families
   python3 src/run_exam.py --all-schemas --rounds 2   # ARML scored pilot
   ```
   Compare round_table / centralized / decentralized on the same problem.

3. **Integrate additional contests** — see [`docs/SOFTWARE_DESIGN.md`](SOFTWARE_DESIGN.md); resolve PR conflicts if any (requirements / registry).

4. **ICPC online judge** — spike: submit via Codeforces/Kattis/etc. and parse verdict text. Deferred after baselines unless blocked.

5. **Lab env-agent** — lower priority for the paper.

Reference: this note + `SOFTWARE_DESIGN.md` + `docs/TESTS_AND_RESULTS.md` + `python3 src/main.py` offline proof of turn/API counters.
