# Data collected — `art/`

Last updated: 2026-07-29

> **Pushable raw data is in git** under [`data/raw/`](../../data/raw/) (data only — no READMEs). `qanta.train.*.json` (177 MB) stays on HF because it exceeds the GitHub file limit; `qanta.dev` is in-repo.

**Current focus:** raw material collection only (problems, cases, rubrics, winning samples) for 9 proposed team competitions in humanities, arts appreciation, ethics debate, and business case (~5-agent teams). Official public sources; mirrored into `data/raw/<id>/`.

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published case set / problem release (one PDF or archive).  
**Question** = one case, problem, or scored item inside a year/session (e.g. one ethics case, one toss-up question, one debate speech).

---

## Summary

### Collected

| Competitions | Years/sessions | Questions |
|-------------:|---------------:|----------:|
| **9** | **126** | **~124,000** |

| ID | Competition | Domain | Years/sessions | Questions |
|----|-------------|--------|---------------:|----------:|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | Philosophy / Ethics | 9 (2021–2026 case sets) | ~140 cases |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | Ethics | **14** (2012–13 … 2025–26) | ~15 cases/set |
| `science_bowl` | DOE National Science Bowl | Science (buzzer quiz) | 33 sample-set groups (508 PDFs) | ~23,691 |
| `qanta` | QANTA Quiz Bowl | General knowledge | 1 (2021.12.20 release) | ~100,000 tossups |
| `gcch_harvard` | Global Case Competition at Harvard | Business (M&A / strategy) | 7 (2018–2026) | 7 cases |
| `cfa_research_challenge` | CFA Institute Research Challenge | Finance (equity research) | 19 (2008–2026) | 19 inferred company tasks + champion reports |
| `wharton_investment` | Wharton Global HS Investment Competition | Finance (portfolio, long-horizon) | 4 (2019–22 + current) | 4 case studies |
| `debatebench` | WUDC / BP Debate (DebateBench) | Debate | 45 debates | 360 scored speeches |
| `vis_moot` | Willem C. Vis Moot | International commercial law | 7 (26th–33rd editions) | 7 Problems |
| **Total** | | | **126** | **~124,000** |

---

## Simulator Matrix

For each competition, the AI agent must be given exactly the same resources a human team has. Rules below are based on the official documents downloaded into each folder and the source pages linked in the **Sources** column.

