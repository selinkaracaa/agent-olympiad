# from_zhongzheng — Domain Catalog

Last updated: 2026-07-29

English index of **multi-agent / team** competitions under [`olympiad/`](olympiad/README.md) and [`art/`](art/README.md).

Solo Origin=1 packs (AIME, OlympicArena, HealthBench, HLE, …) were **removed**. This catalog keeps contests with a **native team track** (Origin ≥ 2, or Individual + Team/Group/Bowl/Case).

**Grading**
- **RULE** — closed-form / tests / flags / exact match (auto-gradable)
- **RUBRIC** — open-ended deliverable scored by rubric, jury, or calibrated LLM judges
- **RULE + RUBRIC** — hybrid

---

## Summary

| Domains | Unique competitions | Sources |
|:-------:|--------------------:|---------|
| **18** | **24** | `olympiad/` · `art/` · `data/raw/` |

| # | Domain | Competitions | RULE | RUBRIC | Hybrid |
|---|--------|-------------:|-----:|-------:|-------:|
| 1 | [STEM / proof team math](#1-stem--proof-team-math) | 1 | 0 | 1 | 0 |
| 2 | [Competitive programming](#2-competitive-programming) | 1 | 1 | 0 | 0 |
| 3 | [AI olympiad](#3-ai-olympiad) | 1 | 0 | 0 | 1 |
| 4 | [Applied math modeling](#4-applied-math-modeling) | 1 | 0 | 1 | 0 |
| 5 | [Experimental science](#5-experimental-science) | 1 | 0 | 1 | 0 |
| 6 | [Chemistry tournament](#6-chemistry-tournament) | 1 | 0 | 1 | 0 |
| 7 | [Astronomy & astrophysics](#7-astronomy--astrophysics) | 1 | 1 | 0 | 0 |
| 8 | [Linguistics](#8-linguistics) | 1 | 1 | 0 | 0 |
| 9 | [Cybersecurity](#9-cybersecurity) | 2 | 2 | 0 | 0 |
| 10 | [Business, finance & economics](#10-business-finance--economics) | 4 | 0 | 2 | 2 |
| 11 | [Law](#11-law) | 1 | 0 | 1 | 0 |
| 12 | [Ethics](#12-ethics) | 2 | 0 | 2 | 0 |
| 13 | [History](#13-history) | 1 | 0 | 0 | 1 |
| 14 | [Debate](#14-debate) | 1 | 0 | 1 | 0 |
| 15 | [Collaborative writing](#15-collaborative-writing) | 1 | 0 | 1 | 0 |
| 16 | [Science & general-knowledge quiz](#16-science--general-knowledge-quiz) | 2 | 2 | 0 | 0 |
| 17 | [Collaborative puzzle hunt](#17-collaborative-puzzle-hunt) | 1 | 1 | 0 | 0 |
| 18 | [Frontier team abstraction](#18-frontier-team-abstraction) | 1 | 1 | 0 | 0 |
| | **Total** | **24** | **9** | **11** | **4** |

---

## 1. STEM / proof team math

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `pumac_power` | PUMaC Power Round (8-agent proofs) | Week-long team proof packet | ~19 packets (2007–2025) | RUBRIC | [olympiad](olympiad/README.md) |

---

## 2. Competitive programming

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `CodeContests` | Codeforces / ICPC-style (AlphaCode) | ICPC-style team programming (shared machine) | **13,610** | RULE | [olympiad](olympiad/README.md) |

---

## 3. AI olympiad

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ioai` | International Olympiad in AI | Individual ML tasks + Team Challenge | **17** tasks | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 4. Applied math modeling

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `modeling_agent` | HiMCM / MCM / ICM / IM2C / MidMCM | Multi-day team math modeling contest | 68 | RUBRIC | [olympiad](olympiad/README.md) |

---

## 5. Experimental science

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `eoes` | EOES / EUSO | 3-person integrated lab practical olympiad | **2 exp/year** · `data/raw/eoes` **~100 PDFs / ~173 MB** | RUBRIC | [olympiad](olympiad/README.md) |

---

## 6. Chemistry tournament

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ichto` | International Chemistry Tournament | IYPT-style oral science fights | **106** problems · 9 sets | RUBRIC | [olympiad](olympiad/README.md) |

---

## 7. Astronomy & astrophysics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ioaa` | Intl. Olympiad on Astronomy & Astrophysics (incl. Group) | Written + observation; **5-person Group** | Group packets in `data/raw/ioaa` | RULE | [olympiad](olympiad/README.md) |

---

## 8. Linguistics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `iol` | International Linguistics Olympiad | Written + **4-person Team Contest** | Team PDFs + HF extract in `data/raw/iol` | RULE | [olympiad](olympiad/README.md) |

---

## 9. Cybersecurity

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `NYU_CTF_Bench` | CSAW CTF (NYU CTF Bench) | Team CTF | 200 | RULE | [olympiad](olympiad/README.md) |
| `Cybench` | Professional CTF | HackTheBox / Sekai / HKCERT packs | **40** | RULE | [olympiad](olympiad/README.md) |

---

## 10. Business, finance & economics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `gcch_harvard` | Global Case Competition at Harvard | Case → deck + pitch | 7 | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `cfa_research_challenge` | CFA Institute Research Challenge | Equity report + defense | **19** tasks + champion reports | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `wharton_investment` | Wharton Global HS Investment Competition | Portfolio sim + strategy defense | 4 | RULE + RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |
| `ieo` | International Economics Olympiad | Economics + **team business case** | case PDFs in `data/raw/business_case` + `data/raw/ieo` | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 11. Law

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `vis_moot` | Willem C. Vis Commercial Arbitration Moot | Memos + oral | 7 | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |

---

## 12. Ethics

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ethics_bowl_appe` | APPE Intercollegiate Ethics Bowl | Adversarial oral cases | ~140 cases | RUBRIC | [art](art/README.md) |
| `ethics_bowl_nhseb` | National High School Ethics Bowl | Dialogic oral cases | **14** National Case Sets | RUBRIC | [art](art/README.md) |

---

## 13. History

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `history_olympiad` | International History Olympiad | Bee/bowl + written exams | ~95 PDFs | RULE + RUBRIC | [olympiad](olympiad/README.md) |

---

## 14. Debate

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `debatebench` | WUDC / BP Debate (DebateBench) | 4 teams × 2 | 360 scored speeches | RUBRIC | [art](art/README.md) · [olympiad](olympiad/README.md) |

---

## 15. Collaborative writing

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `wsc_writing` | World Scholar's Cup — Collaborative Writing | 3-person staged essays | **42** guiding Qs | RUBRIC | [olympiad](olympiad/README.md) |

---

## 16. Science & general-knowledge quiz

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `science_bowl` | DOE National Science Bowl | Team buzzer quiz | **~23,691** | RULE | [art](art/README.md) |
| `qanta` | QANTA Quiz Bowl | Team pyramidal quiz | ~100,000 | RULE | [art](art/README.md) |

---

## 17. Collaborative puzzle hunt

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `mystery_hunt` | MIT Mystery Hunt | Large-team puzzle hunt | **4,202** keyed answers | RULE | [olympiad](olympiad/README.md) |

---

## 18. Frontier team abstraction

| ID | Competition | Format | Questions | Grading | Tracker |
|----|-------------|--------|-----------|---------|---------|
| `ARC-AGI-2` | ARC Prize abstraction puzzles | Team prize grid puzzles | 1,000 train + 120 eval | RULE | [olympiad](olympiad/README.md) |

---

## Cross-reference

| Tracker | Competitions |
|---------|-------------:|
| [`olympiad/README.md`](olympiad/README.md) | team olympiad matrix |
| [`art/README.md`](art/README.md) | 9 |
| **Union** | **24** |

---

## Data location

Pushable originals live in the repo at [`data/raw/`](../data/raw/) (no READMEs — data only). Catalog JSON is under [`data/benchmarks/`](../data/benchmarks/).

**In git (`data/raw/`):** olympiad + art PDF/JSON packs that fit GitHub limits (files &lt; 95 MB). Includes EOES, IChTo, PUMaC, history, ethics bowls, science bowl, CFA/GCCH/Vis/Wharton, WRO, Envirothon, CCDC, IOAI (minus one oversized zip), IOL mirrors, ARC-AGI-2, modeling JSON, etc.

**Not in git (fetch on demand):**
| Pack | Why | How |
|------|-----|-----|
| `CodeContests` | ~7.6 GB parquet | `hf download deepmind/code_contests` |
| `Cybench` | ~2 GB challenge trees + Docker | clone [cybench](https://github.com/andyzorigin/cybench) |
| `NYU_CTF_Bench` | ~1.5 GB | `pip install nyuctf` / clone |
| `MIT_Mystery_Hunt` | ~19 GB puzzle mirror | `mh_answers` + local `puzzles/` mirror |
| `qanta.train.*.json` | 177 MB &gt; GitHub file limit | HF [`TasnimKabir12/qanta`](https://huggingface.co/datasets/TasnimKabir12/qanta); `qanta.dev` is in `data/raw/qanta/` |
| `IOAI/.../Practical-Round-problems.zip` | 120 MB | from IOAI-official GitHub / HF |
