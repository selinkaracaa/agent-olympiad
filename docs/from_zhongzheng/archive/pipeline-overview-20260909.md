# Pipeline 全景：当前系统是怎么跑的（2026-09-09）

> 范围：`agent-team-features-main` 当前工作树。对应代码以 `src/` 为准，行号取自本日快照。
> 相关文档：[contest-systems.md](../contest-systems.md)（协议/版本变更记录）、
> [otc-protocol-fixes-20260906.md](otc-protocol-fixes-20260906.md)、
> [weekly-summary-2026-09-05-to-09-09.md](weekly-summary-2026-09-05-to-09-09.md)。

## 0. 先说清楚：仓库里有两套栈

| | 旧栈（per-problem） | 当前栈（contest session） |
|---|---|---|
| 入口 | `run_competition_batch.py` 不带 `--contest-manifest`；`run_exam.py`、`run_phase_a.py`、`run_phase_b_matrix.py` | `run_competition_batch.py --contest-manifest ...` |
| 选择协作方式 | `--schema round_table / centralized / decentralized / single_agent / open_table_coach / debate / self_consistency / memory_solo / subagent / vanilla_team / liveoi_best_of_8` | `--system-variant single_agent / decentralized / centralized / open_table_coach / open_table_coach_memory`（旧名 `strategic_team` = `open_table_coach`，`vanilla_team` = `decentralized`，见 §2.0） |
| 核心代码 | `src/env.py` + `src/collaboration.py` + `src/actions.py` | `src/contest_runner.py` + `src/contest_session.py` + `src/contest_memory.py` + `src/tool_registry.py` |
| 动作格式 | 文本 `ACTION: speak \| PAYLOAD: ...` | typed function call（native / emulated / prompt-json） |
| 记忆 | `MemoryStore`（remember/recall/publish）、scratchpad、workboard、三层 memory | `ContestMemory` 事件账本 + 不可变 answer version + review |
| 一次运行 | 一道题 | 一整场比赛（多题、共享预算、答题卡、resume） |

**近两周所有实验结果（gold suite、ARML 配对、ICPC full pairs）都是当前栈。** 下文说 “OTC” 一律指 `open_table_coach`（旧名 `strategic_team`），不是旧的 `--schema open_table_coach`。旧栈只在最后一节附带说明。

## 1. 端到端流程

```
data/raw/<comp>/*.pdf ──collectors/*.py──▶ data/benchmarks/<comp>/benchmark.json
                                                   │  (+ data/rubrics, data/rules, samples/packages)
                                                   ▼
                    data/contest_manifests/*.json ──contest_manifest.load──▶ ContestManifest(tasks[], task_family)
                                                   │
                                                   ▼
run_competition_batch.py --contest-manifest ... --system-variant <五个 baseline 之一，见 §2.0>
                                                   │
        ┌──────────────────────────────────────────┤
        │ coach=precontest：Pre_Contest_Coach 一次 LLM 调用 → JSON 分工计划 → 写入每个 agent 的私有 memory
        │ coach=leader（centralized）：同一份计划由 Agent_1 出，之后 Agent_1 留在场上、每轮先行、唯一能提交
        ▼
_run_contest_engine（contest_runner.py）
   for turn in range(max_turns):
       for agent in Agent_1..Agent_N（固定座次）:
           有计划时（coach ≠ none）: scheduler 把共享 active-task 游标移到该 agent 的下一个 work/review 目标
           _actions_for_agent → 该回合合法的 function 集合（动态裁剪）
           一次 LLM 调用（tool_choice=required）→ 恰好执行一个 action
           _apply_action → 写 ContestMemory 事件 + 更新 ContestSession（version/review/submission）
           checkpoint → contest_checkpoint.json
   回合结束：deadline 收集（未提交的非编程草稿自动提交）
                                                   │
                                                   ▼
grade_contest_result（contest_adapters.py）→ gold 判分 / programming solved / rubric_llm_v1 / unavailable
collaboration judge（CS = (Comm+Plan)/2）、可选 CCE
                                                   │
                                                   ▼
results/<run>/<session>/contest_session.json + contest_checkpoint.json + run.log
scripts/*export*.py → summary.tsv / paste_tabs / completed_metrics.tsv
```

## 2. 入口：不同竞赛怎么进来

### 2.0 五个 baseline = 一张开关表（2026-09-09 下午）

`contest_runner.py` 里原来只有 `vanilla | strategic` 两个值、28 处 `if system_variant == ...`。现在改成 `BaselineFeatures`（9 个正交开关）+ `BASELINES` 预设表，引擎只看开关、不看名字：

| `--system-variant` | coach | review 工作流 | memory（remember/recall/share_note） | desk（inspect/triage） | direct_message | 结构化上下文投影 | 3 非 AC cooldown | 答题卡机械切题 | 只有 leader 提交 |
|---|---|---|---|---|---|---|---|---|---|
| `single_agent`（team_size 强制 1） | none | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| `decentralized`（open table 轮转） | none | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| `centralized`（Agent_1 = leader） | leader | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| `open_table_coach`（OTC） | precontest | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| `open_table_coach_memory` | precontest | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| `otc`（rule card 版 OTC，2026-09-09 晚新增） | card（两阶段） | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ |

- **`otc`**：第 10 个开关 `rule_card="enforced"`，只有它打开。`data/rules/<比赛>/collaboration.json` 决定一切：队伍人数（ARML Local 卡是 6 人，所以默认 6 座）、Coach 两阶段（turn 0 盲简报，在开钟前、不占比赛 turn，只花 1 次 API；turn 1 contestants 先动、Coach 读公开事件出总结 + **建议性**分组后退场）、每回合 1 次私有 think 调用 + 1 个 action（API 默认 = turns × team × 2 + 2，ARML 即 146）、`max_chars_by_action` 截断、`memory_entries` → 投影窗口、`discussion_policy`（连续 2 个只 work 不说的回合后只剩讨论动作）、`communication` 预算（超了记 action_error）、`deliberation.mode=structured` 时加 `propose/challenge/provide_evidence/revise/decide` 五件套并要求 ≥ `min_challenges` 次 challenge 才能交卷、`min_turns` 前不能结束、ICPC 的 `exclusive_workstation_lease`（谁最后跑/交了代码谁持键盘 2 回合）与 `run_judging_latency_turns`（verdict 延迟一回合可见、期间不能重交）、`repair_budget_after_rejected_run`（官方 WA 后 2 次执行仍没有新源码的 sample AC → 题目降 low）。不带 review 工作流、不强制分配、不 cooldown。细表见 `docs/contest-systems.md`。
- 别名：`vanilla` / `vanilla_team` → `decentralized`；`strategic` / `strategic_team` → `open_table_coach`（v3 的 strategic 没有 memory action，所以指向不带 memory 的那个）。结果里 `system_variant` 存正名，`baseline` 存开关，`run.requested_variant` 存命令行原名，`plan_author` 记谁出的计划（`Pre_Contest_Coach` / `Agent_1` / null）。
- `single_agent` 与 `decentralized` 开关完全一样，区别只有座位数；两者就是 v3 vanilla 环境（无 desk/memory 工具、原始 12 条上下文、work 后自动跳下一道空题）。
- `centralized` 是旧栈 `--schema centralized` 的 contest-session 版：Agent_1 用 Coach 同款 JSON 出开场计划（事件仍是 `precontest_coach_guidance`，`author=Agent_1`），自己可做任何题、每轮先行、**唯一**能 `submit / submit_code / finish_contest`（worker 看不到这三个；leader 的 `submit_code` 无参，提交活动题最新版本）。leader 独有 `assign_problem(agent, problem_ids, reason?)` 现场替换某人的 work 列表，公开事件，resume 时重放。无 review 工作流，计划里的 review 路由清空。
- 消融：在预设上传 `features=BaselineFeatures(...)` 或 `--require-review / --no-require-review`，名字仍是预设名。
- `action_set_version` 升到 3（加了 `assign_problem`），再升到 4（加了 `deliberation` pack 五件，只有 `otc` 且卡是 structured 才解析），`protocol_version` 仍是 `contest_session_v4`。

