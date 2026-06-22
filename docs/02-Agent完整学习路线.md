---
tags:
  - roadmap
  - agent-engineering
status: active
updated: 2026-06-22
---

# Agent 完整学习路线

> 路线按依赖顺序推进。没有完成前置阶段时，不为了“技术栈好看”提前堆框架。

## 阶段 0：Python 工程基础

- [x] uv、虚拟环境和依赖锁定
- [x] Python 包、模块和 `python -m`
- [x] 类型标注、异常、dataclass
- [x] list、dict、JSON 和文件读写
- [x] pytest、fixture、tmp_path
- [x] Git 暂存、提交、分支、`.gitignore`
- [ ] 格式化、静态检查和类型检查

基础知识：

- 进程、虚拟环境和解释器
- 文件系统路径
- 模块搜索路径
- 测试金字塔

## 阶段 1：LLM 应用基础

- [x] API 客户端
- [x] system / user message
- [x] temperature 和 max tokens
- [x] Prompt Engineering
- [x] 结构化 JSON 输出
- [x] 输出清洗和异常处理
- [x] token 使用量和成本统计
- [x] 调用后预算上限
- [x] 调用前预算预检
- [ ] 流式输出

基础知识：

- HTTP 请求与响应
- TLS、超时和重试
- 序列化
- 上下文窗口

## 阶段 2：RAG

- [x] 文档读取与清洗
- [x] chunk 切分
- [x] embedding
- [x] 向量相似度
- [x] 向量库持久化
- [x] metadata 和缓存失效
- [x] 检索与溯源
- [x] benchmark 和质量门禁
- [ ] 混合检索：BM25 + Vector
- [ ] reranker
- [ ] 查询改写与多查询检索
- [ ] Qdrant 或 Milvus

基础知识：

- 向量和余弦相似度
- 索引与数据库
- Recall、Precision、Top-K
- 缓存一致性

## 阶段 3：Tool Calling 与 Agent Harness

- [x] 工具函数
- [x] Tool Schema
- [x] 工具注册表
- [x] 工具白名单
- [x] LLM 自动选择工具
- [x] Agent Loop
- [x] 最大步数
- [x] 异常恢复
- [x] 执行轨迹
- [x] 工具耗时
- [x] 离线 Harness 测试
- [x] Trace 持久化
- [x] Trace 分析
- [x] 工具调用成功 / 失败记录
- [x] 工具超时
- [x] 工具重试策略
- [x] 工具结果长度限制
- [x] 工具错误标准化
- [ ] 多工具选择策略
- [ ] 并行工具调用

基础知识：

- 函数作为参数
- 依赖注入
- 状态机
- 白名单和最小权限
- 单调时钟
- 容错和熔断

## 阶段 4：Session 与 Memory

- [x] Session ID
- [x] 多轮消息历史
- [x] 会话持久化
- [x] 会话恢复
- [x] 短期工作记忆
- [x] 历史轮数限制
- [x] 历史字符预算
- [x] session metadata
- [x] token / cost 写入 session metadata
- [x] 长期用户记忆
- [x] 记忆写入策略
- [x] 记忆检索与遗忘
- [x] 上下文压缩和摘要

已完成能力：

- `long_term_memory.json`
- 用户画像：例如论文方向
- 薄弱点写入：由 CLI 或任务总结写入
- 训练总结写入：由 CLI 或 `summarize_training` 写入
- 相关记忆检索：按当前问题选择相关 weakness / summary
- 记忆注入开关：`--disable-memory`
- 记忆注入预算：`--max-memory-weaknesses`、`--max-memory-summaries`
- 记忆裁剪：`memory-prune`
- Session 摘要压缩：旧对话进入 `conversation_summary`
- Session 压缩开关：`--disable-session-compaction`
- Session 摘要长度限制：`--compact-summary-max-characters`

基础知识：

- 状态与生命周期
- 数据保留策略
- 原子写入
- 隐私和数据边界
- 上下文压缩

## 阶段 5：多工具和 Skill

- [x] 论文检索工具
- [x] 答辩问题生成工具
- [x] 回答评分工具
- [x] 追问工具
- [x] 训练记录查询工具
- [ ] Skill 定义和动态加载
- [ ] 工具权限与审计策略升级
- [ ] Workspace 隔离

目标：从固定答辩流程升级为模型自主编排能力。

## 阶段 6：Agent 评估

- [x] Tool selection accuracy
- [x] Tool argument accuracy
- [x] Task completion rate
- [x] Groundedness
- [x] Faithfulness
- [x] LLM-as-Judge
- [x] Faithfulness benchmark
- [x] 多轮稳定性评估
- [x] 评估报告生成
- [x] 评估报告回归对比
- [x] 指标下降检测
- [x] 预测翻转检测
- [x] 稳定性退化检测
- [x] 回归数据集
- [ ] 人工盲评
- [ ] Trace 回放
- [ ] 反馈闭环

