# Task 工作流契约

本文件记录当前手写 Task State 工作流的稳定契约。后续 LangGraph 旁路迁移必须复刻这份契约，不能直接覆盖现有实现。

## 节点顺序

```text
retrieve_context
-> generate_question
-> wait_for_answer
-> evaluate_answer
-> rewrite_answer
-> generate_follow_up
-> wait_for_follow_up_answer
-> evaluate_follow_up_answer
-> summarize_training
```

## 节点类型

自动执行节点：

```text
retrieve_context
generate_question
evaluate_answer
rewrite_answer
generate_follow_up
evaluate_follow_up_answer
summarize_training
```

人工输入节点：

```text
wait_for_answer
wait_for_follow_up_answer
```

## 输入输出契约

| 节点 | 类型 | 必需输入 | 主要输出 |
| --- | --- | --- | --- |
| retrieve_context | auto | `query` 或 `topic` | `query`, `context`, `sources` |
| generate_question | auto | `context` | `question`, `questions`, `topic` |
| wait_for_answer | human | `question` | `question`, `answer` |
| evaluate_answer | auto | `question`, `answer` | `evaluation` |
| rewrite_answer | auto | `question`, `answer` | `rewritten_answer` |
| generate_follow_up | auto | `question`, `answer` | `follow_up_question` |
| wait_for_follow_up_answer | human | `follow_up_question` | `follow_up_answer` |
| evaluate_follow_up_answer | auto | `follow_up_question`, `follow_up_answer` | `follow_up_evaluation` |
| summarize_training | auto | 完整训练字段 | `summary`, `weaknesses`, `next_suggestions` |

## Resume 契约

```text
auto 节点 pending/running
-> execute_current_step

human 节点 pending/running
-> wait_for_human_input

completed 节点且存在下一步
-> create_next_step

最后一个节点 completed
-> completed
```

## 后续 LangGraph 迁移边界

LangGraph 只做旁路实现，新增独立目录，例如：

```text
app/langgraph_workflow/
```

禁止覆盖或删除：

```text
app/task_executor.py
app/task_service.py
app/task_resume.py
app/task_runner.py
app/agent.py
```

迁移目标不是替换旧流程，而是验证：

```text
同样的输入
同样的节点顺序
同样的 resume 行为
可与手写 Task State 实现对照学习
```
