# Meeting follow-ups — 2026-08-05

Priorities from Yusen (this week):

1. **Turn budget in collaboration** — DONE  
   - Turn = time; each agent ≤ 1 LLM call/turn or `sleep`  
   - API calls = cost (`--max-api-calls`)  
   - Token caps = per-call + team-wide (`src/contest_budget.py`)  
   - Per-competition defaults: 50 turns; ICPC/IIOT 4K output/call placeholder  
   - Keep all three schemas as baselines

2. **Run baseline table** — next (live)  
   ```bash
   export PERPLEXITY_API_KEY=pplx-...
   python3 src/run_exam.py --all-schemas --rounds 2   # smoke
   # then larger: --rounds 50 with a small agent model
   ```
   Compare round_table / centralized / decentralized on the same problem.

3. **Help Sean integrate** — point him at [`docs/SOFTWARE_DESIGN.md`](SOFTWARE_DESIGN.md); resolve his PR conflicts (mostly requirements / registry).

4. **ICPC online judge** — spike: can we submit via Codeforces/Kattis/etc. and parse verdict text? Deferred after baselines unless blocked.

5. **Lab env-agent** — lower priority for the paper.

Show him: this note + `SOFTWARE_DESIGN.md` + `python3 src/main.py` offline proof of turn/API counters.
