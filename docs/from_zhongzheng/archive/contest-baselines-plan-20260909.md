# Contest session：五个 baseline 的配置化重构（plan）

日期：2026-09-09 · 分支：`feat/contest-session-v4-desk-actions` 之上 · 协议：`contest_session_v4` 不变（action 表面只做子集裁剪，不新增事件语义；`centralized` 新增的 `assign_problem` 走 `action_set_version = 3`）

## 0. 目标

把 `contest_runner.py` 里的二元 `system_variant ∈ {vanilla, strategic}`（28 处 `==` 分支）改成**正交特征开关 + 命名预设**，让下面五个 baseline 都由同一个引擎、同一份 `ContestRunConfig` 跑出来，而不是每个 baseline 再加一串 `if variant == ...`：

| baseline | 名字（`--system-variant`） | 含义 |
|---|---|---|
| single agent | `single_agent` | 一个座位，无 Coach，无 review，无 memory |
| decentralized (open table) | `decentralized` | N 个座位轮转，公开桌面，无 Coach，无 review，无 memory |
| centralized | `centralized` | `Agent_1` 是 leader：开赛出计划，赛中可改派，只有 leader 能提交 |
| open table coach | `open_table_coach` | 赛前 Coach 计划 + 调度器 + review 工作流 + 桌面只读工具 |
| open table coach + memory | `open_table_coach_memory` | 上一行 + `remember / recall / share_note` |

用户已定：**`single_agent` 与 `decentralized` 不带 memory**。桌面只读工具（`inspect_problem / triage_problem`）也不给这两个——它们要和 v3 vanilla 语义保持一致（见 §2 表；如要改只动预设表一行）。

旧名字保留为别名：`vanilla` / `vanilla_team` → `decentralized`，`strategic` / `strategic_team` → `open_table_coach`（v3 的 strategic 没有 memory，所以别名指向不带 memory 的那个）。

## 1. 现状问题（为什么要改）

- `contest_runner.py` 3306 行，`system_variant ==` 28 处、`review_required` 45 处；它们实际在问 6 个不同的问题（有没有 Coach、有没有 review、是不是 reviewed 编程流水线、用哪种 memory 投影、vanilla 机械切题、有没有私信），只是都借 `strategic` 这个字。
- v4 把五个桌面 action 无条件放进 common pack，导致 `strategic_team` 现在已经等于 "OTC + memory"，没有开关能得到 "OTC 不带 memory"。
- `centralized` 在 contest session 里不存在，只有旧栈 `--schema centralized`（`Group_Leader` 一次性计划 + 只有 leader 提交）。

## 2. 设计

### 2.1 `BaselineFeatures`（新，放 `contest_runner.py` 顶部）

```python
CoachMode = Literal["none", "precontest", "leader"]

@dataclass(frozen=True)
class BaselineFeatures:
    coach: CoachMode            # none / 赛前 Coach 出计划后退场 / Agent_1 常驻 leader
    review_workflow: bool       # request_review / review_answer、独立批准门、final review、programming_workflow_v4
    memory_actions: bool        # remember / recall / share_note
    desk_actions: bool          # inspect_problem / triage_problem
    private_channel: bool       # direct_message
    structured_context: bool    # memory.strategic_projection（否则 view()[-12:] 原始事件）
    submission_cooldown: bool   # SubmissionPolicy 连续非 AC 上限 + cooldown_revisit
    mechanical_switch: bool     # 答题卡 work 后自动跳下一道空题；stall 切题计入 baseline_mechanical_switches
    leader_submits: bool        # 只有 Agent_1 能 submit / submit_code / finish_contest；leader 有 assign_problem
```

预设表：

| | coach | review | memory | desk | private | ctx | cooldown | mech | leader |
|---|---|---|---|---|---|---|---|---|---|
| `single_agent` | none | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| `decentralized` | none | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✗ |
| `centralized` | leader | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✓ |
| `open_table_coach` | precontest | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| `open_table_coach_memory` | precontest | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |

