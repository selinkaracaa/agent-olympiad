# Formal benchmark visualizations

Snapshot: **2026-07-28**  
Taxonomy: **2026-07-28.formal-v1**  
Primary source: `data/benchmarks/index_new.json`  
Auxiliary source: `data/benchmarks/index_aux.json`

Current scope: **34 primary dataset IDs / 914 session records**, plus **6 auxiliary corpora / 175,380 rows**.

Reproduce from the repository root:

Requires Python packages `matplotlib` and `numpy`.
Generated format: PNG only.

```powershell
python data/viz/generate.py
```

- **Current formal-catalog overview** — [PNG](01_overview.png)
- **Primary session scale and auxiliary row scale** — [PNG](02_scale_by_track.png)
- **Coarse domain by catalog evaluator type** — [PNG](03_domain_type_heatmap.png)
- **Configured team size and primary scale** — [PNG](04_teamsize_scale_scatter.png)
- **Exact-year primary archive presence** — [PNG](05_year_coverage.png)
- **Coarse task-mode mix under two weighting views** — [PNG](06_task_types.png)
- **Multi-dimensional formal-catalog storyboard** — [PNG](07_storyboard.png)
- **Coarse-domain composition pie charts** — [PNG](08_domains_pie.png)
- **Current primary question and task-unit distribution** — [PNG](09_question_distribution.png)

## Statistical guardrails

- Do not pool primary session records with auxiliary question/challenge rows.
- `index_new.json` (merged `index.json` + promotions) defines the primary scope here.
- Catalog evaluator type and gold claims are metadata, not quality audits.
- Embedded-answer, rubric, and human-baseline coverage are measured directly from JSON rows.
- Equal-ID and raw-row views answer different questions about portfolio composition.
- Exact-year dots show nominal archive presence, not continuous evaluable coverage.
- The primary question distribution uses positive `question_count` values where stored; every other primary row contributes one question/task unit.
