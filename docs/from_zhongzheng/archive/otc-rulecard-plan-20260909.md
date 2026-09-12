# 计划：Open Table Coach × Rule Card 独立路径（2026-09-09）

> **状态（2026-09-09 晚）：已实现，baseline 名字定为 `otc`。** 本文下面的 `open_table_coach_rulecard` 一律读作 `otc`。
> 落地后的行为说明以 `docs/contest-systems.md` 的"`otc`: the rule card drives the session"一节为准；
> 实现在 `src/rulecard_policy.py`（读卡校验）、`src/otc_runtime.py`（从 memory 事件回放 lease / latency / 交流预算 / deliberation / 静默流；Coach 与 think 的 prompt）、
> `src/contest_runner.py`（`coach="card"`、`rule_card="enforced"` 开关和挂点）、`src/tool_registry.py`（`deliberation` pack，`ACTION_SET_VERSION=4`）。
> §6 四个待定项的结论：1 采纳"总结文本 + 机器可读分组建议"；2 完全照卡（每回合 1 次私有 think，API ×2）；
> 3 动作分成**所有比赛共用的 common 集** + **按卡/manifest 打开的比赛专属 bundle**（programming / math / research / resources / deliberation），做成 pipeline；4 名字 `otc`，现有五个 baseline 名字不动。
> **2026-09-10 上午改动：Coach 简报移到 turn 0。** 13 张卡 `precontest_brief.turn` 1→0、`opening_discussion.turn` 2→1；简报在开钟前进行，只花 1 次 API、不占比赛 turn 和模拟分钟，contestants 拿满官方时长的全部 turn（ARML 12 turn 全部可用，API 恰好 = 12×6×2+2 = 146）；开局总结仍在 contestants 第一个回合之后。`rulecard_policy.open_table_policy` 与旧栈 `collaboration.py` 的校验都改成接受 brief turn ∈ {0,1} 且 opening = brief+1，`OpenTablePolicy.brief_turn` 记录取值。之前 §7.2 的五场 live 都是 turn-1 版本（contestants 只有 11 个回合）。
> 另外两点实现时的取舍：(a) 卡的 `team_size_min/default/max` 也照办——ARML Local 卡是 6 人队，所以 `otc` 跑 ARML 默认 6 座、12 turn、146 次调用；(b) 卡里的 `simulation.max_turns` 没删，改成与运行时一致的"官方时长 / 5 分钟"值（13 张启用 OTC 的卡），`turn_budget_basis` 同步改写，编程卡加了 `repair_budget_after_rejected_run: 2`。

## 0. 一句话

在 contest-session 引擎上分出第六个 baseline **`otc`**（计划阶段暂名 `open_table_coach_rulecard`）：
Coach 的形态、contestant 每回合怎么动、能说多少、记多少、什么时候能交，**全部从 `data/rules/<比赛>/collaboration.json` 读**，
`contest_runner` 只负责"读卡执行"。现有五个 baseline 一行不动，仍可做配对对照。

## 1. 为什么要分一条路

| | 旧 `--schema open_table_coach --rules-mode enforced` | 现 `--system-variant open_table_coach` |
|---|---|---|
| 读 rule card | 全读（`_open_table_coach_policy` 校验每个字段） | 不读，只有 `contest_rules.py` 一行字符串 |
| Coach | 卡定义：turn 1 盲赛前简报 → turn 2 看题总结开局讨论 → 退场 | 一次 LLM 出 JSON 计划 → 确定性 scheduler 强制执行 |
| contestant 回合 | 卡定义：1 次私有 think + 1 个 committed action | 1 次 typed function call |
| 记忆 | 卡定义三层：private think 3 / shared work 18 / group 12 / public 24 | `strategic_projection` 固定预算 |
| 交流预算 | 卡定义 `communication`（60 条 / 人均 10 / 1200 字） | 无 |
| 单位 | 单题（`--competitions --problem-id`） | 整场 manifest、多题 |
| 基础设施 | 无 typed action、无 checkpoint/resume、无 programming v4、无 vjudge | 全有 |

两边各有一半。新路径 = 右边的引擎 + 左边的"卡说了算"。

## 2. 卡里已经设定好、要被执行的东西

以 `data/rules/arml_local/collaboration.json` 与 `icpc/collaboration.json` 为准：