`single_agent` 与 `decentralized` 开关完全相同，区别只在 `team_size` 必须为 1（`__post_init__` 校验）。这是有意的：single agent 就是"同一套无 Coach 环境、一个座位"。

### 2.2 `ContestRunConfig`

- `system_variant: str` 保留为构造参数，接受 5 个正名 + 4 个别名；`__post_init__` 里规范化成正名（`object.__setattr__`），并填 `features: BaselineFeatures`（可显式传入覆盖，用于消融）。
- `review_required` / `final_review_required` 默认值改为 `features.review_workflow`。
- `single_agent` 且 `team_size != 1` → `ValueError`；`centralized` 且 `team_size < 2` → `ValueError`。
- 新增 `LEADER_AGENT = "Agent_1"`。

### 2.3 28 处分支的归属

| 行（现） | 现在的判断 | 改为 |
|---|---|---|
| 86, 91 | review 默认值 | `features.review_workflow` |
| 217 | direct_message 可见 | `features.private_channel and team_size > 1` |
| 254 | vanilla 隐藏 review 两个 action | `not config.review_required` |
| 272 | 答题卡 submit 要等 final review | `config.final_review_required and not answer_sheet_submit_ready` |
| 281 | strategic 编程未完赛隐藏 finish_contest | 删（259 行已对所有 variant 生效） |
| 286 | strategic 且有 work_task_ids | 只看 `work_task_ids is not None` |
| 327 | review_answer 队列 enum | `config.review_required` |
| 376, 454 | 编程门 | 去掉 variant 条件，只留 `review_required` |
| 953 | system prompt vanilla 分支 | `features.coach == "none"`；Coach 段拆成 coach 段（precontest / leader 各一版）+ review 段（`review_required`）+ 家族段（编程家族在无 review 时用简短版） |
| 1148 | 上下文投影 | `features.structured_context` |
| 1174 | 答题卡规则文案 | `config.final_review_required`（有 final review 的版本）/ 其余通用版本；leader 模式附一句"只有 Agent_1 提交" |
| 1197 | 源码块 | `config.review_required` |
| 1783 | work 不许覆盖已批准版本 | `config.review_required` |
| 1994, 1999 | execute_code 门 | `config.review_required` |
| 2238 | SubmissionPolicy 上限 | `features.submission_cooldown` |
| 2318 | 赛前 Coach 调用 | `features.coach != "none"`；`precontest` 用 `coach_query_fn`、actor `Pre_Contest_Coach`；`leader` 用 `query_llm_fn`、actor `Agent_1`，事件 kind 仍为 `precontest_coach_guidance`（payload 加 `author`），下游 resume / personal_assignments 不变 |
| 2452 | cooldown_revisit | `features.submission_cooldown` |
| 2515, 2595, 2889 | 编程 reviewed 流水线 | `config.review_required` |
| 2942, 2984 | 答题卡机械切题 | `features.mechanical_switch` |
| 2997 | `in {"strategic","vanilla"}` | 删 |
| 3019 | 机械切题计数 | `features.mechanical_switch` |
| 3211 | programming_workflow_version | `config.review_required` |
| 3293 | facade 分发 | `features.coach == "none"` → vanilla runner，否则 strategic runner；两个 runner 的断言改为按 `features.coach` |

`_resolved_actions(manifest, config)` 增加 `config` 参数：按 `features` 剔除 memory / desk / private / `assign_problem`；这是 baseline 级的 action 表面，`_actions_for_agent` 只做每回合每人的裁剪。结果里的 `action_names` 因此如实反映 baseline。

### 2.4 `centralized`（唯一需要新逻辑的 baseline）

