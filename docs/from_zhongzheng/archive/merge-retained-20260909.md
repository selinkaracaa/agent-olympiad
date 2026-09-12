# 两套栈合并：各自保留了什么（2026-09-09）

对应改动：`contest_session_v4` / `action_set_version=3` / 五个 baseline 预设。
设计与动机见 `contest-baselines-plan-20260909.md`，整体架构见 `pipeline-overview-20260909.md`。

合并原则一句话：**骨架全部是 contest-session 栈的；Selin 那边只搬"动作语义"，不搬对象。**
没有引入 `Workboard`、`MemoryStore`、`rules/`、`deliberation.py` 里的任何类；她的 action 全部重写成
`tool_registry.py` 里的 typed action，落到同一个 `ContestSession` 任务状态 + `ContestMemory` 事件账本上。

---

## 1. 从我这边（contest-session 栈）保留了什么

全部保留，作为唯一的运行时。具体是：

| 模块 | 保留内容 | 文件 |
|---|---|---|
| 状态机 | `ContestSession`：TaskUnit / 不可变 answer version / review / submission / checkpoint & resume | `src/contest_session.py` |
| 记忆 | `ContestMemory` 追加式事件账本；`strategic_projection` 结构化投影；`_shrink_to_budget` 压缩；digest | `src/contest_memory.py` |
| 动作系统 | 单一注册表 + JSON schema；`native` / `emulated` / `prompt-json` 三种调用模式；每回合按状态动态裁剪可见 action | `src/tool_registry.py`, `contest_runner._actions_for_agent` |
| 回合循环 | 轮转座次、`max-turns` / `max-api-calls` / `max-total-tokens` 三重预算、stall guard、deadline 收卷 | `src/contest_runner.py` |
| Coach（OTC） | 一次 LLM 规划（看全部题）→ 确定性 scheduler 全程执行；`coach_personal_assignment` / `assignment_task_scheduled` 事件 | `contest_runner._normalize_coach_plan`, `_scheduled_agent_task` |
| Review 工作流 | `request_review` → `review_answer(approve/reject + hash)` → 才能 `submit`；protocol v3 的 vanilla / OTC 拆分 | `contest_runner`, `contest_session` |
| 提交策略 | `SubmissionPolicy`、cooldown、`mechanical_switch`、答题卡语义 | `contest_runner` |
| 编程赛 | `programming_workflow_v4`：`execute_code` / `submit_code` / vjudge 官方判定 | `contest_runner`, `src/vjudge_gateway.py` |
| 私聊 / 广播 | `speak`（公开）、`direct_message`（私有，现在支持多收件人） | `tool_registry`, `contest_memory` |
| 判分与导出 | gold / rubric / official verdict；CCE、协作分、process metrics；`_export_paste_tabs_3_6.py`、`posthoc_icpc_metrics.py` | `src/run_competition_batch.py`, `scripts/` |
| 入口 | `run_competition_batch.py` 单场；`run_otc_gold_suite.py` / `run_otc_arml_science_bowl.py` / `run_all_icpc_full_pairs.py` 批量；`run_contest_smoke.py` 冒烟 | `src/`, `scripts/` |

我这边**改掉**的只有两点：

- `system_variant` 不再是控制流开关（原来 `contest_runner.py` 里 28 处 `if strategic`），现在只是一个标签；真正的开关是 `BaselineFeatures` 的 9 个正交字段，五个 baseline 是它的 9 个字段的预设组合（见 §4）。
- `verify` 这个旧 action 仍在注册表里（兼容旧栈），但 contest-session 不再解析它，由 `inspect_problem` 取代；`deadline_submit` 死分支删掉。

---

## 2. 从 Selin 库保留了什么

她的 workboard / memory / team 三组 action 里，搬了 **6 个语义**，全部重写成 contest-session 的 typed action：

