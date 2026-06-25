# Memory 阶段复盘

## 阶段定位

本阶段目标不是把所有上下文永久保存，而是建立本地学习版长期记忆机制，让 Agent 能在后续训练中利用稳定信息、薄弱点和训练总结。

Memory 的核心边界是：

```text
长期记忆不是日志。
长期记忆只保存后续训练仍有价值的信息。
```

因此，本项目没有采用“自动全量写入”的方式，而是保留显式写入、显式导出和可裁剪策略。

## 已完成能力

### 1. Profile Memory

位置：

```text
app/long_term_memory.py
```

完成内容：

- 保存用户稳定信息
- 支持通过 CLI 写入 profile 字段
- 支持在 memory context 中展示 profile

典型用途：

```text
论文方向
目标岗位
长期技术路线
```

### 2. Weakness Memory

完成内容：

- 保存训练中暴露出的薄弱点
- 支持绑定来源 task_id
- 支持根据 query 检索相关薄弱点
- 支持裁剪和去重

典型用途：

```text
回答过于笼统
缺少实验指标
缺少工程案例
没有说明模块边界
```

### 3. Training Summary Memory

完成内容：

- 保存每轮训练总结
- 支持绑定 task_id 和 topic
- 支持根据 query 选择相关总结
- 支持保留最近 N 条

### 4. Memory Retrieval

完成内容：

- `build_long_term_memory_context()`
- 根据当前 query 选择相关 weaknesses 和 summaries
- 无匹配时回退到最近记忆

这一点很重要：

```text
Memory 不是全部塞进 prompt。
Memory 需要基于当前任务做选择。
```

### 5. Memory Pruning

完成内容：

- 控制最大 weakness 数量
- 控制最大 summary 数量
- 支持按文本去重
- 保留较新的重复记忆

### 6. Chat Memory Injection

位置：

```text
app/session_service.py
```

完成内容：

- `run_agent_session()` 加载长期记忆
- 根据当前 user_message 构建 memory context
- 注入 Agent messages
- 支持关闭 memory
- 支持控制注入的 weakness / summary 数量

相关 CLI 参数：

```powershell
--disable-memory
--max-memory-weaknesses
--max-memory-summaries
```

### 7. Task Summary Memory Export

位置：

```text
app/task_memory_exporter.py
```

完成内容：

- 从已完成 `DefenseTask` 中读取 `summarize_training` 步骤
- 导出 summary 到 `training_summaries`
- 导出 weaknesses 到 `weaknesses`
- 新增 `export-task-memory` CLI

命令：

```powershell
uv run python -m app.cli export-task-memory `
  --task-id <TASK_ID> `
  --directory data/defense_tasks `
  --memory-path data/long_term_memory.json
```

设计原则：

```text
任务完成后不自动写入长期记忆。
由用户显式执行导出，降低低质量内容污染 memory 的风险。
```

## 当前 Memory 链路

```text
memory-set-profile
-> memory-add-weakness
-> memory-add-summary
-> memory-prune
-> export-task-memory
-> build_long_term_memory_context
-> chat / Agent memory injection
```

## 当前边界

当前尚未做：

- 自动判断哪些内容值得记住
- 基于 LLM 的记忆摘要
- 记忆命中审计
- 记忆使用效果评估
- 记忆版本管理
- 多用户隔离
- 数据库持久化
- 向量化长期记忆

这些不应在当前本地学习版里一次性推进。

## 已学到的核心概念

### 长期记忆不是聊天历史

聊天历史是短期上下文，长期记忆是跨任务保留的稳定知识。

### 记忆需要筛选

如果把所有输出都写入 memory，长期上下文会迅速变脏。

### 记忆需要可控写入

当前项目选择显式命令写入，而不是自动写入。

### 记忆需要检索

长期记忆不能全量注入 prompt。需要根据当前 query 选择相关内容。

### 记忆需要遗忘

无限增长的 memory 会带来噪声、成本和错误上下文。

## 未完成能力

后续仍可继续推进：

- 重复记忆检测报告
- 记忆压缩摘要
- 记忆命中审计
- 记忆使用前后效果对比
- 低质量记忆清理
- 从 feedback record 中提取 memory candidate
- Memory candidate review
- Memory 版本 diff

## 下一阶段建议

建议下一阶段进入：

```text
Memory 质量治理
```

建议顺序：

```text
1. memory-audit：统计 profile / weaknesses / summaries 数量和重复项
2. memory-deduplicate-report：只报告重复，不直接删除
3. memory-prune --dry-run：预览裁剪结果
4. memory-hit-audit：给定 query，显示命中的 memory 项
5. memory-context-report：输出最终注入 prompt 的 memory context
```

暂不建议直接做：

- 数据库版 Memory
- 向量化 Memory
- 多用户 Memory
- 自动 LLM 判断是否记忆

原因：

```text
当前 Memory 还处于本地可控阶段。
先把质量审计和命中审计补齐，再考虑更复杂的存储和检索方式。
```