### 2.1 只有一个通用 runner，竞赛差异靠数据驱动

`src/run_competition_batch.py` 是唯一的正式入口。带 `--contest-manifest` 走当前栈：读 manifest → 解析预算和队伍 → `coach == none` 走 `run_vanilla_contest`，否则 `run_strategic_contest`（两个模块只是薄包装，都调 `contest_runner._run_contest_engine`；`vanilla_contest_runner.py` 的接口故意没有 `coach_query_fn`，防止误开 Coach）。

关键 flag（`run_competition_batch.py:967-1128`）：

| flag | 作用 |
|---|---|
| `--live` | 真实 provider；不带则 mock |
| `--provider perplexity\|tinker`，`--model` | Perplexity 用路由名如 `openai/gpt-5.4-mini`；Tinker 用 HF repo id 如 `Qwen/Qwen3.6-35B-A3B` |
| `--contest-manifest` | 进入 contest-session 模式 |
| `--system-variant` | §2.0 的六个正名 + 四个别名；内部规范化为正名 |
| `--action-calling auto\|native\|emulated\|prompt-json` | 见 §3.3 |
| `--team-size` | 默认取规则卡 roster → benchmark metadata → 3；`otc` 默认取卡的 `team_size_default`，给了但超出卡的范围直接报错 |
| `--max-turns / --max-api-calls / --max-total-tokens / --max-simulated-minutes` | 共享预算；`--max-total-tokens` 只算 **输出** token。`--max-turns` 不给时按官方时长推：1 turn = 5 分钟，ARML 1h → 12、Purple Comet 90m → 18、ICPC 5h → 60，上限 90（MCM 99h 按 60 分钟/turn 也只给 90）；显式给的值同样被夹到 ≤ 90（`src/contest_budget.py`） |
| `--require-review / --no-require-review` | 覆盖预设的 review 开关（默认两个 OTC 开、其余关） |
| `--programming-deadline-submit` | 编程题 deadline 兜底提交（默认关） |
| `--no-judge-task / --no-judge-collab / --no-judge-cce` | 关掉三类判分；CCE 默认关 |
| `--rules-mode off\|prompt_only\|enforced`，`--rules-root`，`--rules-strict` | 规则卡 |
| `--output`，`--resume`，`--start-seat` | 输出目录、断点续跑、首发座位 |

当前跑批的标准配置（`scripts/run_otc_gold_suite.py`、`scripts/run_all_icpc_full_pairs.py` 都用这套）：

```
--live --provider perplexity --model openai/gpt-5.4-mini --action-calling native
--team-size 3 --max-total-tokens 220000 --no-judge-task --no-judge-cce
# 不传 --max-turns：按官方时长 / 5 分钟推（ARML 12、ICPC 60，上限 90）
# 脚本里 --max-api-calls = turns × team_size + 1（Coach 那一次），ARML 三人队即 37
# otc：不传 --team-size 用卡的默认 roster；--max-api-calls 默认 turns × team × (1 + think 次数) + 2，ARML 6 人队即 146
```

9/9 之前的所有结果都是固定 `--max-turns 50 --max-api-calls 151` 跑的，和新预算不直接可比。

### 2.2 Manifest 与 task family 路由

`src/contest_manifest.py`：manifest 含 `session_id`、`competition_id`、有序 `problem_ids`、可选 `split_parts` / `question_ids` / prompt override / metadata（如 `task_family`、`competition_description`）。loader 把 id 拼到该竞赛的 `benchmark.json`，缺 id 直接报错。每个 `ManifestTask` 带 `task_id`、`prompt`（已剥掉 answer/solution 段）、`task_type`、`max_score`、`programming` 标志。

**task family**（`contest_manifest.py:20-97`）决定 system prompt 里的 workflow 段和可用工具包：显式 metadata 优先 → 已知 competition_id 映射（ARML/HMMT/Purple → `mathematics`，Science Bowl/QANTA/History → `short_answer`，Mystery Hunt → `puzzle`）→ 否则按 `programming` / `task_type` / 关键词推断。`programming` family 走 ICPC 四步流水线（§5.3），其他 family 走 answer-sheet 语义。

ICPC 和 ARML 在 orchestration 上没有分支，差别只在数据和判分：ICPC manifest 是若干独立编程题（`split_parts: false`），每题可 `execute_code` / `submit_code`；ARML Local / National Team 把一份 packet split 成 9–10 个编号小题，一个 session 共享一张答题卡；ARML Power / National Power 是一个证明 packet，rubric 判分。

### 2.3 现在覆盖了哪些竞赛

`data/benchmarks/` 下 43 个目录（`docs/DATA_COLLECTION.md` 仍是老的 20 家目录，未更新）。按当前 pipeline 能跑到什么程度分：

