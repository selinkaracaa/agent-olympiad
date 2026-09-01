# VJudge 自动提交与 Codeforces 远程评测集成可行性

调研日期：2026-08-26  
范围：只读核查；未注册账户、未创建 contest、未提交代码。

## 结论摘要

VJudge **能够创建 ICPC/ACM 风格 contest，并从 Codeforces 添加题目**。当前站点公开列出 `CodeForces` 为受支持 OJ，`/problem/CodeForces-4A` 是有效题目路径；contest 编辑器使用 `{oj, probNum}` 题目项，并提供经典赛、分组赛、回放赛及罚时等设置。

但 VJudge **没有查到官方、公开、稳定、带版本的自动化 API**。当前网页前端确实调用了创建 contest、提交 solution 和轮询结果的 HTTP 端点，但这些是随前端 bundle 发布的内部 Web 接口，不是公开 API 合约。它们依赖登录会话，并可能触发 Cloudflare Turnstile。直接把这些端点当 SDK 使用，存在随时失效、账号风控及合规风险。

VJudge 对 Codeforces 的处理是**远程代理评测**，不是在 VJudge 本地执行 Codeforces 测试。VJudge 把代码提交到远端 OJ，再查询远端结果。普通 VJudge 用户通常可以使用平台管理的远端账号，不必提供个人 Codeforces 凭据；当前 UI 同时存在“绑定自己的远端账号”的可选路径。VJudge 服务端无论采用平台账号还是用户绑定账号，都需要可用的 Codeforces 登录身份。

因此，对 agent-olympiad 的建议是：

1. 核心评测保持为可复现的本地/自托管 judge。
2. VJudge 只做可插拔的外部验证适配器，不作为唯一真值源。
3. 第一阶段采用“人工建赛 + 人工确认提交”的半自动流程。
4. 只有在取得 VJudge 明确许可后，才实现持久化会话的网页适配器；遇到验证码必须停下并交给人工，不能绕过。

## 1. 已验证事实

### 1.1 支持 Codeforces 题目和 contest

- VJudge 当前题目页的受支持 OJ 列表包含 `CodeForces`，并链接到 Codeforces。
- `https://vjudge.net/problem/CodeForces-4A` 返回有效 VJudge 题目页面，表明题目标识采用 `OJ-problemId` 形式。
- 当前 contest 编辑器的数据模型包含 `problems: [{oj, probNum, alias, ...}]`；保存时向 `/contest/edit` POST JSON。
- 编辑器支持经典赛、分组赛、回放赛；经典计分预设包含 `sumTime: 1`、`penalty: 1200`（20 分钟），符合常见 ICPC 罚时语义。
- 公开 contest 列表展示 owner、开始时间和时长；官方 FAQ 也直接讨论“你创建的 contest”及 contest manager 视图。

结论：用 `oj = "CodeForces"` 和相应 `probNum` 组织 ICPC 风格题单在产品能力上可行。

证据：

