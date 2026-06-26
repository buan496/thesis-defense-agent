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
```

## 后续边界

后续可以继续扩展 LangGraph 旁路流，但必须遵守：

```text
不覆盖现有 task_* 实现。
不删除手写 Agent Harness。
每扩展一个 LangGraph 节点，都要能映射回 Task Workflow Contract。
```
