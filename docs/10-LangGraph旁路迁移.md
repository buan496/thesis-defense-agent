# LangGraph 旁路迁移

本阶段的目标不是替换现有 Task State 实现，而是用独立目录学习 LangGraph 的状态图、interrupt、checkpoint 和条件路由。

现有手写实现仍然是主线：

```text
app/task_executor.py
app/task_service.py
app/task_resume.py
app/task_runner.py
```

LangGraph 旁路实现放在：

```text
app/langgraph_workflow/
```

## 已完成的旁路 Demo

```text
demo_task.py
-> retrieve_context
-> generate_question
-> wait_for_answer

interrupt_demo.py
-> retrieve_context
-> generate_question
-> answer_interrupt

checkpointer_demo.py
-> 使用 InMemorySaver 检查 interrupt 前后的 checkpoint

persistent_checkpoint_demo.py
-> 将 checkpoint 摘要保存为 JSON 快照

conditional_demo.py
-> 根据是否已有 answer 选择 finalize 或 answer_interrupt

evaluate_rewrite_demo.py
-> retrieve_context
-> generate_question
-> answer_interrupt
-> evaluate_answer
-> rewrite_answer

follow_up_demo.py
-> retrieve_context
-> generate_question
-> answer_interrupt
-> evaluate_answer
-> rewrite_answer
-> generate_follow_up
-> follow_up_interrupt
-> evaluate_follow_up_answer

summary_demo.py
-> retrieve_context
-> generate_question
-> answer_interrupt
-> evaluate_answer
-> rewrite_answer
-> generate_follow_up
-> follow_up_interrupt
-> evaluate_follow_up_answer
-> summarize_training
```

## 与 Task Workflow Contract 的关系

当前 LangGraph demo 只覆盖完整任务流的前三步：

```text
retrieve_context
generate_question
wait_for_answer
```

其中 `answer_interrupt` 是 LangGraph 的 interrupt 节点，对应主流程里的人工输入节点：

```text
answer_interrupt -> wait_for_answer
```

已新增契约对齐模块：

```text
app/langgraph_workflow/contract_alignment.py
```

它用于验证：

```text
LangGraph demo 节点顺序
-> 是否仍然匹配 Task Workflow Contract 的前缀

LangGraph interrupt 节点
-> 是否映射到 human input contract step
```

## CLI 命令

```powershell
uv run python -m app.cli graph-demo-task `
  --topic "系统架构"

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
```

## evaluate / rewrite 旁路节点

本阶段新增两个 LangGraph 旁路节点：

```text
evaluate_answer
rewrite_answer
```

它们复用现有业务函数：

```text
app.evaluation.evaluate_answer
app.answer_rewrite.rewrite_answer
```

测试中使用 fake evaluator / fake rewriter，避免调用真实 LLM。

这一阶段学到的重点：

```text
LangGraph 节点不应该重新发明业务逻辑。
正确做法是复用已有函数，把节点作为状态推进和编排层。
```

## follow-up 旁路节点

本阶段新增完整追问链路：

```text
generate_follow_up
follow_up_interrupt
evaluate_follow_up_answer
```

它展示了 LangGraph 中同一条工作流里的两次人工输入：

```text
answer_interrupt
-> 学生回答原问题

follow_up_interrupt
-> 学生回答追问
```

这一阶段学到的重点：

```text
多轮答辩训练不是简单的一次 interrupt。
真实任务型 Agent 需要在同一条状态图中多次暂停、恢复，并继续继承前文状态。
```

## summarize_training 旁路节点

本阶段新增完整训练总结节点：

```text
summarize_training
```

完整 LangGraph 旁路链路已经覆盖 Task State 主链路：

```text
retrieve_context
-> generate_question
-> wait_for_answer / answer_interrupt
-> evaluate_answer
-> rewrite_answer
-> generate_follow_up
-> wait_for_follow_up_answer / follow_up_interrupt
-> evaluate_follow_up_answer
-> summarize_training
```

这一阶段学到的重点：

```text
工作流的最后一步不只是结束，而是把完整状态汇总成可保存、可复盘、可进入 Memory 的训练产物。
LangGraph 的价值在于状态继承和节点编排，业务逻辑仍然复用现有函数。
```

## 后续边界

后续可以继续扩展 LangGraph 旁路流，但必须遵守：

```text
不覆盖现有 task_* 实现。
不删除手写 Agent Harness。
每扩展一个 LangGraph 节点，都要能映射回 Task Workflow Contract。
```
