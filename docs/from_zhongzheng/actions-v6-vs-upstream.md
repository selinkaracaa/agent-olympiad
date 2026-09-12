<!-- markdownlint-disable MD060 -->

# Selin's actions/tools → v6: itemized change list

> Upstream = Selin's `agent-olympiad` (`selinkaracaa/agent-olympiad`, HEAD `60bb0222`):
> `src/env.py: ALL_ACTIONS` (22 names) + `src/icpcrun.py` ICPC JSON interface (15 names) = 31 distinct names.
> v6 = `agent-team-features-main/src/tool_registry.py`, `ACTION_SET_VERSION = 6`, 29 actions.

## Totals

| Outcome | Count | Names |
|---|---:|---|
| Kept as-is (same name, same job) | 11 | `speak`, `use_calculator`, `web_search`, `read_lab_equipment`, `read_star_chart`, `query_rules`, `propose`, `challenge`, `provide_evidence`, `revise`, `decide` |
| Kept name, changed behaviour | 2 | `submit_code`, `execute_code` |
| Merged into a v6 action (old name still parses as alias) | 4 | `write_scratchpad→work`, `write_private_notes→remember`, `sleep→rest`, `submit_final→submit` |
| Merged into a v6 action (old name does NOT parse) | 7 | `memory_note→remember`, `memory_recall→recall`, `memory_publish→share_note`, `set_focus→select_problem`, `submit_run→submit_code`, `evidence→provide_evidence`, `done→rest` |
| Dropped (no v6 handler) | 7 | `read_official_materials`, `inspect_environment`, `start_environment`, `execute_environment_command`, `reset_environment`, `workstation_acquire`, `workstation_release` |
| New in v6 (no upstream counterpart) | 10 | `direct_message`, `select_problem`, `skip_problem`, `inspect_problem`, `triage_problem`, `assign_problem`, `request_review`, `review_answer`, `finish_contest`, `check_budget` |

31 upstream names → 11 + 2 + 4 + 7 + 7 = 31. v6 = 11 + 2 + 4 (targets) + 2 new targets from the ICPC merges (`recall`, `share_note`) + 10 new = 29.

## v6 total: 29 = 23 actions + 6 tools

| Pack | Kind | Count | Names |
|---|---|---:|---|
| `common` (always on, both runtimes) | action | 18 | `speak` `direct_message` `work` `rest` `submit` `select_problem` `skip_problem` `inspect_problem` `triage_problem` `review_answer` `request_review` `assign_problem` `finish_contest` `remember` `recall` `share_note` `check_budget` `query_rules` |
| `deliberation` (OTC + card `deliberation.mode == "structured"`) | action | 5 | `propose` `challenge` `provide_evidence` `revise` `decide` |
| `math` | tool | 1 | `use_calculator` |
| `programming` | tool | 2 | `execute_code` `submit_code` |
| `research` | tool | 1 | `web_search` |
| `resources` (explicit capability only) | tool | 2 | `read_lab_equipment` `read_star_chart` |

Plus 15 legacy aliases (`sleep`, `submit_final`, `write_scratchpad`, `verify_problem`, …) that only map old spellings onto the 29; they are not separate actions.

## Itemized table

Kind: **action** = collaboration/desk verb, **tool** = contest instrument gated by the tool allowlist.
Surface: where upstream defined it (`env` = generic environment, `icpc` = ICPC session runner).