## 阶段 7：异步与长任务

- [ ] `async` / `await`
- [ ] 异步 LLM 和工具调用
- [ ] 并发限制
- [ ] 超时和取消
- [ ] 后台任务
- [x] 向量库构建 checkpoint
- [x] 向量库构建断点恢复
- [ ] 幂等性
- [x] Agent 任务恢复

基础知识：

- 线程、进程、协程
- 事件循环
- I/O 密集与 CPU 密集
- 竞态条件

## 阶段 8：LangGraph

- [ ] State
- [ ] Node
- [ ] Edge
- [ ] Conditional Edge
- [ ] Checkpointer
- [ ] Human-in-the-loop
- [ ] 将当前手写 Agent Loop 旁路迁移到 LangGraph

原则：

- 先理解手写 Harness，再使用框架。
- LangGraph 迁移必须旁路实现。
- 新增独立目录，例如 `app/langgraph_workflow/`。
- 新增独立 CLI，例如 `python -m app.cli graph-demo-task`。
- 不覆盖 `app/task_*`、`app/agent.py` 等现有手写实现。
- 保留两套实现用于对照学习。

## 阶段 9：MCP 与 Sub-Agent

- [ ] MCP Client
- [ ] MCP Server
- [ ] 工具发现
- [ ] 工具授权
- [ ] Sub-Agent 任务委派
- [ ] Planner / Researcher / Evaluator
- [ ] 多 Agent 共享上下文边界
- [ ] 失败回收和预算控制

## 阶段 10：服务化与界面

> 当前机器暂不推进服务器部署相关学习。FastAPI、Web 前端、数据库、Docker、K8s 等内容后续放到另一台服务器笔记本上继续。

- [ ] FastAPI
- [ ] Pydantic 请求模型
- [ ] SSE 或 WebSocket
- [ ] 前端答辩界面
- [ ] 文件上传
- [ ] 会话列表
- [ ] Trace 查看器
- [ ] 用户认证

## 阶段 11：可观测与交付

- [x] 结构化日志
- [x] Agent trace JSONL
- [x] token / cost 审计
- [x] CI
- [x] GitHub Actions 离线质量门禁
- [x] CI 失败诊断和修复
- [ ] Langfuse
- [ ] Prometheus 指标
- [ ] 错误告警
- [ ] Docker
- [ ] PostgreSQL
- [ ] Qdrant / Milvus
- [ ] K8s 基础部署
- [ ] 私有化配置和密钥管理

## 当前阶段：本机学习版 Agent Harness 完整闭环

当前项目已经完成本机学习版 Agent Harness 的完整闭环：

```text
RAG
→ Tool Calling
→ Agent Loop
→ Session
→ Long-term Memory
→ Trace
→ Evaluation
→ CI
→ Task State
→ Resumable Workflow
→ Markdown Export
```

已经完成的 Task State 能力：

- [x] `DefenseTask / TaskStep`
- [x] 任务 JSON 保存和加载
- [x] 任务推进 service
- [x] Task CLI
- [x] `retrieve_context`
- [x] `generate_question`
- [x] `wait_for_answer`
- [x] `evaluate_answer`
- [x] `rewrite_answer`
- [x] `generate_follow_up`
- [x] `wait_for_follow_up_answer`
- [x] `evaluate_follow_up_answer`
- [x] `summarize_training`
- [x] `submit-task-answer`
- [x] `submit-follow-up-answer`
- [x] `resume-task`
- [x] `analyze-task`
- [x] `export-task-markdown`
- [x] 任务总结自动写入长期记忆

边界说明：

- LangGraph 后续只做旁路迁移，不覆盖当前手写 Task State / Agent Harness 源码。
- FastAPI、Docker、K8s、数据库、服务器部署和私有化运行环境放到另一台服务器笔记本学习。

## 下一步学习重点

下一阶段进入 **Trace 回放与反馈闭环**：

1. 离线回放某次 Agent / Task 运行
2. 对比新旧输出
3. 检测工具选择变化、评价分数变化和 faithfulness 变化
4. 将用户反馈写入 benchmark 候选集

之后再进入：

1. BM25 + Vector 混合检索
2. reranker
3. query rewrite
4. LangGraph 旁路迁移

## 最终简历能力目标

- 能独立解释并实现 Agent Harness，而不只是调用框架
- 能完成 RAG 数据链路、评估和优化
- 能治理工具权限、异常、超时、审计和成本
- 能设计 Session、Memory、Workspace 和 Skill 边界
- 能实现 Agent Trace、LLM-as-Judge 和反馈闭环
- 能将 Agent 通过 API、数据库、容器和监控交付
- 能使用 LangGraph、MCP 和 Sub-Agent，但不被框架绑架