**`simulation.open_table_coach`**
- `precontest_brief`：turn 1，`problem_access=false`，只能 `speak/sleep`，`advice_scope` 限定建议范围（时间分配 / triage / 交流协议 / 独立验证 / 答题卡核对）
- `opening_discussion`：turn 2，`problem_access=true`，`purpose`＝把 contestants 的开局讨论总结成优先级、检查点、**可被 contestants 之后改掉的**临时分组
- `after_opening_access=false`：之后 Coach 永不再出现
- `may_submit=false`、`allowed_tools=[]`、`counts_toward_shared_api_and_token_budget=true`
- `min_turns`：至少跑到这一回合；之后全员 ready 可提前结束
- `contestant_turn_policy`
  - `mode=private_deliberation_then_single_action`，`private_think_calls_per_turn=1`
  - `allowed_actions`：`work / speak / rest`（ICPC 多 `submit_code`），`exactly_one_action=true`，`unstructured_response=rest`
  - `final_submission=synthesis_only`
  - `visibility`：think 私有、work 共享、speak 团队、rest 私有
  - `max_chars_by_action`：think 2400 / work 2400(ICPC 4000) / speak 320 / rest 80 / submit_code 12000
  - `memory_entries`：private_think_per_agent 3 / shared_work 18 / group_messages 12 / public_messages 24
  - `discussion_policy`：`report_after_work`、`silent_work_turn_requires_discussion`、`conflicts_require_targeted_speak`

**卡的其他部分**
- `agent_constraints`（"After a rejected run, construct a failing hypothesis … do not blindly thrash"、"Treat private reasoning as unknown to teammates until you communicate it" 等）
- `rule_sections`：`typical_contest_workflow`、`failure_recovery`、`conflict_resolution`、`handoff_protocol`、`review_protocol`、ICPC 的 `shared_workstation_protocol` / `pending_run_and_scoreboard`
- `information_policy`（shared: problem / contest_rules / team_discussion / scratchpad）
- `communication`：ARML `limited`（60 / 10 / 1200 字，计数动作列表）；ICPC `unlimited`
- `deliberation`：ARML `structured, min_challenges=1, decision_maker=submitter`；ICPC `unstructured`
- `agent_roles[].may_submit`
- ICPC 独有：`exclusive_workstation_lease=enforced`、`run_judging_latency_turns=1`、`pending_run_policy`
- `simulation.max_turns=30`（旧标准化预算，与今天改的"官方时长 ÷ 5 分钟"冲突，见 §5）

有 OTC block 的卡（14 个）：arml_local、arml_national_team、cfa_research_challenge、codeforces、history_olympiad、hmmt_guts、icpc、mystery_hunt、nyu_ctf_bench、purple_comet、qanta、science_bowl、wmtc。
**没有** OTC block 的：arml_national_power、arml_power、iiot 等 24 个——新 baseline 对这些比赛直接拒跑（和旧路径一致："requires an enforced rule card with an explicit open_table_coach policy"）。

## 3. 设计

### 3.1 配置：两个新开关 + 一个预设

```python
class BaselineFeatures:
    coach: Literal["none", "precontest", "leader", "card"]   # 新增 "card"
    rule_card: Literal["off", "prompt_only", "enforced"]      # 新增，默认 "off"
    ...

BASELINES["open_table_coach_rulecard"] = BaselineFeatures(
    coach="card", rule_card="enforced",
    review_workflow=False,        # 卡里 review_protocol 说 optional；由 deliberation/结构化辩论替代
    memory_actions=True, desk_actions=True,
    private_channel=True, structured_context=True,
    submission_cooldown=False, mechanical_switch=False, leader_submits=False,
)
```

现有五个 preset 都是 `rule_card="off"`，行为不变。
`rule_card="prompt_only"` 留给以后想给别的 baseline 看卡但不强制的实验。

### 3.2 读卡与记录

- `run_competition_batch.py` manifest 路径：`features.rule_card != "off"` 时 `load_rule_card(manifest.competition_id, rules_root)`；没卡或卡里没 `open_table_coach` → `SystemExit`，不静默退化。
- `ContestRunConfig` 加 `rule_card: RuleCard | None`。
- 结果与 checkpoint 写 `rule_card_hash`（`rules.baseline.card_content_hash`）、`rules_mode`；`baseline` 展开表里带上两个新字段。
- `data/rules` 的卡文件本身**不改语义**，只做 §5 的两处补字段。

### 3.3 Prompt：卡进 system prompt