| 类别 | 竞赛 | 数据形态 | 判分 | 现状 |
|---|---|---|---|---|
| 数学短答 | ARML Local 2009–2014、ARML National Team 2009–2023、Purple Comet、HMMT Guts、WMTC | `gold_label.parts`（id/expected/points/aliases） | `gold_answer_v1` 归一化匹配 | 主战场；gold suite + 配对实验 |
| 数学证明 | ARML Power（Fall 2018–Spring 2025）、National Power 2009–2023 | 一个 packet，`[4]`/`[3 pts.]` 内嵌分值 | `rubric_llm_v1`（`scripts/build_arml_power_rubrics.py` 生成 26 份 rubric） | 26 个 session 已跑，但 contest-session 路径的 grader 还接不到 rubric → 全部 `unavailable`（见 §7） |
| 短答/问答/谜题 | Science Bowl、QANTA、History Olympiad、Mystery Hunt | 题级 gold，`match_mode=normalized` | gold | gold suite 771×2 |
| 编程 | ICPC WF 2012–2025、IIOT、Codeforces | `ao.icpc-package/v1` + samples + 远程 OJ 映射 | 本地 sample（Docker）+ Kattis/VJudge 官方判 | ICPC `remote_judge_ready` 的年份 24 个 job 在跑（`icpc_all_full_pairs_20260909`） |
| 报告/多模态 | IOL、IOAA、IJSO、IEO、MCM/ICM、IYPT、WSC、Jessup、Vis Moot 等 | PDF/文本 | rubric / slide_deck_v1 | 有数据和 evaluator，没接进 contest-session 批跑 |
| CTF/网络 | Cybench、NYU CTF、CCDC | flag/Docker/场景 | 需要真实环境 | 未接入 |

LiveOIBench 不在 `data/` 里，是外挂目录，由 `src/liveoibench_adapter.py` 离线适配。"gold suite" 不是一个数据目录，是 `run_otc_gold_suite.py` 从 benchmark gold 里筛出的 deterministic 子集。

### 2.4 批跑脚本

- `scripts/run_otc_gold_suite.py`：遍历指定竞赛的 structured-gold 记录，自动生成 manifest。ARML Local / National Team 把整份 packet 按题 split；Power 保持 packet；Science Bowl 按官方 `parent_session_id`（试卷/round）合并题目；QANTA 按 `year + tournament` 合并；Mystery Hunt 按 `year` 合并。逐 session 起子进程，跳过已完成的，持续重建 `summary.tsv`。2026-09-09 之前的 gold-suite 表把 Science Bowl / QANTA / Mystery Hunt 的 question-level benchmark row 各自当成一场，其 `N=140/240/261` 是旧的评测 session 数，不是届数；这些旧结果不能直接改标签，需按新 manifest 重跑。当前 `arml_all_protocol_v3_{otc,vanilla}_20260909` 就是它跑的。
- `scripts/run_all_icpc_full_pairs.py`：选所有 `remote_judge_ready` 的 ICPC WF 年份，生成全年 manifest，OTC/vanilla 成对调度，按 session+variant 断点续跑，每个 job 前先探 `vjudge_gateway /health`，不健康就 `status: blocked` 停下（而不是继续产 PENDING）。
- `scripts/run_arml_2009_protocol_check.py`：单场 ARML 2009 配对 + `paired_config.json` / `paired_summary.json`。
- `scripts/regrade_contest_sessions.py`、`scripts/score_power_rubrics.py`：事后重判。
- `scripts/_export_paste_tabs_3_6.py`、`scripts/posthoc_icpc_metrics.py`、`scripts/export_results_sheet.py`：导 TSV 给表格。

## 3. Actions：agent 到底能干什么

### 3.1 一个注册表，23 个 typed action（`contest_session_v4`，`action_set_version=3`）

`src/tool_registry.py` 的 `_SPECS` / `ACTION_REGISTRY` 是唯一定义处。每个 `ActionSpec` 有 name、description、JSON 参数 schema、visibility、所属 capability pack、预算语义、handler。**同一份定义同时用于**：生成 provider 的 function schema、渲染到 prompt 的说明、参数校验、dispatch。

> 9/9 的 v4 把 Selin 旧栈 workboard/workspace 里真正补缺的动作以 typed action 形式接进来（"桌面" action），存储仍只有 `ContestSession` + `ContestMemory`，旧栈不动。变更记录见 [contest-systems.md](../contest-systems.md) "contest_session_v4: desk actions"。

**common pack**（所有 family 都有）：

| action | 参数 | 干什么 |
|---|---|---|
| `select_problem` | `problem_id` | 切换共享 active task；有计划（coach ≠ none）时 enum 限制为分给你的题且不含当前题 |
| `speak` | `content` | 公开广播。编程题作者对已 sample-AC 的版本 speak，同时被记为 "local run report / 请求 review" |
| `direct_message` | `recipients[], content` | 私聊一个或多个队友（v4 由 `recipient` 改为列表，替代旧栈 `message_group`）；只在 `private_channel` 开且 team_size>1 的 baseline（centralized、两个 OTC）出现，元素 enum 限定为其他队友 |
| `work` | `content` | 记录一个 **不可变 answer version**（答题卡的某题草稿）；编程 reviewed 模式下降级为"分析笔记"，不改源代码。v4：内容与该题**任一历史版本**相同时不建版本，回一条私有 `work_duplicate`（谁在第几轮已记录、还有哪些题空着） |
| `request_review` | `content, reviewer?` | 发 review 请求；只有 `review_workflow` 开的 baseline（两个 OTC）有；编程题也没有（用 speak 代替） |
| `review_answer` | `problem_id, version_hash, decision(approve/reject), content` | 独立评审某个精确版本；不能评自己写的；只有两个 OTC 有；enum 限定为路由给你的待审版本 |
| `submit` | `answer` 或无参 | 非编程提交。answer-sheet 竞赛变为无参数：一次性交整张卡并结束比赛 |
| `skip_problem` | `reason?` | 离开当前题（会触发 problem digest） |
| `finish_contest` | `reason?` | 所有 baseline 都只在所有题都有有效提交时才出现（v4 之前 vanilla 暴露但 handler 必拒）；answer-sheet 竞赛永远隐藏；centralized 下只有 leader 有 |
| `rest` | `reason?` | 跳过本回合 |
| `assign_problem` | `agent, problem_ids[], reason?` | **仅 centralized 的 leader**：替换某队友的强制 work 列表（公开事件，resume 重放）；`LEADER_ACTION_NAMES` |

**桌面（desk）action**（同属 common，不受 Coach 分配限制；`DESK_ACTION_NAMES` = `DESK_READONLY_ACTION_NAMES`{inspect, triage} ∪ `MEMORY_ACTION_NAMES`{remember, recall, share_note}。哪个 baseline 有哪个 bundle 见 §2.0：no-coach 两个都没有，centralized / open_table_coach 只有只读两个，open_table_coach_memory 五个全有）：

