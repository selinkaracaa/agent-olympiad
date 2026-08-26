# Data collected — `olympiad/`

Last updated: 2026-07-29

> **Pushable raw data is in git** under [`data/raw/`](../../data/raw/) (data files only — no READMEs). Formal catalog JSON is under [`data/benchmarks/`](../../data/benchmarks/). Multi-GB packs (`CodeContests`, `Cybench`, `NYU_CTF_Bench`, `MIT_Mystery_Hunt`) and files ≥95 MB stay **on demand** — see [Downloading](#downloading).

**Current focus:** multi-agent **team** competitions (ICPC-style coding, CTF, modeling, olympiad Team/Group rounds, debate, moot, ethics bowl, puzzle hunt, …). Solo Origin=1 packs were removed. Grading type is marked per row in the [Simulator Matrix](#simulator-matrix) (**RULE** = auto-graded; **RUBRIC** = open-ended / jury).

**Suite size:** native multi-agent / team contests only (solo Origin=1 packs removed). Pushable originals → `data/raw/`; oversized → fetch on demand.

**Competition** = one contest type (one row in the tracker).  
**Year/session** = one published contest release, split, or benchmark edition (e.g. one CTF set, one COMAP problem, one IOAI year).  
**Question** = one scored problem / task / conversation / paper leaf inside a year/session.

**Team size notation** (matrix + deep-dive cards):
- **Origin** — how many humans the real contest uses (official rules).
- **Rec** — recommended agent count for multi-agent simulation. For native team contests, Rec usually matches Origin; for hybrid contests (Individual + Team/Group), Rec is listed per track.

---

## Simulator Matrix

For each competition, the AI agent team must be given the same resources a human competitor (or human team) would have in the origin setting. Rules below are taken from the upstream benchmark papers / contest regulations and the source pages linked in **Sources**.

| ID | Full Name | Grading | Origin | Rec (sim) | Input Modality | Computers | Allowed Tools & Resources | Final Deliverable | Sources |
|----|-----------|---------|--------|-----------|----------------|-----------|--------------------------|-------------------|---------|
| `CodeContests` | CodeContests (AlphaCode) | RULE | 3 (ICPC-style) | 3 (shared machine + penalty queue) | Contest problem text | 1 shared machine | Hidden tests · wrong-submit penalty | Accepted code | [HF](https://huggingface.co/datasets/deepmind/code_contests) |
| `NYU_CTF_Bench` | NYU CTF Bench (CSAW) | RULE | 4–6 (typical CTF team) | 4–6 (by category) | Challenge brief + Docker | Required | CTF tooling in container | Flag string | [GitHub](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench) |
| `Cybench` | Cybench | RULE | 4–6 (typical CTF team) | 4–6 (by category / subtask) | Challenge brief + Docker | Required | Professional CTF tooling | Flag + subtask progress | [GitHub](https://github.com/andyzorigin/cybench) |
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | RUBRIC | 3–4 (COMAP) | 3–4 | Open-ended modeling statement | Unrestricted | Multi-day open-book | Modeling paper | [COMAP](https://www.comap.com/contests) |
| `cfa_research_challenge` | CFA Institute Research Challenge | RUBRIC | 3–5 | 3–5 | Public company + filings | Unrestricted | Full market research | Equity report + defense | See [`art/README.md`](../art/README.md) |
| `gcch_harvard` | Global Case Competition at Harvard | RUBRIC | 2–5 | 2–5 | Case PDF | Unrestricted | Full internet | Deck + pitch | See [`art/README.md`](../art/README.md) |
| `wharton_investment` | Wharton Global HS Investment Competition | RULE + RUBRIC | 4–7 | 4–7 | Client case + simulator | Online simulator | 10-week portfolio | Track record + strategy report | See [`art/README.md`](../art/README.md) |
| `vis_moot` | Willem C. Vis Moot | RUBRIC | 2–8 | 2–8 | 60–90 pp. case record | Unrestricted | Full legal research | Memos + oral pleading | See [`art/README.md`](../art/README.md) |
| `debatebench` | WUDC / BP Debate (DebateBench) | RUBRIC | 8 (4×2) | 8 | Motion (15 min prep) | None during prep | Printed materials only in prep | Speeches ranked by judges | See [`art/README.md`](../art/README.md) |
| `ethics_bowl` | APPE + NHSEB Ethics Bowl | RUBRIC | APPE 5 · NHSEB 3–7 | 5 (APPE) / 3–7 (NHSEB) | Case set PDF | None during match | Oral discussion only at match | Oral case presentation | See [`art/README.md`](../art/README.md) |
| `ioai` | Intl. Olympiad in AI | RULE + RUBRIC | Indiv. 1 · Team Challenge national team | Indiv. Rec 3 · Team Rec 3–5 | Notebooks + datasets / Team brief | Required (GPU) for Individual | Contest data + ML stack | Predictions / Team artifact | [HF IOAI2025](https://huggingface.co/datasets/IOAI-official/IOAI2025) · [GitHub](https://github.com/IOAI-official) |
| `eoes` | EOES / EUSO | RUBRIC | 3 | 3 | Lab protocols + answer sheets | Lab benches (no personal computers) | Organizer equipment | Answer sheets / lab report | [EUSO](http://euso.eu/about/experiments/) · [EOES](https://www.eoes.science/Previous%20olympiads/previous.html) |
| `ichto` | International Chemistry Tournament | RUBRIC | 3+ (Reporter / Opponent / Reviewer) | 3+ (role rotation) | Open chemistry problem set | Prep: laptops; fights: on-site | Literature in prep | Oral report + opposition / review | [ichto.org](http://ichto.org/en/problems/) |
| `pumac_power` | PUMaC Power Round | RUBRIC | 8 | 8 | Multi-part proof packet | Unrestricted in window | Team collaboration · no outside humans | Written proof packet | [PUMaC Archives](https://jason-shi-f9dm.squarespace.com/archives) |
| `mystery_hunt` | MIT Mystery Hunt | RULE | 5–150 (specialty squads) | 8–20 for lab sims (scale as needed) | Web / PDF / multimedia puzzles | Shared workstations | Full internet · arbitrary tooling | Puzzle → meta → coin | [puzzles.mit.edu](https://puzzles.mit.edu/) · [mh_answers](https://github.com/dgulotta/mh_answers) |
| `iol` | International Linguistics Olympiad | RULE | Indiv. 1 · Team Contest 4 | Indiv. Rec 2–3 · Team Rec 4 | Problem PDFs | None | Paper & pencil · no devices | Written answers / rule inferences | [ioling.org](https://ioling.org/problems/by_year/) · [HF](https://huggingface.co/datasets/agurung/ioling) |
| `history_olympiad` | International History Olympiad | RULE + RUBRIC | Bee 1 · Bowl team | Bee Rec 2–3 · Bowl Rec 4 | Bee/Bowl + written exams | None for bees | Study guides · timed rounds | Short answers / essays | [historyolympiad.com](https://www.historyolympiad.com/resources/) |
| `ieo` | International Economics Olympiad | RULE + RUBRIC | Econ 1 · Business Case 3–5 | Econ Rec 2–3 · Case Rec 3–5 | Problem sets + case PDFs | Unrestricted for case | Research on Business Case | Numeric answers + case deck | [IEO prepare](https://ieo-official.org/prepare) |
| `ioaa` | Intl. Olympiad on Astronomy & Astrophysics | RULE | Indiv. 1 · Group 5 | Indiv. Rec 2–3 · Group Rec 5 | Theory / data / observation / group | Organizer calculator only | Constants · charts · data tables | Boxed numerical answers | [IOAA past](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | RUBRIC | 3 | 3 | 3–4 prompts | None (devices banned) | Handwritten staged collab | 3 essays (one per writer) | [WSC Events](https://scholarscup.org/events/) |
| `ARC-AGI-2` | ARC Prize / ARC-AGI-2 | RULE | team (prize) | 3 (hypothesize / verify / program) | Few-shot grid puzzles | Required | Code + search over programs | Output grid | [GitHub](https://github.com/arcprize/ARC-AGI-2) · [arcprize.org](https://arcprize.org) |
---

## CodeContests · `CodeContests/` (on demand)

| | |
|---|---|
| **Domain** | Competitive programming — Codeforces / ICPC-style (AlphaCode training data) |
| **Years/sessions** | Multi-year contest archive |
| **Questions** | **13,610** (train 13,328 · valid 117 · test 165) |
| **Team size** | **Origin: 3** (ICPC-style) · **Rec: 3** (shared machine + penalty queue) |
| **Time** | ICPC-style contest window with time penalty |
| **Answer type** | Source code accepted by hidden judge |
| **Grading** | Hidden test cases |
| **Source** | One shared machine; languages as in ICPC-style settings |
| **Link** | [HF: deepmind/code_contests](https://huggingface.co/datasets/deepmind/code_contests) |
| **Data** | ⏳ on demand (~7.6 GB) — see [Downloading](#downloading) |
| **Notes** | Best fit for simulating a real 3-person programming team under a shared penalty budget. |

---

## NYU CTF Bench · `NYU_CTF_Bench/` (on demand)

| | |
|---|---|
| **Domain** | Cybersecurity — CSAW capture-the-flag |
| **Years/sessions** | CSAW CTF challenge archive (NeurIPS 2024 benchmark) |
| **Questions** | 200 across 6 categories (web, pwn, forensics, rev, crypto, misc) |
| **Team size** | **Origin: 4–6** (typical CTF team) · **Rec: 4–6** (split by category) |
| **Time** | Open-ended within challenge Docker lifetime |
| **Answer type** | Exact flag string |
| **Grading** | Exact flag match inside the challenge's Docker environment; fully automatic |
| **Source** | Full CTF tooling inside the container; challenges cloned on first use |
| **Link** | [GitHub NYU-LLM-CTF/NYU_CTF_Bench](https://github.com/NYU-LLM-CTF/NYU_CTF_Bench) · [site](https://nyu-llm-ctf.github.io/) |
| **Data** | ⏳ on demand — `pip install nyuctf`; challenges cloned on first `CTFDataset(split=...)` call |
| **Notes** | Log which specialist solved each flag for role-specialization metrics. |

---

## Cybench · `Cybench/`

| | |
|---|---|
| **Domain** | Cybersecurity — professional CTF (HackTheBox / Sekai / HKCERT) |
| **Years/sessions** | 1 (Cybench release) |
| **Questions** | **40** tasks with subtask decomposition (local packs under HackTheBox / Project Sekai / HKCERT) |
| **Team size** | **Origin: 4–6** (typical CTF team) · **Rec: 4–6** (category / subtask split) |
| **Time** | Open-ended within per-task Docker |
| **Answer type** | Flag (+ intermediate subtask checkpoints) |
| **Grading** | Flag match + per-subtask checks in Docker |
| **Source** | Per-task Docker images with professional CTF tooling |
| **Link** | [GitHub andyzorigin/cybench](https://github.com/andyzorigin/cybench) · [cybench.github.io](https://cybench.github.io) · [arXiv:2408.08926](https://arxiv.org/abs/2408.08926) |
| **Data** | ⏳ on demand (~2 GB) — clone Cybench; per-challenge folders + Docker for interactive web/pwn eval |
| **Notes** | Harder / more professional tier than NYU CTF Bench. For **problem-only** use: take `README` + `challenge`/`dist` + prompts; hide `metadata/solution` and `answer` fields. Full agent eval still needs the Cybench runner + Docker. |

---

## Math modeling contests · `modeling_agent/`

| | |
|---|---|
| **Domain** | Applied math modeling — statistics, optimization, simulation, data analysis |
| **Years/sessions** | 2001–2025 across 5 contest series: MCM (24), ICM (20), HiMCM (19), MidMCM (3), IM2C (2) |
| **Questions** | 68 full modeling problems (Middle School 3 · High School 21 · Undergraduate 44) |
| **Team size** | **Origin: 3–4** (COMAP) · **Rec: 3–4** |
| **Time** | Multi-day contest window (typically 4 days / 14 days depending on series) |
| **Answer type** | Open-ended modeling paper: assumptions, model, analysis, recommendations |
| **Grading** | Rubric-based; each problem annotated with per-category `requirements` (grading points) for LLM-judge scoring |
| **Source** | Open-book: unrestricted internet, software, and references during contest |
| **Link** | [COMAP contests](https://www.comap.com/contests) |
| **Data** | `data/raw/modeling_agent/modeling_data_final.json` — 68 entries keyed by `year_title`; fields: `year`, `title`, `level`, `source`, `link`, `question` (with inline image descriptions), `requirements`, `eval_roles`, `decomposition` |
| **Notes** | Each problem ships with **suggested evaluator roles** (e.g. Mathematician / Data Scientist / domain expert) and a **decomposition into grading points** — directly usable to build a multi-agent solver plus an LLM-judge panel. Natural fit for 3–4 agent team simulation with role split. |

---

## Newly collected olympiads

Real competitions added for multi-agent coverage. Pushable files under [`data/raw/`](../../data/raw/).

### Batch 2026-07-21a — team STEM / AI / puzzle

Five contests: `ioai`, `eoes`, `ichto`, `pumac_power`, `mystery_hunt` (cards below).

### Batch 2026-07-21b — diversity domains

Nine contests filling linguistics, geography, earth science, philosophy, history, economics, astronomy, and collaborative writing.

### IOAI · `IOAI/`

| | |
|---|---|
| **Domain** | Artificial intelligence olympiad — ML, CV, NLP + Team Challenge |
| **Years/sessions** | 2024 (Burgas), 2025 (Beijing), 2026 (Astana) |
| **Questions** | **17** tasks (deduped local packs; `IOAI2025/` HF mirror not double-counted) |
| **Team size** | **Origin:** Individual **1** · Team Challenge national team · **Rec:** Individual **3** · Team **3–5** |
| **Time** | At-home + on-site Individual windows; Team Challenge timed on-site |
| **Answer type** | Model predictions / code notebooks (Individual); Team Challenge artifact (robotics / generative) |
| **Grading** | Task metrics on hidden tests for Individual; rubric / jury for Team Challenge |
| **Source** | Contest-provided data only; Python + standard ML stack |
| **Link** | [HF: IOAI-official/IOAI2025](https://huggingface.co/datasets/IOAI-official/IOAI2025) · [GitHub 2024](https://github.com/IOAI-official/IOAI-2024) · [2025](https://github.com/IOAI-official/IOAI-2025) · [2026](https://github.com/IOAI-official/IOAI-2026) · [Resources](https://ioai-official.org/resources/) |
| **Data** | `data/raw/ioai/` — Team Challenge + task packs in git; `Practical-Round-problems.zip` (120 MB) fetch from IOAI-official (skipped for GitHub limit) |
| **Notes** | Best new multi-agent AI olympiad with official datasets. Pair ML-specialist agents on Individual tasks; use a separate robotics / planning team for the Team Challenge. CC-BY-4.0. |

---

### EOES / EUSO · `EOES/`

| | |
|---|---|
| **Domain** | Interdisciplinary experimental science (physics + chemistry + biology practicals) |
| **Years/sessions** | EUSO 2003–2019; EOES 2021–2025 |
| **Questions** | 2 integrated experiments (A/B) per year; local mirror **~90 PDFs / ~172 MB** (EUSO 2003–2017 partial + EOES 2021/2023–2025 task packs; 2022 tasks still unpublished on host) |
| **Team size** | **Origin: 3** · **Rec: 3** |
| **Time** | Multi-hour lab practicals during olympiad week |
| **Answer type** | Completed answer sheets / measurements / short lab writeups |
| **Grading** | Official marking schemes (partial credit); rubric-style for open responses |
| **Source** | Organizer-provided lab equipment; no outside help during exam |
| **Link** | [EUSO experiments](http://euso.eu/about/experiments/) · [EOES previous olympiads](https://www.eoes.science/Previous%20olympiads/previous.html) |
| **Data** | `data/raw/eoes/` — `euso/<year>/` experiment PDFs + `eoes/<year>/` task packs + mirrors (~100 PDFs / ~173 MB) |
| **Notes** | Closest European counterpart to `ijso_practical`. Natural roles: experimentalist / data-analyst / report writer. EOES 2022 official task PDFs not public yet (`eoes2022.uhk.cz`); older EUSO years 2005/2008–2010/2016/2018–2019 mostly dead-host only. |

---

### IChTo · `IChTo/`

| | |
|---|---|
| **Domain** | Chemistry research / open problems (IYPT-style tournament) |
| **Years/sessions** | 2017–2026 (9 published problem sets; 2020/2021 combined) |
| **Questions** | **106** open problems across 9 sets (2017–2024 & 2026: 12 each; 2025: 10; no separate 2021 PDF) |
| **Team size** | **Origin: 3+** (Reporter / Opponent / Reviewer) · **Rec: 3+** (role rotation) |
| **Time** | Months of prep; timed oral fights at the tournament |
| **Answer type** | Oral scientific report + opposition / review speeches |
| **Grading** | Jury rubric during Physics-Fight-style chemistry rounds |
| **Source** | Full literature during prep; fight-protocol limits on live aids |
| **Link** | [ichto.org/en/problems](http://ichto.org/en/problems/) · [Rules](http://ichto.org/en/rules/) |
| **Data** | `data/raw/ichto/` — official problem-set PDFs (2017–2026) |
| **Notes** | Chemistry twin of `iypt`. Strong multi-agent fit: assign Reporter / Opponent / Reviewer agents and score with a calibrated LLM-judge panel. |

---

### PUMaC Power Round · `PUMaC_Power/`

| | |
|---|---|
| **Domain** | Proof-based team mathematics |
| **Years/sessions** | 2007–2025 Power Rounds (archive coverage) |
| **Questions** | ~19 Power packets locally (2007–2025; one multi-part proof packet per year) |
| **Team size** | **Origin: 8** · **Rec: 8** |
| **Time** | ~1 week collaborative window before contest day |
| **Answer type** | Written proof packet submitted as a team |
| **Grading** | Proof rubric / official solutions for reference |
| **Source** | Team collaboration allowed; no outside human help |
| **Link** | [PUMaC Archives](https://jason-shi-f9dm.squarespace.com/archives) · [Power Round page](https://jason-shi-f9dm.squarespace.com/power-round) |
| **Data** | `data/raw/pumac_power/` — Power Round problem (+ solution) PDFs |
| **Notes** | Longer collaboration window than ARML Power / HMMT Team. Good stress test for multi-session agent teams that must share lemmas and write a coherent proof document. |

---

### MIT Mystery Hunt · `MIT_Mystery_Hunt/`

| | |
|---|---|
| **Domain** | Large-scale collaborative puzzle hunt (not a classical STEM olympiad; included for extreme multi-agent structure) |
| **Years/sessions** | 1982 + 1994–2025 indexed; answer keys 1994–present |
| **Questions** | **4,202** keyed answers (`mh_answers`); puzzle bodies+media mirrored under `puzzles/` (see local README) |
| **Team size** | **Origin: 5–150** (specialty squads) · **Rec: 8–20** for lab sims (scale as needed) |
| **Time** | ~48-hour hunt weekend (remote-capable in recent years) |
| **Answer type** | Short string answers → meta answers → coin location |
| **Grading** | Exact / normalized answer match (RULE); structure in `metapuzzles.yml` |
| **Source** | Full internet and arbitrary tooling; extreme division of labor |
| **Link** | [puzzles.mit.edu](https://puzzles.mit.edu/) · [Archive by year](https://puzzles.mit.edu/huntsbyyear.html) · [Puzzle Index](http://devjoe.appspot.com/huntindex/) · [mh_answers](https://github.com/dgulotta/mh_answers) |
| **Data** | ⏳ on demand (~19 GB) — `mh_answers/` + puzzle HTML/media mirror; not in git |
| **Notes** | Strongest public multi-agent collaboration dataset. Local mirror links answers→puzzle pages via `answers.tsv` + huntindex. Procedurally generated rounds (e.g. Infinite Corridor / Hydra) excluded from keys. |

---

### IOL · `IOL/`

| | |
|---|---|
| **Domain** | Linguistics — morphology, phonology, syntax, semantics, writing systems |
| **Years/sessions** | Official IOL archive from 2003 onward; HF extract covers solution-backed problems |
| **Questions** | 130 solution-backed source problems · 555 HF records (478 text-strict); ~1,500 sub-instances in IOLBENCH-style splits |
| **Team size** | **Origin:** Individual **1** · Team Contest **4** · **Rec:** Individual **2–3** · Team **4** |
| **Time** | Timed olympiad rounds |
| **Answer type** | Rule inference + short answers / paradigms |
| **Grading** | RULE — match against official solutions / structured answer units |
| **Source** | Closed-book; paper & pencil; no devices |
| **Link** | [ioling.org/problems](https://ioling.org/problems/by_year/) · [HF agurung/ioling](https://huggingface.co/datasets/agurung/ioling) · [IOLBENCH](https://arxiv.org/abs/2501.04249) |
| **Data** | `data/raw/iol/` — official team/individual PDF mirrors + HF extract |
| **Notes** | Strongest new humanities-STEM bridge. Prefer HF structured rows for auto-grading; keep PDFs for figures/scripts. |

---

### International History Olympiad · `History_Olympiad/`

| | |
|---|---|
| **Domain** | History — bees, bowls, written exams, historiography, art history |
| **Years/sessions** | Multi-year resource archive (exams + keys + rubrics) |
| **Questions** | ~90 exam/key/rubric PDFs across 6 editions (2014, 2018–2019, 2022–2024); multiple event types per edition |
| **Team size** | **Origin:** Bee **1** · Bowl team · **Rec:** Bee **2–3** · Bowl **4** |
| **Time** | Timed rounds per event |
| **Answer type** | Short answers / buzzes / essays |
| **Grading** | RULE for keyed bees; RUBRIC for historiography / written exams |
| **Source** | Study guides; no devices in bees |
| **Link** | [historyolympiad.com/resources](https://www.historyolympiad.com/resources/) |
| **Data** | `data/raw/history_olympiad/` — year folders of exams/keys/rubrics |
| **Notes** | Best public history olympiad dump with mixed auto-gradable and rubric tracks. |

---

### IEO · `IEO/`

| | |
|---|---|
| **Domain** | Economics + business case |
| **Years/sessions** | Annual olympiad tasks (economics open + business case) |
| **Questions** | ~1 economics open set (2018) + ~10+ business-case / task PDFs locally; typically multi-problem economics + 1 team case per year |
| **Team size** | **Origin:** Economics **1** · Business Case **3–5** · **Rec:** Econ **2–3** · Case **3–5** |
| **Time** | Timed economics; multi-hour case with slides |
| **Answer type** | Short/numeric economics answers; slide deck + pitch |
| **Grading** | RULE for economics keys; RUBRIC for case presentation |
| **Source** | Full research allowed on Business Case |
| **Link** | [ieo-official.org/prepare](https://ieo-official.org/prepare) · [Syllabus PDF](https://files.ieo-official.org/IEO_Syllabus.pdf) |
| **Data** | `data/raw/ieo/` + `data/raw/business_case/` — syllabus/regulations + business-case PDFs |
| **Notes** | Complements `gcch_harvard` / `cfa` with an official international olympiad brand. |

---

### IOAA · `IOAA/`

| | |
|---|---|
| **Domain** | Astronomy & astrophysics |
| **Years/sessions** | Annual IOAA theory / data / observation / group packets |
| **Questions** | ~20 years of multi-paper sets (174 PDFs, 2007–2025); 16 Group/Team Competition packets for multi-agent runs |
| **Team size** | **Origin:** Individual **1** · Group **5** · **Rec:** Individual **2–3** · Group **5** |
| **Time** | Timed papers; group session |
| **Answer type** | Numerical answers with units; data-analysis writeups |
| **Grading** | RULE (official marking) |
| **Source** | Organizer calculator + constants / charts; no personal formula books |
| **Link** | [IOAA past problems](https://ioaastrophysics.org/resources/problems-from-past-ioaa) |
| **Data** | `data/raw/ioaa/` — Group/Team competition packets (+ prior ARML-era group files) |
| **Notes** | Prefer Group Competition / Team Competition packets for multi-agent simulation. |

---

### WSC Collaborative Writing · `WSC_Writing/`

| | |
|---|---|
| **Domain** | Collaborative creative / analytical writing |
| **Years/sessions** | Seasonal WSC events (prompts vary) |
| **Questions** | **42** public guiding questions locally; live Collaborative Writing uses **3–4 prompts/session** (not pre-published) |
| **Team size** | **Origin: 3** · **Rec: 3** |
| **Time** | Staged: plan → individual write → peer edit |
| **Answer type** | Three handwritten essays |
| **Grading** | RUBRIC (WSC judging criteria) |
| **Source** | No electronic devices; handwritten only |
| **Link** | [WSC Events](https://scholarscup.org/events/) · [WSC Wiki](https://www.owiki.org/wiki/World_Scholar%27s_Cup) |
| **Data** | `data/raw/wsc_writing/` — guiding questions + discussion prompts |
| **Notes** | The 42 guiding Qs are prep/proxy items from official themes — not the sealed on-site prompts. |

---

## Frontier team abstraction

### ARC-AGI-2 · `ARC-AGI-2/`

| | |
|---|---|
| **Domain** | Abstraction / few-shot grid puzzles (ARC Prize) |
| **Questions** | 1,000 public train + 120 public eval |
| **Team size** | **Rec: 3** (hypothesize / verify / program) |
| **Grading** | RULE — exact grid match |
| **Data** | `data/raw/arc_agi2/` (~6 MB) |
| **Link** | [arcprize/ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2) |

## Entries living under `art/`

These open-ended / quiz competitions are part of the olympiad suite catalog but their files and full deep-dive tables live in [`art/README.md`](../art/README.md):

| ID | Where documented |
|----|------------------|
| `cfa_research_challenge` | [`art/README.md`](../art/README.md) → CFA Institute Research Challenge |
| `gcch_harvard` | [`art/README.md`](../art/README.md) → Global Case Competition at Harvard |
| `wharton_investment` | [`art/README.md`](../art/README.md) → Wharton Global HS Investment Competition |
| `vis_moot` | [`art/README.md`](../art/README.md) → Willem C. Vis Moot |
| `debatebench` | [`art/README.md`](../art/README.md) → WUDC / BP Debate |
| `ethics_bowl` (`ethics_bowl_appe` + `ethics_bowl_nhseb`) | [`art/README.md`](../art/README.md) → APPE / NHSEB Ethics Bowl |
| `science_bowl` | [`art/README.md`](../art/README.md) → DOE National Science Bowl |
| `qanta` | [`art/README.md`](../art/README.md) → QANTA Quiz Bowl |

---

## Downloading

Pushable packs are already in [`data/raw/`](../../data/raw/). Fetch only the oversized / Docker-bound sets:

```bash
# Large rule-based (not in git)
hf download deepmind/code_contests --repo-type dataset --local-dir data/raw/codecontests  # ~7.6 GB

# Docker / GitHub-based (not in git)
#   NYU CTF Bench : pip install nyuctf ; challenges cloned on first CTFDataset(split=...) call
#   Cybench       : git clone https://github.com/andyzorigin/cybench
#   Mystery Hunt  : git clone --depth 1 https://github.com/dgulotta/mh_answers.git data/raw/mystery_hunt/mh_answers

# Optional backfills for files skipped by the 95 MB GitHub limit
hf download TasnimKabir12/qanta --repo-type dataset --local-dir data/raw/qanta_full
# IOAI Practical-Round-problems.zip → from IOAI-official GitHub releases / HF IOAI2025
```

---

## Collection backlog

| ID | Action |
|----|--------|
| `modeling_agent` | Collect Outstanding-winner papers (COMAP publishes abstracts; full papers via UMAP Journal) as gold-standard references |
| `CodeContests` | Pull locally when coding-track evals start (~7.6 GB) |
| `NYU_CTF_Bench` / `Cybench` | Cybench challenge packs already local; install Docker and smoke-test one challenge per category for full flag grading |
| `ioai` | Expand Team Challenge simulation assets (robotics env / generative briefs beyond statements) |
| `eoes` | In `data/raw/eoes/`; still missing EOES 2022 official tasks + several dead-host EUSO years |
| `ichto` | Optional: collect winning fight recordings / written solutions if published |
| `pumac_power` | Rename PDFs to `YYYY_problems.pdf` / `YYYY_solutions.pdf` for uniform loading |
| `mystery_hunt` | Keep off-git; continue answer→puzzle media mirror locally if needed |
| `iol` | Prefer HF structured answers; backfill figure/script PDFs for multimodal rows |
| `history_olympiad` | Flatten year event names; separate RULE bees from RUBRIC written exams |
| `ieo` | Fill missing year business-case PDFs from ieo-official.org/prepare |
| `ioaa` | Prioritize Group Competition packets for multi-agent runs |
| `wsc_writing` | Archive seasonal prompts + rubrics from scholarscup.org each season |

---

## Evaluation design

**RULE** contests are fully auto-gradable (harness / executor). **RUBRIC** contests use judges that must pass the **calibration gate** in `art/README.md` (Evaluation design → Judge validation) — `debatebench` human scores are the anchor.

### RULE

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `CodeContests` | Hidden test cases; ICPC-style (one shared machine, penalty per wrong submission). | 3 agents sharing one submission queue under a penalty budget — direct ICPC analogue. |
| `NYU_CTF_Bench` / `Cybench` | Exact flag match (and per-subtask checks for Cybench) inside Docker; fully automatic. | CTF teams split by category (pwn / crypto / web / rev); log which specialist solved each flag. |
| `mystery_hunt` | Exact / normalized answer match; meta structure from `metapuzzles.yml`. | Specialty squads + meta lead; log unlock graph, idle time, and cross-squad handoffs. |
| `ioai` (Individual) | Task metrics on hidden tests. | ML specialists per modality (CV / NLP / tabular) + aggregator. |
| `iol` | Match against official / HF answer units; keep figure-dependent items for vision solvers. | 4-agent Team Contest simulation; compare vs solo on the same problems. |
| `ioaa` (individual papers + Group) | Official keys / numeric tolerances. | Optional lab-role split on practicals; **Group Competition** for multi-agent. |
| `history_olympiad` (bees / bowls) | Exact / normalized answer match. | Team Bowl conferring vs individual Bee. |
| `ieo` (economics) | Official numeric / short-answer keys. | Solo economics baseline before team case. |
| `ARC-AGI-2` | Exact grid match (ARC Prize metric). | Hypothesis / verifier / programmatic-solver team. |

### RUBRIC

| ID | Scoring | Team adaptation |
|----|---------|-----------------|
| `modeling_agent` | LLM-judge panel walking per-problem `requirements` with `eval_roles` as judge personas. | 3–4 agents per COMAP rules (modeler / coder / writer); `decomposition` field seeds the role split. |
| `cfa` / `gcch` / `wharton` / `vis_moot` / `debatebench` / `ethics_bowl` / `science_bowl` / `qanta` | See Evaluation design in [`art/README.md`](../art/README.md) (`science_bowl` / `qanta` are RULE quiz bowls documented there). | Same as `art/` — those contests define the humanities/business/law/quiz team protocols. |
| `eoes` | Official marking schemes on answer sheets; partial credit as published. | 3 agents as experimentalist / analyst / scribe; compare against solo agent at equal lab steps. |
| `ichto` | Tournament jury rubric (Reporter / Opponent / Reviewer). Calibrate LLM judges like `iypt`. | Role-rotating agents; score both content quality and opposition/review usefulness. |
| `pumac_power` | Proof rubric against official solutions; stepwise credit on subparts. | 8 agents sharing lemmas over a multi-day window; measure document coherence + coverage. |
| `ioai` (Team Challenge) | Jury / rubric for robotics or generative deliverable. | Separate planning / control / perception team. |
| `history_olympiad` (historiography) | Official written-exam rubrics. | Writer / critic / editor split. |
| `ieo` (Business Case) | Case deck + oral presentation rubric. | 3–5 agents (research / model / slides / pitch). |
| `wsc_writing` | WSC collaborative-writing criteria; score plan / draft / peer-edit stages. | Strict 3-agent staged protocol with no tools. |

All RUBRIC judges must report inter-judge agreement and run pairwise comparisons position-swapped. Cross-cutting: log the same team-level metrics as `art/` (budget consumed, inter-agent messages, role-specialization entropy, team-vs-solo delta). For contamination, prefer newest team releases — IOAI 2025/2026, post-2023 modeling problems, newest Vis / Wharton / case sets — for headline numbers.