- `CONTEST RULES` 段 = `rules.views.agent_view(card, team_size)`（已自动隐藏 evaluation / scoring / submission），替掉 `rule_guidance` 一行。
- Coach 两个阶段的 system/user prompt 直接从 `precontest_brief.advice_scope` 和 `opening_discussion.purpose` 生成（搬 `collaboration.py::_coach_system_prompt / _precontest_coach_prompt` 的文案）。
- contestant prompt 加一段 `TURN POLICY`：来自 `contestant_turn_policy`（先 think 再一个动作、字数上限、`discussion_policy` 三条）。

### 3.4 Coach 形态：按卡走两阶段

| turn | 谁 | 看什么 | 产出 |
|---|---|---|---|
| 1 | Coach | 只看卡 + 题量/时长，**不看题** | `precontest_coach_guidance` 公开事件（纯文本，限 `advice_scope`） |
| 2 | 每个 contestant | 全部题 + Coach 简报 | 各自 1 think + 1 action（多半是 `speak` 提分工） |
| 2 末 | Coach | 全部题 + 本回合 contestants 的 speak/work | `opening_summary` 公开事件；**同时**输出一份机器可读的 `work_assignments`（可选字段） |
| ≥3 | contestants | — | Coach 不再被调用，也不在收件人里 |

与现 OTC 的关键区别：Coach 的分组是**建议**。scheduler 用它做默认排序，但 `select_problem` 对所有人开放，contestants 可以改（卡：`suggest temporary working groups that contestants may later change`）。Coach 两次调用都计入 `max_api_calls` / tokens（`counts_toward_shared_api_and_token_budget`）。

### 3.5 contestant 回合：先 think 再动作

每回合每人：
1. **think 调用**（`private_think_calls_per_turn` 次，纯文本，不给 function）→ 存成 `think` 私有事件，`max_chars_by_action.think` 截断；prompt 里显示自己最近 `private_think_per_agent` 条。
2. **action 调用**（现有 typed function calling）→ 恰好一个动作；没有合法调用按 `unstructured_response` 记 `rest`。

API 成本 = 现 OTC 的 2 倍（每回合每人 2 次），`--max-api-calls` 默认改成 `turns × team_size × 2 + 2`。

### 3.6 动作集：卡的名字 → typed action

| 卡里 `allowed_actions` | typed action | 备注 |
|---|---|---|
| `work` | `work` | `max_chars.work` 截断 |
| `speak` | `speak` + `direct_message` | `conflicts_require_targeted_speak` → 需要点名时用 DM；两者都算 `communication` 计数 |
| `rest` | `rest` | `max_chars.rest` |
| `submit_code` | `submit_code`（仅编程卡列了才给） | |
| （引擎必需） | `select_problem` / `skip_problem` / `submit` / `inspect_problem` / `triage_problem` / `remember` / `recall` / `share_note` | 卡没禁止且不产生"新能力"的桌面动作；`submit` 只给 `agent_roles[].may_submit=true` 的人 |
| 不给 | `request_review` / `review_answer` / `assign_problem` | 卡说 review optional，用 §3.7 的结构化辩论替代；分配权不给任何 contestant |

### 3.7 卡里的几条"强制"怎么落地

| 卡字段 | 落地 |
|---|---|
| `memory_entries` | 传给 `strategic_projection` 当各切片上限（现在是常量） |
| `communication`（limited） | 复用 `src/communication.py::CommunicationBudget`：`speak`/`direct_message`/`share_note` 计数，超预算返回私有 `action_error`；每回合 `BUDGET` 段显示剩余 |
| `deliberation.structured, min_challenges` | **待定**（§6-3）。方案 A：移植 `propose/challenge/provide_evidence/revise/decide` 五个 typed action，`decide` 只给 `decision_maker`；方案 B：不加 action，用 `speak` 内容前缀 `[challenge]` 由 runner 计数 |
| `discussion_policy.silent_work_turn_requires_discussion` | 连续两回合 `work` 无 `speak` → 下回合 prompt 顶部警告；enforced 下第三回合只剩 `speak`/`rest` |
| `exclusive_workstation_lease=enforced`（ICPC） | **新机制**（旧路径也从没实现）：同一回合内 `execute_code`/`submit_code` 只对当前 lease 持有者可见；lease 随 `select_problem` 移交，持有者 `rest`/`speak` 两回合自动释放。直接消掉"三人围攻一题" |
| `run_judging_latency_turns=1`（ICPC） | 远程提交后该题 N 回合内隐藏 `submit_code`，`TASK STATUS` 里标 `pending` |
| `failure_recovery`（ICPC/ARML 都有文字） | 新字段 `simulation.repair_budget_after_rejected_run`（默认 2）→ `ProgrammingProgress.record` 的"进度"改为**样例 verdict 变好或拿到远程 verdict**；超预算 `set_triage(low)` + 私有提示 |
| `agent_roles[].may_submit` | 替代 `leader_submits` 的判定来源（rulecard baseline 下） |
| `min_turns` + 全员 ready | `finish_contest` 只在 `turn ≥ min_turns` 且答题卡无空白时可见（现在的逻辑已接近） |
| `final_submission=synthesis_only` | deadline 收卷保留；不额外做 synthesis 调用（引擎的答题卡就是 synthesis） |