| action | 参数 | 来源 | 干什么 |
|---|---|---|---|
| `inspect_problem` | `problem_id?, focus?` | 旧栈 `open_problem` + `verify` | 只读：题面 + 全部 version（正文截 2000 字）+ review + submission（编程题带 sample report），私有 `inspect_problem_result` 事件；**不动共享游标**，不算 review。取代编程 pack 里的 `verify` |
| `triage_problem` | `problem_id, priority(high/normal/low/hopeless), reason?` | `mark_hopeless` + `set_priority` | 写 `TaskUnit.priority/triage_reason/triaged_by/triaged_turn` + 公开 `task_triaged`；scheduler 的 work 列表按 priority 稳定排序（Coach `task_order` 在同档内保持），hopeless 排最后但不剔除，deadline 照旧收其最新草稿 |
| `remember` | `content, problem_id?` | `remember` | 私有 `note` 事件（这条事件本身就是笔记，`note_id` = event_id），可带题号 |
| `recall` | `query?, problem_id?` | `recall` | 私有 `recall_result`：自己的 note + 全队 `note_shared`，排序移植 `memory.py`：题号命中 → 词频 → 新近，按内容去重，≤ 8 条 |
| `share_note` | `note_id` | `publish_memory` | 把自己一条 note 复制成公开 `note_shared`（带 `source_event_id`）；分享别人的或重复分享 → `action_error` |

**capability pack**（按竞赛 allowlist 决定）：

| pack | actions | 给谁 |
|---|---|---|
| programming | `execute_code(code, language?)`、`submit_code(code, language?)`（`verify` 仍在注册表里给旧栈用，contest session 的 frozen set 里已去掉） | ICPC、IIOT、Codeforces；MCM/ICM 拿 `execute_code` 但不是编程提交题 |
| math | `use_calculator(expression)` | Purple Comet、Fyziklani、IYPT、IJSO、IOAA；**ARML 没有**（曾经广告了 calculator 但执行拒绝，9/6 修掉） |
| research | `web_search(query)` | Fyziklani、MCM/ICM、IEO、Jessup、IYPT |
| physical | `read_lab_equipment`、`read_star_chart` | 只在 benchmark 显式声明 capability 且有 handler 时才出现 |

ARML / HMMT / IOL / WSC：没有任何 task tool，只有 common 十六个（再按 baseline 裁掉不属于它的 bundle）。

没搬的：`list_problems`（每回合已注入 `TASK STATUS`，v4 只补了 `versions/priority/hopeless/triaged_by` 列）、`claim_problem/release_problem`（OTC 有 Coach 分配 + runtime 强制；给 vanilla 加 claim 等于给基线加策略）、旧 `verify_problem`（`review_answer` 绑 `version_hash` 更强）、`check_budget`（`BUDGET` 已注入，v4 补 `blank_tasks`）、deliberation 五件套。

### 3.2 每回合动态裁剪（`_actions_for_agent`）

注册表给的是上限；每次调用前 runner 再按状态裁：

- 先按 baseline 开关剔除不属于它的 bundle（`_trim_to_baseline`：memory / desk / direct_message / assign_problem）。
- 所有 baseline：`finish_contest` 在任一题没有有效提交时隐藏；桌面 action 的 `problem_id` enum 填成本场全部题号。
- `review_required` 关（no-coach、centralized）：删 `request_review`、`review_answer`。
- centralized：worker 删 `submit` / `submit_code` / `finish_contest`；leader 的 `assign_problem` 的 `agent` enum = 其他座位、`problem_ids` 元素 enum = 全部题号；编程题 leader 的 `submit_code` 变无参。
- answer-sheet 竞赛：删 `finish_contest`；任一必答题没草稿时删 `submit`；strategic 还要 final review 完成才给 `submit`；一旦条件满足，**只剩 `submit`**（避免在最后一题上反复重写；桌面 action 此时也没有）。
- 有计划的 baseline（centralized、两个 OTC；下文 "strategic" 均指此）：`select_problem` 只能选分配内的其他题；active task 不在你的 work 分配里时，`work` / `skip_problem` / `submit_code` 全隐藏，只留 common 的沟通类 + 桌面；active 已被独立 approve 后隐藏 `work`。
- strategic 编程（reviewed）：`work` 描述改为"只记笔记"；`submit_code` 只在"最新版本有 sample-AC 证据 **且** 有非作者 review（approve 或 reject 都算）且该版本没提交过"时出现，且变为**无参数**，提交的是冻结源码；`request_review` 删除；连续两次无产出动作（桌面 action 也算无产出）后，**只剩 `execute_code`**（source-required 门）。

### 3.3 Function call 的三种传输（`--action-calling`）

`src/llm.py` 统一为 `LLMRequest(tools=..., tool_choice=...)` / `LLMResponse(tool_calls=...)`。

| 模式 | provider | 实现 |
|---|---|---|
| `native` | Perplexity `/v1/agent`、OpenAI Responses API | 每个 `ActionSpec` 渲染为 OpenAI 风格 `{"type":"function","name","description","parameters"}`；runner 传全部当前可用 function + `tool_choice="required"`；解析 `output[type=function_call]`。这是当前所有 gpt-5.4-mini 实验用的 |
| `emulated` | Tinker（Qwen） | Tinker SDK 没有原生 tools / constrained JSON，所以把同样的 schema 渲染进 prompt，要求回 `{"name":..., "arguments":{...}}`；`llm.py:326-533` 容忍 fence / `<tool_call>` 标签 / 字符串化 arguments，校验 required、类型、enum，最多 **2 次**纠错重试，重试消耗共享 API/token 预算 |
| `prompt-json` | 任意 | 不走 tool adapter，模型直接回 `{"action":..., "arguments":{...}}`，`actions.parse_typed_action` 解析。只用于兼容实验 |

`auto` = Perplexity/OpenAI 用 native，Tinker 用 emulated。实际用的传输记在 `contest_session.json.action_calling`，每次调用记在 `action_transport_log`。

### 3.4 一个回合发生什么（`contest_runner.py:2206-2609`）

1. 外层 `for turn`：消耗 1 turn + 5 分钟模拟钟（`minutes_per_turn`，默认 5）；`max_turns` = 官方时长 ÷ 5，上限 90，所以模拟钟走满正好等于官方时长。
2. 内层按固定座次 `Agent_1..N`（`--start-seat` 只改首发，不逐轮轮转）。
3. 有计划的 baseline：`_scheduled_agent_task` 把共享游标移到该 agent 的目标（§5.2）；centralized 下 leader 永远排第一位。
4. `_actions_for_agent` 算合法 function 集。
5. 预扣 1 次 API call → 调模型。超 token 余额则扣完余额后不执行动作。
6. **只执行第一个 function call**，多余的记 `extra_function_calls_ignored`。
7. `_apply_action`：先 append 一条 ContestMemory 事件，再改 `ContestSession`。任何解析/schema/分配越权/前置条件不满足/运行错误 → 记一条私有 `action_error` 事件，本回合作废，继续。
8. checkpoint 落盘。