| # | Upstream name | Kind | Surface | Outcome | v6 name | Detail |
|--:|---|---|---|---|---|---|
| 1 | `speak` | action | env, icpc | kept | `speak` | unchanged |
| 2 | `use_calculator` | tool | env | kept | `use_calculator` | unchanged; `math` pack |
| 3 | `web_search` | tool | env | kept | `web_search` | unchanged; `research` pack |
| 4 | `read_lab_equipment` | tool | env | kept | `read_lab_equipment` | unchanged; now only when the benchmark/card declares the capability, never inferred from competition |
| 5 | `read_star_chart` | tool | env | kept | `read_star_chart` | same as above |
| 6 | `query_rules` | action | env | kept | `query_rules` | upstream took a free-text query; v6 is argument-less. Session emits a private `rules_result` event; hidden from the prompt unless the rule card lists it |
| 7 | `propose` | action | env, icpc | kept | `propose` | added optional `problem_id` |
| 8 | `challenge` | action | env, icpc | kept | `challenge` | `proposal_id` is a typed field, enum-pinned to open proposals |
| 9 | `provide_evidence` | action | env | kept | `provide_evidence` | same as above |
| 10 | `revise` | action | env, icpc | kept | `revise` | author-only in both |
| 11 | `decide` | action | env, icpc | kept | `decide` | `outcome` enum `accept/reject/defer`; decision maker is the card-designated role (upstream: any `may_submit` role) |
| 12 | `submit_code` | tool | env | kept name, **new semantics** | `submit_code` | upstream: private **sample-only** check, "does not finalize". v6: a real submission attempt — remote judge when the gateway is on, finalizes on AC, wrong-submission penalty otherwise; sample judging is only the fallback. Under OTC requires a prior `SAMPLE_AC` from `execute_code` and an approved `review_answer` |
| 13 | `execute_code` | tool | env, icpc | kept name, **new semantics** | `execute_code` | ICPC `stdin` argument dropped; optional `language` added; for programming tasks the sandbox also runs the official sample and reports `SAMPLE_AC/WA/RE` (this replaces upstream's sample-only `submit_code`) |
| 14 | `write_scratchpad` | action | env | merged (alias) | `work` | one overwritable shared string → immutable per-problem answer versions with a hash; optional `problem_id`; repeats of an already-recorded answer are refused |
| 15 | `write_private_notes` | action | env | merged (alias) | `remember` | replaceable notes block → append-only notes with ids (`M1`, …) and optional problem tag |
| 16 | `sleep` | action | env | merged (alias) | `rest` | rename only |
| 17 | `submit_final` | action | env | merged (alias) | `submit` | answer-sheet contests merge the text with recorded board answers; OTC exposes it argument-free only once review gates pass |
| 18 | `memory_note` | action | icpc | merged (no alias) | `remember` | same store as #15 |
| 19 | `memory_recall` | action | icpc | merged (no alias) | `recall` | `scope` argument dropped: always own notes + team-shared notes |
| 20 | `memory_publish` | action | icpc | merged (no alias) | `share_note` | `memory_ids[]` → `note_id` (comma-separated allowed) |
| 21 | `set_focus` | action | icpc | merged (no alias) | `select_problem` | free-text focus → a real problem id with claim semantics (one per agent, refused if held by someone else) |
| 22 | `submit_run` | tool | icpc | merged (no alias) | `submit_code` | see #12 |
| 23 | `evidence` | action | icpc | merged (no alias) | `provide_evidence` | ICPC spelling not accepted |
| 24 | `done` | action | icpc | merged (no alias) | `rest` | upstream ICPC let an agent chain several observation-returning actions in one turn and then `done` to end it; in v6 every action ends the turn (only the first validated call runs), so there is nothing for `done` to signal. See §"Why the ICPC-specific verbs went away" |
| 25 | `read_official_materials` | tool | env | **dropped** | — | not ICPC-related. Only `science_olympiad` used it; that competition is in neither v6's `COMPETITION_TOOL_REGISTRY` (19 competitions) nor `contest_rules.py`, so nothing would ever request it |
| 26 | `inspect_environment` | tool | env | **dropped** | — | not ICPC-related. Docker runtime actions for `cybench` / `ccdc` / `wro` / `eoes` / `ijso_practical` (spin up a target box, run shell commands). `runtimes.py` was not ported and none of those competitions are in v6's registry; `ijso_practical` uses `read_lab_equipment` fixtures instead. Names survive only as labels in `evaluation/error_taxonomy.py` / `team_metrics.py`. ICPC code runs through `execute_code` + `submit_code`, not these |
| 27 | `start_environment` | tool | env | **dropped** | — | same as #26 |
| 28 | `execute_environment_command` | tool | env | **dropped** | — | same as #26 |
| 29 | `reset_environment` | tool | env | **dropped** | — | same as #26 |
| 30 | `workstation_acquire` | action | icpc | **dropped** | — | ICPC's one-keyboard constraint is kept, the verb is not. The lease is implicit: whoever last ran `execute_code`/`submit_code` holds it for `LEASE_TURNS = 2` turns (`otc_runtime.workstation_holder`), enforced only when the card sets `simulation.exclusive_workstation_lease: "enforced"`. See §"Why the ICPC-specific verbs went away" |
| 31 | `workstation_release` | action | icpc | **dropped** | — | same as #30; the lease lapses by itself after 2 idle turns, so nothing needs releasing |
| 32 | — | action | — | **new** | `direct_message(recipients[], content)` | private message to one teammate or a sub-group (upstream `TOOLING_GAPS.md` §2 listed this as deferred) |
| 33 | — | action | — | **new** | `select_problem(problem_id)` | claim a problem (also the target of #21) |
| 34 | — | action | — | **new** | `skip_problem(reason?)` | release the current problem |
| 35 | — | action | — | **new** | `inspect_problem(problem_id?, focus?)` | read statement + full version / review / submission history; upstream had no readable history |
| 36 | — | action | — | **new** | `triage_problem(problem_id, priority, reason?)` | team priority `high/normal/low/hopeless` |
| 37 | — | action | — | **new** | `assign_problem(agent, problem_ids[], reason?)` | leader replaces a teammate's work list (centralized baseline) |
| 38 | — | action | — | **new** | `request_review(content, reviewer?)` | ask for a review; never approves |
| 39 | — | action | — | **new** | `review_answer(problem_id, version_hash?, decision, content)` | independent approve/reject pinned to a version hash; upstream had only `speak` |
| 40 | — | action | — | **new** | `finish_contest(reason?)` | explicit terminal action with completion gates |
| 41 | — | action | — | **new** | `check_budget` | turns / API / tokens / clock / penalties / blank problems on demand |

## Tool allowlist changes (`COMPETITION_TOOL_REGISTRY`)

| | Upstream | v6 |
|---|---|---|
| Competitions listed | 39 | 19 |
| `ieo_business_case` | `use_calculator, execute_code, web_search` | `web_search` |
| `ijso_practical` | `use_calculator, inspect_environment` | `use_calculator, read_lab_equipment` |
| `cybench`, `ccdc`, `wro`, `eoes`, `science_olympiad`, `cfa_research_challenge`, `ichto`, `pumac_power`, `vis_moot`, `wharton_investment`, `gcch_harvard`, `ioai_team`, `envirothon`, `mystery_hunt`, `nyu_ctf_bench`, `debatebench`, `ethics_bowl_*`, `odyssey_of_the_mind`, `wmtc`, `qanta`, `science_bowl` | present | absent (fall back to `contest_rules.encoded_tools` if a rules entry exists, else no tools) |
| Unlisted competitions | tools by capability token | same, but a capability can never grant a tool the contest rules forbid |

## Plumbing changes that apply to every row

| | Upstream | v6 |
|---|---|---|
| Definition | three hand-kept lists (`ALL_ACTIONS`, `TOOL_ACTIONS`, prompt string) + a separate ICPC JSON prompt | one typed `ActionSpec` per action; prompt text, JSON schema, function tools and validation all rendered from it |
| Wire format | `ACTION: name \| PAYLOAD: text`; ICPC: one JSON object | typed `{action, arguments}` via native function calling / emulated / prompt-json; old `ACTION \| PAYLOAD` still parsed through the 15 aliases |
| Actions per response | every `ACTION:` block executed in order | only the first validated call executes |
| Forbidden action | rewritten to `sleep`; non-submitter `submit_final` redirected to `write_scratchpad` | not advertised in the schema; a slip is logged as `action_error` |
| Visibility | inferred from the result string | declared per spec (`private` / `team` / `contest`) + explicit DM recipients |
| Budget | 1 turn per action | per-spec `turns`, `tool_calls`, `submission_attempts`, `terminal` |
| Communication budget counts | `speak` (default) | `speak`, `direct_message`, `share_note` |
