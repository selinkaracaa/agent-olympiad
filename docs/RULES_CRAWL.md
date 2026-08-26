# Competition rules crawl (2026-08-11)

## Related research report

A deeper primary-source pass with per-competition hard constraints and confidence
labels is in [`docs/rules_crawl_2026-08-11.md`](rules_crawl_2026-08-11.md). A follow-up
pass over the seven cards that pass left at low confidence is in
[`docs/rules_lowconf_2026-08-12.md`](rules_lowconf_2026-08-12.md). Both are merged into
the `data/rules` rule-card store via:

```bash
python collectors/merge_rules_crawl_report.py
python collectors/merge_rules_crawl_report.py --report docs/rules_lowconf_2026-08-12.md
```

Reports are replayable in any order and the merge is additive, so a later report can
only add facts. When it instead *retracts* an earlier entry — the 08-11 `gcch_harvard`
entry cited a retired domain and the wrong event — mark that entry with
`"superseded_by": "<newer report path>"` and the merge skips it.

## What we did

1. Crawled official rule pages/PDFs into `data/rules/sources/{competition_id}/`.
2. Enriched every assembled rule card with:
   - contestant-facing `human_constraints` grounded in official sources / simulator matrix
   - provenance URLs, crawl status, and short crawled excerpts
3. Merged the research report's hard constraints + confidence into the same rule cards.
4. Rewrote every generated placeholder `rules_text` into a contestant-facing briefing
   composed from the card's own fields (format, roster, submission, official timing,
   simulation caveats), so the agent prompt no longer carries pipeline debug strings.
5. Agents receive these constraints through `src/collaboration.py` system prompts and may call `query_rules`.

Most competitions use `data/rules/{competition_id}.json`. The WSC Writing pilot
stores three canonical components under `data/rules/wsc_writing/`:
`competition.json`, `collaboration.json`, and `evaluation.json`.
`src/rules/storage.py` composes them before normal `RuleCard` validation, and all
collectors use the same storage interface when writing fields back to their owner.

## Commands

```bash
python collectors/crawl_competition_rules.py
python collectors/enrich_rules_from_sources.py
python collectors/merge_rules_crawl_report.py
python collectors/rewrite_rules_text.py
python collectors/align_deliverables.py
python collectors/derive_turn_budgets.py
python collectors/write_role_duties.py
python collectors/configure_coordination_rules.py
python collectors/lint_rule_cards.py
python src/run_rulebased_demo.py --competition iol_team --problem iol_team_2008
```

`lint_rule_cards.py` is the gate: it checks schema conformance, tool/resource
contradictions, roster arithmetic, duplicate constraints, and prompt hygiene.
`--fix` applies the safe subset; `tests/test_rule_card_lint.py` enforces zero errors.

## Coverage

- 37/37 competitions have rule cards.
- Most competitions have successfully crawled local text/PDF archives under `data/rules/sources/`.
- A few sites blocked automation (403/DNS). For those we stored fallback notes derived from public pages / known official constraints:
  - `science_olympiad`
  - `odyssey_of_the_mind`
  - `gcch_harvard`
  - `qanta`

## Important limitation

Crawled text improves prompt fidelity, but some human mechanisms are still only partially executable in `src/`:

- progressive batch release (HMMT Guts)
- lock-out buzzers (Science Bowl / History Bowl)
- physical labs / robots
- live oral cross-examination

Those cards remain marked `proxy` / draft where needed. Tools and resource bans are still enforced by `OlympiadEnvironment`.