三个预算：`max_turns` 每轮扣；`max_api_calls` 每次模型调用（含 Coach、含 emulated 重试）前扣；`max_total_tokens` 只算输出。墙钟只记录不限制。

### 3.5 编程题流水线（`programming_workflow_v4`）

1. 作者 `execute_code(code)` → Docker 沙箱（`src/isolated_python.py`，`--pull=never`、无网络、只挂源码、stdin 喂输入）跑官方 sample，逐 case 返回 expected vs actual；只有 sample AC 才给该版本挂 `evidence_refs`。
2. 作者 `speak` 报告 sample 结果 → 该版本进入共享 review 队列。
3. **另一个** agent `review_answer(problem_id, version_hash, approve|reject, content)`，prompt 里给的是完整源码 + sample report。
4. `submit_code()` 无参 → adapter 再跑一遍 sample（失败返回免费的 `SAMPLE_WA/RE`，不消耗远程次数）→ Kattis / VJudge gateway 官方判。
5. WA/TLE 后 prompt 注入 verdict checklist；连续 3 次有效非 AC → 该题 `BLOCKED` 进入冷却，`StrategicPolicy.can_revisit` 到期才能回来。

v4 额外：失败执行去重（源码+语言+题+judge 指纹相同则直接复用结果，不再跑沙箱）、Infiltration 语义 checker、deadline 候选选择（sample-AC 优先 → 有独立 review → 最近）。reject 不是否决：任一独立 review 即满足 submit 门，远程 judge 才是最终 oracle。

## 4. Memory：是 function call 吗？怎么存？

**结论：记忆的主体是所有 action 的副作用——每个被接受的 action 先被 append 成一条 `ContestMemory` 事件，然后 runner 再把 tool 结果、judge 结果、控制事件也 append 进去。agent 每回合看到的是这个账本的一个有界投影，不是全量。v4 起另有三个显式的 function（`remember` / `recall` / `share_note`），但它们写的也是同一本账（`note` / `note_shared` 事件），没有第二套存储。**

### 4.1 存储：`ContestMemory`（`src/contest_memory.py`）

append-only 事件账本，绑定 `run_id / session_id / competition_id`。每条 `ContestEvent`：

```
event_id, task_id, question_id, actor, visibility, recipients, kind, payload(JSON), turn
```

`visibility` 四档（`contest_memory.py:170-183`）：

| 档 | 谁能看 | 当前 runner 里用在哪 |
|---|---|---|
| `public` | 所有人 | speak、work、review、scoreboard、submit_code 结果、Coach 总计划、`task_triaged`、`note_shared` |
| `private` | actor + 显式 recipients | direct_message（recipients=[一个或多个队友]）、tool 结果（calculator/execute_code/`inspect_problem_result`/`recall_result`）、`note`、`work_duplicate`、`action_error`、每人的 `coach_personal_assignment` |
| `group` | actor 或所在组 | API 支持，runner 目前没用 |
| `judge` | 仅 `is_judge=True` 的查看者 | API 支持，runner 目前没写 |

与账本并列的是 **`ContestSession`**（`src/contest_session.py`）——权威的任务状态机，不是给 agent 读的文本：每题的 `AnswerVersion`（content、`version_hash`=sha(task+part+parent+content)、author、`evidence_refs`）、`Review`（绑精确 hash，版本一更新旧 review 全部 `stale`）、`Submission`（verdict/score/valid）、state（`UNTOUCHED/CANDIDATE/SOLVED/BLOCKED`）、cooldown、预算账本。

### 4.2 写入路径

| 谁写 | 写什么 |
|---|---|
| agent 的 action（间接） | `speak`→public 事件；`work`→public 事件 + 新 `AnswerVersion`；`review_answer`→public 事件 + `Review`；`direct_message`→private 事件；`triage_problem`→public `task_triaged` + `TaskUnit.priority` |
| agent 的桌面 action（显式） | `remember`→private `note`（带 problem_id）；`share_note`→public `note_shared`（`source_event_id` 指回原 note）；`inspect_problem` / `recall` 只读，结果作为 private tool 事件回给本人 |
| runner | tool 结果（private）、judge 结果（public）、`scoreboard`（每回合 `_task_rows`）、`action_error`、switch/skip 记录、deadline 事件、`programming_*` 进度计数 |
| Coach | `precontest_coach_guidance`（public，含完整 plan）+ 每人一条 `coach_personal_assignment`（private） |
| runner 在切题时 | `create_problem_digest(task_id, viewer=agent)`：把该 agent 在离开的题上最近 12 条可见事件压成一个 `ProblemDigest`（排除 judge-only 和答案泄漏字段） |

没有任何 LLM 摘要步骤；所有压缩都是确定性截断。

### 4.3 注入 prompt（`_user_prompt`，`contest_runner.py:1030-1203`）

每回合 user prompt 的组成：

```
[FINAL REVIEW PHASE 提示（若有）]
ACTIVE TASK <id> + 完整题面
TASK STATUS  (所有题的 state/versions/latest_author/priority/hopeless/triaged_by/是否 solved)
SHARED REVIEW HISTORY  (每题最多 5 版、每条 800 字符)
YOUR ELIGIBLE PENDING REVIEWS  (路由给你的待审版本：题面 + 完整答案/源码 + sample report)
BUDGET  (+ blank_tasks：还没草稿的题)
YOUR ENFORCED PERSONAL COACH MEMORY  (strategic：你的 work_tasks / review_tasks / task_order / switch_conditions / final_check)
ACTIVE PROGRAMMING SOURCE  (strategic 编程：最新版本完整源码 + hash + reviews + 最近官方提交，不占下面的 6000 字符)
CONTEXT:
   vanilla   → memory.view(agent) 最后 12 条可见事件
   strategic → memory.strategic_projection(viewer, current_task_id, max_chars=6000)
```

`strategic_projection`（`contest_memory.py:332-443`）的结构：

```
contest_capsule, scoreboard,
current_task_events   ≤ 8 条（排除 scoreboard/direct_message/编程进度计数类；当前题上的 note 会出现在这里）
recent_digests        ≤ 4 个（该 agent 自己在其他题上留下的 digest，含 note）
recent_notes          ≤ 4 条（v4：自己的 note + 全队 note_shared，排除已在 current_task_events 里的）
procedural_lessons    ≤ 6 条
direct_messages       ≤ 8 条（recipients 为列表）
```

超 6000 字符时反复从最大的列表头部弹出，仍超则把 capsule/scoreboard 置 `{"truncated": true}`。跨题的笔记检索靠 `recall`，不靠投影。