| Selin 原 action | 现在的 action | 落到哪 | 保留的是什么 / 改了什么 |
|---|---|---|---|
| `open_problem` | `inspect_problem(problem_id)` | 读 `ContestSession` 任务，追加 `inspect_problem_result` 私有事件 | 保留"不改状态地看一题全部历史"（题面、版本、review、提交、优先级）；**改**：不移动 active cursor，不算 approval，纯自查 |
| `mark_hopeless` + `set_priority` | `triage_problem(problem_id, priority, reason)` | `TaskUnit.priority / triage_reason / triaged_by / triaged_turn`，`task_triaged` 事件 | 两个合成一个；`priority ∈ {high, normal, low, hopeless}`；**新增**：scheduler 按 `priority_rank` 排序，hopeless 题**仍在**答题卡上、deadline 照常收卷（测试 `test_hopeless_draft_is_still_collected_at_deadline`） |
| `remember` | `remember(content, problem_id?)` | `ContestMemory` 追加 `note` 事件（私有） | 保留私有笔记；存储不再是 `MemoryStore`，就是账本里一种事件 |
| `recall` | `recall(query?, problem_id?)` | `ContestMemory.recall()`，返回 `recall_result` 私有事件 | **排序逻辑原样搬**自 `src/memory.py`：题号命中 → 关键词命中 → 时间新近；按内容 hash 去重 |
| `publish_memory` | `share_note(content, problem_id?)` | `note_shared` 事件，`visibility=public` | 保留"把私有笔记公开"；改成直接写公开笔记，不需要先 `remember` 再发 |
| `message_group` | `direct_message(recipients: [..])` | `ArgumentSpec` 支持 `array`；`inbox` 投影按收件人列表过滤 | 保留"给指定几个人发"；合进原有 `direct_message`，不另起 action |

另外两个**机制**也是从她那边来的：

- **重复提交反馈**：她 workboard 对重复 `submit_problem` 有检查；现在 `work` 写入与任何历史版本内容相同时，不再静默接受，而是给该 agent 私有 `work_duplicate` 事件（`TaskUnit.find_duplicate_answer`）。
- **投影里带笔记**：`strategic_projection` 新增 `recent_notes`（最多 4 条、排除当前题已有的），对应她的"memory 出现在上下文里"。

这 6 个 action 加上 `assign_problem`（centralized 新增）合起来叫 **desk actions**，分成三个可独立开关的包：

- `DESK_READONLY_ACTION_NAMES = {inspect_problem, triage_problem}`
- `MEMORY_ACTION_NAMES = {remember, recall, share_note}`
- `LEADER_ACTION_NAMES = {assign_problem}`

---

## 3. Selin 库里**没有**搬的，以及原因

| 她的 action / 对象 | 为什么不搬 |
|---|---|
| `list_problems` | prompt 里 `TASK STATUS` 表 + `strategic_projection` 每回合已经给全板；再加一个 action 只会多花 API call |
| `claim_problem` / `release_problem` | Coach 分配 + `select_problem` / `skip_problem` 已经是占题语义；"一人一题闲置过期"和 scheduler 冲突 |
| `submit_problem` | 对应 `work`，但 `work` 产生不可变 version + hash，是 review 工作流的基础，不能退回"板上最新一条" |
| `verify_problem`（agree / disagree / unsure） | 对应 `review_answer(approve/reject + version hash)`；三态无 hash 会破坏"审的是哪一版"的可追溯性 |
| `check_budget` | `BUDGET` 段每回合注入 prompt（含 `blank_tasks`），不需要花一次调用去问 |
| `propose` / `challenge` / `provide_evidence` / `revise` / `decide` | 结构化辩论是另一套协议，且每步都计费；OTC 的设计是 Coach 一次规划 + scheduler，不做多轮辩论 |
| `Workboard` / `MemoryStore` / `rules/` / `deliberation.py` 对象 | 会出现两份状态；所有状态只允许在 `ContestSession` + `ContestMemory` |

---

## 4. 谁能用什么：五个 baseline

