---
tags:
  - roadmap
  - agent-engineering
status: active
updated: 2026-06-22
---

# Agent 完整学习路线

> [!note]
> 路线按依赖顺序排列。未完成前置阶段时，不为了“技术栈多”而提前堆框架。

## 阶段 0：Python 工程基础

- [x] uv、虚拟环境和依赖锁定
- [x] Python 包、模块和 `python -m`
- [x] 类型标注、异常、dataclass
- [x] list、dict、JSON 和文件读写
- [x] pytest、fixture、`tmp_path`
- [x] Git 暂存、提交和 `.gitignore`
- [ ] 格式化、静态检查和类型检查

基础知识：

- 进程、虚拟环境和解释器
- 文件系统路径
- 模块搜索路径
- 测试金字塔

## 阶段 1：LLM 应用基础

- [x] API 客户端
- [x] system/user message
- [x] temperature 与 max tokens
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
- [ ] 混合检索 BM25 + Vector
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
- [x] LLM 自动选工具
- [x] Agent Loop
- [x] 最大步数
- [x] 异常恢复
- [x] 执行轨迹
- [x] 工具耗时
- [x] 离线 Harness 测试
- [x] Trace 持久化
- [x] Trace 分析
- [x] 工具调用成功 / 失败记录
- [ ] 工具超时
- [ ] 工具重试策略
- [ ] 工具结果长度限制
- [ ] 多工具选择
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
- [ ] 长期用户记忆
- [ ] 记忆写入策略
- [ ] 记忆检索与遗忘
- [ ] 上下文压缩和摘要

基础知识：

- 状态与生命周期
- 数据库事务
- 并发写入
- 隐私和数据保留

## 阶段 5：多工具和 Skill

- [x] 论文检索工具
- [x] 答辩问题生成工具
- [ ] 回答评分工具
- [ ] 追问工具
- [ ] 训练记录查询工具
- [ ] Skill 定义和动态加载
- [ ] 工具权限与审计
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
- [ ] 人工盲评
- [ ] Trace 回放
- [x] 回归数据集
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
- [ ] 将当前手写 Agent Loop 迁移到 LangGraph

原则：先理解手写 Harness，再使用框架。LangGraph 迁移必须采用旁路实现，新增独立目录和独立 CLI，不覆盖 `app/task_*`、`app/agent.py` 等现有手写实现，保留两套实现用于对照学习。

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

> 当前机器暂不推进服务器部署相关学习；FastAPI、Web 前端、数据库、Docker、K8s 等内容后续放到另一台服务器笔记本上继续。

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
- [ ] Langfuse
- [ ] Prometheus 指标
- [ ] 错误告警
- [ ] Docker
- [x] CI
- [x] GitHub Actions 离线质量门禁
- [x] CI 失败诊断和修复
- [ ] PostgreSQL
- [ ] Qdrant / Milvus
- [ ] K8s 基础部署
- [ ] 私有化配置和密钥管理

## 当前阶段：Task State / 可恢复任务型 Agent

当前项目已经完成“本机学习版 Agent Harness 完整闭环”：RAG、Tool Calling、Agent Loop、Session、Trace、评估、CI、Task State、可恢复任务流和 Markdown 报告导出已经连成完整链路。下一阶段不再继续堆新框架，而是进入工具稳定性治理，并为后续 Memory、Trace 回放和 LangGraph 旁路迁移打基础。

已完成能力：

- [x] 设计 `DefenseTask` 数据结构
- [x] 设计 `TaskStep` 数据结构
- [x] 定义提问、回答、评价、改写、追问、总结的状态流转
- [x] 实现任务 JSON 保存和加载
- [x] 实现任务推进 service
- [x] 接入 Task CLI
- [x] 为任务模型、存储、状态推进、服务层和 CLI 补 pytest
- [x] 将每一步的输入、输出、证据、工具调用、token 和 cost 写入任务记录
- [x] 支持任务中断后 `resume-task`
- [x] 支持任务级 `analyze-task` trace 汇总
- [x] 将任务步骤接入真实 RAG 和 LLM
- [x] 支持 `retrieve_context`、`generate_question`、`wait_for_answer`、`evaluate_answer`、`rewrite_answer`、`generate_follow_up`、`wait_for_follow_up_answer`、`evaluate_follow_up_answer`、`summarize_training` 完整流程
- [x] 支持 `submit-task-answer` 和 `submit-follow-up-answer`
- [x] 支持 `export-task-markdown` 导出任务训练报告

后续边界：

- LangGraph 迁移只做旁路实现，不覆盖当前手写 Task State / Agent Harness 源码。
- FastAPI、Docker、K8s、数据库、服务器部署和私有化运行环境放到另一台服务器笔记本学习。

下一步学习重点：工具结果长度限制、工具重试、工具超时和工具错误标准化。这一阶段对应企业级 Agent 中的 `Task / Workspace / Session / Trace` 边界，是从“能回答问题的 Agent”走向“能执行稳定流程的 Agent”的关键一步。

## 最终简历能力目标

- 能独立解释并实现 Agent Harness，而不只会调用框架
- 能完成 RAG 数据链路、评估和优化
- 能治理工具权限、异常、超时、审计和成本
- 能设计 Session、Memory、Workspace 和 Skill 边界
- 能实现 Agent Trace、LLM-as-Judge 和反馈闭环
- 能将 Agent 通过 API、数据库、容器和监控交付
- 能使用 LangGraph、MCP 和 Sub-Agent，但不被框架绑架
