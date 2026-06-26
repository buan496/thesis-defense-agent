# LangGraph 阶段复盘

## 阶段定位

本阶段目标不是用 LangGraph 替换现有手写 Agent Harness，而是在旁路目录中复刻、观察和验证同一条任务工作流。

保留主线实现：

```text
app/task_executor.py
app/task_service.py
app/task_resume.py
app/task_runner.py
app/agent.py
```

旁路学习目录：

```text
app/langgraph_workflow/
```

## 已完成能力

### 1. 基础 StateGraph

文件：

```text
app/langgraph_workflow/demo_task.py
```

覆盖节点：

```text
retrieve_context
-> generate_question
-> wait_for_answer
```

学到的点：

```text
LangGraph 的核心是状态字典在节点之间流动。
节点返回的 dict 会合并回 state。
```

### 2. 人工输入中断

文件：

```text
app/langgraph_workflow/interrupt_demo.py
```

覆盖能力：

```text
answer_interrupt
Command(resume=...)
```

学到的点：

```text
interrupt 不是普通 input，而是图执行过程中的暂停点。
恢复时必须依赖 thread_id 和 checkpointer。
```

### 3. Checkpointer 状态检查

文件：

```text
app/langgraph_workflow/checkpointer_demo.py
```

覆盖能力：

```text
InMemorySaver
graph.get_state(...)
checkpoint_id
snapshot.next
snapshot.values
snapshot.interrupts
```

学到的点：

```text
可恢复工作流必须能观察 checkpoint。
否则只能知道“卡住了”，不知道卡在哪一步、已有状态是什么。
```

### 4. Checkpoint 快照持久化

文件：

```text
app/langgraph_workflow/persistent_checkpoint_demo.py
```

覆盖能力：

```text
保存 checkpoint 摘要为 JSON
加载 checkpoint snapshot
汇总 interrupted / resumed 状态
```

学到的点：

```text
生产级长任务不能只依赖内存状态。
即使本阶段不接数据库，也要理解 checkpoint 快照的结构。
```

### 5. 条件路由

文件：

```text
app/langgraph_workflow/conditional_demo.py
```

覆盖能力：

```text
add_conditional_edges
route_by_answer
```

学到的点：

```text
LangGraph 的路由应该基于明确状态字段，而不是隐式判断。
```

### 6. evaluate / rewrite 旁路节点

文件：

```text
app/langgraph_workflow/evaluate_rewrite_demo.py
```

覆盖节点：

```text
evaluate_answer
rewrite_answer
```

学到的点：

```text
LangGraph 节点不应该重新发明业务逻辑。
正确做法是复用已有业务函数，把节点作为状态推进和编排层。
```

### 7. follow-up 多次中断

文件：

```text
app/langgraph_workflow/follow_up_demo.py
```

覆盖节点：

```text
generate_follow_up
follow_up_interrupt
evaluate_follow_up_answer
```

学到的点：

```text
多轮任务型 Agent 不是一次 interrupt 就结束。
同一条图里可以多次暂停、恢复，并继续继承前文状态。
```

### 8. summarize_training 完整收敛

文件：

```text
app/langgraph_workflow/summary_demo.py
```

覆盖节点：

```text
summarize_training
```

完整旁路链路：

```text
retrieve_context
-> generate_question
-> answer_interrupt
-> evaluate_answer
-> rewrite_answer
-> generate_follow_up
-> follow_up_interrupt
-> evaluate_follow_up_answer
-> summarize_training
```

学到的点：

```text
工作流的最后一步不是简单结束，而是把完整状态汇总成可复盘、可保存、可进入 Memory 的训练产物。
```

### 9. Parity Report

文件：

```text
app/langgraph_workflow/parity_report.py
```

映射关系：

```text
answer_interrupt -> wait_for_answer
follow_up_interrupt -> wait_for_follow_up_answer
```

学到的点：

```text
迁移不是“新实现能跑”就算完成。
必须证明新旁路实现与旧工作流契约等价。
```

## CLI 汇总

```powershell
uv run python -m app.cli graph-demo-task --topic "系统架构"

uv run python -m app.cli graph-interrupt-demo `
  --topic "系统架构" `
  --thread-id "thread-1"

uv run python -m app.cli graph-checkpointer-demo `
  --topic "系统架构" `
  --thread-id "thread-1"

uv run python -m app.cli graph-persistent-checkpoint-demo `
  --topic "系统架构" `
  --thread-id "thread-1" `
  --answer "系统采用模块化设计。" `
  --output data/langgraph_checkpoints/thread-1.json

uv run python -m app.cli graph-conditional-demo `
  --topic "系统架构" `
  --thread-id "thread-1" `
  --resume-answer "系统采用模块化设计。"

uv run python -m app.cli graph-evaluate-rewrite-demo `
  --topic "系统架构" `
  --thread-id "thread-1" `
  --answer "系统采用模块化设计。"

uv run python -m app.cli graph-follow-up-demo `
  --topic "系统架构" `
  --thread-id "thread-1" `
  --answer "系统按模块划分。" `
  --follow-up-answer "这样方便定位问题。"

uv run python -m app.cli graph-summary-demo `
  --topic "系统架构" `
  --thread-id "thread-1" `
  --answer "系统按模块划分。" `
  --follow-up-answer "这样方便定位问题。"

uv run python -m app.cli graph-task-parity
```

## 阶段结论

```text
LangGraph 是编排层，不是业务逻辑替代品。
迁移前必须有 Task Workflow Contract。
迁移后必须有 Parity Report。
旁路迁移优先于覆盖式重构。
```

## 当前边界

本阶段暂不做：

```text
替换 app/task_* 主线实现
接数据库 checkpoint
部署到服务器
Web UI
多用户隔离
```

这些内容后续在服务化和服务器学习阶段处理。