### 3.8 不进这条路的

- 旧路径的 `Workboard` / `MemoryStore` / `write_scratchpad` 对象——状态仍只在 `ContestSession` + `ContestMemory`。
- 卡里的 `scheduler: round_table_or_centralized` 字段——座次仍是引擎的固定轮转。

## 4. 文件改动清单

| 文件 | 改什么 |
|---|---|
| `src/contest_runner.py` | `BaselineFeatures` 两个新字段 + preset；`ContestRunConfig.rule_card`；`coach == "card"` 的两阶段；think 调用；`_actions_for_agent` 的 rulecard 裁剪（§3.6）；lease / latency / 交流预算 / discussion_policy 检查；prompt 段 |
| `src/rulecard_policy.py`（新） | 从 `RuleCard` 解析出 `OpenTablePolicy`（搬 `collaboration.py::_open_table_coach_policy` 的校验）、`WorkstationLease`、`PendingRunLatency`；纯函数，方便单测 |
| `src/contest_memory.py` | `think` 事件种类；`strategic_projection(limits=...)` 接受卡的 `memory_entries` |
| `src/programming_workflow.py` | "进度"定义改为 verdict 变好；`repair_budget_after_rejected_run` |
| `src/tool_registry.py` | 若选 §6-3 方案 A：加五个 deliberation action，`ACTION_SET_VERSION=4` |
| `src/run_competition_batch.py` | 读卡、hash、api 默认值、`--rules-root` 生效于 manifest 路径；`--system-variant` 多一个选项 |
| `src/contest_budget.py` | 无（卡的 `max_turns` 不再使用，见 §5） |
| `scripts/run_otc_gold_suite.py` 等 | variant 选项、api 预算 ×2 |
| `data/rules/*/collaboration.json` | §5 两处 |
| `tests/test_rulecard_policy.py`（新）、`tests/test_contest_runner.py` | §7 |
| `docs/contest-systems.md`、`pipeline-overview` | 第六个 baseline |

## 5. 要顺手改的卡字段

1. `simulation.max_turns: 30` + `turn_budget_basis: "30 global turns"` → 删 `max_turns`，`turn_budget_basis` 改为 `"official duration / minutes_per_turn (see contest_budget.py), cap 90"`。否则卡和预算表两个真相。
2. 新增 `simulation.repair_budget_after_rejected_run`（ICPC 2、codeforces 2；非编程卡不写）。

## 6. 待你定的

1. **Coach 的开局总结要不要同时出机器可读分组**（§3.4）。出：scheduler 有默认排序，agents 可改；不出：纯文本，完全靠 contestants 自己 `select_problem`。我倾向出（可对照现 OTC）。
2. **每回合私有 think 调用**：卡说 1 次，API 成本翻倍。照卡（推荐，这是你设定的核心），还是 `private_think_calls_per_turn` 先当 0 跑一版看差异。
3. **ARML 卡的 `deliberation.structured, min_challenges=1`**：方案 A 移植五个 deliberation action（忠实、动作集变大、`ACTION_SET_VERSION` 升）；方案 B 用 `speak` 前缀计数（不加 action，弱一点）。
4. **名字**：`open_table_coach_rulecard`，还是把它就叫 `otc`、把现在的 `open_table_coach` 改叫 `open_table_coach_lite`。影响结果目录和导出列名。

## 7. 测试

- `test_rulecard_policy.py`：14 张有 OTC block 的卡都能解析；缺字段 / 不安全值报错；无 OTC block 的比赛拒跑。
- runner：Coach 恰好两次调用且 turn ≥3 不再出现；think 事件私有且只保留 N 条；`max_chars` 截断；交流预算耗尽后 `speak` 报 `action_error`；lease 下非持有者看不到 `execute_code`；latency 下提交后 N 回合无 `submit_code`；`may_submit=false` 的人没有 `submit`；`repair_budget` 超限自动 `set_triage(low)`。
- 现有五个 baseline 全量测试不变（`rule_card="off"` 路径零改动）。
- mock 跑 arml_local_2009 与 icpc_wf_2012_5；live 各跑一场与 `open_table_coach_memory` 对照。

