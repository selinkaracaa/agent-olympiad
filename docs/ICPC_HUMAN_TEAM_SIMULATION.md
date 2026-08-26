# Human ICPC Team Simulation

## Purpose

This document defines a source-grounded human-team protocol for an onsite ICPC
World Finals-style contest. It does not define an Agent JSON schema and does not
prescribe an implementation. Its purpose is to answer a prior question:

> Which official contest constraints make teamwork necessary, and what human
> collaboration can emerge under those constraints?

The target research question is:

> Can a multi-agent system develop effective, human-like teamwork when it faces
> the same task, resource, scoring, and information constraints as an onsite
> ICPC team?

This is different from asking whether three language models solve more isolated
problems than one model. A faithful simulation must reproduce the coupled
contest: three contestants, a packet of problems, one shared workstation, a
five-hour clock, an online judge, and a score determined by both solved problems
and time penalty.

## Scope and source discipline

### Normative target

The normative target is the standard onsite **2026 ICPC World Finals** format.
Regional and qualifying contests may use different materials, languages,
hardware, judge systems, clarification policies, tie-breakers, and scoreboard
freeze rules. Those variations are parameters, not universal ICPC facts.

Normative claims below come from:

1. [2026 ICPC World Finals rules](https://worldfinals.icpc.global/2026/about/),
   especially sections 4, 7, 8, 9, 10, and 18.
2. The official
   [World Finals Programming Environment](https://docs.icpc.global/worldfinals-programming-environment/).
3. Official
   [World Finals On-Site Registration instructions](https://icpc.global/worldfinals/on-site-registration).
4. The official
   [2025 ICPC Fact Sheet](https://icpc.global/static/media/ICPC-Fact-Sheet-2025.38e5ecab.pdf),
   used only to corroborate the stable public contest format.

Regional examples are explicitly labeled. Human strategy examples are
secondary or anecdotal evidence and are never promoted into official rules.

### Three epistemic layers

Every statement in the eventual benchmark should belong to exactly one layer:

- **Official competition rule**: a requirement imposed by the contest.
- **Human collaboration dynamic**: behavior that may emerge because of the
  rules, but is not mandatory.
- **Simulation design choice**: a modeling mechanism used to make the official
  constraints executable.

For example:

- “The team receives one shared workstation” is an official rule.
- “Two teammates solve on paper while one codes” is a possible human dynamic.
- “Workstation access is represented by an exclusive lease” is a simulation
  design choice.

Conflating these layers would make the benchmark circular: agents would appear
to discover teamwork that the prompt had already assigned to them.

## Official World Finals baseline

### Team and contest

- A finalist team consists of exactly three contestants. The 2026 rules do not
  permit a reserve to replace one of the qualified finalists (§4).
- The contest is scheduled for five hours. The Finals Director may extend it
  for unforeseen circumstances and attempts to notify all teams uniformly
  (§7).
- The team receives a set of English-language programming problems. The exact
  number is event-specific; the 2026 rules describe recent championships as
  having ten or more problems (§7). The simulation must therefore accept a
  problem packet as an event input rather than hard-code a constant.
- Problems may be attempted in any order. Scoring rewards solving more
  problems, so the contest is a portfolio-allocation problem, not three copies
  of a single-problem task.

### One shared workstation

- Each team receives one computer (§9).
- The current official Programming Environment says explicitly that one
  workstation is shared between team members and identifies this as the
  traditional ICPC setup.
- Hardware substitutions are not allowed. The team cannot introduce another
  keyboard, computer, terminal, or private execution device.
- Only the shared workstation provides the contest editor, compiler, local
  execution environment, and contest-control submission interface.

The single workstation is the central collaboration bottleneck:

> Human reasoning can proceed in parallel; machine-mediated implementation and
> testing must proceed serially.

### Submission and judge feedback

- A proposed solution submitted to the judges is a run (§7).
- The judge compiles and executes source code against hidden tests in a
  sandbox, as documented by the Programming Environment.
- Relevant verdict classes are Accepted, Compilation Error, Run-Time Error,
  Time-Limit Exceeded, and Wrong Answer (§7).
- A rejected run may be corrected and resubmitted.
- The rules do not promise the failing test, a counterexample, or a detailed
  diagnostic. Hidden tests remain authoritative and inaccessible.

### Scoring

World Finals ranking is determined by (§8):

1. most problems solved;
2. least total time penalty;
3. earliest submission time of the team's last accepted run.

For each solved problem, penalty is:

```text
minutes from contest start to first Accepted run
+ 20 × prior rejected runs, excluding Compilation Error
```

Rejected runs on a problem that is never solved do not contribute to the final
time penalty. This creates a conditional risk: an early rejection is costly
only if the team later converts the problem to Accepted, but debugging that
problem still consumes scarce contest and workstation time.

### Clarifications

- A contestant may submit a clarification request when a problem is believed
  to contain an ambiguity or error (§7).
- Judges may answer the team or issue a clarification when they agree that the
  statement requires correction.
- The World Finals text does not require every response to be broadcast to all
  teams. The simulation must distinguish a team-specific response from a
  globally issued clarification.

Clarification is a contest action, not ordinary teammate communication. It has
latency, an authoritative responder, and possible global effects.

### Scoreboard and uncertainty

- During the contest, a scoreboard displays rank and performance statistics
  (§§7–8).
- Accepted-run notifications may be suspended at an announced time while
  rejected-run notifications continue.
- The scoreboard is typically frozen before the end, but the World Finals rules
  do not prescribe a universal exact freeze time.
- Pending results are later revealed through the Resolver (§18).

The freeze changes the team's information state, not the underlying judge
state. A faithful model must separate what the judge knows from what the team
can observe.

### Communication, materials, and outside help

- Contestants may converse only with teammates and designated contest
  personnel (§10).
- Systems staff may help with system failures but not with solving a problem.
- Outside problem-solving help is prohibited.
- Contestants may not bring additional computers, terminals, calculators,
  arbitrary electronics, or machine-readable software/data into the team area
  (§§7, 9).
- Current World Finals rules permit inspected, pre-deposited materials,
  including printed Team Reference Documents and inspected dictionaries. Exact
  page counts and administrative procedures are versioned event details; the
  current registration instructions specify up to 25 single-sided Letter/A4
  pages for a Team Reference Document.
- The contest workstation has no Internet or root access. Approved local
  documentation is available.
- The current official environment lists C, C++, Java, Kotlin, and Python 3.
  Versions and compiler flags are event-specific.
- Internal AI functionality in installed IDEs is disabled.

## Regional variability

The following must not be encoded as universal World Finals rules:

- EUC 2026 fixes the scoreboard freeze one hour before the finish; World Finals
  rules only say a freeze typically occurs.
- Some North American regional rules allow broader books, notes, and papers
  than the inspected World Finals material policy.
- Hardware can vary by site; some events require or permit team-provided
  equipment.
- World Finals documentation currently specifies PC², while other events may
  use DOMjudge, Kattis, or another contest-control system.
- Languages, compiler versions, memory limits, and machine images vary.
- Regional minimum problem counts and tie-breakers vary.
- Some regional rules explicitly broadcast an agreed clarification to every
  team; the current World Finals wording is less specific.

The human protocol therefore separates a stable core from event parameters:

```text
Stable core:
  team_size = 3
  shared_workstations = 1
  multi_problem_packet = true
  judge_hidden_tests = true
  outside_help = forbidden

Event parameters:
  duration
  problem_packet
  languages_and_limits
  material_policy
  judge_system
  clarification_distribution
  scoreboard_freeze
  tie_breakers
```

## How rules induce collaboration

The benchmark should model causal pressures, not preferred team roles.

### Three people plus one workstation

**Rule:** Three contestants share one workstation.

**Pressure:** Only one person can perform machine-mediated implementation,
compilation, testing, or submission at a time.

**Possible emergent behaviors:**

- parallel statement reading and paper reasoning;
- a ready-to-code queue;
- workstation scheduling and preemption;
- algorithm-to-coder handoff;
- visible-code review by a teammate;
- temporary specialization and later role rotation.

**Observable signals:**

- workstation utilization and idle time;
- queue length and wait time;
- keyboard ownership duration and rotation;
- amount of useful off-machine work completed while the workstation is busy;
- handoff frequency, completeness, and repair cost.

No rule says that one contestant must permanently be the coder. Fixed
driver/navigator/tester identities would be an imposed benchmark strategy, not
an ICPC rule.

### Many problems plus a five-hour clock

**Rule:** The team receives more problems than team members and has a fixed
contest duration.

**Pressure:** Full-set coverage, difficulty estimation, and opportunity cost
matter. Time spent on one hard problem prevents progress elsewhere.

**Possible emergent behaviors:**

- early problem scouting;
- provisional ownership;
- difficulty and implementation-risk estimation;
- abandonment and reassignment;
- maintaining several partially developed candidates;
- dynamic reprioritization as easy problems are discovered.

**Observable signals:**

- time to first read and full-packet coverage;
- duplicate reading or duplicated algorithm work;
- time from viable idea to workstation request;
- abandoned-work rate and recovery of abandoned ideas;
- accuracy of difficulty and implementation-time estimates;
- changes in priority after new evidence.

### Solves plus penalty time

**Rule:** Rank depends first on solved count and then on time penalty; most
rejected runs add 20 minutes if the problem is eventually solved.

**Pressure:** Teams must balance early submission against review and testing.
They must also decide whether debugging an uncertain problem is worth the
workstation time.

**Possible emergent behaviors:**

- pre-submission peer review;
- explicit confidence thresholds;
- edge-case generation by a non-coder;
- escalation after repeated rejection;
- switching from implementation debugging back to algorithm validation;
- choosing a safer ready problem over a risky nearly complete one.

**Observable signals:**

- pre-submission review coverage;
- rejected-run rate and eventual penalty minutes;
- correction-causing reviews;
- time from rejection to diagnosis and resubmission;
- number of repeated submissions without a changed diagnosis;
- calibration between stated confidence and verdict.

### Hidden tests and categorical feedback

**Rule:** The judge returns a categorical verdict but not hidden tests.

**Pressure:** Failure diagnosis must combine algorithm reasoning, code
inspection, local tests, and teammate knowledge.

**Possible emergent behaviors:**

- asking another teammate to reproduce or isolate the failure;
- transferring debugging ownership;
- revisiting proof or complexity assumptions;
- constructing adversarial tests on paper before requesting workstation time.

**Observable signals:**

- whether diagnosis distinguishes algorithm, implementation, complexity, and
  environment failures;
- reviewer diversity after rejection;
- diagnostic latency;
- local test quality before resubmission;
- whether a handoff preserves known evidence.

### Restricted external resources

**Rule:** Internet, outside help, extra devices, and arbitrary machine-readable
resources are unavailable.

**Pressure:** The team must pool internal knowledge and approved references.

**Possible emergent behaviors:**

- asking which teammate remembers a theorem or implementation pattern;
- consulting a Team Reference Document;
- explaining knowledge instead of linking to an external source;
- shifting a problem to a teammate with relevant expertise.

**Observable signals:**

- source of decisive knowledge;
- approved-reference use;
- unsupported external claims;
- knowledge-transfer latency;
- dependence on one teammate's memory.

### Scoreboard freeze

**Rule:** Accepted notifications and standings may become incomplete near the
end of the contest.

**Pressure:** Strategy must operate under partial information.

**Possible emergent behaviors:**

- reducing scoreboard-driven switching;
- prioritizing internal confidence over rank feedback;
- submitting before the end despite unresolved public status;
- changing risk tolerance.

**Observable signals:**

- strategy before and after the freeze;
- response to pending submissions;
- decisions based on stale versus internal evidence;
- final-hour risk profile.

## Human simulation state

The state below is a simulation design, not an official rule.

### Contest state

Track:

- current contest time and scheduled end;
- problem packet;
- team score and penalty;
- visible scoreboard state;
- internal judge state;
- accepted-notification suspension and freeze state;
- global clarifications;
- event parameters and permitted materials.

Time is a shared resource. Reading, discussing, handing off, waiting, typing,
compiling, testing, submitting, and receiving a verdict all consume time.

### Participant state

For each of three participants, track:

- current problem;
- current activity: scouting, reading, designing, proving, reviewing, coding,
  testing, debugging, communicating, waiting, or consulting references;
- private paper notes and hypotheses;
- algorithm confidence and unresolved assumptions;
- known constraints, edge cases, and complexity analysis;
- perceived state of every problem;
- workstation request and queue position;
- fatigue, interruption count, and recent context switches;
- awareness of verdicts, clarifications, and visible standings.

Domain strengths may differ, but they are capabilities rather than permissions.
Every contestant may reason, communicate, use the workstation when acquired,
review code, and submit.

### Problem state

For each problem, track:

- unread, skimmed, or fully read, including by whom;
- statement version and applicable clarifications;
- estimated difficulty and implementation time;
- candidate algorithms and their authors;
- proof status, complexity validation, and unresolved assumptions;
- known edge cases and test plan;
- provisional owner, contributors, reviewer, and blockers;
- priority and reason for that priority;
- implementation state: none, paper/pseudocode, workstation draft, compiled,
  locally tested;
- workstation files and source snapshot;
- submission history and verdicts;
- potential and realized penalty;
- solved, abandoned, or scheduled-for-revisit state.

Problem ownership is advisory and transferable. It must not prevent another
participant from contributing or taking over.

### Shared workstation state

Track one exclusive workstation with:

- current owner;
- ownership start time;
- active problem and files;
- source snapshot;
- active operation: editing, compiling, local execution, testing, or submitting;
- visible terminal/editor state;
- queue of workstation requests;
- pending judge runs;
- installed languages and approved local documentation.

If no participant owns the workstation, no one can compile, execute, edit
machine files, or submit. The other two participants never receive hidden
terminals or private execution channels.

They may still:

- read statements;
- reason and write pseudocode on paper;
- prepare tests manually;
- talk with teammates;
- inspect code that is visibly shared;
- consult approved printed materials;
- prepare a handoff.

### Workstation request

A queue entry contains:

- requester;
- problem;
- requested operation;
- readiness and confidence;
- estimated workstation duration;
- urgency and expected score value;
- blocking dependencies.

The queue is visible and advisory. The team may override it, preempt the owner,
or leave the machine idle. These decisions are observations, not automatically
classified as correct or incorrect.

### Handoff state

A handoff may contain:

1. problem identity and current objective;
2. intended algorithm and invariants;
3. complexity and resource-limit argument;
4. input/output hazards;
5. known edge cases and tests;
6. current source status or pseudocode;
7. known defects and unresolved questions;
8. next concrete action.

The simulation records what was actually communicated. It does not silently
copy all private notes into the recipient's state.

### Judge state

Each run tracks:

- problem;
- submitting contestant;
- source snapshot;
- language;
- submission time;
- judging start and completion;
- internal verdict;
- verdict visible to the team or temporarily pending;
- whether the run counts as a rejected attempt for eventual penalty.

The lifecycle is:

```text
draft
  → submitted
  → judging
  → Accepted | CompilationError | RunTimeError | TimeLimitExceeded | WrongAnswer
```

Accepted marks the problem solved at submission time. Rejection returns the
problem to a diagnosable state; it does not automatically assign a debugger or
force an immediate resubmission.

### Clarification state

A clarification tracks:

- requester;
- problem;
- claimed ambiguity or error;
- submission time;
- pending, team-specific response, or global clarification;
- response text and affected statement version;
- which participants have read the response.

## Human action space

### Off-workstation actions

Any participant may:

- scan, read, or reread a problem;
- estimate difficulty and implementation risk;
- claim, release, transfer, or reprioritize a problem;
- derive an algorithm or proof;
- analyze complexity and limits;
- write pseudocode or manual tests;
- consult approved printed references;
- explain an idea or request review;
- challenge an assumption;
- review visible code;
- prepare or perform a handoff;
- request or cancel workstation access;
- inspect visible verdicts, clarifications, and scoreboard information;
- abandon or revisit a problem.

### Workstation actions

Only the current workstation owner may:

- edit source files;
- invoke a compiler;
- execute a program;
- run local tests;
- interact with the contest-control system;
- submit a run;
- inspect workstation-local documentation.

Workstation ownership grants temporary resource access, not authority over the
team or permanent problem ownership.

### Contest-official actions

A contestant may:

- submit a solution run through the workstation;
- submit a clarification request;
- report a technical problem to designated staff.

### Disallowed actions

Participants may not:

- access the public Internet;
- use another computer, terminal, calculator, phone, or electronic device;
- obtain outside problem-solving assistance;
- inspect hidden tests or judge internals;
- import unapproved machine-readable code or data;
- create simultaneous private execution environments for off-workstation
  teammates.

## State transitions

### Problem work

```text
unread
  → skimmed
  → investigated
  → candidate_algorithm
  → reasoned
  → ready_to_code
  → queued_for_workstation
  → coding
  → locally_tested
  → submitted
```

Transitions are reversible. A Wrong Answer may move a problem to debugging,
algorithm reconsideration, reassignment, or abandonment. A new clarification
may invalidate a previously reasoned solution.

### Workstation ownership

```text
free
  → requested
  → acquired_by_participant
  → active_work
  → released | preempted
  → free
```

Acquisition and release should be explicit. Context switching consumes time,
especially when the new owner lacks a complete handoff.

### Verdict and recovery

```text
submitted
  → judging
  → Accepted

submitted
  → judging
  → Rejected
  → classify_failure
  → inspect_code | construct_tests | revisit_algorithm | request_help
  → ready_to_code
  → resubmit | abandon
```

The model must not implement rejection as unlimited private self-reflection by
the original coder. Keeping ownership, transferring it, or asking for help are
all available choices whose consequences can be measured.

## Five-hour protocol example

This example demonstrates valid dynamics; it is not an optimal script.

### 00:00–00:05: packet coverage

- Participant A scans Problems A and B.
- Participant B scans C and D.
- Participant C scans E and F, then continues through the packet if time allows.
- The workstation remains free because no implementation is ready.

At 00:05:

- A estimates A as a low-risk greedy problem and requests the workstation.
- B has a partial shortest-path state design for C.
- C considers F a likely simulation problem but has not completed its test plan.

The team chooses A's ready request. This is the first resource-allocation
decision; it is not predetermined by identity.

### 00:05–00:16: serial coding, parallel reasoning

- A owns the workstation and implements A.
- B continues proving C off-machine.
- C completes F's algorithm, constructs examples, and prepares a handoff.

At 00:14 A requests review. C notices an `n = 1` boundary error in the visible
code. A fixes it, runs local tests, and submits.

At 00:16 A receives Accepted. The workstation becomes available.

### 00:16–00:31: pipeline

- B's C solution is now reasoned and enters the workstation queue.
- C's F solution is also ready but estimated to take longer.
- B acquires the workstation for C.
- A begins scouting a previously unread problem G.
- C continues preparing F and reviews B's implementation when useful.

This is a pipeline:

```text
scout
  → reason
  → queue
  → acquire workstation
  → implement
  → review and test
  → submit
  → react to verdict
```

### 00:31–00:40: failure recovery

B submits C and receives Wrong Answer.

The team does not assume the failure is a local typo. B explains the invariant
and implementation. C attempts to construct an adversarial edge case while B
checks code. A continues off-machine work on G.

C identifies an initialization case inconsistent with B's invariant. B repairs
the source and resubmits. Accepted arrives at 00:40. If C had instead found the
algorithm invalid, the rational transition could have been back to paper
reasoning or abandonment rather than immediate workstation reuse.

### Mid-contest: dynamic roles

Later, A may own the workstation for G while B reviews and C scouts. After a
rejection, C may take over the workstation because C understands the failing
case. No permanent role permission changes are needed; the observed
specialization is a consequence of task state and expertise.

### Final hour: partial scoreboard information

When accepted notifications or standings become incomplete, the team must
distinguish:

- internally tested but unsubmitted work;
- submitted and visibly rejected work;
- submitted work whose accepted status may be pending;
- solved problems already confirmed.

Reprioritization now relies more heavily on internal confidence and remaining
workstation time than on live rank.

## Evaluation framework

The future benchmark should report three separate outcomes. A high contest score
must not conceal rule violations, and a verbose discussion must not count as
good collaboration by itself.

### Performance

Measure:

- number of solved problems;
- official total time penalty;
- final rank or normalized rank when a comparison field exists;
- time to first Accepted;
- solve timeline;
- accepted runs by problem;
- rejected runs and realized penalty;
- remaining viable work at contest end.

### Rule compliance

Measure:

- concurrent or unauthorized workstation access;
- off-owner compile, run, edit, or submission attempts;
- Internet, extra-device, outside-help, or hidden-test access;
- use of unapproved references;
- invalid communication with non-team actors;
- submission and clarification protocol violations.

Compliance should be evaluated independently from score. An illegal extra
terminal may improve solves while invalidating fidelity.

### Collaboration quality

These metrics are descriptive evidence, not a prescribed ideal role structure:

- time to packet coverage;
- useful off-workstation parallel work;
- workstation utilization and avoidable idle time;
- workstation queue wait and preemption;
- handoff frequency, completeness, and repair cost;
- time from reasoned solution to implementation;
- duplicate reading and duplicate algorithm effort;
- problem reassignment and abandoned-work recovery;
- pre-submission review coverage and reviewer diversity;
- corrections caused by peer review;
- rejection-to-diagnosis and rejection-to-resubmission time;
- repeated submissions without a changed diagnosis;
- communication latency from discovery to team awareness;
- workload and workstation-ownership imbalance;
- fraction of solves with substantive contributions from multiple teammates;
- confidence calibration;
- strategy changes after verdicts, clarifications, and scoreboard freeze.

Collaboration quality must be interpreted conditionally. For example, low
keyboard rotation can be effective if freely chosen by a team with a fast coder;
it becomes suspicious only when paired with bottlenecks, fatigue, poor handoffs,
or unused teammate capacity.

## Human dynamics supported by secondary evidence

These observations justify making behaviors possible, not mandatory:

- An [MIT interview with the 2022 winning team](https://computing.mit.edu/news/mit-wins-world-finals-of-the-45th-international-collegiate-programming-contest/)
  describes alternating coders, cross-checking solutions, combining partial
  ideas, and rejecting a permanent coder/thinker split because of fatigue.
- G. K. van der Vegt, J. A. van der Vegt, and A. W. van der Vegt discuss
  specialization, early problem assessment, and one-computer scheduling in
  [“Programming contest strategies”](https://doi.org/10.1145/332132.332139).

The protocol therefore permits stable specialization, rapid rotation, or a
hybrid strategy. It does not declare one of them the ICPC rule.

## Fidelity audit of the current repository

The current repository does not yet simulate this protocol.

### Single problem instead of a contest packet

`OlympiadEnvironment` is constructed with one `problem_id` and loads one row
from `data/benchmarks/icpc/benchmark.json`. Although the data directory contains
many ICPC problems, one run does not expose a shared multi-problem packet or
allow portfolio allocation across problems.

Consequence: problem scouting, packet coverage, task allocation, abandonment,
and cross-problem reprioritization cannot emerge.

### No exclusive workstation owner

The ICPC rule card permits `execute_code`, and the environment exposes that tool
to agents without a workstation lease or owner.

Consequence: all three agents can effectively receive parallel computers,
violating the dominant onsite constraint.

### Static benchmark-assigned roles

The current card assigns driver/synthesizer, navigator/algorithm designer, and
tester/edge-case hunter.

Consequence: division of labor is scripted before the task begins. The
benchmark cannot determine whether agents discover specialization, rotate
roles, or recover from a poor initial allocation.

### One final submission instead of per-problem runs

The environment has a single `submitted` flag and one final-answer workspace.

Consequence: it cannot represent independent problem states, repeated runs,
judge latency, verdict histories, Accepted times, or conditional penalty.

### No operational programming judge

ICPC benchmark rows mark the programming judge as deferred. `grade_submission`
reports that an isolated judge sandbox is required.

Consequence: Wrong Answer, Compilation Error, Run-Time Error, Time-Limit
Exceeded, hidden tests, and failure recovery are not executable contest events.

### No clarification or scoreboard state

The environment has no clarification lifecycle, public standings, accepted
notification suspension, or scoreboard freeze.

Consequence: the benchmark cannot evaluate authoritative statement updates or
strategy under partial contest information.

### Turn budget is not a contest clock

The card maps five hours to 60 abstract turns using an approximate
minutes-per-turn conversion.

Consequence: workstation actions, reading, communication, waiting, compilation,
judging, and context switching do not consume a common continuous resource with
different durations.

### Current fidelity label

Until packet-level state, exclusive workstation access, repeated judged runs,
and official scoring are implemented, the current environment is an ICPC-themed
single-problem collaboration proxy rather than a World Finals-equivalent
simulation. This document records that conclusion but does not modify the rule
card.

## Acceptance criteria before Agent environment design

Do not translate this protocol into JSON or code until the next design phase can
answer all of the following:

1. Does one run expose a full problem packet and one five-hour contest clock?
2. Can every participant reason off-machine while exactly one participant owns
   the workstation?
3. Are edit, compile, run, and submit impossible without ownership?
4. Can ownership rotate dynamically without changing fixed role permissions?
5. Does each problem retain independent reasoning, implementation, review,
   submission, verdict, and penalty state?
6. Does the judge support AC, CE, RTE, TLE, and WA with hidden tests?
7. Is World Finals penalty computed exactly, including the CE exception and
   unsolved-problem behavior?
8. Can the team submit and receive clarifications?
9. Are internal judge truth and team-visible scoreboard information separated?
10. Are official constraints, emergent behavior, and simulation choices labeled
    separately?
11. Can performance, compliance, and collaboration be reported independently?
12. Can a team choose its own division of labor rather than inherit one?

Only after these questions have concrete answers should the human protocol be
translated into an Agent action/state schema.

## Template for later competition analyses

ICPC establishes a reusable analysis sequence for other competitions:

1. Select a precise official competition variant and season.
2. Extract only primary-source competition constraints.
3. Identify scarce resources, temporal coupling, information boundaries, and
   failure feedback.
4. Explain which human behaviors those constraints make useful, without
   declaring them rules.
5. Define human state, action space, and environment transitions.
6. Define performance, compliance, and collaboration observations separately.
7. Audit the current repository against the human protocol.
8. Design Agent JSON and runtime mechanisms only after the protocol is stable.

Different competitions should produce different bottlenecks. ICPC is organized
around a shared workstation and multi-problem scheduling. A moot court may be
organized around opposing positions and oral response; a laboratory competition
around scarce instruments and chain-of-custody; a writing event around staged
individual work and peer review. The method transfers, not the ICPC state
machine itself.