| baseline | coach | review | desk_readonly | memory | private_channel | leader_submits |
|---|---|---|---|---|---|---|
| `single_agent`（team_size=1） | none | ✗ | ✗ | ✗ | ✗ | ✗ |
| `decentralized`（旧 `vanilla_team`） | none | ✗ | ✗ | ✗ | ✓ | ✗ |
| `centralized` | leader（Agent_1 出计划 + `assign_problem`） | ✗ | ✓ | ✗ | ✓ | ✓ |
| `open_table_coach`（旧 `strategic_team`） | coach | ✓ | ✓ | ✗ | ✓ | ✗ |
| `open_table_coach_memory` | coach | ✓ | ✓ | ✓ | ✓ | ✗ |

要点：`decentralized` 和 `single_agent` **不带**任何 Selin 的 action，语义等同 protocol v3 的 vanilla；
Selin 的东西只在 `centralized` / `open_table_coach`（只读桌面）和 `open_table_coach_memory`（全部）里出现。
`open_table_coach` 与 `open_table_coach_memory` 的**唯一**差别就是 `remember` / `recall` / `share_note` 三个 action 是否可见。

旧名字全部保留为别名：`vanilla_team → decentralized`，`strategic_team → open_table_coach`，结果 JSON 同时写 `system_variant`（规范名）、`requested_variant`（命令行原字）、`baseline`（展开后的开关表）。

---

## 5. 兼容性

- checkpoint 带 `protocol_version=contest_session_v4` 与 `action_set_version=3`；`--resume` 遇到旧版本直接 `SystemExit`，不混跑。
- v3 之前的实验结果（`results/*protocol_v3*`）仍可读，但不与 v4 直接配对比较；ICPC 配对脚本里的等价集合已按新名字更新。

---

## 6. 试跑：`open_table_coach_memory` × ARML Local 2009（live）

```powershell
..\.venv\Scripts\python.exe -u src\run_competition_batch.py --live --provider perplexity --model openai/gpt-5.4-mini `
  --contest-manifest data\contest_manifests\arml_local_2009.json --system-variant open_table_coach_memory `
  --action-calling native --team-size 3 --max-turns 50 --max-api-calls 151 --max-total-tokens 220000 `
  --no-judge-task --no-judge-cce --output results\otc_memory_probe_20260909\arml_local_2009