注意：`procedural_lesson` 和 `contest_capsule` 两个槽位在投影 API 里有，但 **runner 目前没有任何地方 emit 这两类事件**（grep 只命中 `contest_memory.py`），所以实际投影里这两项一直是空/None。

### 4.4 持久化与 resume

每个 session 目录：

- `contest_checkpoint.json` = `{protocol_version, action_set_version, session: ContestSession.to_dict(), memory: ContestMemory 全量 JSON 字符串}`，每个 action 后覆盖写。`--resume` 时 `protocol_version` 不等于当前代码（`contest_session_v4`）直接退出，v3 的 checkpoint 不能续跑到 v4。
- `contest_session.json` = 最终结果：config、frozen action set、`action_calling`、`action_transport_log`、每题 versions/reviews/submissions、`shared_review_history`、budget/timing、diagnostics、metrics（TaskUtility、AAR、AB、review coverage、stalled turns、switches…）、grade、coordination（CS）、`precontest_coach_plan`、archival memory 全量。
- `run.log`。

`--resume` 同目录：校验 task 集和 scope 一致后重建；Coach 计划从 memory 里读回，不再调用；`ProgrammingProgress` 计数也从 memory 恢复。checkpoint 与 variant 绑定，vanilla/strategic 不能互相复用。

### 4.5 旧栈的 memory（了解即可）

`src/memory.py` 的 `MemoryStore` 才是"显式 function 式记忆"：`remember`（写私有 `M1..`）、`recall`（按 problem_ref/词法/新近度取 ≤8 条，结果作为下回合的 private observation）、`publish_memory`（拷成共享 `S1..`）。另有 `write_private_notes` / `write_scratchpad`（整块覆盖）、`Workboard`（claim/attempt/review 按题）、open_table_coach 的三层 memory（personal = 最近 N 条 private think；group = 最近 N 条定向消息；public = 最近 N 条广播，N 由规则卡定，ARML Local 是 3/12/24）。这一套在 `--schema` 路径下仍能跑，当前实验没用。

## 5. Open Table Coach 是怎么做的

### 5.1 Coach = 一次性的 LLM 规划调用，不是常驻 agent

`contest_runner.py:714-757` `_precontest_coach_prompts`。system prompt 原文要点：

> You are Coach. Produce a structured pre-contest brief for the contestant agents, then exit. You may assign one problem per agent, several agents to one problem, or the whole team to one problem. ... Do not solve the problems and do not call contestant actions. Respect the declared task family ... Return only one JSON object with this schema: `{"summary","work_assignments":{"Agent_1":[problem_id]},"review_assignments":{...},"task_order":[...],"switch_conditions":[...],"final_check":[...]}`

user prompt 给：competition_id、task_family、competition_description、team_size、四项预算、规则卡文字、全部题目（id/type/programming/完整 prompt），并要求"每题至少一个 worker 和一个 reviewer，只用精确的 Agent_N 和 problem_id"。

Coach 用的模型和 contestants 相同（`run_competition_batch.py:1342-1355` 传同一个 query fn），消耗 1 次共享 API call 和输出 token，**不占 turn**（在 `for turn` 循环之前）。resume 时不重跑。

`_normalize_coach_plan`（`contest_runner.py:819-883`）兜底：JSON 解析失败 → 抓第一个 `{...}` → 仍失败则 round-robin 默认分配；漏分的题补 round-robin worker；每题不足 2 个 reviewer 时补一个 backup；task_order 缺失则用 manifest 顺序。

产出落两处：public 事件 `precontest_coach_guidance`（完整 plan）；每人一条 private `coach_personal_assignment`（`work_tasks`、`review_tasks`、`task_order`、`switch_conditions`、`final_check`）→ 就是 prompt 里的 `YOUR ENFORCED PERSONAL COACH MEMORY`。system prompt 也拼进 `PRE-CONTEST COACH BRIEF` 全文。

### 5.2 Coach 退场后：确定性 scheduler 执行计划

每次调某个 agent 前，`_scheduled_agent_task` 先把我的 work 列表按 `triage_problem` 的 priority 稳定排序（high → normal → low → hopeless；同档内保持 Coach `task_order`，v4），再按以下优先级把**共享 active-task 游标**移到该 agent 的目标：

1. 路由给我的、待审的 **编程** 版本（reviewer 先把 ready 的代码审掉，避免 sample-AC 代码烂在队列里）；
2. 我自己写的、已 sample-AC、但还没 `speak` 报告的版本；或已 sample-AC 且有独立 review 但还没 `submit_code` 的版本；
3. 我的 work 列表里 **还没任何版本** 的题，或需要修源码（sample 失败 / 官方 WA）的编程题 —— 二者按同一轮转顺序，防止新题无限压住修 bug；
4. 路由给我的其他 family 待审版本；
5. 我的 work 列表里：最新版本被 reject 的题 → 未锁的编程题 → 尚无独立 approve 且最新版本不是我写的题。

所以"**shared active**"= 全队只有一个当前题游标，但它不是所有权锁：scheduler 在每人调用前重指，agent 对分配外的题动手会被 `coach assignment does not allow ...` 拒绝并记 `action_error`。

补充机制：

- **rescue**：某题连续 2 个版本被 reject 后进入 `rescue_task_ids`，work/review 资格向全队放开。
- **stall**：`StrategicPolicy(stall_turns=3)` —— 3 轮无进展或 `BLOCKED` → 记 switch reason，游标移走，稍后可回访。vanilla 也有 stall guard，但其自动移动单独计为 `baseline_mechanical_switches`。
- **final review phase**：answer-sheet 竞赛里所有必答题都有普通 approve 后，控制器进入 final review，reviewer 再审一遍最新版；完成后才放出无参 `submit`。
- **deadline**：循环结束后，所有没有效提交的非编程草稿由环境直接提交（两个 variant 都一样，不额外花模型调用）；编程题只有开 `--programming-deadline-submit` 才兜底。

### 5.3 "Open table" 指什么

所有 action 落在同一个可见性分级的账本里；`speak`/`work`/`review`/`task_triaged`/`note_shared` 是公开的，谁都能在自己的投影里看到（受 8 条/6000 字符上限）。`direct_message`（可多收件人）是唯一的私聊通道；`inspect_problem` 让任何人不动游标就能看别人的题。没有独立的"消息板"对象，也没有投票或 Coach 终裁——最终答案的整合方式就是：answer-sheet 一次性交每题最新草稿；编程题交冻结的已审源码。

### 5.4 代码里出现过的一些名字对应什么

