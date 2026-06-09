---
tags:
  - roadmap
  - agent-engineering
status: active
updated: 2026-06-09
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
- [ ] 流式输出
- [ ] token 使用量和成本统计

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
- [ ] Trace 持久化
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

- [ ] Session ID
- [ ] 多轮消息历史
- [ ] 会话持久化
- [ ] 短期工作记忆
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

- [ ] 论文检索工具
- [ ] 答辩问题生成工具
- [ ] 回答评分工具
- [ ] 追问工具
- [ ] 训练记录查询工具
- [ ] Skill 定义和动态加载
- [ ] 工具权限与审计
- [ ] Workspace 隔离

目标：从固定答辩流程升级为模型自主编排能力。

## 阶段 6：Agent 评估

- [ ] Tool selection accuracy
- [ ] Tool argument accuracy
- [ ] Task completion rate
- [ ] Groundedness
- [ ] Faithfulness
- [ ] LLM-as-Judge
- [ ] 人工盲评
- [ ] Trace 回放
- [ ] 回归数据集
- [ ] 反馈闭环

## 阶段 7：异步与长任务

- [ ] `async` / `await`
- [ ] 异步 LLM 和工具调用
- [ ] 并发限制
- [ ] 超时和取消
- [ ] 后台任务
- [ ] checkpoint
- [ ] 幂等性
- [ ] 任务恢复

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

原则：先理解手写 Harness，再使用框架。

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

- [ ] FastAPI
- [ ] Pydantic 请求模型
- [ ] SSE 或 WebSocket
- [ ] 前端答辩界面
- [ ] 文件上传
- [ ] 会话列表
- [ ] Trace 查看器
- [ ] 用户认证

## 阶段 11：可观测与交付

- [ ] 结构化日志
- [ ] Langfuse
- [ ] Prometheus 指标
- [ ] 错误告警
- [ ] Docker
- [ ] CI
- [ ] PostgreSQL
- [ ] Qdrant / Milvus
- [ ] K8s 基础部署
- [ ] 私有化配置和密钥管理

## 最终简历能力目标

- 能独立解释并实现 Agent Harness，而不只会调用框架
- 能完成 RAG 数据链路、评估和优化
- 能治理工具权限、异常、超时、审计和成本
- 能设计 Session、Memory、Workspace 和 Skill 边界
- 能实现 Agent Trace、LLM-as-Judge 和反馈闭环
- 能将 Agent 通过 API、数据库、容器和监控交付
- 能使用 LangGraph、MCP 和 Sub-Agent，但不被框架绑架