```

（这一跑在"按官方时长定 turn 数"改动之前，所以还是固定 50 turn / 151 call；现在 ARML 默认 12 turn / 37 call，见 pipeline-overview §2。）

产物：`results/otc_memory_probe_20260909/arml_local_2009/contest_session.json`（`protocol_version=contest_session_v4`，`action_set_version=3`，`baseline` 展开表已写入）。

### 6.1 有没有错

没有。`action_error` 0 条、`transport_failures` 0、`transport_retries` 0、`stalled_turns` 0；
正常走完 final review → `submit` → `deadline_drafts_submitted`，checkpoint 每回合落盘正常，退出码 0。

### 6.2 分数与成本（对照 9/6 protocol v3 的 OTC 同场次）

| | v3 OTC（`strategic_team`） | v4 OTC + memory |
|---|---|---|
| 得分 | 26.67 / 40（6/9） | 26.67 / 40（6/9） |
| turns | 28 | 26 |
| API calls | 84 | 79 |
| tokens | 23 514 | 13 935 |
| 墙钟 | 345 s | 252 s |
| CS | 2.5 | 3.5 |

分数持平（对 1 2 4 6 8 9，错 3 5 7），成本略低。第 10 题（KenKen）两次都是 ungraded：题面是图，manifest 里只有文字，所以 max_score 是 40 不是 44.4，这是数据问题不是代码问题。

### 6.3 新 action 实际怎么被用的

| | 次数 | 观察 |
|---|---|---|
| `inspect_problem` | 19（占 79 次调用的 24%） | 前 4 次是拿到分配后先看一眼再 `work`，合理。**其余 15 次全部打在第 10 题上**：Agent_2 一个人查了 12 次，同一题、同样结果。题面本来就缺图，查多少次都一样 |
| `remember` | 4 | 内容质量不错：一条第 9 题解题计划、一条第 9 题最终答案、两条"第 10 题缺 KenKen 网格无法作答" |
| `recall` | 0 | 26 回合 10 道题，`recent_notes` 已经把笔记投影进 prompt，没有召回的必要 |
| `share_note` | 0 | 两条"第 10 题缺图"的笔记本该 share 给队友，但都留在私有 |
| `triage_problem` | 0 | 第 10 题明显 hopeless，没人标；agents 选择反复 inspect + `rest` |
| `work_duplicate` | 6 | 第 9 题 review 被拒后 Agent_1 / Agent_3 在 turn 11–13 交了三次一字不差的同一稿（互相抄）；Agent_1 手头题做完后 turn 18、20 又重录第 1 题的旧稿。私有反馈给了，但没能阻止下一次重复 |
| `speak` / `direct_message` | 0 | 全程零沟通，协作全部走 review 通道 |

### 6.4 结论与下一步

1. **代码层面通过**：v4 合并后的 OTC + memory 在 live 上跑通，无异常，分数与 v3 持平、成本更低。
2. **memory 三个 action 在这种规模下基本闲置**：`recall` 一次没用；`remember` 的内容合理但没有转成团队信息。要看 memory 的效果得挑长赛（Power Round、ICPC 全场、50 turn 跑满的场次）。
3. **`inspect_problem` 有被滥用的口子**：对不可解的题会反复查。两个可选修法（都没改，等决定）：
   - 同一 agent 对同一题、状态未变时再 inspect，返回值里加一句 "unchanged since your last inspect at turn N"，或直接把该题从这个 agent 的 `inspect_problem` enum 里去掉直到状态变化；
   - DESK TOOLS prompt 里加一句：题面信息不足以作答时用 `triage_problem(hopeless)` + `share_note`，不要重复 inspect。
4. **`work_duplicate` 只是提示，不是拒收**：目前重复稿不入版本、只发私有反馈；如果想更硬，可以在同一 agent 连续第二次重复时把 `work` 从它的可见 action 里临时拿掉一回合。
5. `--no-judge-cce` 所以 CCE 为空；这次只看错误和流程，正式对比要开 judge。

## 7. 试跑：`open_table_coach_memory` × ICPC WF 2012（live，新预算）

第一场用"官方时长 ÷ 5 分钟"预算的 live：不传 `--max-turns` → 60 turn，`--max-api-calls 181`（60×3+1），
`--programming-deadline-submit --start-seat 0`，其余同 §6。产物 `results/otc_memory_probe_20260909/icpc_wf_2012/`。

| | v3 OTC（WF 2013 / 2015 / 2016，50 turn） | v4 OTC + memory（WF 2012，60 turn） |
|---|---|---|
| AC | 1/11、1/13、1/13 | **1/12**（fibonacci，第 6 turn 一发 AC） |
| turns / api | 50 / 151 | 60 / 181（两个都正好用满） |
| tokens | 61k–92k | 108k |
| 墙钟 | 19–24 min | 24 min |
| 远程判题 | 13–19 次 | 14 次（3 次主动 + 11 次 deadline），全部拿到有效 verdict |

- **错误**：`action_error` 1 条（turn 12，模型 tool-call 参数里多了一个键 `"\n# left/right tangent from P"`，是模型把代码注释当成了 JSON key；按设计记私有错误、本回合作废，不影响后续）。传输失败 0、重试 0、gateway 0 次不健康、stall 0。
- **60 turn 预算下的行为**：模拟钟走满 300 分钟；deadline 兜底把 11 道没主动提交的题全交了（10 WA + 1 TLE），和 v3 结论一致——瓶颈是解题而不是流程。
- **时间分配**：`execute_code` 113 次里 bustour 占 37、takeover 占 19，Agent_1/Agent_2 大半场卡在这两题上；`triage_problem` 依旧 0 次，没人把卡住的题降级。
- **memory**：`remember` 1（bustour 的 bug 定位笔记，质量高）、`recall` 1（turn 8 查 keys，账本里还没有笔记，返回空）、`share_note` 0；`inspect_problem` 15。跟 ARML 一样，memory action 在单场里几乎没被当成团队工具用。
