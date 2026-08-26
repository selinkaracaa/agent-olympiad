# Tooling gaps

## Priority principle: correct feedback and isolation first

Adding tool names does not improve validity if results reach the wrong agent,
secret data leaks, host code executes unsafely, or nominally shared resources
are unconstrained. The first priority is correct ownership, visibility,
grading scope, and reproducible timing. Tool breadth comes after those
invariants.

## Evidence-based priorities

### 1. Per-agent observations — fixed and tested

**Status: implemented.** Tool results are queued for the calling agent,
included once in that agent's next prompt, marked private in the action log,
and not copied into public chat. `tests/test_observability.py` verifies caller
delivery, non-delivery to peers, one-time consumption, and transcript fields.
Programming submission feedback is likewise private.

Remaining work is stress testing across every protocol and ensuring
orchestrator/synthesis paths do not consume another agent's pending result.

### 2. Private and direct messaging

**Status: baseline-specific private memory implemented; direct
agent-to-agent messaging deferred.** `memory_solo` has bounded private memory.
There is no general private-note action or addressed channel with sender,
recipient, delivery, budget, and transcript visibility semantics.

Priority implementation should distinguish private self-memory, direct
messages, public speech, and shared artifacts. Graders need access to the full
audit log while agents receive only authorized views.

### 3. Bounded per-agent memory

**Status: baseline-specific implementation; general policy partial.**
`memory_solo` enforces a bounded recalled private store, and the ICPC session
has private/shared memory with explicit publication. Ordinary collaboration
still injects full public history and unbounded-looking private-note text.

Add per-agent byte/token/item limits, deterministic eviction, scope labels,
and memory-use accounting. Bounds should be part of the experimental resource
envelope, not silently provider-dependent context truncation.

### 4. Shared versioned files and locks

**Status: deferred.** The common scratchpad is a single replaceable string
without versions, diffs, file ownership, merge conflicts, locks, or a
one-owner workstation lease.

Add versioned read/write operations, compare-and-swap or leases, immutable
history, and explicit conflict results. This is required to study handoffs,
parallel editing, stale state, and one-computer contests honestly.

### 5. C++ sandbox

**Status: implemented core; integration and coverage partial.** The Docker
judge compiles C++17 with network disabled, a read-only container,
capabilities dropped, no-new-privileges, PID/memory/CPU limits, and fails
closed when Docker is unavailable. Tests inspect the command contract.

Priorities are end-to-end mounted LiveOIBench packages, custom checker/grader
hardening, image pinning/digests, output quotas, cleanup, and platform/CI
coverage. Never fall back to host execution for untrusted submissions.

### 6. Multimodal task fidelity

**Status: partial.** PDF/image ingest and some artifact paths exist, but many
benchmarks are text extractions. Diagrams, charts, star maps, slide delivery,
oral exchanges, and lab equipment can materially determine task difficulty.

Store source page references and assets, verify agent-visible rendering, and
record modality-loss flags per task. Physical manipulation should remain
deferred rather than represented as full-fidelity text.

### 7. Official tests

**Status: LiveOIBench adapter ready; broad official judging deferred.** The
adapter validates locally mounted test/subtask paths without exposing contents
or running upstream scripts. The upstream local research checkout documents
403 problems and official test shards. The repository ICPC benchmark mostly
has no official secret bundles; one Kattis sample path cannot support official
correctness claims.

Acquire and checksum authorized official bundles, map checker/subtask
semantics, keep test contents in the trusted judge boundary, and label every
result `official-secret`, `sample-only`, or `proxy`. No automatic download
should occur during evaluation.

### 8. Timestamps and event time

**Status: partial/deferred.** Runs have coarse artifact timestamps and turns
carry ordering, but message/action events lack a uniform monotonic timestamp
and duration schema. Simulated minutes are not enough to reconstruct latency,
parallelism, queue waits, handoffs, or time-to-verdict.

Record UTC wall time, monotonic elapsed time, simulated contest time, turn,
causal parent, and start/end timestamps for calls, tools, messages,
workstation leases, submissions, and verdicts. Keep wall-clock performance
separate from the reproducible contest-time model.

## “More tools” versus valid tools

**Correct feedback/isolation work:** caller-only observations, authorization
views, direct-message privacy, version/lock semantics, sandbox boundaries,
secret-test separation, deterministic clocks, and complete audit logs.

**Additional capability work:** browsers, richer IDEs, plotting, domain
software, slide editors, lab simulators, and more search providers.

The second category is useful only after the first can establish who used a
tool, what they were allowed to observe, what resource it consumed, and
whether its result was graded in the claimed scope.
