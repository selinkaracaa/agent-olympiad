# Capability matrix

## Status legend

- **Measured (M):** implemented observable with a runnable current path.
- **Proxy (P):** observable exists but does not faithfully measure the human
  construct or uses a heuristic/LLM grader.
- **Deferred (D):** required state, modality, grader, or experiment is absent.

Statuses describe repository capability, not completed paper-scale evidence.
Deterministic transcript metrics are measured as logs but remain **proxies for
semantic quality**.

## Competition families × abilities × grader coverage

Abilities are **PS** problem solving/decomposition, **SR** strategy/resource
allocation, **COM** communication, and **COH** cohesion beyond independent
subagents.

| Family | PS | SR | COM | COH | Current grader coverage / observable |
|---|---|---|---|---|---|
| IOL team | P | P | P | D | rubric LLM; transcript/log proxies; images may be incomplete |
| IOAA group | P | P | P | D | some gold shorts; charts/data and fastest-time rule are partial |
| ARML Power | P | P | P | D | proof rubric proxy; packet transcripts |
| ARML National Team | M | P | P | D | curated short-answer gold; strategy/communication logs |
| ARML National Power | P | P | P | D | proof rubric proxy |
| ARML Local | M | P | P | D | multipart gold; preliminary protocol matrix; no completed cohesion decomposition |
| IJSO practical | P | P | P | D | written-report rubric; no physical measurements |
| IEO business case | P | P | P | D | slide-text/rubric path; full presentation fidelity deferred |
| IYPT | P | P | P | D | report/debate rubric; live oral and experiment fidelity deferred |
| HMMT team | P | P | P | D | rubric path; packet dependencies only partially represented |
| HMMT guts | M | P | P | D | curated gold available; progressive release/live scoring partial |
| MCM | P | P | P | D | report rubric; 99-hour process compressed |
| ICM | P | P | P | D | report rubric; 99-hour process compressed |
| Fyziklání | P | P | P | D | numerical/rubric coverage varies; progressive online queue partial |
| Purple Comet | M | P | P | D | curated HS/MS gold for selected years; shared-computer fidelity partial |
| ITYM | P | P | P | D | research/report rubric; months of preparation and oral fight deferred |
| WSC writing | P | P | P | D | essay rubric; staged handwriting/peer-edit process is a proxy |
| Jessup | P | P | P | D | memorial rubric; oral pleading and multi-month research deferred |
| IIOT | P | P | P | D | programming interface exists; full official tests and two-PC fidelity deferred |
| ICPC | P | P | P | D | sample judge and sandbox components measured; official packet/tests incomplete |

Across families, current deterministic process observables include talk-share
Gini, silence, lexical redundancy, addressed and question-follow-up rates,
tool-observation reuse, parse failures, part coverage, duplicate effort,
budget utilization, premature submit, verification terms, answer churn,
unresolved disagreement, synthesis fidelity, leader concentration, penalties,
and rule violations. MultiAgentBench-style CS is an LLM-judged proxy.

## Baselines × capability isolated

| Baseline | Status | Capability isolated | Required interpretation |
|---|---|---|---|
| Plain single agent | M | raw solo ability | May underuse budget through early submit |
| Equal-budget single agent | M | team structure at matched call/turn envelope | Match actual model/context policies |
| Memory solo | M | bounded persistence without peers | Not communication |
| Self-consistency | M | independent sampling plus deterministic voting | Not collaboration |
| Subagent | M | decomposition and aggregation with isolated workers | Reference point for division gain |
| Round-table discussion | M | full-history peer interaction | Includes context/coordination overhead |
| Centralized | M | leader delegation and aggregation | Exposes leader bottleneck |
| Decentralized | M | peer control without manager | Shared history/workspace still available |
| Open table + coach | M | temporary preparation/opening advice | Coach is not a contestant and exits |
| Debate | M | proposals, challenge, evidence, revision, decision | Structured interaction differs from free discussion |
| LiveOIBench best-of-8 | M interface; D full local run | eight independent candidates with oracle official-score selection | External upper anchor, not autonomous collaboration |
| Handicap sweeps | M runner; D paper matrix | sensitivity to solo turns/calls | Needed before resource-robust claims |

## Derived capability comparisons

- **Division gain = subagent − solo:** implemented, but **deferred as a paper
  result** until matched triplets exist.
- **Cohesion gain = interactive team − subagent:** implemented, but
  **deferred as a paper result** for the same reason.
- **Synthesis loss = transcript ceiling − team:** implemented with explicit
  null reasons; **deferred** until a valid transcript-ceiling grader is run.