| ID | Full Name | Input Modality | Team Setup | Computers | Allowed Tools & Resources | Materials Provided | Final Deliverable | Sources |
|----|-----------|----------------|------------|-----------|--------------------------|-------------------|-------------------|---------|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | Case set PDF (released weeks in advance) | 5 agents | None during match | Cases studied in advance · during match: oral discussion only, no electronic devices · full rules & scoring guides in folder | Case set, rules PDF, judging/scoring guides | Oral presentation → opposing commentary → response → judge Q&A | [appe-ethics.org](https://www.appe-ethics.org/cases-rules-guidelines/) |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | Case set PDF (released in advance) | 3–7 agents | None during match | Same structure as APPE with a dialogic (non-adversarial) format · cases CC-licensed | National case set (15 cases + discussion questions) | Oral case discussion judged by rubric | [nhseb.org/case-library](https://nhseb.org/case-library) |
| `science_bowl` | DOE National Science Bowl | Question sets (read aloud; PDF here) | 4 agents + 1 alternate | None | No calculators · no reference materials · Toss-Up: **no conferring**; Bonus: team conferring allowed · buzzer-based | Toss-Up + Bonus question rounds (~25 questions/round) | Spoken short answers on buzzer | [science.osti.gov NSB](https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources) |
| `qanta` | QANTA Quiz Bowl | Pyramidal tossup text, revealed clue by clue | 4 agents | None | Clues revealed incrementally · earlier buzz = more knowledge credit · no external references · buzz-timing decision is part of the task | JSON question stream with answers & metadata | Answer at chosen buzz point, auto-judged | [qanta-org.github.io](https://qanta-org.github.io/data-and-code/) · [HF mirror](https://huggingface.co/datasets/TasnimKabir12/qanta) |
| `gcch_harvard` | Global Case Competition at Harvard | Case PDF | 2–5 agents | Unrestricted | Full internet & any software · winning decks from past editions serve as gold-standard references | Case PDF | Slide deck + recorded/live pitch | [thecasecompetition.org](https://www.thecasecompetition.org/past-editions) |
| `cfa_research_challenge` | CFA Institute Research Challenge | Assigned public company + public filings | 3–5 agents | Unrestricted | Full internet research · public company data · industry-standard rubric (valuation, writing, presentation) | Subject company; 19 years of champion reports as reference | 10-page equity research report (buy/sell) + oral defense | [cfainstitute.org](https://www.cfainstitute.org/insights/events/research-challenge/past-champions) |
| `wharton_investment` | Wharton Global HS Investment Competition | Client case study (HTML) + trading simulator | 4–7 agents | Online simulator | 10-week simulated portfolio management · full research allowed · client constraints defined in case | Client case study with background & investment constraints | Portfolio track record + final strategy report & defense | [globalyouth.wharton.upenn.edu](https://globalyouth.wharton.upenn.edu/investment-competition/) |
| `debatebench` | WUDC / British Parliamentary Debate | Motion text (revealed 15 min before round) | 8 agents (4 teams × 2) | None during prep | BP format: 15-minute prep after motion release · printed materials only, no internet during prep · 7-minute speeches in fixed order | Motion; 45 scored matches in `scores.xlsx` (32 with full transcripts) | 7-minute speech per agent; ranked by judges | [DebateBench on HF](https://huggingface.co/datasets/utkarsh2105/DebateBench) · [arXiv:2502.06279](https://arxiv.org/abs/2502.06279) |
| `vis_moot` | Willem C. Vis International Commercial Arbitration Moot | Problem PDF (60–90 pp. case record) | 2–8 agents | Unrestricted | Full legal research · months of preparation · Procedural Order No. 2 provides official clarifications · same structure as Jessup (pipeline reusable) | Problem + PO2 + current rules | Claimant & Respondent memoranda + oral pleading | [vismoot.org](https://www.vismoot.org/previous-moots/) |

---

## APPE Intercollegiate Ethics Bowl · `ethics_bowl_appe`

| | |
|---|---|
| **Domain** | Philosophy / Ethics (humanities) |
| **Years/sessions** | 9 case sets (2021 regional – 2026 national) |
| **Questions** | ~140 cases (~15–17 per set, each with discussion questions) |
| **Team size** | 5 students |
| **Time** | Cases released weeks in advance; timed oral rounds at match |
| **Answer type** | Oral: position statement → opposing commentary → response → judge Q&A |
| **Grading** | Judge rubric (argument quality, responsiveness to objections); official scoring guides included |
| **Source** | Advance case set; no electronic devices during match |
| **Link** | [appe-ethics.org/cases-rules-guidelines](https://www.appe-ethics.org/cases-rules-guidelines/) |
| **Data** | `data/raw/ethics_bowl_appe/` — 9 case sets + `rules-2025-national.pdf` / `rules-2025-regional.pdf` + judging/scoring guides (14 files) |
| **Notes** | Natural multi-turn adversarial structure; public rubric suits LLM-judge + human-eval hybrid. 2001–2021 Case Library exists on the official Google Drive, organized by 28 topics (incl. Art and Cultural Heritage) — see backlog. |

---

## National High School Ethics Bowl · `ethics_bowl_nhseb`

| | |
|---|---|
| **Domain** | Ethics (humanities) |
| **Years/sessions** | **14** National Case Sets (2012–13 … 2025–26) |
| **Questions** | ~15 cases + discussion questions per set |
| **Team size** | 3–7 students |
| **Time** | Cases released in advance; timed oral rounds at match |
| **Answer type** | Dialogic (non-adversarial) case discussion |
| **Grading** | Judge rubric, similar to APPE |
| **Source** | Advance case set (CC-licensed); no devices during match |
| **Link** | [nhseb.org/case-library](https://nhseb.org/case-library) · [National Case Set PDFs](https://nhseb.org/s/) |
| **Data** | `data/raw/ethics_bowl_nhseb/` — 14 National Case Set PDFs |
| **Notes** | Same structure as APPE at a lower difficulty tier — usable for curriculum. |

---

## DOE National Science Bowl · `science_bowl`

| | |
|---|---|
| **Domain** | Science — physics, chemistry, biology, earth science, energy, math (buzzer quiz) |
| **Years/sessions** | HS sample sets only (MS dropped), 1990s–2022 |
| **Questions** | **~11.6k HS** in full archive; primary eval is ≤20/year subsample (~140) |
| **Team size** | 4 students + 1 alternate |
| **Time** | Short timed buzzer rounds |
| **Answer type** | Spoken short answers; Toss-Up = no conferring, Bonus = team conferring allowed |
| **Grading** | Objective answers, auto-gradable; buzzer collaboration can be simulated |
| **Source** | No calculators, no references |
| **Link** | [science.osti.gov NSB resources](https://science.osti.gov/wdts/nsb/Regional-Competitions/Resources) |
| **Data** | `data/raw/science_bowl/` — `HS-Sample-Questions/` only |
| **Notes** | Toss-Up (individual decision) vs Bonus (team deliberation) is a built-in "individual vs team" controlled-comparison scenario. |

---

## QANTA Quiz Bowl · `qanta`

| | |
|---|---|
| **Domain** | General knowledge (humanities + sciences) |
| **Years/sessions** | 1 (2021.12.20 dataset release, train + dev) |
| **Questions** | ~100,000 pyramidal tossups with answers, category, tournament, and year metadata |
| **Team size** | 4 students |
| **Time** | Real-time: clues revealed hard-to-easy; earlier buzz = stronger knowledge signal |
| **Answer type** | Short answer at chosen buzz point |
| **Grading** | Automatic |
| **Source** | Incremental clue stream; no external references |
| **Link** | [qanta-org.github.io](https://qanta-org.github.io/data-and-code/) · [HF mirror TasnimKabir12/qanta](https://huggingface.co/datasets/TasnimKabir12/qanta) |
| **Data** | `data/raw/qanta/qanta.dev.2021.12.20.json` in git; train JSON (177 MB) → HF [`TasnimKabir12/qanta`](https://huggingface.co/datasets/TasnimKabir12/qanta) |
| **Notes** | Supports simulating a 4-agent team with per-category specialization plus buzz-timing decisions. |

---

## Global Case Competition at Harvard · `gcch_harvard`

| | |
|---|---|
| **Domain** | Business case — finance / M&A / strategy |
| **Years/sessions** | 7 official cases (2018–2026) |
| **Questions** | 7 (one open-ended case per edition) |
| **Team size** | 2–5 students |
| **Time** | Multi-day case window + pitch |
| **Answer type** | Slide deck + pitch |
| **Grading** | Judge rubric on deck + pitch; requires partial human evaluation |
| **Source** | Unrestricted internet & software |
| **Link** | [thecasecompetition.org/past-editions](https://www.thecasecompetition.org/past-editions) |
| **Data** | `data/raw/gcch_harvard/` — case PDFs + winning-team decks + `past-editions-page.html` (17 files) |
| **Notes** | Real M&A/strategy cases with winning decks as gold-standard references. |

---

## CFA Institute Research Challenge · `cfa_research_challenge`

| | |
|---|---|
| **Domain** | Finance — equity research reports |
| **Years/sessions** | 19 (2008–2026, one global champion per year) |
| **Questions** | 19 inferred subject-company tasks (`tasks.json`) + 19 champion written reports (+ defense presentations), 38 PDFs |
| **Team size** | 3–5 students |
| **Time** | Months-long: research → 10-page report → oral defense |
| **Answer type** | Buy/sell/hold equity research report on an assigned listed company + oral defense |
| **Grading** | Industry rubric (valuation, writing, presentation); real winning samples as ground truth |
| **Source** | Unrestricted public research |
| **Link** | [cfainstitute.org past champions](https://www.cfainstitute.org/insights/events/research-challenge/past-champions) |
| **Data** | `data/raw/cfa_research_challenge/` — `tasks.json` + 38 PDFs (Commonwealth Bank, Vestas, Canadian Tire, …) |
| **Notes** | **Task (same every year):** For a host-society–assigned publicly listed company, research using only public information and produce an approximately 10-page equity research report with a BUY / SELL / HOLD recommendation, then defend it orally. CFA Institute does **not** publish separate yearly problem statements on the Past Champions page—only winning reports and presentations—so subject companies in `tasks.json` are **inferred from each global champion’s written report** (the company that society assigned that year). Champion PDFs are gold references for pairwise / rubric judging, not inputs for the solver. Natural 3–5 agent role split: valuation / industry / writing / defense. |

---

## Wharton Global HS Investment Competition · `wharton_investment`

| | |
|---|---|
| **Domain** | Finance — investment strategy (long-horizon) |
| **Years/sessions** | 4 (2019–20, 2020–21, 2021–22 client case studies + current-season case) |
| **Questions** | 4 full case texts (client background + investment constraints) |
| **Team size** | 4–7 students |
| **Time** | 10-week simulated portfolio + final strategy report & defense |
| **Answer type** | Portfolio decisions over time + written strategy report |
| **Grading** | Strategy report & defense judged; portfolio performance observable |
| **Source** | Online trading simulator; full research allowed |
| **Link** | [globalyouth.wharton.upenn.edu](https://globalyouth.wharton.upenn.edu/investment-competition/) |
| **Data** | `data/raw/wharton_investment/` — `case-study-2019-2020/2020-2021/2021-2022.html` + `case-study-current.html` |
| **Notes** | **Best long-horizon candidate** — deterministic evaluation possible by replaying real historical market data. Analyst/PM role split for 4–7 agents. Past winning reports are scattered on Issuu/SlideShare (see backlog). |

---

## WUDC / BP Debate — DebateBench · `debatebench`

| | |
|---|---|
| **Domain** | Debate (humanities, adversarial) |
| **Years/sessions** | 32 British Parliamentary debates |
| **Questions** | 360 scored speeches across 45 debates (`scores.xlsx`); 32 debates also have full transcripts |
| **Team size** | 8 speakers per round (4 teams × 2) |
| **Time** | 15-minute prep after motion release; 7-minute speeches |
| **Answer type** | Structured speeches in fixed BP order |
| **Grading** | **Official judge speaker scores + team rankings included as ground truth** (`scores.xlsx`); Debatrix-style LLM-as-adjudicator reproducible |
| **Source** | Printed materials only during prep; no internet |
| **Link** | [DebateBench on HF](https://huggingface.co/datasets/utkarsh2105/DebateBench) · [arXiv:2502.06279](https://arxiv.org/abs/2502.06279) |
| **Data** | `data/raw/debatebench/` — `cleaned_speeches/` (32 transcript files) + `scores.xlsx` |
| **Notes** | The only humanities adversarial dataset here with official judge scores as ground truth. ~32k tokens per match → long-context, multi-party adversarial evaluation. |

---

## Willem C. Vis Moot (International Commercial Arbitration) · `vis_moot`

| | |
|---|---|
| **Domain** | International commercial law (humanities) |
| **Years/sessions** | 7 Problems (26th edition, 2019 → 33rd edition, 2026) |
| **Questions** | 7 (one full arbitration case record per edition, 60–90 pages: contracts, correspondence, witness statements; incl. Procedural Order No. 2 clarifications) |
| **Team size** | 2–8 students |
| **Time** | Months of preparation; written memoranda + oral rounds |
| **Answer type** | Claimant & Respondent memoranda + oral pleading |
| **Grading** | Memorandum + oral advocacy rubrics; past winning memoranda available (Pace database) for comparison |
| **Source** | Unrestricted legal research |
| **Link** | [vismoot.org/previous-moots](https://www.vismoot.org/previous-moots/) |
| **Data** | `data/raw/vis_moot/` — 7 Problems + 33rd-edition rules (8 PDFs) |
| **Notes** | Complete task chain: read case record → write both memoranda → oral rounds. Structurally identical to the Jessup competition already in the tracker — pipeline is reusable. |

---

## Collection backlog

| ID | Action |
|----|--------|
| `ethics_bowl_appe` | 2001–2021 Case Library on official Google Drive (28 topic categories, incl. Art and Cultural Heritage) |
| `ethics_bowl_nhseb` | National Case Sets 2012–13…2025–26 already in `data/raw/ethics_bowl_nhseb/`; optional: regional archives |
| `gcch_harvard` | Open the 9 untitled winning decks (`gcch_*.pdf`) to confirm edition and rename |
| `wharton_investment` | Past winning reports scattered on Issuu/SlideShare (not archived centrally by the organizer) |
| `vis_moot` | Earlier Problems (1994–2018) archived on per-edition pages at vismoot.org; winning memoranda from the Pace database |

---

## Evaluation design

The 9 competitions fall into three tiers by how objectively the deliverable can be scored. Every score reported from Tier 2/3 must be backed by the judge-validation step below.

### Tier 1 — Rule-based auto-grading

Closed-form answers; no judge needed.

| ID | Protocol |
|----|----------|
| `science_bowl` | Normalized exact match against official answers (accept listed alternate forms). Preserve the round protocol: Toss-Up = one agent answers with no conferring (individual decision), Bonus = team confers then answers — a built-in individual-vs-team controlled comparison. Score = official point rules (4/10 pts). |
| `qanta` | Reveal clues incrementally; team must decide **when to buzz** and what to answer. Metrics: answer accuracy + expected-wins-style buzz-position credit (earlier correct buzz scores higher, wrong early buzz penalized), following the official QANTA evaluation. Fully automatic. |
| `wharton_investment` (portfolio half) | Deterministic replay: execute the team's trade decisions against real historical market data for the 10-week window, scoring return / drawdown / constraint compliance against the client case's stated constraints. The strategy-report half falls under Tier 3. |

### Tier 2 — Reference-anchored comparison (gold samples or human scores exist)

| ID | Anchor | Protocol |
|----|--------|----------|
| `debatebench` | Official speaker scores + team rankings (`scores.xlsx`) | **This is the calibration set.** First validate an LLM adjudicator on the 360 human-scored speeches in `scores.xlsx` (Spearman vs official speaker scores; pairwise ranking accuracy on team rankings). Only a judge that passes this gate is used elsewhere. Then run agent teams in BP self-play (4 teams × 2 agents, 15-min-prep budget) and rank matches with the validated adjudicator. |
| `gcch_harvard` | 9 winning decks | Pairwise LLM-judge under the official criteria: agent deck vs champion deck, position-swapped, → win rate. A well-below-50% win rate is expected; track it over time rather than reading it as absolute quality. |
| `cfa_research_challenge` | 19 inferred company tasks + champion reports | Same pairwise protocol on the assigned company's report; rubric axes = valuation rigor / financial analysis / writing / presentation (the published CFA criteria). Champion reports double as few-shot references for the judge, not for the solver. |
| `vis_moot` | Winning memoranda (Pace database, backlog) | Pairwise memorandum comparison per edition (Claimant and Respondent scored separately) once winning memoranda are collected; until then falls back to Tier 3 rubric judging. |

### Tier 3 — Rubric-based judge panel (no gold reference)

| ID | Protocol |
|----|----------|
| `ethics_bowl_appe` / `ethics_bowl_nhseb` | Run the full adversarial match structure between **two agent teams** (presentation → opposing commentary → response → judge Q&A), not single-output grading. A panel of ≥3 LLM judges scores with the official judging/scoring guides included in the folder; team-vs-team outcomes aggregate into Elo across the case set. Self-play makes only relative ranking meaningful — which is exactly what the benchmark needs. |
| `wharton_investment` (report half) | Panel-judged against the official judging emphasis (strategy coherence, constraint fit, risk articulation); combined score = weighted portfolio replay (Tier 1) + report rubric. |

### Judge validation & bias controls

- **Gate:** every LLM judge configuration must first pass the `debatebench` calibration (target: Spearman ≥ 0.5 with official speaker scores, pairwise team-ranking accuracy meaningfully above chance) before its Tier 2/3 scores are trusted.
- **Position bias:** all pairwise comparisons run twice with order swapped; disagreements count as ties.
- **Verbosity bias:** enforce the competition's own length limits (page/time caps from the rules PDFs) before judging; over-limit output is truncated, mirroring real rules.
- **Panel:** ≥3 judge models (or 3 prompts) with score averaging; report inter-judge agreement alongside results.

### Team-level metrics (all tiers)

Besides deliverable quality, log per run: turn/token budget consumed, number of inter-agent messages, role-specialization entropy (how unevenly work is distributed), and a solo-agent baseline with the same total budget — the headline claim of the benchmark is the team-vs-solo delta, not the absolute score.

### Contamination note

QANTA (2021 release), DebateBench transcripts, and older case sets predate current model training cutoffs — assume memorization. Prefer the newest sessions (2025–26 case sets, 33rd Vis Problem, current Wharton case) for headline numbers, and use older years as development splits.
