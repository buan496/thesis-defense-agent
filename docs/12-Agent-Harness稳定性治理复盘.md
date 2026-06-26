# Agent Harness 稳定性治理复盘

## 阶段定位

本阶段目标不是继续增加新工具，而是复盘当前手写 Agent Harness 已经具备的工具执行治理能力。

Agent 能调用工具只是第一步。真正可维护的 Agent Harness 还必须控制工具的：

```text
权限
耗时
失败
重试
输出长度
审计记录
```

否则 Agent 很容易出现以下问题：

- 工具输出过长，把上下文撑爆。
- 工具卡住，导致整轮 Agent 运行无法返回。
- 临时网络错误直接中断任务。
- 工具异常格式不统一，后续评估和 trace 分析困难。
- 工具权限边界不清楚，后续接入外部工具时风险扩大。

## 当前实现位置

核心文件：

```text
app/tool_registry.py
app/tool_executor.py
app/agent.py
app/agent_models.py
```

相关配置：

```text
TOOL_RESULT_MAX_CHARACTERS
TOOL_MAX_RETRIES
TOOL_TIMEOUT_SECONDS
```

## 已完成能力

### 1. 工具注册表

`app/tool_registry.py` 通过 `REGISTERED_TOOLS` 管理所有可用工具。

每个工具不仅有 OpenAI tool schema，还绑定了工程侧元信息：

```text
name
description
permission
owner
enabled
timeout_seconds
retry_count
result_max_characters
input_schema
output_schema
```

这一步的价值是把“模型能看到的工具 schema”和“工程运行时需要治理的工具 metadata”分开管理。

### 2. 工具白名单与权限治理

`app/tool_executor.py` 中通过 `ALLOWED_TOOL_PERMISSIONS` 限制允许执行的工具权限类型：

```text
read
llm_generate
llm_evaluate
```

执行工具前会校验：

- 工具是否启用
- 权限是否允许
- retry 配置是否合法
- result limit 配置是否合法
- timeout 配置是否合法

这一步保证后续新增工具时，不能只写函数，还必须明确它的权限和运行边界。

### 3. 工具结果长度限制

`limit_tool_result_text()` 会限制工具返回内容长度。

如果工具结果超过 `result_max_characters`，返回结构化截断结果：

```json
{
  "truncated": true,
  "original_characters": 12000,
  "max_characters": 6000,
  "content": "..."
}
```

这解决的是 Agent Harness 的上下文预算问题。

工具结果如果无限制进入下一轮 LLM，就会带来两个风险：

- prompt token 成本不可控
- 关键信息被长文本稀释

### 4. 工具重试

`execute_tool_function_with_retry()` 支持有限次数重试。

当前逻辑：

```text
max_retries = 0  -> 执行 1 次
max_retries = 2  -> 最多执行 3 次
```

这适合处理临时失败，例如：

- 网络抖动
- embedding API 短暂不可用
- 文件读写短时冲突

需要注意：重试只适合幂等工具。未来如果接入写操作工具，必须区分工具是否允许重试。

### 5. 工具超时

`execute_tool_function_with_timeout()` 使用 `ThreadPoolExecutor` 包装工具执行。

当工具超过 `timeout_seconds` 未返回，会抛出 timeout 错误：

```text
tool execution timed out after N seconds
```

这一步避免 Agent 卡死在单个工具调用上。

需要注意：当前是本地学习版 timeout。线程取消不等于强制杀死底层阻塞 IO；未来服务化阶段如果要做强隔离，应考虑进程级隔离、异步 timeout 或任务队列。

### 6. 标准化错误

`execute_tool_call_safely()` 会把工具异常转换成统一 JSON：

```json
{
  "success": false,
  "error_type": "ValueError",
  "message": "...",
  "tool_name": "search_thesis"
}
```

这比直接把 Python traceback 交给模型更适合工程化：

- LLM 更容易理解错误
- trace 更容易解析
- benchmark 更容易比较失败类型
- CLI 输出更稳定

### 7. Trace 审计

`app/agent.py` 在每次工具调用后记录：

```text
step
tool_name
arguments
result
success
duration_ms
```

这让 Agent 不只是“返回答案”，还可以回答：

- 调用了哪个工具？
- 工具参数是什么？
- 工具成功还是失败？
- 工具耗时多少？
- 最终答案是否建立在工具结果上？

## 当前工具治理链路

```text
LLM tool call
-> parse arguments
-> resolve registered tool
-> validate metadata
-> execute with timeout
-> retry on failure
-> serialize result
-> limit result length
-> record trace
-> feed tool result back to LLM
```

## 当前边界

当前版本仍然是本地学习版，有几个边界需要明确：

- 没有进程级工具隔离。
- 没有异步并发工具调度。
- 没有不同用户 / workspace 的权限隔离。
- 没有工具调用审批流。
- 没有外部 MCP 工具市场接入。

这些不是当前阶段缺陷，而是后续服务化、MCP 和私有化部署阶段的学习内容。

## 学到的关键点

```text
Agent Harness 的核心不是“能调用工具”，而是“能治理工具”。
工具治理必须前置到注册阶段，而不是等出错后再补。
工具输出、失败、耗时和权限都必须可观测、可限制、可审计。
```

## 简历表达

可以写成：

```text
实现本地 Agent Harness 工具治理机制，支持工具注册表、权限白名单、工具超时、有限重试、结果长度限制、标准化错误返回和工具调用 trace 审计，提升多工具 Agent 在长任务中的稳定性和可观测性。
```

## 后续学习

下一阶段可以继续推进：

```text
1. Sub-Agent 权限边界和 dry-run 执行策略
2. Tool audit report
3. Trace replay 与工具选择变化检测
4. 服务化阶段的异步工具调用和任务取消
```