| 名字 | 实际含义 |
|---|---|
| dynamic coach | 就是上面这个一次性、看到全部题面的 LLM Coach（测试名），不是持续介入 |
| personal coach / enforced personal coach memory | 每人 private 的 `coach_personal_assignment`，不是另一个 agent |
| shared active | 全队一个游标（§5.2） |
| staged / forced pipeline | 编程四步 + answer-sheet 的 draft→review→final review→submit 强制阶段，不是独立 variant |
| protocol v3 | 9/6 把 vanilla 和 OTC review 工作流拆开的那次修订（§6.3） |
| protocol v4 / desk actions | 9/9 接入 `inspect_problem` / `triage_problem` / `remember` / `recall` / `share_note`、多收件人 DM、`work` 重复反馈（§3.1）；结果记 `protocol_version=contest_session_v4` |
| 五个 baseline / `BaselineFeatures` | 9/9 下午把 `vanilla|strategic` 二元变量拆成 9 个开关 + 5 个预设（§2.0）；`action_set_version=3`（加 `assign_problem`） |
| leader / `assign_problem` | `centralized` 预设里的 Agent_1：出计划、每轮先行、唯一提交、可现场改派（§2.0） |
| programming_workflow_v2/v3/v4 | 编程流水线三次修订（§3.5） |

### 5.5 与旧 `--schema open_table_coach` 的区别

旧版：turn 1 Coach 给"不看题"的准备简报；turn 2 contestants 看题开局后 Coach 再总结一次优先级/分组然后永久退出；之后每个 contestant 每回合先一次私有 deliberation 调用再一次 committed action 调用，都计费。当前版：Coach 一次调用（看全部题）+ 确定性 scheduler 全程执行。

## 6. Agent 怎么分类、内部怎么分工

### 6.1 没有 persona，只有 `Agent_1..N`

当前栈所有 contestant 用同一 base prompt：`You are {agent}, one contestant in a {N}-agent team. You decide which provided function best advances the contest. Choose exactly one function and call it once.`（`contest_runner.py:885-909`）。没有代数/几何/coder/scribe 之类固定角色。**差异化来自三处**：Coach 分给谁哪些题、谁被路由去审谁的版本、当前回合动态裁剪后剩下哪些 function。

规则卡（`data/rules/<comp>/collaboration.json`）里 ARML Local 和 ICPC 都故意定义了对等的 `contestant` 角色，并写明"临时专长应保持动态"。当前栈唯一的固定角色是 `centralized` 预设里的 leader（`Agent_1`，见 §2.0）；旧栈的 `centralized` 用 `Group_Leader`；规则卡的 fallback 角色（captain/primary solver/verifier）只在旧栈 `--rules-mode enforced` 下注入。

system prompt 按开关和 family 拼接（`_system_prompt`）：

- 有桌面 action 的 baseline：base 后面有一段 `DESK TOOLS`：说明 `inspect_problem` 不动游标、`remember` 是笔记 / `work` 才是候选答案、`triage_problem` 影响调度、hopeless 仍会 deadline 提交、桌面动作也消耗回合。
- `coach == none`（single_agent / decentralized）：base（+ 规则卡文字）。就这些。
- `coach == precontest`（两个 OTC）：base + DESK TOOLS + `PRE-CONTEST COACH OPERATING PRINCIPLE`（跟随 Coach 分配；active task 是共享游标不是锁；不要覆盖已审过的好版本；私事用 direct_message、公事用 speak；`work` 只放实质候选答案）+ review 段（`review_required` 时）+ family 段（`ANSWER-SHEET COACH PROTOCOL` / `MANDATORY PROGRAMMING WORKFLOW` / `MATHEMATICS WORKFLOW` / `SHORT-ANSWER WORKFLOW` / `PUZZLE WORKFLOW` / general）+ `PRE-CONTEST COACH BRIEF` 全文 + 规则卡。
- `coach == leader`（centralized）：base + DESK TOOLS + `LEADER PROTOCOL`（leader 版：计划被强制执行、可 `assign_problem`、只有你能提交；worker 版：只做自己列表里的题、用 speak 报告、用 direct_message 找 leader、你不能提交）+ 无 review 的 family 段（`ANSWER-SHEET PROTOCOL` / `PROGRAMMING WORKFLOW`）+ `OPENING LEADER PLAN` 全文 + 规则卡。

### 6.2 分工怎么落地

- **谁做哪题**：Coach 的 `work_assignments`（允许一题多人）；runtime 强制。
- **谁审谁**：Coach 的 `review_assignments`，normalize 保证每题 ≥2 个 reviewer；runtime 把"路由给你、非你所写、当前最新"的版本放进 `YOUR ELIGIBLE PENDING REVIEWS`，`review_answer` 的 enum 也只包含这些。
- **审的规则**：作者不能审自己；只能审当前最新版本（`version_hash` 必须匹配）；版本一更新旧 review 全 stale；非编程提交要求"有非作者 approve 且无未过期 reject"；编程提交要求"有 sample 证据 + 任一独立 review"。
- **最终整合**：无投票、无 Coach 终裁。answer-sheet：所有必答题有草稿 + 普通 review + final review → 一次无参 `submit`。编程：每题各自 `submit_code()` 冻结源码。deadline 兜底见 §5.2。
- **卡住怎么办**：stall 3 轮切题；3 次官方非 AC 冷却；2 次 reject 进 rescue 放开分配；编程 2 次无产出动作后只剩 `execute_code`。

### 6.3 五个 baseline 各自有什么、没什么

开关表见 §2.0；这里按行为对照：

| | single_agent / decentralized | centralized | open_table_coach | open_table_coach_memory |
|---|---|---|---|---|
| 计划 / 私有分配 | 无 | Agent_1 开场出计划，赛中 `assign_problem` 改派；runtime 强制 | Pre_Contest_Coach 一次性计划；runtime 强制 | 同左 |
| 可见 actions | common 去掉 `request_review`/`review_answer`/桌面/DM + 竞赛 pack | + `inspect_problem`/`triage_problem`/`direct_message`；leader 多 `assign_problem`，worker 无 `submit`/`submit_code`/`finish_contest` | + 桌面只读 + DM + review 两个 | + `remember`/`recall`/`share_note` |
| 每回合 | 每人 1 次调用、1 个公开 action | 同；leader 先行 | 同（Coach 调用在循环外） | 同 |
| memory 视图 | 最后 12 条可见事件 | 6000 字符 projection + personal memory | 同 + pinned source | 同 + recent_notes |
| review / 不可变版本 | 有版本无 review；重复 `work` 回 `work_duplicate` | 同左 | 版本 + review + final review | 同 |
| 游标移动 | `work` 后自动跳下一道空题；stall guard（计 `baseline_mechanical_switches`） | scheduler 按分配 + priority + stall + cooldown | 同 | 同 |
| 提交 | 所有必答题有草稿后只剩 `submit` | 同，但只有 leader 看到 `submit`；编程题 leader `submit_code` 无参 | final review 完成后只剩 `submit`；编程题走四步 | 同 |
| deadline 收集 / 判分 / 预算 / 规则 / Docker / 远程 judge | 完全相同 | 完全相同 | 完全相同 | 完全相同 |