## 7.1 实际测试结果（2026-09-09 晚）

- `tests/test_otc_rulecard.py` 20 个用例全过（含 Coach JSON 解析的 TeX 转义 / 截断抢救、`work(problem_id)` 一步切题、计数消息截断而不拒、无 open proposal 时不提供跟进动作）：卡解析（ARML / ICPC / iiot 拒跑 / team-size 区间 / 截断）、`otc` 动作面（common + 卡打开的 bundle；五个旧 baseline 动作面逐一不变）、lease、latency、`min_turns`+`min_challenges` 门、静默流、ARML 端到端（脚本 LLM：盲简报第一、think→action 成对、开局总结恰在 1+6×2 处、之后无 Coach、320 字截断、P1 propose/challenge、API = 1+11×6×2+1、deadline 收卷）、交流预算第 11 条被拒、`min_turns` 前无 `submit`、ICPC repair budget → low + lease/latency 提示文本、`work(problem_id)` 一步切题 + 焦点自动前进。
- 全量 `unittest`：415 个，通过 403；12 个失败全部是环境问题——11 个要 Docker（Docker Desktop 当时没开：isolated_python / judge / adapters / phase4）、1 个 `test_reference_only_gold_is_unavailable` 是 grading 侧的既有失败（本次没有改 grading 代码）。
- mock：ARML otc 12 turn / 146 api（用 134：1 简报 + 11×6×2 + 1 总结）；ICPC otc 60 turn / 362 api。mock LLM 只回旧格式文本，所以只验证机制。

## 7.2 live 对照（ARML Local 2009，gpt-5.4-mini，native action calling，`results/otc_rulecard_probe_20260909/`）

| 目录 | baseline | 座位 | turns | api | 输出 token | wall | 分 / 40（9 题可判） | 备注 |
|---|---|---|---|---|---|---|---|---|
| `arml_local_2009_otcm_12t` | `open_table_coach_memory` | 3 | 12 | 37 | 7.9k | 123 s | **26.67**（6/9） | 对照组；0 action_error |
| `arml_local_2009_v1_focus_stuck` | `otc`（第一版） | 6 | 12 | 134 | 17.7k | 369 s | 8.89（2/9） | 焦点卡死：每个座位一直停在 Coach 建议的第一题（答题卡题永不"锁"），think 里想去 Q4，`work` 却记到 Q1；6 人只碰了 6 题 |
| `arml_local_2009_v2` | `otc`（修焦点后） | 6 | 12 | 134 | 20.7k | 416 s | **22.22**（5/9） | 全部 10 题在 turn 3 前都有人碰；turn 4 五个人同时挤到唯一空白的 #10（KenKen，题面没图，全体 rest）；3 个 action_error 都是对不存在的 P1 发 challenge；deliberation 五件套一次没用 |
| `arml_local_2009_v3` | `otc`（再修：空白题只让一个空闲座位接手，其余回自己的题复核；协议文本列出当前 open proposals） | 6 | 12 | 134 | 25.2k | 467 s | 13.33（3/9） | 分散生效（turn 4 六人在 6 道不同题上）；但 10 个 action_error：7 个是对已 decide 的 P1 反复 challenge/decide，1 个 propose 1677 字被交流上限 1200 **整条拒掉**，1 个 `P?`，1 个无 function call；#1 这次也错了（v1/v2 都对）——单次方差很大 |
| `arml_local_2009_v4` | `otc`（三修：无 open proposal 时不提供 challenge/provide_evidence/revise/decide，有则 proposal_id 枚举只列 open 的；计数消息按 min(卡上限, 交流上限) 截断而不是拒） | 6 | 12 | 134 | 17.9k | 412 s | 17.78（4/9） | **0 action_error**；但 Coach 开局 JSON 里写了 TeX `\(f(3)\)`，非法转义让 `json.loads` 失败 → 分组全空 → 无分组座位跟着共享游标走，turn 4–12 六个人全挤在 #10 再全挤在 #9 |
| `arml_local_2009_v5` | `otc`（四修：解析器容忍 TeX 转义 / 截断只抢救 summary；无分组座位回自己最近的题而不是共享游标） | 6 | 12 | 128 | 19.3k | 356 s | 13.33（3/9） | **机制全部按卡走通**：0 action_error；分组解析成功（6 人各 1–2 题）；turn 3 前 10 题全被碰过、无堆题；turn 11 `propose` P1 → turn 12 `challenge`（满足 `min_challenges=1`）→ Agent_3 `submit` 提前收卷（所以 api 128 < 134）。分低是答案错（#1/#3/#5/#6/#8） |

