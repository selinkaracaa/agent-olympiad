# Human versus agent setting

## Fidelity labels

- **High:** the operative constraint and its consequences are enforced.
- **Partial:** a meaningful analogue exists, but important human mechanics are
  missing.
- **Low:** only prompt text or a coarse proxy exists.
- **Not transferable:** the human rule has no defensible agent equivalent.

Fidelity is assessed per rule. A source-grounded human rule does not imply a
high-fidelity simulator.

## Rule-by-rule transfer assessment

| Human rule or condition | Agent analogue | Fidelity | Assessment |
|---|---|---|---|
| Shared computer | No current one-owner workstation lease in the upstream collaboration environment | Low | Tool authorization exists, but mutual exclusion, handoff, and keyboard/UI contention remain deferred. |
| Fatigue and five-hour duration | Official minutes mapped to bounded turns and simulated minutes | Low | Time scarcity transfers; fatigue, attention decay, breaks, and accumulated motor/cognitive load do not. A 60-turn ICPC run is not evidence of five human hours. |
| Speech bandwidth | Public messages, per-agent message budgets where rules require them, and token limits | Low | Tokenized asynchronous text omits overlap, gesture, prosody, interruption, listening effort, and room awareness. Agent text can be denser and faster than speech. |
| Fixed roles | Protocol roles such as leader, worker, coach, or equal contestant | Partial | Synthetic leader/worker roles are treatments, not claims about human teams. ICPC roles should remain dynamic. |
| Internet access or prohibition | Tool registry plus search blocking; no network in programming sandbox | Partial | Search availability is enforceable in the environment, but model pretraining cannot be ``unlearned,'' and prompt text alone cannot eliminate memorized public solutions. |
| Submissions, feedback, and penalties | `submit_code`, private caller-only verdicts, pending/attempt state in ICPC session, wrong-submission clock cost, deterministic leaderboard scoring | Partial | Core mechanics exist, including 20-minute accounting paths, but official per-problem histories, packet-wide standings, clarifications, freeze behavior, and official tests are incomplete. |
| Physical laboratories | Text, images, supplied files, and report rubrics | Low / not transferable for manipulation | Written reasoning can be assessed; sensing, calibration, dexterity, equipment contention, safety, and real measurement noise cannot currently be reproduced. |
| Heterogeneous skill | Mixed model rosters and role prompts | Partial | Model heterogeneity is measurable, but it differs from human experience, trust, domain specialization, and learning history. Provider/model identity may also change cost and context behavior. |

## Transfer principles

1. Preserve the consequence of a rule, not only its wording. A shared computer
   requires mutual exclusion; ``one computer'' in a prompt is insufficient.
2. Report official, adapted, and deferred dimensions separately.
3. Treat turn count as a reproducible budget proxy, not elapsed human time.
4. Do not infer human-like communication from message count or CS.
5. Do not compare an agent with hidden parallel execution against a human team
   limited to one workstation.
6. For physical and oral contests, label report/text evaluation as a modality
   proxy and avoid claims about full contest performance.

## Threats to human comparison

Public problem contamination, different access to memorized knowledge,
non-human context windows, cloneable teammates, absence of fatigue, model
version drift, judge-model bias, and compressed multi-day preparation all
limit direct human ranking claims. Human standings are appropriate only when
task versions, scoring, resources, feedback, and time semantics are aligned.
LiveOIBench's official tests and human distributions are a useful programming
comparison, but oracle best-of-8 remains a sampling protocol rather than a
human-team analogue.