预算是**相同上限**而非相同消耗：OTC 的 Coach 和 review 调用都吃共享预算。实测 OTC 输出 token 约为 vanilla 的 3×（ICPC 2012 v4 配对），API 调用约 10×（ARML Local 五年配对）。

历史口径：`arml_all_protocol_v3_*`、`icpc_all_full_pairs_20260909` 是 v3 的 `vanilla_team` / `strategic_team`，对应今天的 `decentralized` / `open_table_coach`，但 OTC 那一侧多了 `inspect_problem` / `triage_problem`，严格比较要用新目录重跑。

## 7. 判分与产物

- `grade_contest_result`（`src/contest_adapters.py:328-378`）：编程题按 session state 是否 `solved` 给 0/1；非编程题用 `gold_answer_v1`（归一化：小写、去空白/LaTeX 标点、统一负号/根号/分数/科学计数，接受 aliases；**没有**数值 epsilon 或代数等价）；无 gold / reference-only / rubric 题标 `unavailable`，从分母剔除。返回 `graded`、`evaluation_coverage`、`graded_tasks`、`ungraded_tasks`、`score/max_score`、`task_utility`、每题明细。注意 `graded` 在"全部 unsupported"时也为 True（正是本周那个失败测试的争议点），下游应看 `evaluation_coverage`。
- `rubric_llm_v1`（`src/evaluation/rubric_llm.py`）：结构化 criterion，LLM 逐条给分+证据，`models.py` 校验 id/上限/总分。**contest-session 路径目前接不到它**：`run_competition_batch.py` 的 manifest 分支只走 `grade_contest_result`，`regrade_contest_sessions.py` 也一样，所以 26 个 Power session 全部 `unavailable`。
- 协作分：`collaboration_score.py` 的 CS = (Comm 0–5 + Plan 1–5)/2，LLM 判；CCE（`cce.py`）是因果动作图指标，默认关。
- 过程指标：TaskUtility、AAR（active-agent rate）、AB（1−动作数 Gini）、review coverage、final-review coverage、attempts-to-AC、stalled turns、switches、`programming_repair_yields`、`programming_source_required_actions`、`programming_duplicate_executions_avoided`、deadline 提交计数、`action_transport_log` 统计；v4 新增 `inspect_count`、`notes_recorded`、`notes_shared`、`recall_count`、`triage_changes`、`items_hopeless`、`repeat_draft_attempts`。
- 批级产物：gold suite → `summary.tsv`（+ `rubric_scores.tsv`）；ICPC → `runs/<year>_{otc,vanilla}/` + `completed_metrics.tsv`（`model, variant, contest, Acc, score, max_score, CS, Comm, Plan, AAR, AB, turns, api_calls, tokens, penalty_min, sec, remote_attempts, valid_remote_results, protocol, inspect, notes, notes_shared, recalls, triage, hopeless, repeat_drafts, artifact`）；表格 → `results/gold_suite_sheets_20260903/paste_tabs/`（tab4/tab5 每 session 行同样多了 `protocol` 到 `repeat_drafts` 八列，v3 的 session 这些列为空）。

## 8. 目前已知的口子

1. `procedural_lesson` / `contest_capsule` 投影槽位没有生产者（§4.3）。
2. ~~循环内的 `deadline_submit` 死代码~~ —— v4 已删；deadline 收集只在循环结束后由控制器做。
3. rubric 判分没接进 contest-session 路径（§7），Power 26 个 session 待评。
4. `grade_contest_result.graded` 语义 vs `test_reference_only_gold_is_unavailable`，待定（目前全量测试里唯一失败项）。
5. `contest_rules.py` 里的 `progressive_batches` / `max_wrong_submissions` / `allow_partial_credit` / `search_policy` 只是描述和审计字段，typed runner 不用它们门控；实际生效的只有工具 allowlist 和注入 prompt 的规则文字。罚时 20 分钟来自 benchmark metadata 默认值而非规则卡。
6. Kattis `out of submission tokens` 被映射成通用 `SUBMIT_FAILED`（`src/judge/kattis.py:130`），需要单独分类 + 退避。
7. vanilla 的前置缺口：~~`finish_contest` 仍暴露但 handler 必拒~~（v4 已对两个 variant 隐藏）；AC 后游标不前进；同源重提在 AC lock 之前到达 executor。
8. `docs/DATA_COLLECTION.md` 仍描述 20 家，实际 43 个 benchmark 目录。
9. v4 之后 `arml_all_protocol_v3_*` 与 `icpc_all_full_pairs_20260909` 都是 v3 结果；要比较桌面 action 的效果得用新目录重跑，旧 checkpoint 不能 `--resume`。
10. 可选未做：`src/actions.py` 的 `WORKBOARD_INSTRUCTIONS` / `WORKSPACE_INSTRUCTIONS` 和 `src/env.py` 的 `BOARD_ACTIONS` / `MEMORY_ACTIONS` 仍是手写字符串，没有改成从 registry 渲染（那是 Selin 的文件，先确认再动）。

## 9. 常用命令

```powershell
# 单场 OTC + memory（ARML National Power 2013）；不传 --max-turns → 1h/5min = 12 turn，api = 12×3+1
..\.venv\Scripts\python.exe -u src\run_competition_batch.py --live --provider perplexity --model openai/gpt-5.4-mini `
  --contest-manifest data\contest_manifests\generated\arml_national_power_2013.json `
  --system-variant open_table_coach_memory --action-calling native --team-size 3 `
  --max-api-calls 37 --max-total-tokens 220000 --no-judge-task --no-judge-cce `
  --output results\<run>\arml_national_power_2013

# 配对基线：同上，只改 --system-variant decentralized（review 开关由 baseline 决定，不用再传 --require-review）

# ARML 全部 sweep（turn / api 预算脚本按比赛自动算）
python -u scripts\run_otc_gold_suite.py --competitions arml_local,arml_national_team,arml_national_power,arml_power `
  --system-variant open_table_coach --output results\arml_all_otc_<date>

# ICPC 全年配对（需 vjudge_gateway 在本地跑）
python -u scripts\run_all_icpc_full_pairs.py

# 单场配对 + paired_summary
python -u scripts\run_arml_2009_protocol_check.py --output results\arml_2009_new_pair

# 断点续跑
python src\run_competition_batch.py ... --resume --output <同一目录>
```
