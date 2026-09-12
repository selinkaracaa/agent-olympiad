# AgentWorld evaluation metrics

> Primary source: Shu et al., **“AgentWorld: Benchmarking Long-Horizon Collaboration of Multi-agent LLMs”**, COLM 2026 ([paper PDF](https://ryanzhumich.github.io/files/AgentWorld.pdf))  
> Scope: exact metrics and evaluation procedure reported in the paper  
> Last updated: 2026-09-02

## Summary

AgentWorld evaluates **outcomes** with task success rate (**SR**) and partial success rate (**PSR**), and evaluates **collaboration/process efficiency** with causal collaboration effectiveness (**CCE**). Appendix F also defines per-agent contribution (**PAC**) as a diagnostic decomposition of CCE. The main results additionally report average rounds and chats as behavior descriptors; these are not presented as collaboration-quality scores. [§3.5, p. 7; Table 2, p. 8; Appendix F.1.4, p. 19]

## 1. Metric inventory

| Type | Exact name | Definition / formula | Scope and aggregation |
| --- | --- | --- | --- |
| Outcome | **Task Success Rate (SR)** | Each task has a Python verifier. A trajectory succeeds iff **all** success criteria are met; the verifier checks the final game state and may also inspect the trajectory. Dataset SR is the percentage of tasks that succeed. | Used on both the 100 human-annotated **main set** and 100 **augmented variants**, across all eight task categories. Main and augmented SR are reported separately; category SR is also analyzed. [§§3.2, 3.4–3.5, pp. 5–7; §4.1 and Table 2, pp. 7–8] |
| Outcome | **Partial Success Rate (PSR)** | For a task, the fraction of verifier checkpoint items achieved; fully successful tasks receive **PSR = 100%**. Reported PSR is averaged across tasks. | Used on both main and augmented sets for every evaluated model. Example checkpoints include item counts, kill counts, and survival. [§3.5, p. 7; Table 2, p. 8] |
| Collaboration / process | **Causal Collaboration Effectiveness (CCE)** | Let \(T\) be all tool-use and chat actions, \(S\) the actions directly achieving success, and \(C=S\cup\operatorname{ancestors}(S)\) the actions on causal paths to success in the Causal Action Graph. \(\mathrm{CCE}=\lvert C\rvert/\lvert T\rvert\). Failed tasks have **CCE = 0**. | Computed per trajectory and averaged over **all tasks** (failed tasks contribute zero), separately for main and augmented sets. The paper also analyzes CCE conditioned on successful tasks. [§3.5, p. 7; §4.3, pp. 8–9; Eq. 1–2, Appendix F.1, pp. 18–19; Table 2, p. 8] |
| Collaboration / process diagnostic | **Per-Agent Contribution (PAC)** | For agent \(i\), with action set \(T_i\): \(\mathrm{PAC}_i=\lvert C\cap T_i\rvert/\lvert T_i\rvert\). Skew across agents indicates that only a subset drove success. | Defined as an agent-level diagnostic in Appendix F; it is not a headline column in the main benchmark table. [Eq. 3, Appendix F.1.4, p. 19] |
| Behavior descriptor | **Rounds**, **Chats** | Mean rounds completed and chat messages sent per task; no normalized score or quality formula is defined. | Table 2 reports main-set averages. Table 6 also reports average rounds/chats for baselines; Table 3 reports them for a 35-task ablation subset. [Table 2, p. 8; Table 3, p. 10; Table 6, p. 14] |

## 2. Verifiers, causal judge, and aggregation

### Outcome judging

- Human annotators write a task-specific Python verifier with objective checkpoints. It programmatically inspects inventories, kills, survival, and—when needed—the trajectory, so SR/PSR do **not** use an LLM judge. [§§3.2–3.3, p. 5; §3.5, p. 7; example verifiers, Appendix B, pp. 15–16]
- All models use the same task definitions, round protocol, prompts, and tools. The principal comparison runs four models over all 100 main tasks and all 100 augmented tasks. [§4.1, p. 7]
- Table 2 reports SR and PSR separately by split. PSR is a task-level checkpoint fraction averaged over tasks; CCE is likewise averaged over tasks, with failures set to zero. [§3.5, p. 7; Table 2 caption, p. 8]
- Figure 3d's category-level success rate is averaged across the four primary models: Gemini 3 Flash, Claude Haiku 4.5, GPT-5 Mini, and DeepSeek R1-70B. [Figure 3d, p. 6; §4.1, p. 7]

### CCE construction and judge

1. Build a **Causal Action Graph (CAG)** whose nodes are every API call or chat message and whose directed edges mean “action \(x\) causally enabled action \(y\).” [Appendix F.1.1–F.1.2, pp. 18–19]
2. Use an LLM to identify terminal success actions, then sweep backward by round and make inclusive binary causal decisions; marginally helpful actions count as contributing. Each contributing action has equal weight. [§3.5, p. 7; Appendix F.2–F.3, pp. 20–21]
3. The primary CCE judge is **GPT-4.1 at temperature 0**. The paper recomputes CCE with **Claude Sonnet 4** and **Llama-4 Maverick**; model ranking is unchanged and absolute CCE shifts by at most about 0.05. [§4.3, pp. 8–9; Table 5, p. 14; Appendix F.3, p. 20]
4. Human validation covers 84 action-contribution judgments from Gemini 3 Flash and Claude Haiku 4.5 trajectories across 11 tasks: human–GPT-4.1 agreement is **69/84 (82%)**, Cohen’s **κ = 0.64**. GPT-4.1–Claude Sonnet 4 agreement is **84%**, **κ = 0.66**, over 7,298 decisions. Because labeling is inclusive, the authors say CCE is best interpreted as an **upper bound** on genuinely useful actions. [§4.3, pp. 8–9]

## 3. Evaluation dimensions and task coverage

- **Goal completion:** SR asks whether the full primary objective was completed; PSR captures progress through intermediate checkpoints. [§3.5, p. 7]
- **Team action efficiency:** CCE measures the fraction of total team actions causally connected to success, including communication as first-class actions. It is not merely communication volume, nor does it directly measure the fraction of cross-agent edges: both within-agent and cross-agent causal actions can enter \(C\). [Figure 4, p. 6; §3.5, p. 7; Appendix F.1.2–F.2, pp. 19–20]
- **Individual usefulness:** PAC measures useful effort per agent and exposes contribution imbalance. [Appendix F.1.4, p. 19]
- **Behavior/communication volume:** average rounds, chats, and prose-reported action counts describe rollout behavior. The authors separately inspect and cluster communication errors into six categories, reported as counts/ratios over 61 errors; they specify no judge model or formal clustering metric for this analysis, and it is not a benchmark score. [§§4.2, 4.5, pp. 8, 10; Table 4, p. 14]
- **Coverage:** the metrics apply to AgentWorld’s 200 tasks—100 main plus 100 augmented—spanning combat, crafting, gathering, trading, exploration, survival, construction, and coordination/other tasks, with 3–20 agents and 25–55-round budgets. [§§3.2–3.4, pp. 5–7; Figure 3, p. 6]

## 4. Important interpretation details

- CCE mixes outcome and process because a failed task is forced to zero. The paper therefore also reports successful-task CCE in prose (for example, Claude Haiku 4.5: 0.653; Gemini 3 Flash: 0.609) to isolate efficiency conditional on success. [§4.3, p. 8]
- Approximate anchors given by the authors are: CCE \(=1\), every action contributed; CCE \(\approx1/N\), only one of \(N\) agents contributed; CCE \(\approx0\), almost no action contributed. [Appendix F.1.4, p. 19]
- Run-to-run robustness is assessed separately on a 35-task Gemini 3 Flash subset with three temperature-0.7 seeds: SR is 54.3% for every seed (SD 0.0), while rounds/chats have SD about 0.7. This is a robustness check, not an additional benchmark metric. [§4.4, p. 10]

## Source

Shu, R. et al. “AgentWorld: Benchmarking Long-Horizon Collaboration of Multi-agent LLMs.” COLM 2026. [PDF](https://ryanzhumich.github.io/files/AgentWorld.pdf). Key locations: §3.5 (p. 7), Table 2 (p. 8), §4.3 (pp. 8–9), Tables 4–6 (p. 14), and Appendix F (pp. 18–21).