- [VJudge contest 列表](https://vjudge.net/contest)
- [VJudge Codeforces 4A 题目页](https://vjudge.net/problem/CodeForces-4A)
- [VJudge FAQ](https://vjudge.net/article/2771)
- [当前 contest 列表前端 bundle](https://vjudge.net/static/bundle/22fd64419c073d2fdeac.js)
- [当前 contest 编辑器 bundle](https://vjudge.net/static/bundle/8d5741a12216e71ee399.js)

上述带哈希的 bundle 只用于证明 2026-08-26 当日站点行为，不构成稳定接口。

### 1.2 账户和权限

- 未登录访问 `GET /contest/create` 会返回 `errMsg: "Please login first."`，因此创建 contest 明确要求 VJudge 登录账户。
- contest 具有 owner/manager 概念；分组赛编辑器只提供当前用户可管理的 groups。可以合理判断，修改已有 contest 受 owner/manager 权限控制，但本次没有用账户实际验证各权限边界。
- 提交表单通过 VJudge 会话调用 `/problem/submit/{OJ}-{problem}` 或 `/contest/submit/{contestId}/{problemNum}`，返回 VJudge `runId`。contest 还可能要求 access code。
- 查看公开题面或公开榜单不等于拥有提交或管理权限。

已验证的最低要求是：**创建 contest 和提交代码需要有效的 VJudge 登录会话；编辑他人 contest 不应假设可行。**

证据：

- [未登录 contest 创建入口](https://vjudge.net/contest/create)
- [当前提交表单 bundle](https://vjudge.net/static/bundle/1ab4f2a25ddef0442d12.js)

### 1.3 没有查到官方公开写 API

VJudge 官方导航和 FAQ 未提供 API 文档、OpenAPI/Swagger 描述、API key 流程或版本/兼容性承诺；`/api` 返回 404。查到的调用均来自当前网页自身：

- 读取创建表单：`GET /contest/create`
- 创建或编辑 contest：`POST /contest/edit`，JSON body
- 普通题提交：`POST /problem/submit/{OJ}-{problem}`
- contest 内提交：`POST /contest/submit/{contestId}/{problemNum}`
- 提交详情/单条轮询：`POST /solution/data/{runId}`
- 状态列表：`GET /status/data`
- 批量刷新处理中记录：`POST /status/dataById`

这些端点说明“技术上可由 HTTP 客户端复现网页行为”，但**不能称为官方公开 API**。参数、认证、限流、返回结构、错误码和端点路径都可能无通知变化。

Codeforces 的官方 API 同样是读取型接口。官方 methods 页面列出 `problemset.problems`、`contest.status`、`user.status` 等查询方法，但没有创建 contest/mashup 或提交 solution 的 API 方法。因此不能用 Codeforces 官方 API 替代写操作。

证据：

- [VJudge FAQ](https://vjudge.net/article/2771)
- [VJudge 当前提交 bundle](https://vjudge.net/static/bundle/1ab4f2a25ddef0442d12.js)
- [VJudge 当前状态页 bundle](https://vjudge.net/static/bundle/1a90f1633cd8072e9a18.js)
- [Codeforces 官方 API methods](https://codeforces.com/apiHelp/methods)

### 1.4 登录、CSRF、验证码和反自动化

已验证：

- VJudge 使用 `JSESSIONID`/会话 Cookie；创建 contest 未登录会被拒绝。
- 当前提交表单把 `source`、`language`、`method` 和 `token` 发给内部提交端点。
- 若服务端响应 `challenge`，前端会动态加载 Cloudflare Turnstile，并把 Turnstile 回调 token 放入下一次提交。
- VJudge 本身由 Cloudflare 保护；部分只读请求也可能得到“启用 JavaScript 和 cookies”的机器人验证页面。
- VJudge `robots.txt` 只明确禁止 `/user/`，没有给出自动提交授权。
- Codeforces 当前 `robots.txt` 对 `curl`、`Wget`、`python-requests` 等只允许 `/api/`，并对通用机器人禁止 `/contest`、`/problemset/submit`、`/submissions` 等路径。

当前 VJudge bundle 中没有看到独立命名的 CSRF 字段；其中 `token` 可确认是 Turnstile token。**这不等于服务端没有其他 CSRF/Origin/SameSite 防护**，也不应据此绕开浏览器安全模型。

没有找到 VJudge 对自动提交的明确服务条款许可，也没有找到“全面禁止自动化”的正式条款。证据不足时应按未获授权处理：联系 VJudge 维护者确认机器人提交、频率、专用账号和验证码处理政策。验证码出现时必须人工接管；自动破解或规避验证码不应进入设计。

Codeforces 官方 Terms 禁止损害网站或影响其他用户访问的使用方式；结合 robots 规则，直接自动化 Codeforces 网页提交风险更高。VJudge 自身会代表用户访问 Codeforces，但这不自动授予第三方对 VJudge 内部接口进行大规模自动化的权利。

证据：

- [VJudge Turnstile 实现 bundle](https://vjudge.net/static/bundle/c3f3e58a8b614edeeb46.js)
- [VJudge 提交表单 bundle](https://vjudge.net/static/bundle/1ab4f2a25ddef0442d12.js)
- [VJudge robots.txt](https://vjudge.net/robots.txt)
- [Codeforces robots.txt](https://codeforces.com/robots.txt)
- [Codeforces Terms and Conditions](https://codeforces.com/terms)

### 1.5 远程代理评测和 Codeforces 凭据

VJudge 官方 FAQ 对 “Submit Failed / Login Failed” 的解释是：代码没有成功提交到 **remote OJ**，原因可能是远端 OJ 宕机、网络异常、远端更新或 VJudge 适配器故障；FAQ 建议 rejudge，而不是重复提交。这直接证明结果依赖远端 OJ。

历史官方源码进一步显示其机制：

- `CodeForcesLoginer` 使用 remote account、Codeforces 登录页和 `csrf_token` 登录。
- `CodeForcesSubmitter` 登录后向 Codeforces `/problemset/submit` 提交代码。
- `CodeForcesQuerier` 读取 Codeforces submission 页面获得状态。
- 官方部署 wiki 要求部署者“Register accounts in remote OJs”，并配置 `remote_accounts.json`。

这些源码停留在 2016 年前后的历史版本，不能证明当前具体 URL/字段仍相同，但与当前 FAQ 的远程代理语义一致。

凭据结论：

- **VJudge 最终必须有 Codeforces 远端账号可用。**
- 使用 VJudge 默认代理方式时，最终用户通常不必把个人 Codeforces 密码交给 agent；VJudge 使用其管理的账号池。
- 当前提交 UI 还支持绑定“自己的远端账号”的模式；若选择该模式，则需要用户主动在 VJudge 中配置远端凭据。agent-olympiad 不应收集或明文保存这些凭据。

证据：

- [VJudge FAQ](https://vjudge.net/article/2771)
- [历史官方部署 wiki](https://github.com/chaoshxxu/virtual-judge/wiki/How-to-deploy-your-own-Virtual-Judge)
- [历史 CodeForcesLoginer](https://github.com/chaoshxxu/virtual-judge/blob/9dc0be82ed7e05dc17b7f042a935bf3db8435ce4/src/remote-provider/java/judge/remote/provider/codeforces/CodeForcesLoginer.java)
- [历史 CodeForcesSubmitter](https://github.com/chaoshxxu/virtual-judge/blob/9dc0be82ed7e05dc17b7f042a935bf3db8435ce4/src/remote-provider/java/judge/remote/provider/codeforces/CodeForcesSubmitter.java)
- [历史 CodeForcesQuerier](https://github.com/chaoshxxu/virtual-judge/blob/9dc0be82ed7e05dc17b7f042a935bf3db8435ce4/src/remote-provider/java/judge/remote/provider/codeforces/CodeForcesQuerier.java)

## 2. 推断与未决问题

以下不是已获官方承诺的事实：

- 内部 Web 端点短期内大概率可被带 Cookie 的客户端调用，但其稳定性、速率限制和可接受用途未知。
- 当前前端的 `method = 0/1/2` 看起来区分平台代理账号、自己的账号等提交方式；具体语义可能按 OJ 和账户状态动态变化，不应硬编码。
- contest owner/manager 的精确编辑、查看源码、重判权限需要用受控测试账户验证。
- Turnstile 是按风险触发还是每次触发、token 有效期和复用规则均未形成 VJudge 公开契约。
- VJudge 是否愿意为研究项目提供专用账号、白名单或正式 API，需要直接向维护者确认。
- Codeforces 是否明确认可 VJudge 当前代理方式、允许的提交频率和账号池使用方式，本次未找到公开的一手授权文本。

## 3. 最小可行验证计划

在获得 VJudge 维护者许可后，建议按以下顺序验证。每一步都使用专用测试账户、公开旧题和低频请求。

1. **人工基线**
   - 人工注册并验证 VJudge 账户。
   - 人工创建私有经典 contest。
   - 添加一题公开旧题，例如 `CodeForces-4A`。
   - 人工提交一个已知正确和一个已知错误的短程序。
   - 记录 UI 中的 `runId`、状态转换、最终 verdict、远端 run id 是否可见。

2. **只读适配器**
   - 只实现登录状态检查和已有 contest/提交结果读取。
   - 轮询间隔从 2–5 秒起，指数退避并设置总超时。
   - 验证 `processing -> final`、Submit Failed、Login Failed、重判和网络中断。

3. **单次提交**
   - contest 仍由人工创建。
   - 自动化只执行一次 contest 内提交。
   - 若返回 challenge、401/403/429 或页面结构变化，立即停止并要求人工处理。
   - 用幂等键避免网络重试造成重复提交；不要把“请求超时”直接视为“未提交”。

4. **建赛自动化**
   - 最后才测试 `/contest/edit`。
   - 创建后读回并核对题目顺序、开始时间、时区、罚时、可见性和 access code。
   - 默认创建私有 contest，禁止自动公开。

5. **失效演练**
   - 会话过期、Turnstile、远端 Login Failed、VJudge/Codeforces 维护、429、返回 HTML 而非 JSON、bundle hash/字段变化。
   - 所有失败必须进入可恢复队列，不能无限重试。

本次调研按用户要求未执行上述任何写操作。

## 4. 适合 agent-olympiad 的稳定架构

### 4.1 核心边界

建议定义与平台无关的 `SubmissionProvider`，至少包含：

- `prepare_contest(spec) -> external_contest_ref`
- `submit(contest_ref, problem_ref, language, source, idempotency_key) -> external_run_ref`
- `get_result(external_run_ref) -> normalized_verdict`
- `cancel_or_stop_polling(external_run_ref)`

provider 返回原始响应摘要和规范化 verdict，但不让 agent 直接接触 Cookie、密码或 Turnstile token。

### 4.2 分层

1. **可信本地层**
   - 编译、样例测试、静态检查、资源限制和源码归档。
   - 即使外部平台不可用，实验仍可复现并给出本地结果。

2. **提交队列**
   - 单账户串行或严格限速。
   - 持久化状态机：`queued -> submitted -> polling -> final/needs_human/failed`。
   - 使用源码哈希、contest/problem/language 组成幂等键。

3. **VJudge Web 适配器（实验性）**
   - 独立进程和最小权限专用账户。
   - 加密 Cookie/凭据，日志自动脱敏。
   - 解析失败时 fail closed，不猜字段、不自动重新提交。
   - Turnstile、登录失效、权限错误进入 `needs_human`。

4. **结果规范化**
   - 保存 VJudge `runId`、远端 run id（若授权可见）、原始状态、最终 verdict、时间/内存、轮询时间线。
   - 区分 `judge verdict` 与 `transport failure`；`Submit Failed` 不是 Wrong Answer。

5. **审计与实验隔离**
   - 记录谁触发提交、所用源码哈希、外部请求次数和人工接管。
   - 不让一个 agent 读取另一个 agent 的私有源码或凭据。
   - 外部 verdict 作为单独证据源，不覆盖本地可复现记录。

### 4.3 推荐落地顺序

- **推荐近期方案：** 人工创建 contest；agent 生成代码并完成本地验证；人工确认后提交；系统只读采集结果。
- **经许可后的方案：** 在上述队列和审计层后加入 VJudge Web 适配器，先提交、后建赛。
- **不推荐：** agent 直接保存 VJudge/Codeforces 密码；绕过 Turnstile；根据当前 bundle 硬编码后无限重试；把 VJudge 当作有 SLA 的正式 API。
- **长期稳定方案：** 对有授权测试数据的题目使用自托管 judge；VJudge 仅用于与公开远端 OJ 结果做抽样交叉验证。

## 5. 最终判断

产品功能层面，目标流程可行；工程和政策层面，**“无人值守、稳定、官方支持的 VJudge API 集成”目前不可证实**。最安全的 MVP 是半自动流程。若必须全自动，应先取得 VJudge 对专用账号和机器人提交的明确许可，再把当前内部接口封装为可熔断、可人工接管、低频率的实验性 provider，而不是核心评测基础设施。

## 6. 已实现的 turn 内闭环（2026-08-27 / 更新 2026-08-28）

当 `VJUDGE_GATEWAY_URL` 已配置时，编程 agent 的 `submit_code` / 编程 `submit_final` 现在执行：

1. 先跑本地 sample judge；未通过则直接把本地 verdict 返回下一 turn。
2. 本地 AC 后，自动调用 localhost gateway 提交源码到 VJudge。
3. **默认 problem mode**（不建 contest）：用 benchmark 里的 `evaluation.vjudge_oj` + `vjudge_prob_num`（如 `CodeForces-231A`）走 `POST /problem/submit/{OJ}-{probNum}`。
4. 若显式设 `VJUDGE_SUBMIT_MODE=contest` 且有 `vjudge_contest_id`，则仍走旧的 contest 提交。
5. 同步轮询 VJudge：远程 `AC` 结束；`WA/...` 回下一 turn；`Challenge` → `needs_human`。
6. Final grading 复用已有远程结果，不重复提交相同候选。

本地题号同步（只处理已有 packages，不爬全站）：

```powershell
e:\agent_olympiad\.venv\Scripts\python.exe collectors\sync_local_codeforces_vjudge.py --ids-only
```

当前本地 packages：`4A`、`231A` → `CodeForces-4A` / `CodeForces-231A`。
