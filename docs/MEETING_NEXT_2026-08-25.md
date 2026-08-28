# Meeting follow-ups — 2026-08-25

Notes from collaborator discussion after the ARML Local model×schema table.

---

## Takeaways

1. **MultiAgentBench CS is a useful baseline, not the final metric.**  
   Higher task score does **not** require higher CS (and often won’t). CS measures
   collaboration process; task score measures answer correctness. Keep both axes.

2. **On ARML (math), strong solos often beat or match multi-agent** (Claude / Gemini).  
   Possible causes: (a) contest type — math packets may not need much teamwork;
   (b) models may collaborate poorly under our protocols. Need more domains to separate
   these.

3. **Next science goal:** see when multi-agent > single-agent. Extend the same table
   beyond math (e.g. linguistics / astronomy / science practical / programming).

4. **Better collaboration metric (research follow-up, not blocking):**  
   Interaction-level eval — score each chat/action for whether it helped the final
   answer — instead of one global CS prompt. MultiAgentBench stays the published
   baseline until that exists.

5. **Baselines to keep:** `single_agent`, `centralized`, `round_table`, `decentralized`
   (+ homogeneous / hetero models). Expanding contests matters more than inventing
   new schemas right now.

---

## What to do now

### Already running (do not stop)

Full Phase B matrix: **5 gold contests × 4 teams × 4 schemas = 80 cells**  
Artifact: `results/phase_b/full_matrix/phase_b_matrix.json`  
Status as of 2026-08-25: **~36/80** (ARML Local + National Team done; Purple Comet in progress; HMMT + ICPC next).

Contests in this wave (mostly math / short-answer gold):

| Contest | Domain | Why |
|---|---|---|
| ARML Local | Math | Done — meeting table |
| ARML National Team | Math | Done |
| Purple Comet HS | Math | In progress |
| HMMT Guts | Math | Queued |
| ICPC bottles | Programming | Queued (sample judge) |

### Next experiment wave (after this 80 finishes)

Same 4 schemas × (gpt / claude / gemini / hetero), **contest-first**, prefer contests
outside pure short-answer math so multi-agent has a chance to help:

| Priority | Contest | Domain | Grader readiness |
|---|---|---|---|
| 1 | `iol_team` | Linguistics | Rubric LLM (no full gold shorts) |
| 2 | `ioaa_group` | Astronomy | Partial gold / rubric |
| 3 | `ijso_practical` | Science lab report | Rubric LLM |
| 4 | More ICPC / IIOT | Programming | Sample judge today; secret tests later |

Hypothesis to test: **on non-math / multi-modal / tool-heavy contests, multi-agent
beats equal-budget single-agent more often than on ARML.**

### Later (metric research)

- Prototype **interaction-level collaboration score** (label helpful vs unhelpful turns).  
- Compare against MultiAgentBench global CS on the same logs.  
- Do **not** block contest expansion on this.

---

## Immediate action

**Yes — keep running / extend experiments.**  

1. Let the current **80-cell** job finish (PID in `results/phase_b_live_run.pid`).  
2. Summarize National Team + Purple + HMMT + ICPC into the same style as the ARML table.  
3. Start wave 2 on **IOL / IOAA / IJSO** (or whichever has the cleanest grader) with the
   same schemas and models.

Commands (wave 2 sketch):

```bash
python3 scripts/daemon_phase_b.py \
  --competitions iol_team,ioaa_group,ijso_practical \
  --resume results/phase_b/wave2_domains/phase_b_matrix.json
```

(Wire those competition IDs into `PHASE_A_CASES` / `--competitions` once problem IDs
and graders are confirmed.)
