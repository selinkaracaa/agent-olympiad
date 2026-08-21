# ICPC 整包规则、结构化记忆与 Debate Runner 总结

## 1. 文件位置与目标

主要实现位于：

- `src/icpcrun.py`
- 复用的 LLM 调用入口：`src/llm.py`
- ICPC 规则来源：`data/rules/icpc/competition.json`、`collaboration.json`、`evaluation.json`
- ICPC 题目来源：`data/benchmarks/icpc/benchmark.json`

这个 runner 把参赛者可见的完整 RuleCard 写入每个 Agent 的 system prompt。隐藏评测字段（`scoring`、`evaluation_guidance`）不进 prompt。

流程：

1. Agent 启动时获得完整 contestant-visible 规则包；
2. 算法笔记和代码观察仍是私有记忆，必须 `memory_publish` 才进团队共享；
3. Agent 使用 `propose → challenge → evidence → revise → decide` 进行可追踪 debate；
4. 最终 Agent_1 根据题目、共享记忆和 debate ledger 生成源码。

## 2. 当前不施加本地 Token 限制

`icpcrun.py` 当前不设置应用层的 prompt token 或字符预算：不截断团队历史、debate ledger、工具结果、或进入 prompt 的记忆。最终 synthesis 不再重复整包规则，只保留 stdin/stdout 提交约定。live 调用 Perplexity 时不发送 `max_output_tokens`。

模型和供应商仍有自己的上下文窗口与输出上限。

仍保留的流程限制：RuleCard 最大行动回合、每回合最大工具步数、单工作站所有权、隔离 Python 执行时限、禁止网络/外部帮助/隐藏解答。

## 3. 总体流程

```text
ICPC benchmark problem
        |
        v
OlympiadEnvironment
        |
        +-- load data/rules/icpc/*.json
        |
        v
每个 Agent 的 system prompt
        |
        +-- CONTEST RULE PACKET（整包，参赛者可见）
        |
        v
memory_note / execute_code / debate
        |
        v
Agent_1 Final Synthesis
        |
        v
source code -> submit_final -> judge_sandbox_required
```

## 4. Prompt 里有什么

每个 Agent 的 system prompt 始终包含：

- 三人一机、禁止外网和隐藏答案；
- 完整 `rules_text`、human/agent constraints、resources、roles、rule_sections、answer format；
- 当前角色职责；
- ACTION INTERFACE（一次返回一个 JSON）。

user prompt 包含题面、私有/共享记忆、团队事件、debate ledger、本回合 tool trace。

## 5. 私有记忆与团队共享记忆

```text
note              Agent 自己的算法、理解和推论
tool_observation  隔离代码执行结果
```

只有显式 `memory_publish` 后，记忆才进入共享空间。

## 6. 工具结果立即回传

`execute_code`、`memory_*`、工作站操作的结果会立刻进入当前 Agent 的 `TOOL TRACE`，然后同一 Agent 可以继续行动。公开动作（propose / speak / done 等）结束本回合。

`execute_code` 允许 `import sys`，并可带 `stdin` 跑 sample：

```json
{"action":"execute_code","code":"import sys\nprint(sys.stdin.read())","stdin":"5 3\n2 7 1\n"}
```

只有当前工作站 owner 可以执行代码。这不是正式多语言判题沙箱。

## 7. 最终答案生成

最终 Agent_1 获得题面、debate 状态、共享记忆、私有记忆和团队事件，只返回一份完整源码。

## 8. 运行命令

```powershell
python src\icpcrun.py --self-test
python src\icpcrun.py --list-problems
python src\icpcrun.py --problem icpc_wf_2016_ceiling --rounds 2 --print-json
```

Live（Tinker 或 Perplexity）：

```powershell
python src\icpcrun.py --live --provider tinker --model openai/gpt-oss-20b --problem icpc_wf_2016_ceiling --rounds 2 --output results\icpc_ceiling.json
```

## 9. 当前评测限制

仓库里的 ICPC 题只有题面，没有隐藏测试。grade 仍是 `judge_sandbox_required`。在 programming judge 接入之前，不能把结果报成 Accepted。