- **计划**：赛前由 `Agent_1` 用 `_precontest_coach_prompts` 的 leader 版本出同结构 JSON 计划（`work_assignments` / `task_order` …，`review_assignments` 忽略）；走现有 `_normalize_coach_plan`；leader 自己的 `work_tasks` 强制为全部题号。
- **改派**：新 action `assign_problem(agent, problem_ids: array, reason?)`（仅 leader 可见；`agent` enum = 其他座位，`problem_ids` 元素 enum = 全部题号）。语义：**替换**该座位的 work 列表。事件就是普通的公开 action 事件 `assign_problem {agent, problem_ids, reason}`（实施时没有另起 `assignment_changed` kind，和其他 action 一致）；`personal_assignments` 就地更新；resume 时按 `actor == leader` 的 `assign_problem` 事件顺序重放到 Coach 计划之上。
- **提交权**：workers 的 action 集合去掉 `submit / submit_code / finish_contest`；leader 的 `submit_code` 变为无参（提交活动题最新版本；没有版本则报错），与 reviewed 模式一致。答题卡：只有 leader 看到 `submit`。
- **座次**：leader 每回合先行，其余座位仍按 `start_seat` 轮转。
- **截止收卷**：不变（环境策略，所有 baseline 一致）。
- `action_set_version` → 3，`ACTION_REGISTRY` 加 `assign_problem`（common pack，visibility `public`）。

### 2.5 入口与产物

- `run_competition_batch.py --system-variant` choices = 5 正名 + 4 别名；`single_agent` 强制 `team_size=1`；结果 `run.system_variant` 与顶层 `system_variant` 存**正名**；新增 `baseline: asdict(features)`；`score_coordination(schema=正名)`。
- `run_all_icpc_full_pairs.py` 的等价集合加上正名；`run_otc_gold_suite.py` / `run_otc_arml_science_bowl.py` 的 `require_review = variant == "strategic_team"` 改为按 `ContestRunConfig(...).review_required`（不再在脚本里重复推断）。
- `run_contest_smoke.py`：跑 `decentralized` 与 `open_table_coach`（输出键保留 `vanilla_team` / `strategic_team` 以免动 `test_contest_smoke.py`）；"两个 variant action_names 相同"的断言改为"共同核心动作相同"。
- 导出脚本 (`_export_paste_tabs_3_6.py`, `posthoc_icpc_metrics.py`)：variant 列直接透传正名，别名不做映射。

### 2.6 不做的事

- 不改旧栈（`collaboration.py` / `env.py` / `actions.py`）。
- 不动 `ContestMemory` / `ContestSession` 的数据结构；`centralized` 只加一个事件 kind。
- 不改 `PROTOCOL_VERSION`（`v4` 结果仍可与本次并排比较，`baseline` 字段区分）。

## 3. 测试

- `test_contest_runner.py`：
  - 五个预设各自 `_resolved_actions` 的动作面（memory / desk / dm / assign_problem 有无）。
  - `single_agent` 拒绝 `team_size=3`；`centralized` 拒绝 `team_size=1`；别名规范化。
  - `centralized`：计划由 `Agent_1` 出、事件 actor 为 `Agent_1`；worker 不见 `submit`；leader `assign_problem` 后 worker 下一回合被调度到新题；resume 后改派仍生效；leader 无参 `submit_code` 提交最新版本。
  - 现有 `remember/recall/share_note` 测试改到 `open_table_coach_memory`；`open_table_coach` 上断言这三个 action 不可见。
  - 原 `test_desk_actions_are_available_to_both_variants_but_not_in_submit_only_phase` 改为按预设表断言。
- `test_tool_registry.py`：`assign_problem` 属性、`ACTION_SET_VERSION == 3`。
- `test_contest_variant_runners.py`：按 `features.coach` 的断言。
- 全量 `unittest discover`（已知失败仅 `test_reference_only_gold_is_unavailable`）。
- `run_contest_smoke.py` 通过；再用 mock 跑一次 `--system-variant centralized` 与 `single_agent` 的 `run_competition_batch`。

## 4. 文档

- `docs/contest-systems.md`：五 baseline 表 + 开关表。
- `pipeline-overview-20260909.md` §5.4 / §6.3：variant 名字对应、vanilla 别名说明。