v1 → v2 的两处修法（已进代码 + 测试）：
1. `_card_focus_task`：Coach 建议列表按顺序推进，答题卡题一有草稿就算"settled"跳过（编程题要 AC 才算），全部 settled 后先接手全局空白题，否则回到自己最后一题复核。
2. 卡要求每回合恰好一个动作，所以 `otc` 下 `work` 多一个可选 `problem_id`：`work(problem_id=X, content=…)` = 切题 + 记草稿一步完成，同时写一条 `select_problem` 事件（`via: "work"`），之后焦点跟着走。协议文本里明说这一点。

v2 → v3：`_card_task_claimed_this_turn`（本回合或上回合已有别的座位在该题上）→ 其余空闲座位回自己的题；`protocol_text` 加 "open proposals now: …/none (use propose first)"。

v4 → v5：`parse_coach_summary` 先按原文、再按 `{…}` 片段、再把非法反斜杠转义加倍各试一次 `json.loads`，全失败时用正则抢救 `"summary"` 字符串；`_card_focus_task` 在没有建议可走时优先回该座位自己最近碰过的题（`own_recent`），共享游标只是最后的兜底。

v3 → v4：`_card_gate` 在没有 open proposal 时隐藏四个跟进 deliberation 动作、有时把 `proposal_id` 的 enum 钉到 open 列表（和 `finish_contest` 只在可用时出现是同一原则：不提供必然报错的动作）；`_apply_card_rules` 对计数消息动作按 `min(卡的 max_chars, communication.max_message_chars)` 截断并记 `card_content_clipped`，交流预算只在**条数**用完时才拒。

读法（5 次 `otc` 各 1 场、对照 1 场，都是单样本）：

- 机制：v5 已经把 v1–v4 暴露的四类 runner 缺陷（焦点卡死、堆题、无效 deliberation 动作被提供、Coach JSON 解析脆弱）都修掉，并且各有测试；卡设定的每一条（盲简报→开局总结→退场、每回合 think+1 action、截断、交流预算、静默流、min_turns、min_challenges 门、答题卡 deadline 收卷/`submit` 提前收卷）在 live 记录里都能对上。
- 分数：`otc` 五场 8.9 / 22.2 / 13.3 / 17.8 / 13.3（均值 ≈ 15/40），对照 `open_table_coach_memory` 3 人 12 turn 一场 26.7/40。同一模型下 6 座 × think 花 3.6 倍 API 没有换来更高分。两组都错 #3（期望值）、#5（等角六边形）、#7；`otc` 多错的题在不同场次里不一样（#1 在 v3/v5 错、v1/v2/v4 对；#6、#8 类似）——是模型层面的方差，不是某道题系统性丢分。
- 一个值得你在卡层面决定的取舍：现在的焦点规则是"答题卡题一有草稿就算 settled，座位自动去下一道空白题"，所以 turn 2 六人各写一题后基本不再回头复核，Coach 总结里"verify #1/#5"这类建议没人执行；对照组只有 3 人、每题被多看几轮并有 `review_answer`。要提高复核，可选：(a) 卡里加一条 `verify_before_move`（有草稿的题至少再被另一个座位 `inspect_problem`/`work` 一次才算 settled），(b) 把 Coach 建议列表按字面顺序走、靠 `work(problem_id)` 让 agent 自己决定何时离开。两种都是卡/协议层的决定，runner 两边都支持，我没有替你选。
- structured deliberation 在 gpt-5.4-mini 上很少被自发使用（v1 4 次 propose、v2 0、v3 1、v4 0、v5 1+1 challenge），`min_challenges=1` 因此多数场次把 `submit` 挡到 deadline 收卷；这是卡设定的预期行为。

## 8. 关于 git

工作树里现在有 987 个未提交改动（大部分是 `results/`、`data/contest_manifests/generated/` 的删除），且有另一个 agent 在同一目录工作，所以这次**不切分支**；代码上的"分路"靠 preset 隔离。要开分支的话等工作树干净了再 `git switch -c feat/otc-rulecard`。
