---
tags:
  - roadmap
  - agent-engineering
status: active
updated: 2026-07-01
---

# Agent 完整学习路线

> 路线按依赖顺序推进。没有完成前置阶段时，不为了“技术栈好看”提前堆框架。
>
> 本文后半部分保留了按时间追加的 `roadmap-update-*` 学习记录，其中的“下一步学习”表示当时阶段的下一步。当前有效状态以本文顶部阶段清单、`docs/01-当前进度.md` 和文末“当前边界 / 下一阶段建议顺序”为准。

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
- [x] 流式输出

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
- [x] 混合检索：BM25 + Vector
- [x] Hybrid 权重扫描
- [x] 规则版 reranker
- [x] 模型版 reranker
- [x] 规则版查询改写
- [x] LLM 查询改写
- [x] 多查询检索
- [x] 检索策略组合对比
- [x] 向量库 repository 抽象
- [x] Qdrant Compose service / config skeleton
- [x] QdrantVectorStoreRepository minimal implementation
- [x] JSON vs Qdrant benchmark comparison
- [x] Qdrant collection delete CLI with explicit confirmation
- [x] Qdrant snapshot backup/restore SOP
- [x] Vector DB 生产化治理报告
- [x] Qdrant / Milvus 对比边界说明
- [x] Qdrant backup retention policy CLI
- [x] Qdrant snapshot smoke plan / report template
- [x] Qdrant snapshot API runner
- [x] Qdrant snapshot drill plan
- [x] Qdrant snapshot drill one-time runner
- [x] Qdrant snapshot schedule config
- [x] Qdrant snapshot schedule install plan
- [x] Qdrant snapshot schedule verification plan
- [x] Qdrant snapshot schedule evidence template
- [x] Qdrant snapshot schedule install executor
- [x] Qdrant Windows Task Scheduler 本机定时 snapshot 实验
- [x] Qdrant Kubernetes CronJob manifest / client-side dry-run
- [x] Qdrant Kubernetes StatefulSet / Service / PVC / PDB runtime validation
- [x] Qdrant Kubernetes CronJob apply / manual Job smoke evidence
- [x] Qdrant Kubernetes CronJob natural schedule one-cycle evidence
- [x] Qdrant cron / Kubernetes CronJob / 多周期长期运行调度证据
- [x] MilvusVectorStoreRepository skeleton
- [x] Milvus Compose service / import CLI / optional benchmark entry
- [x] Milvus runtime benchmark report
- [x] Milvus backup / restore SOP
- [x] Milvus destructive operation guardrails

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
- [x] Trace 回放
- [x] 反馈闭环

## 阶段 7：异步与长任务

- [x] `async` / `await`
- [x] 异步 LLM / 工具调用边界
- [x] 原生异步 LLM SDK 调用
- [x] async tool function 执行支持
- [x] 并发限制
- [x] 超时和取消
- [x] 后台任务基础 runner
- [x] FastAPI 后台任务 API：create / status / cancel
- [x] 异步 DefenseTask step execution API
- [x] 向量库构建 checkpoint
- [x] 向量库构建断点恢复
- [x] 幂等性
- [x] 后台任务持久化状态恢复
- [x] Agent 任务恢复

基础知识：

- 线程、进程、协程
- 事件循环
- I/O 密集与 CPU 密集
- 竞态条件

## 阶段 8：LangGraph

- [x] State
- [x] Node
- [x] Edge
- [x] Conditional Edge
- [x] Checkpointer
- [x] Human-in-the-loop
- [x] 最小旁路 demo：`retrieve_context -> generate_question -> wait_for_answer`
- [x] Interrupt / resume demo：`retrieve_context -> generate_question -> interrupt -> resume`
- [x] Checkpointer 状态观察 demo
- [x] Conditional edge demo：已有回答跳过 interrupt，无回答进入 interrupt
- [x] 将当前手写 Agent Loop 旁路迁移到 LangGraph

原则：

- 先理解手写 Harness，再使用框架。
- LangGraph 迁移必须旁路实现。
- 新增独立目录，例如 `app/langgraph_workflow/`。
- 新增独立 CLI，例如 `python -m app.cli graph-demo-task`。
- 不覆盖 `app/task_*`、`app/agent.py` 等现有手写实现。
- 保留两套实现用于对照学习。

## 阶段 9：MCP 与 Sub-Agent

- [x] MCP 工具协议概念对照
- [x] Tool discovery / schema / metadata / invocation 对照
- [x] Resource / Prompt / Audit / Permission 对照
- [x] Sub-Agent spec
- [x] Sub-Agent allowed tools 权限边界
- [x] Sub-Agent plan-first / dry-run
- [x] Sub-Agent execution trace
- [x] Sub-Agent plan / execution comparator
- [x] 真实 MCP Client 最小 stdio 版本
- [x] MCP resource / prompt 能力
- [x] 真实 MCP Server 最小 stdio 版本
- [ ] Planner / Researcher / Evaluator 多角色协作
- [ ] 多 Agent 共享上下文边界
- [ ] 失败回收和预算控制

## 阶段 10：服务化与界面

> 当前机器已经完成 FastAPI 服务化、静态 Web 前端增强、stdio MCP Server、stdio MCP Client、MCP resource / prompt 能力、Docker Compose、Prometheus 本地验证、Alertmanager 本机路由、外部通知路由本地可审计版本、K8s 基础 manifests、生产化基础字段、smoke test 计划 CLI 与执行记录模板 CLI、Docker 镜像 CI 构建、GHCR 镜像发布、PostgreSQL runtime smoke、Qdrant 最小后端、Vector DB 生产化治理报告、Qdrant backup retention policy CLI、Qdrant snapshot API runner、Windows Task Scheduler 本机实验、Milvus runtime benchmark、Milvus backup / restore SOP 和 Milvus destructive operation guardrails。K8s 真实集群 smoke test 执行证据已经在本机 kind 集群完成；cron / Kubernetes CronJob 调度证据、Qdrant 长期运行验证和服务器长期运行继续作为后续阶段。

- [x] FastAPI
- [x] Pydantic 请求模型
- [x] SSE 基础流式输出
- [x] 真实 LLM SSE 流式输出
- [x] WebSocket 双向交互
- [x] 静态前端答辩界面
- [x] 前端增强：SSE / WebSocket / 文件上传 UI / trace 可视化
- [x] 文件上传
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
- [x] Prometheus 指标
- [x] Prometheus 告警规则
- [x] 日志保留与查询文档
- [x] Alertmanager 本机路由
- [x] 外部通知渠道 / on-call routing 本地可审计版本
- [x] API request Correlation ID
- [x] request -> task -> tool call 全链路 Correlation ID
- [x] Docker
- [x] Docker build CI
- [x] GHCR 镜像发布流程
- [x] GHCR 镜像拉取与运行验证
- [x] PostgreSQL 存储抽象设计
- [x] PostgreSQL Docker Compose service
- [x] PostgreSQL schema / migration files
- [x] PostgreSQL migration runner
- [x] PostgresTaskRepository
- [x] PostgresSessionRepository
- [x] PostgresTraceRepository
- [x] Repository factory / STORAGE_BACKEND selection
- [x] JSON-to-PostgreSQL import scripts
- [x] Task runtime repository pilot
- [x] Session runtime repository integration
- [x] Trace runtime repository integration
- [x] PostgreSQL runtime smoke test
- [x] Vector store repository abstraction
- [x] Qdrant Compose service / config skeleton
- [x] QdrantVectorStoreRepository minimal implementation
- [x] JSON vs Qdrant benchmark comparison
- [x] Qdrant collection delete CLI with explicit confirmation
- [x] Qdrant snapshot backup/restore SOP
- [x] Vector DB 生产化治理报告
- [x] Qdrant / Milvus 对比边界说明
- [x] Qdrant backup retention policy CLI
- [x] Qdrant snapshot smoke plan / report template
- [x] Qdrant snapshot API runner
- [x] Qdrant snapshot drill plan
- [x] Qdrant snapshot drill one-time runner
- [x] Qdrant snapshot schedule config
- [x] Qdrant snapshot schedule install plan
- [x] Qdrant snapshot schedule verification plan
- [x] Qdrant snapshot schedule evidence template
- [x] Qdrant snapshot schedule install executor
- [x] Qdrant Windows Task Scheduler 本机定时 snapshot 实验
- [x] Qdrant Kubernetes CronJob manifest / client-side dry-run
- [x] Qdrant Kubernetes StatefulSet / Service / PVC / PDB runtime validation
- [x] Qdrant Kubernetes CronJob apply / manual Job smoke evidence
- [x] Qdrant Kubernetes CronJob natural schedule one-cycle evidence
- [x] Qdrant cron / Kubernetes CronJob / 多周期长期运行调度证据
- [x] MilvusVectorStoreRepository skeleton
- [x] Milvus Compose service / import CLI / optional benchmark entry
- [x] Milvus runtime benchmark report
- [x] Milvus backup / restore SOP
- [x] Milvus destructive operation guardrails
- [x] K8s 基础 manifests
- [x] K8s 生产化基础字段
- [x] K8s smoke test 计划生成 CLI
- [x] K8s smoke test 执行记录模板 CLI
- [x] K8s smoke test runner CLI
- [x] K8s 真实集群 smoke test 执行证据（kind 本机集群）
- [x] Qdrant StatefulSet / Service / PVC / PDB 本机 kind 运行验证
- [x] Qdrant Kubernetes CronJob apply / manual Job smoke evidence
- [x] Qdrant Kubernetes CronJob natural schedule one-cycle evidence
- [x] Qdrant Kubernetes CronJob multi-cycle schedule evidence
- [ ] 私有化配置和密钥管理

## 当前阶段：本机学习版 Agent Harness + 交付基础闭环

当前项目已经完成本机学习版 Agent Harness 和本机交付基础闭环：

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
→ FastAPI / SSE / WebSocket
→ Docker / Compose / GHCR
→ Prometheus metrics / alert rules
→ PostgreSQL optional runtime backend
→ Qdrant minimal vector backend
```

<!-- roadmap-update-2026-06-29-postgres-compose -->

## 2026-06-29 路线同步：PostgreSQL Compose Service 已完成

本阶段完成的是数据库基础设施准备，不是业务存储切换。

已完成：

- [x] `docker-compose.yml` 增加 `postgres` service
- [x] `postgres_data` volume 持久化数据库数据
- [x] `pg_isready` healthcheck
- [x] `.env.example` 增加 `STORAGE_BACKEND`、`DATABASE_URL` 和 PostgreSQL 本地参数
- [x] `app.config` 增加 `STORAGE_BACKEND` 和 `DATABASE_URL`
- [x] `docs/deployment/postgresql.md` 记录本地启动和边界
- [x] 测试锁定 Compose 与 env 模板关键配置

当前边界：

```text
STORAGE_BACKEND=json 仍是默认值。
API 当前仍使用 JSON / JSONL 文件存储。
PostgreSQL 只作为本地集成测试和后续 repository 实现的基础设施。
```

下一步学习：

```text
PostgreSQL schema / migration。
先定义表结构和迁移脚本，再实现 PostgresTaskRepository / PostgresSessionRepository / PostgresTraceRepository。
```

<!-- roadmap-update-2026-06-29-postgres-migrations -->

## 2026-06-29 路线同步：PostgreSQL Schema / Migration 已完成

本阶段完成的是迁移资产和只读迁移计划查看，不执行数据库写入。

已完成：

- [x] `db/migrations/postgres/001_initial_schema.sql`
- [x] `schema_migrations` 表设计
- [x] `defense_tasks` 表设计
- [x] `agent_sessions` 表设计
- [x] `trace_records` 表设计
- [x] `feedback_records` 表设计
- [x] `benchmark_candidates` 表设计
- [x] 关键索引设计
- [x] `app.postgres_migrations` 迁移文件读取、版本解析、checksum 计算
- [x] `postgres-migrations` CLI 只读查看迁移计划
- [x] 离线测试覆盖 migration SQL 与 CLI

当前边界：

```text
尚未引入 PostgreSQL Python client。
尚未执行 SQL。
尚未记录已应用 migration。
尚未实现 PostgresTaskRepository / PostgresSessionRepository / PostgresTraceRepository。
业务存储仍默认使用 JSON / JSONL。
```

下一步学习：

```text
PostgreSQL migration runner。
选择 PostgreSQL client 后，连接 DATABASE_URL，执行未应用 migration，并写入 schema_migrations。
```

<!-- roadmap-update-2026-06-29-postgres-migration-runner -->

## 2026-06-29 路线同步：PostgreSQL Migration Runner 已完成

本阶段完成的是真实 migration runner，不切换业务存储。

已完成：

- [x] 选择 `psycopg` 作为 PostgreSQL client
- [x] `app.postgres_migration_runner`
- [x] 自动 bootstrap `schema_migrations`
- [x] 读取已应用 migration
- [x] 跳过 checksum 匹配的已应用 migration
- [x] 检测 checksum drift 并失败
- [x] 执行 pending migration
- [x] 写入 `schema_migrations`
- [x] commit / rollback / close 生命周期处理
- [x] `run-postgres-migrations` CLI
- [x] CLI 不打印完整 `DATABASE_URL`
- [x] fake connection 单元测试，不依赖真实数据库

当前边界：

```text
数据库 schema 可以通过 runner 创建。
业务存储仍默认使用 JSON / JSONL。
尚未实现 PostgresTaskRepository / PostgresSessionRepository / PostgresTraceRepository。
尚未实现 JSON -> PostgreSQL 导入脚本。
```

下一步学习：

```text
PostgreSQL repository implementations。
先实现 PostgresTaskRepository，对齐 JsonTaskRepository 行为，再逐步实现 Session / Trace。
```

<!-- roadmap-update-2026-06-29-postgres-task-repository -->

## 2026-06-29 路线同步：PostgresTaskRepository 已完成

本阶段完成的是 `DefenseTask` 的 PostgreSQL repository adapter，不切换默认业务存储。

已完成：

- [x] `app.postgres_task_repository.PostgresTaskRepository`
- [x] `save(task)` 写入 `defense_tasks`
- [x] `load(task_id)` 从 `payload` 还原 `DefenseTask`
- [x] `INSERT ... ON CONFLICT (task_id) DO UPDATE`
- [x] `JSONB` payload 保存完整任务对象
- [x] denormalized columns：`topic`、`status`、`current_step_id`、`created_at`、`updated_at`
- [x] `task_id` 校验复用现有规则
- [x] commit / rollback / close 生命周期处理
- [x] fake connection 单元测试，不依赖真实数据库

当前边界：

```text
PostgresTaskRepository 已实现。
API service 仍默认使用 JSON task store。
尚未实现 PostgresSessionRepository。
尚未实现 PostgresTraceRepository。
尚未实现 STORAGE_BACKEND repository factory。
```

下一步学习：

```text
PostgresSessionRepository。
对齐 JsonSessionRepository 行为，保存和加载 AgentSession payload。
```

<!-- roadmap-update-2026-06-29-postgres-session-repository -->

## 2026-06-29 路线同步：PostgresSessionRepository 已完成

本阶段完成的是 `AgentSession` 的 PostgreSQL repository adapter，不切换默认业务存储。

已完成：

- [x] `app.postgres_session_repository.PostgresSessionRepository`
- [x] `save(session)` 写入 `agent_sessions`
- [x] `load(session_id)` 从 `payload` 还原 `AgentSession`
- [x] `INSERT ... ON CONFLICT (session_id) DO UPDATE`
- [x] `JSONB` payload 保存完整会话对象
- [x] `updated_at = now()` 由数据库维护
- [x] `session_id` 校验复用现有规则
- [x] commit / rollback / close 生命周期处理
- [x] fake connection 单元测试，不依赖真实数据库

当前边界：

```text
PostgresTaskRepository 已实现。
PostgresSessionRepository 已实现。
API service 仍默认使用 JSON task/session store。
尚未实现 PostgresTraceRepository。
尚未实现 STORAGE_BACKEND repository factory。
```

下一步学习：

```text
PostgresTraceRepository。
对齐 JsonlTraceRepository 行为，实现 append-only trace 写入和读取。
```

<!-- roadmap-update-2026-06-29-postgres-trace-repository -->

## 2026-06-29 路线同步：PostgresTraceRepository 已完成

本阶段完成的是 append-only trace 的 PostgreSQL repository adapter，不切换默认业务存储。

已完成：

- [x] `app.postgres_trace_repository.PostgresTraceRepository`
- [x] `append(record)` 写入 `trace_records`
- [x] `load_all()` 按插入顺序读取 payload
- [x] `JSONB` payload 保存完整 trace record
- [x] `source_type`、`source_id`、`event_type`、`success` 查询列填充
- [x] Agent trace / Sub-Agent trace 常见字段推断
- [x] commit / rollback / close 生命周期处理
- [x] fake connection 单元测试，不依赖真实数据库

当前边界：

```text
PostgresTaskRepository 已实现。
PostgresSessionRepository 已实现。
PostgresTraceRepository 已实现。
API service 仍默认使用 JSON / JSONL storage。
尚未实现 STORAGE_BACKEND repository factory。
尚未实现 JSON -> PostgreSQL 导入脚本。
```

下一步学习：

```text
Repository factory / configuration selection。
根据 STORAGE_BACKEND=json|postgres 创建 Task / Session / Trace repositories。
```

<!-- roadmap-update-2026-06-29-repository-factory -->

## 2026-06-29 路线同步：Repository Factory 已完成

本阶段完成的是 repository 创建与配置选择，不切换现有 service 的默认运行路径。

已完成：

- [x] `app.repository_factory.RepositoryBundle`
- [x] `create_repositories(storage_backend=...)`
- [x] `STORAGE_BACKEND=json` 创建 `JsonTaskRepository` / `JsonSessionRepository` / `JsonlTraceRepository`
- [x] `STORAGE_BACKEND=postgres` 创建 `PostgresTaskRepository` / `PostgresSessionRepository` / `PostgresTraceRepository`
- [x] PostgreSQL backend 要求 `DATABASE_URL`
- [x] `show-repositories` CLI
- [x] CLI 不打印完整 `DATABASE_URL`
- [x] factory 和 CLI 单元测试

当前边界：

```text
repository factory 已完成。
默认 backend 仍是 json。
runtime service 尚未通过 factory 注入 repository。
JSON -> PostgreSQL 导入脚本已在后续阶段完成。
```

后续学习记录：

```text
JSON-to-PostgreSQL import scripts 已在下一节完成。
```

<!-- roadmap-update-2026-06-29-postgres-json-import -->

## 2026-06-29 路线同步：JSON-to-PostgreSQL Import 已完成

本阶段完成的是显式导入工具，不切换默认运行路径。

已完成：

- [x] `app.postgres_json_importer`
- [x] task JSON directory -> PostgreSQL task repository
- [x] session JSON directory -> PostgreSQL session repository
- [x] trace JSONL file -> PostgreSQL trace repository
- [x] `--dry-run` 预览
- [x] `--skip-tasks` / `--skip-sessions` / `--skip-traces`
- [x] `import-json-to-postgres` CLI
- [x] CLI 不打印完整 `DATABASE_URL`
- [x] fake repository 单元测试，不依赖真实数据库

当前边界：

```text
导入工具已完成。
默认 STORAGE_BACKEND 仍是 json。
runtime service 尚未通过 repository factory 注入。
尚未提供切换前的自动回滚策略。
```

下一步学习：

```text
Runtime repository integration design。
先设计 service 注入边界和 rollback 策略，再决定是否把 task/session/trace service 接到 repository factory。
```

<!-- roadmap-update-2026-06-29-runtime-repository-integration-design -->

## 2026-06-29 路线同步：Runtime Repository Integration Design 已完成

本阶段完成的是运行时存储切换设计，不直接切换默认存储后端。

设计文档：

```text
docs/storage/runtime-repository-integration.md
```

已明确：

- [x] 当前 JSON / JSONL runtime path 与 repository path 的边界
- [x] `RepositoryBundle` 的注入位置
- [x] Task / Session / Trace 的分阶段迁移顺序
- [x] `STORAGE_BACKEND=json|postgres` 的配置规则
- [x] `DATABASE_URL` 不打印完整值的安全要求
- [x] JSON 默认后端保留策略
- [x] PostgreSQL 切换失败时回滚到 JSON 的策略
- [x] 不要求普通单元测试依赖真实 PostgreSQL

下一步学习：

```text
Task runtime repository pilot。
先把 task workflow 的 create/start/execute/submit/resume/analyze/export 接到 task_repository 依赖。
保持 STORAGE_BACKEND=json 为默认值，不在同一 PR 内迁移 session 和 trace。
```

<!-- roadmap-update-2026-06-29-task-runtime-repository-pilot -->

## 2026-06-29 路线同步：Task Runtime Repository Pilot 已完成

本阶段只迁移 task workflow 的运行时存储入口，不迁移 session 和 trace。

已完成：

- [x] `task_service` 支持注入 `task_repository`
- [x] 不传 `task_repository` 时保持原 JSON directory 行为
- [x] Task CLI 通过 `RepositoryBundle` 创建 task repository
- [x] `create-task`
- [x] `start-task-step`
- [x] `complete-task-step`
- [x] `execute-task-step`
- [x] `submit-task-answer`
- [x] `submit-follow-up-answer`
- [x] `resume-task`
- [x] `analyze-task`
- [x] `export-task-markdown`
- [x] `export-task-memory`
- [x] `show-task`
- [x] fake repository 测试覆盖 service 注入边界
- [x] CLI 测试覆盖 repository factory 接入

当前边界：

```text
Task runtime repository pilot 已完成。
默认 STORAGE_BACKEND 仍是 json。
Session runtime 尚未接 session_repository。
Trace runtime 尚未接 trace_repository。
```

下一步学习：

```text
Session runtime repository integration。
把 chat/session resume/session metadata 相关路径接入 session_repository，仍保持 JSON 默认后端。
```

<!-- roadmap-update-2026-06-29-session-runtime-repository-integration -->

## 2026-06-29 路线同步：Session Runtime Repository Integration 已完成

本阶段只迁移 chat/session runtime，不迁移 trace。

已完成：

- [x] `run_agent_session` 支持注入 `session_repository`
- [x] 不传 `session_repository` 时保持原 JSON directory 行为
- [x] 新 session 创建走 repository save
- [x] 已有 session resume 走 repository load
- [x] session token/cost metadata 通过 repository 持久化
- [x] session compaction 结果通过 repository 持久化
- [x] chat CLI 通过 `RepositoryBundle` 创建 session repository
- [x] fake repository 测试覆盖 service 注入边界
- [x] CLI 测试覆盖 repository factory 接入

当前边界：

```text
Task runtime repository pilot 已完成。
Session runtime repository integration 已完成。
默认 STORAGE_BACKEND 仍是 json。
Trace runtime 尚未接 trace_repository。
```

下一步学习：

```text
Trace runtime repository integration。
把 Agent trace / Sub-Agent trace / trace analysis 相关写入读取路径接入 trace_repository，仍保持 JSON 默认后端。
```

<!-- roadmap-update-2026-06-29-trace-runtime-repository-integration -->

## 2026-06-29 路线同步：Trace Runtime Repository Integration 已完成

本阶段完成 trace runtime 的 repository 接入，不改变默认 JSONL 行为。

已完成：

- [x] `save_agent_trace` 支持注入 `trace_repository`
- [x] `load_agent_trace_records` 支持注入 `trace_repository`
- [x] `analyze_agent_traces` 支持注入 `trace_repository`
- [x] `replay_agent_trace` 支持注入 `trace_repository`
- [x] `replay_trace_file` 支持注入 `trace_repository`
- [x] `save_sub_agent_plan_trace` / `load_sub_agent_plan_traces`
- [x] `save_sub_agent_execution_trace` / `load_sub_agent_execution_traces`
- [x] `dry_run_sub_agent_tool_call` 支持 trace repository
- [x] `execute_sub_agent_tool_call` 支持 trace repository
- [x] trace CLI 通过 `RepositoryBundle` 创建 trace repository
- [x] fake repository 测试覆盖读写路径
- [x] CLI 测试覆盖 repository factory 接入

当前边界：

```text
Task runtime repository pilot 已完成。
Session runtime repository integration 已完成。
Trace runtime repository integration 已完成。
默认 STORAGE_BACKEND 仍是 json。
比较两个显式 trace 文件的 compare 命令仍保持文件路径语义。
```

下一步学习：

```text
PostgreSQL runtime smoke test。
本机启动 PostgreSQL，运行 migrations，导入 JSON 数据，然后用 STORAGE_BACKEND=postgres 跑一条小的 task/chat/trace 工作流。
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
- FastAPI、静态 Web 前端、stdio MCP Server、Dockerfile、docker-compose、Prometheus、Alertmanager 本机路由、外部通知路由本地可审计版本、K8s 基础 manifests、生产化基础字段、smoke test 计划 CLI 与执行记录模板 CLI、本机 PostgreSQL runtime smoke、Qdrant 最小后端、Vector DB 生产化治理报告、Qdrant backup retention policy CLI、Qdrant snapshot API runner 和 Windows Task Scheduler 本机实验已完成。
- K8s 真实集群 smoke test 执行证据已经完成；Qdrant Kubernetes CronJob manifest 生成和 client-side dry-run 已完成；cron / 实际 Kubernetes CronJob 长期调度证据、Qdrant 长期运行验证、私有化部署、服务器长期运行和真实 Feishu / WeCom / email 通知提供方继续作为后续阶段。Milvus repository、Compose 服务、导入 CLI、本机 runtime benchmark、backup / restore SOP 和 destructive operation guardrails 已完成。

## 下一步学习重点

当前已经完成本机 Agent Harness、RAG、Tool Calling、Memory、Trace、Sub-Agent、LangGraph 旁路迁移、FastAPI / Web / Docker / Prometheus / PostgreSQL / Qdrant / Milvus 基础治理、Qdrant Windows Task Scheduler 本机实验、Qdrant Kubernetes CronJob manifest dry-run、K8s smoke runner CLI、K8s kind 本机真实集群 smoke 验证，以及 AsyncTaskRunner / FastAPI 后台任务 / DefenseTask 当前步骤后台执行 / 异步 LLM 与工具调用边界 / 原生异步 LLM SDK / async tool function 执行支持 / 后台任务幂等请求 / 后台任务持久化状态恢复。下一阶段进入调度与长期运行验证：

1. 服务器长期运行前置检查和证据索引整理
2. 服务器长期运行验证

## 最终简历能力目标

- 能独立解释并实现 Agent Harness，而不只是调用框架
- 能完成 RAG 数据链路、评估和优化
- 能治理工具权限、异常、超时、审计和成本
- 能设计 Session、Memory、Workspace 和 Skill 边界
- 能实现 Agent Trace、LLM-as-Judge 和反馈闭环
- 能将 Agent 通过 API、数据库、容器和监控交付
- 能使用 LangGraph、MCP 和 Sub-Agent，但不被框架绑架
<!-- roadmap-update-2026-06-23-feedback-loop -->

## 2026-06-23 路线同步：Trace 回放与反馈闭环已完成

本阶段新增完成能力：

- [x] Agent Trace 回放
- [x] Agent Trace 新旧对比
- [x] 用户反馈记录
- [x] Feedback JSONL 本地存储
- [x] Feedback 统计
- [x] Feedback 导出 Benchmark Candidate
- [x] Benchmark Candidate 人工复核
- [x] Accepted Candidate 导出 Benchmark Draft
- [x] Benchmark Draft 字段校验
- [x] Validated Draft 转成正式 Benchmark 草稿文件

当前数据闭环：

```text
replay-agent-trace
→ compare-agent-traces
→ record-feedback
→ export-feedback-candidates
→ review-benchmark-candidate
→ export-benchmark-draft
→ validate-benchmark-draft
→ export-validated-benchmark-draft
```

当前本地测试基线：

```text
432 passed
```

注意：导出的 benchmark 文件仍然是草稿，不直接覆盖现有正式 benchmark。正式合并前必须人工检查。

<!-- roadmap-update-2026-06-23-hybrid-retrieval -->

## 2026-06-23 路线同步：BM25 + Vector 混合检索已完成

本阶段新增完成能力：

- [x] BM25 关键词检索
- [x] Vector 语义检索与 BM25 检索结果融合
- [x] Hybrid score 归一化与加权合并
- [x] `evaluate-rag --retriever vector|bm25|hybrid`
- [x] `compare-retrievers`
- [x] `scan-hybrid-weights`
- [x] 使用 benchmark 自动扫描 `vector_weight` / `bm25_weight`

本阶段学到的核心方法：

```text
不要凭感觉选 hybrid 权重。
先用 benchmark 比较 vector、bm25、hybrid。
再扫描多组 vector_weight / bm25_weight。
最后根据 average_score、missing keywords 和稳定性选择默认参数。
```

当前建议默认值：

```text
vector_weight=0.7
bm25_weight=0.3
```

理由：该配置保留语义检索为主，同时让模块名、数据集名、算法名等关键词命中参与排序。

<!-- roadmap-update-2026-06-23-reranker -->

## 2026-06-23 路线同步：规则版 Reranker 已完成

本阶段新增完成能力：

- [x] `app/reranker.py`
- [x] `rerank_results(query, results, top_k)`
- [x] 关键词命中奖励
- [x] 章节特征奖励
- [x] 短文本惩罚
- [x] `evaluate-rag --rerank`
- [x] `--rerank-candidate-multiplier`
- [x] rerank 前后 benchmark 对比

本轮真实 benchmark 对比：

```text
hybrid no rerank: average_score = 0.8667
hybrid rerank x3: average_score = 0.8333
hybrid rerank x5: average_score = 0.8333
```

阶段结论：

```text
规则版 reranker 已完成工程闭环，但当前规则对这份 benchmark 没有收益。
因此默认不启用 reranker，只保留为实验开关。
```

学到的关键点：

```text
reranker 是第二阶段排序器，不是召回器。
reranker 不一定天然提升效果。
必须用 benchmark 验证 rerank 前后 average_score 和 missing keywords。
```

后续若继续优化 reranker，可以考虑：

- 增强英文术语 token 匹配。
- 为专业名词设置同义词表。
- 引入模型版 reranker 或 cross-encoder reranker。

<!-- roadmap-update-2026-06-23-query-rewrite -->

## 2026-06-23 路线同步：规则版 Query Rewrite 已完成

本阶段新增完成能力：

- [x] `app/query_rewriter.py`
- [x] `rewrite_query(query)`
- [x] 系统架构类问题补充模块术语
- [x] 数据集类问题补充 AISHELL / LibriSpeech 等术语
- [x] 语言感知类问题补充 `LanguageAwareFrontend`、`BiLSTM`、注意力池化等术语
- [x] 后续改进类问题补充预训练微调、流式识别、数据扩展、模型压缩
- [x] `evaluate-rag --rewrite-query`
- [x] 报告中保留 `query` 和 `rewritten_query`
- [x] query rewrite 前后 benchmark 对比

本轮真实 benchmark 对比：

```text
hybrid no query rewrite: average_score = 0.8667
hybrid with query rewrite: average_score = 1.0
hybrid with query rewrite + rerank x3: average_score = 0.925
```

阶段结论：

```text
规则版 query rewrite 对当前 benchmark 有明显收益。
当前推荐实验策略是 hybrid + query rewrite。
当前不推荐默认叠加规则版 reranker。
```

学到的关键点：

```text
query rewrite 发生在检索前，解决“拿什么去搜”的问题。
reranker 发生在检索后，解决“搜到后怎么排”的问题。
二者都必须通过 benchmark 独立验证，不能凭感觉打开。
```

后续可继续学习：

- 多查询检索：为同一问题生成多个 query 后合并结果。
- LLM query rewrite：用模型根据用户问题生成更自然的检索 query。
- 查询改写质量评估：对比 rewrite 前后召回、MISSING 和 token/cost。

<!-- roadmap-update-2026-06-23-multi-query -->

## 2026-06-23 路线同步：多查询检索已完成

本阶段新增完成能力：

- [x] `app/multi_query_rewriter.py`
- [x] `generate_multi_queries(query)`
- [x] 为系统架构、数据集、语言感知前端、后续改进等问题生成多个检索 query
- [x] 多 query 检索结果合并
- [x] 按 chunk id / source + text 去重
- [x] 保留 `search_queries` 进入评估报告
- [x] `evaluate-rag --multi-query`
- [x] `compare-retrievers --multi-query`
- [x] `scan-hybrid-weights --multi-query`
- [x] multi-query benchmark 对比

本轮真实 benchmark 结果：

```text
hybrid + multi-query: average_score = 1.0
```

阶段结论：

```text
multi-query retrieval 对当前 benchmark 有正收益，能够通过多个检索视角提升召回稳定性。
它不是替代 query rewrite，而是把“一个增强 query”扩展为“多个 query 并行召回后合并”。
```

学到的关键点：

```text
query rewrite 关注单个 query 如何写得更准。
multi-query 关注同一个问题能不能从多个角度去搜。
多查询检索会增加 embedding 调用和检索成本，因此必须记录 cache hits / misses，并用 benchmark 验证收益。
```

后续可继续学习：

- 模型版 reranker 或 cross-encoder reranker。
- LLM query rewrite。
- 对比 `query rewrite`、`multi-query`、`query rewrite + multi-query` 的召回收益与成本。

<!-- roadmap-update-2026-06-23-model-reranker -->

## 2026-06-23 路线同步：模型版 Reranker 已完成

本阶段新增完成能力：

- [x] `app/model_reranker.py`
- [x] `build_rerank_prompt(query, candidate)`
- [x] `score_candidate_with_llm(query, candidate)`
- [x] `rerank_results_with_model(query, results, top_k)`
- [x] LLM JSON 分数解析
- [x] 分数裁剪到 0~1
- [x] `evaluate-rag --model-rerank`
- [x] `--model-rerank-candidate-multiplier`
- [x] 模型版 reranker benchmark 对比

本轮真实 benchmark 结果：

```text
hybrid + model reranker x2: average_score = 0.9667
missing: 卷积层
```

阶段结论：

```text
模型版 reranker 工程链路已经跑通，但当前 benchmark 上没有超过 query rewrite 或 multi-query。
模型版 reranker 成本更高，因为每个候选 chunk 都需要一次 LLM 评分。
当前不建议默认启用 model reranker，只保留为实验开关。
```

学到的关键点：

```text
第一阶段召回负责把可能相关的 chunk 拉进候选集。
第二阶段重排负责更精细地判断 query 和 chunk 是否匹配。
模型版 reranker 比规则版更灵活，但更贵、更慢，也可能误排。
是否启用 reranker 不能凭感觉，必须看 benchmark、missing keywords 和调用成本。
```

后续可继续学习：

- LLM query rewrite。
- 对比 `query rewrite`、`multi-query`、`model reranker` 的组合收益与成本。
- 后续如需真正 cross-encoder reranker，可单独接本地或 API 模型，不覆盖当前实现。

<!-- roadmap-update-2026-06-23-llm-query-rewrite -->

## 2026-06-23 路线同步：LLM Query Rewrite 已完成

本阶段新增完成能力：

- [x] `app/llm_query_rewriter.py`
- [x] `build_llm_query_rewrite_prompt(query)`
- [x] `rewrite_query_with_llm(query)`
- [x] LLM JSON 输出解析
- [x] Markdown JSON 代码块清洗
- [x] 空 query 与缺字段校验
- [x] `evaluate-rag --llm-rewrite-query`
- [x] `compare-retrievers --llm-rewrite-query`
- [x] `scan-hybrid-weights --llm-rewrite-query`
- [x] LLM query rewrite benchmark 对比

本轮真实 benchmark 对比：

```text
hybrid + LLM query rewrite: average_score = 0.8333
hybrid + LLM query rewrite + multi-query: average_score = 1.0
```

阶段结论：

```text
LLM query rewrite 单独使用时不稳定，会因为过度概括而丢失论文中的关键术语。
LLM query rewrite + multi-query 可以恢复召回，但会增加 LLM 调用和 embedding 调用成本。
当前不建议默认启用 LLM query rewrite，只保留为实验开关。
```

学到的关键点：

```text
规则版 query rewrite 稳定、便宜，但覆盖范围有限。
LLM query rewrite 更灵活，但可能改丢关键术语。
multi-query 可以补充多个检索视角，但会增加 embedding 成本。
检索优化不能只看 average_score，还要看 missing keywords、cache hits / misses、LLM 调用次数和整体耗时。
```

后续可继续学习：

- LangGraph 旁路迁移前，整理手写 Agent Harness 的状态机和节点图。

<!-- roadmap-update-2026-06-23-retrieval-strategy-comparison -->

## 2026-06-23 路线同步：检索策略组合对比已完成

本阶段新增完成能力：

- [x] `compare_retrieval_strategies(...)`
- [x] `compare-retrieval-strategies`
- [x] 默认扫描低成本策略组合
- [x] 使用 `--include-expensive` 显式纳入 LLM query rewrite 和模型版 reranker
- [x] 输出 `best_strategy`、`best_average_score`、cache hits / misses 和 missing summary
- [x] 保存组合对比 JSON 报告

默认低成本组合：

```text
hybrid
hybrid + query rewrite
hybrid + multi-query
hybrid + query rewrite + multi-query
hybrid + reranker
```

本轮真实 benchmark 结果：

```text
hybrid: average_score = 0.8667
hybrid + query rewrite: average_score = 1.0
hybrid + multi-query: average_score = 1.0
hybrid + query rewrite + multi-query: average_score = 0.925
hybrid + reranker: average_score = 0.8333
```

阶段结论：

```text
当前推荐低成本默认策略是 hybrid + query rewrite。
hybrid + multi-query 同样有效，但查询数量更多，成本更高。
reranker 和盲目叠加组合在当前 benchmark 上没有收益。
```

学到的关键点：

```text
检索优化不是“功能越多越好”。
每个组合都要放进同一份 benchmark 里比较。
选择默认策略时要同时看 average_score、missing keywords、cache hits / misses、LLM 调用次数和整体复杂度。
```

下一步学习：

- LangGraph 旁路迁移前的手写状态机复盘。
- 画出当前 Task State 的节点、边、状态和人工输入点。
- 后续 LangGraph 只做旁路对照，不覆盖当前实现。

<!-- roadmap-update-2026-06-24-langgraph-demo-task -->

## 2026-06-24 路线同步：LangGraph 最小旁路 Demo 已完成

本阶段新增完成能力：

- [x] 新增 `langgraph` 项目依赖
- [x] 新增独立目录 `app/langgraph_workflow/`
- [x] 新增 `LangGraphDefenseState`
- [x] 新增 `retrieve_context_node`
- [x] 新增 `generate_question_node`
- [x] 新增 `wait_for_answer_node`
- [x] 新增 `build_demo_task_graph`
- [x] 新增 `run_demo_task`
- [x] 新增 CLI：`graph-demo-task`
- [x] 保持旁路实现，不覆盖 `app/task_*` 和 `app/agent.py`

当前最小图：

```text
retrieve_context
-> generate_question
-> wait_for_answer
```

对应 LangGraph 概念：

```text
LangGraphDefenseState -> State
retrieve_context_node -> Node
generate_question_node -> Node
wait_for_answer_node  -> Node
add_edge(...)         -> Edge
graph.compile()       -> 可执行 graph
```

当前没有勾选的原因：

```text
Conditional Edge：还没有条件分支。
Checkpointer：还没有接持久化 checkpoint。
Human-in-the-loop：当前只是普通 wait_for_answer 节点，还没有使用 LangGraph interrupt / resume。
```

下一步学习：

- 学习 LangGraph interrupt / resume，把 `wait_for_answer` 从普通节点升级为真正的人机中断点。
- 再学习 checkpointer，把图执行状态持久化。
- 所有 LangGraph 实验继续保留在 `app/langgraph_workflow/`，不替换手写 Task State。

<!-- roadmap-update-2026-06-24-langgraph-interrupt-demo -->

## 2026-06-24 路线同步：LangGraph Interrupt / Resume Demo 已完成

本阶段新增完成能力：

- [x] 新增 `app/langgraph_workflow/interrupt_demo.py`
- [x] 使用 `interrupt(...)` 暂停图执行
- [x] 使用 `Command(resume=...)` 恢复图执行
- [x] 使用 `InMemorySaver` 保存同一进程内的图状态
- [x] 新增 `graph-interrupt-demo` CLI
- [x] 新增 interrupt / resume 单元测试
- [x] 保持旁路实现，不覆盖 `app/task_*` 和 `app/agent.py`

当前图：

```text
retrieve_context
-> generate_question
-> answer_interrupt
```

第一次执行：

```text
graph.invoke(...)
-> 返回 __interrupt__
-> 暂停等待人工回答
```

恢复执行：

```text
graph.invoke(Command(resume="学生回答"), config=same_thread_id)
-> answer_interrupt 节点继续执行
-> state 写入 answer
```

CLI 示例：

```powershell
uv run python -m app.cli graph-interrupt-demo `
  --topic "系统架构"

uv run python -m app.cli graph-interrupt-demo `
  --topic "系统架构" `
  --answer "系统按职责拆分模块，便于定位问题。"
```

当前限制：

```text
本阶段使用 InMemorySaver，只演示同一进程内 interrupt / resume。
它还不是跨进程、跨命令、可落盘的持久化恢复。
```

学到的关键点：

```text
普通 wait_for_answer 节点只是返回 needs_human_input=True。
LangGraph interrupt 会让图真正暂停。
resume 需要同一个 thread_id 和 checkpointer。
checkpointer 是 LangGraph 可恢复执行的关键基础设施。
```

下一步学习：

- LangGraph checkpointer 对照学习。
- 比较 InMemorySaver 与持久化 checkpointer 的差异。
- 明确它和当前 `task_store.py` JSON 落盘机制的对应关系。

<!-- roadmap-update-2026-06-24-langgraph-checkpointer-demo -->

## 2026-06-24 路线同步：LangGraph Checkpointer 状态观察 Demo 已完成

本阶段新增完成能力：

- [x] 新增 `app/langgraph_workflow/checkpointer_demo.py`
- [x] 复用 interrupt demo 构建可中断图
- [x] 显式创建并返回 `InMemorySaver`
- [x] 使用 `graph.get_state(config)` 观察 checkpoint 状态
- [x] 输出 `checkpoint_id`
- [x] 输出 `next`
- [x] 输出 `values`
- [x] 输出 `interrupts`
- [x] 新增 `graph-checkpointer-demo` CLI
- [x] 新增 checkpointer 单元测试
- [x] 保持旁路实现，不覆盖 `app/task_*` 和 `app/agent.py`

本阶段观察到的状态变化：

```text
第一次 invoke 后：
next = ["answer_interrupt"]
interrupts = [{"type": "answer_required", ...}]
values 中已有 topic / query / context / question

Command(resume=...) 后：
next = []
interrupts = []
values 中新增 answer
```

CLI 示例：

```powershell
uv run python -m app.cli graph-checkpointer-demo `
  --topic "系统架构"

uv run python -m app.cli graph-checkpointer-demo `
  --topic "系统架构" `
  --answer "系统按职责拆分模块，便于定位问题。"
```

学到的关键点：

```text
thread_id 标识同一条图执行线程。
checkpointer 保存图执行到哪一步，以及当前 state values。
interrupt 后如果没有 checkpointer，就无法 resume。
InMemorySaver 只适合同一进程学习和测试，不适合跨进程持久恢复。
当前项目里的 task_store.py 是手写 JSON 持久化；LangGraph checkpointer 是框架级状态保存接口。
```

下一步学习：

- LangGraph 条件边 / 分支路由。
- 用一个简单判断：如果已有 answer，则跳过 interrupt；如果没有 answer，则进入 interrupt。
- 后续再学习持久化 checkpointer，不在当前机器做数据库部署。

<!-- roadmap-update-2026-06-24-langgraph-conditional-demo -->

## 2026-06-24 路线同步：LangGraph Conditional Edge Demo 已完成

本阶段新增完成能力：

- [x] 新增 `app/langgraph_workflow/conditional_demo.py`
- [x] 使用 `add_conditional_edges` 实现条件路由
- [x] 新增 `route_by_answer` 路由函数
- [x] 新增 `finalize_answer_node` 完成节点
- [x] 新增 `graph-conditional-demo` CLI
- [x] 新增条件边单元测试与 CLI 测试
- [x] 保持旁路实现，不覆盖 `app/task_*` 和 `app/agent.py`

当前条件路由：

```text
generate_question
-> route_by_answer
   -> 已有 answer: finalize
   -> 没有 answer: answer_interrupt -> finalize
```

CLI 示例：

```powershell
uv run python -m app.cli graph-conditional-demo `
  --topic "系统架构" `
  --answer "系统按职责拆分模块，便于定位问题。"

uv run python -m app.cli graph-conditional-demo `
  --topic "系统架构" `
  --resume-answer "系统按职责拆分模块，便于定位问题。"
```

学到的关键点：

```text
Edge 是固定流程。
Conditional Edge 根据 state 动态选择下一步。
分支路由函数应保持小而纯，只负责返回路由标签。
复杂业务逻辑仍放到 node 中。
```

下一步学习：

- LangGraph 持久化 checkpointer 对照学习。
- MCP / Sub-Agent 前置概念学习。

<!-- roadmap-update-2026-06-24-langgraph-persistent-checkpoint-snapshot-demo -->

## 2026-06-24 路线同步：LangGraph Persistent Checkpoint Snapshot Demo 已完成

本阶段新增完成能力：

- [x] 新增 `app/langgraph_workflow/persistent_checkpoint_demo.py`
- [x] 将 interrupted / resumed checkpoint state 导出为 JSON 快照
- [x] 新增 `graph-persistent-checkpoint-demo` CLI
- [x] 新增 checkpoint snapshot 保存、读取、摘要测试
- [x] 保持旁路实现，不覆盖 `app/task_*` 和 `app/agent.py`

当前学习边界：

```text
InMemorySaver 负责同一进程内的 LangGraph interrupt / resume。
JSON snapshot 负责把可观察 checkpoint state 保存下来，用于审计、对比和学习。
它不是数据库级持久化 checkpointer，也不承诺跨进程恢复 graph 执行。
真正的数据库版持久化 checkpointer 留到服务器 / 数据库学习阶段。
```

CLI 示例：

```powershell
uv run python -m app.cli graph-persistent-checkpoint-demo `
  --topic "系统架构" `
  --answer "系统按职责拆分模块，便于定位问题。" `
  --output data/langgraph_checkpoints/system_architecture.json
```

学到的关键点：

```text
checkpoint 是图执行状态，不只是业务输出。
可观察字段包括 checkpoint_id、next、values、interrupts。
把 checkpoint state 落盘后，可以做审计、对比和调试复盘。
执行恢复能力和快照审计能力是两个层次，不能混为一谈。
```

下一步学习：

- MCP / Sub-Agent 前置概念学习。
- 或在不接服务器数据库的前提下，继续做 LangGraph 路由与状态对照小 demo。

<!-- roadmap-update-2026-06-24-tool-registry-metadata -->

## 2026-06-24 路线同步：Tool Registry 元信息增强已完成

本阶段新增完成能力：

- [x] 新增 `ToolMetadata`
- [x] 新增 `RegisteredTool`
- [x] 新增 `app/tool_registry.py`
- [x] 工具函数、OpenAI Tool Schema、工程治理元信息统一注册
- [x] `tool_executor.py` 从注册表构建工具函数白名单
- [x] 新增 `list-tools` CLI
- [x] 新增工具注册表测试

学到的关键点：

```text
Tool Schema 解决“模型怎么调用工具”。
Tool Metadata 解决“工程系统怎么治理工具”。
MCP / Sub-Agent 学习前，需要先理解工具的可发现性、权限、owner、启停、超时、重试和审计。
```

下一步学习：

- 工具权限与 enabled 开关在执行器中的强约束。
- 然后进入 MCP / Sub-Agent 前置概念学习。

<!-- roadmap-update-2026-06-24-tool-execution-governance -->

## 2026-06-24 路线同步：工具执行治理强约束已完成

本阶段新增完成能力：

- [x] `tool_executor.py` 执行前解析 `ToolMetadata`
- [x] 强制拒绝 `enabled=False` 的工具
- [x] 强制拒绝非白名单 permission
- [x] 支持按工具 metadata 使用 timeout / retry / result length
- [x] 保留旧 `TOOL_REGISTRY` 作为测试和临时 fake tool 兼容入口
- [x] 新增 `tests/test_tool_executor_governance.py`

学到的关键点：

```text
工具注册表是治理入口。
工具执行器是治理落点。
只有在执行器里强制校验 enabled、permission、timeout、retry、result limit，工具治理才真正生效。
```

下一步学习：

- MCP / Sub-Agent 前置概念学习。
- 先做本地 MCP 概念映射文档，不接真实 MCP 服务器。

<!-- roadmap-update-2026-06-24-mcp-sub-agent-concepts -->

## 2026-06-24 路线同步：MCP / Sub-Agent 前置概念已完成

本阶段新增完成内容：

- [x] 新增 `docs/06-MCP与Sub-Agent前置概念.md`
- [x] 梳理 MCP Host / Client / Server / Tool / Resource / Prompt
- [x] 将当前项目的 Tool Registry、Tool Executor、Agent Loop 映射到 MCP 概念
- [x] 区分 Tool Schema 与 Tool Metadata
- [x] 梳理 Sub-Agent 与普通 Tool 的区别
- [x] 给出 Retrieval Agent、Evaluation Agent、Follow-Up Agent 等本项目候选 Sub-Agent
- [x] 明确当前阶段不接真实 MCP Server，不做服务器部署，不覆盖现有 Agent Harness

学到的关键点：

```text
MCP 是工具和上下文能力的标准化协议。
Sub-Agent 是有独立职责、上下文、工具集和输出边界的小执行者。
Tool 是能力，Sub-Agent 是带目标的小工作流。
```

下一步学习：

- 新增本地 `SubAgentSpec` 数据结构。
- 先定义 Sub-Agent 的 role、allowed_tools、input_fields、output_fields、max_steps。
- 暂时不做真实多 Agent 调度。

<!-- roadmap-update-2026-06-24-sub-agent-specs -->

## 2026-06-24 路线同步：本地 SubAgentSpec 已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_specs.py`
- [x] 新增 `SubAgentSpec`
- [x] 定义 Retrieval / Defense Question / Evaluation / Follow-Up / Training Record 子 Agent 规格
- [x] 校验 allowed_tools 是否存在于工具注册表
- [x] 新增 `list-sub-agents` CLI
- [x] 新增 Sub-Agent 规格测试

学到的关键点：

```text
Sub-Agent 不是普通函数。
Sub-Agent 需要声明 role、allowed_tools、input_fields、output_fields 和 max_steps。
先定义边界，再做调度，能避免多 Agent 系统变成不可控的黑箱。
```

下一步学习：

- 做本地 Sub-Agent 权限校验器。
- 验证某个 Sub-Agent 是否允许调用某个工具。
- 暂时仍不做真实多 Agent 调度。

<!-- roadmap-update-2026-06-24-sub-agent-permission-guard -->

## 2026-06-24 路线同步：本地 Sub-Agent 工具权限校验已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_permissions.py`
- [x] 新增子 Agent 工具权限检查结果模型
- [x] 支持判断某个子 Agent 是否允许调用某个工具
- [x] 支持权限失败时抛出明确错误
- [x] 新增 `check-sub-agent-tool` CLI
- [x] 新增子 Agent 权限测试

学到的关键点：

```text
工具级治理管工具本身。
子 Agent 级治理管某个 Agent 能不能用某个工具。
这两层权限要叠加，不能互相替代。
```

下一步学习：

- 做本地 Sub-Agent 执行计划对象，但仍不真正执行工具。
- 目标是学习多 Agent 调度前的 planning 数据结构。

<!-- roadmap-update-2026-06-24-sub-agent-execution-plan -->

## 2026-06-24 路线同步：本地 Sub-Agent 执行计划对象已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_plan.py`
- [x] 新增 `SubAgentExecutionPlan`
- [x] 支持校验子 Agent 输入字段
- [x] 支持校验子 Agent 工具权限
- [x] 支持生成 planned 状态的执行计划
- [x] 新增 `plan-sub-agent-call` CLI
- [x] 新增执行计划测试

学到的关键点：

```text
Sub-Agent 调度不能直接从“想调用工具”跳到“执行工具”。
中间应该有一个可审计的计划对象。
计划对象让后续 trace、权限审计、预算控制和人工复核都有稳定载体。
```

下一步学习：

- 做本地 Sub-Agent plan trace / audit 记录。
- 或开始实现单步 Sub-Agent dry-run，不执行真实工具，只返回计划审计报告。

<!-- roadmap-update-2026-06-24-sub-agent-plan-powershell-arguments -->

## 2026-06-24 路线同步：Sub-Agent Plan CLI 参数体验已优化

本阶段补充完成能力：

- [x] `plan-sub-agent-call` 保留 `--arguments JSON`
- [x] 新增 `--argument KEY=VALUE`
- [x] 支持多次传入 `--argument`
- [x] 避免 PowerShell 中 JSON 双引号被吞导致解析失败

学到的关键点：

```text
CLI 设计要考虑用户所在 shell 的参数解析规则。
Windows PowerShell 对内联 JSON 不友好时，可以提供 KEY=VALUE 作为工程上更稳的输入形式。
```

<!-- roadmap-update-2026-06-24-sub-agent-plan-trace -->

## 2026-06-24 路线同步：Sub-Agent Plan Trace / Audit 已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_plan_trace.py`
- [x] 支持把 Sub-Agent 执行计划保存为 JSONL
- [x] 支持读取 Sub-Agent plan trace
- [x] 支持按 sub_agent / tool 汇总 trace
- [x] `plan-sub-agent-call` 支持 `--save-trace`
- [x] 新增 `analyze-sub-agent-plans` CLI
- [x] 新增 Sub-Agent plan trace 测试

学到的关键点：

```text
计划也是需要审计的对象。
多 Agent 系统不只要记录执行结果，还要记录执行前的计划。
这能支撑后续权限审计、trace replay、回归对比和人工复核。
```

下一步学习：

- 做单步 Sub-Agent dry-run。
- dry-run 只校验计划和生成审计报告，不执行真实工具。

<!-- roadmap-update-2026-06-24-sub-agent-dry-run -->

## 2026-06-24 路线同步：单步 Sub-Agent Dry-Run 已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_dry_run.py`
- [x] 新增 `SubAgentDryRunReport`
- [x] 支持生成 Sub-Agent 执行计划
- [x] 支持执行前权限校验
- [x] 支持可选保存 dry-run plan trace
- [x] 新增 `dry-run-sub-agent-call` CLI
- [x] 新增 Sub-Agent dry-run 测试

学到的关键点：

```text
dry-run 是真实执行前的安全演练。
它不会调用真实工具，也不会让 Sub-Agent 产生外部副作用。
它只把“计划、权限、参数、审计记录”提前跑通，方便后续做人工复核、trace replay 和回归对比。
```

下一步学习：

- 做 Sub-Agent dry-run report replay / comparison。
- 或实现最小真实 Sub-Agent executor，但限制为单工具、单步执行。
- 不进入复杂多 Agent 自动协作，也不替换现有手写 Agent Harness。

<!-- roadmap-update-2026-06-24-sub-agent-plan-comparison -->

## 2026-06-24 路线同步：Sub-Agent Plan Replay / Comparison 已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_plan_comparator.py`
- [x] 支持对比 baseline / candidate 两份 plan trace
- [x] 支持检测新增计划
- [x] 支持检测删除计划
- [x] 支持检测稳定字段变化
- [x] 新增 `compare-sub-agent-plans` CLI
- [x] 新增 Sub-Agent plan comparison 测试

学到的关键点：

```text
多 Agent 系统的回归测试不应该只看最终答案。
执行前的计划也需要被比较。
如果同样的 Sub-Agent、工具和参数突然生成了不同 max_steps、输出字段或状态，就说明调度层稳定性可能退化。
```

当前比较边界：

```text
忽略 plan_id 和 created_at。
它们是运行时生成字段，不适合用于稳定性判断。
当前只比较计划身份和关键稳定字段。
```

下一步学习：

- 实现最小真实 Sub-Agent executor。
- 仍然只允许单 Sub-Agent、单工具、单步执行。
- 执行前必须复用 permission guard 和 execution plan。

<!-- roadmap-update-2026-06-24-sub-agent-single-step-executor -->

## 2026-06-24 路线同步：最小真实 Sub-Agent Executor 已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_executor.py`
- [x] 新增 `app/sub_agent_execution_trace.py`
- [x] 支持单 Sub-Agent 单工具执行
- [x] 执行前复用 permission guard
- [x] 执行前复用 execution plan
- [x] 执行过程复用统一 tool executor
- [x] 支持保存 Sub-Agent execution trace
- [x] 新增 `execute-sub-agent-call` CLI
- [x] 新增 `analyze-sub-agent-executions` CLI
- [x] 新增 Sub-Agent executor 测试

学到的关键点：

```text
真正执行 Sub-Agent 时，不能绕过已有治理层。
执行必须经过：SubAgentSpec -> permission guard -> execution plan -> tool executor -> execution trace。
这条链路保证了角色边界、工具权限、输入参数、执行结果和审计记录都可检查。
```

当前边界：

```text
这不是复杂多 Agent 协作。
它只是一个最小单步执行器。
目的是学习企业级 Agent Harness 中“执行前有计划、执行中有治理、执行后有审计”的基本闭环。
```

下一步学习：

- 做 Sub-Agent execution replay / comparison。
- 对比两次执行 trace 的成功率、工具结果结构、耗时和错误类型。
- 暂不做并行 Sub-Agent，也不做自动任务分解。

<!-- roadmap-update-2026-06-25-sub-agent-execution-comparison -->

## 2026-06-25 路线同步：Sub-Agent Execution Replay / Comparison 已完成

本阶段新增完成能力：

- [x] 新增 `app/sub_agent_execution_comparator.py`
- [x] 支持对比 baseline / candidate 两份 execution trace
- [x] 支持检测新增执行记录
- [x] 支持检测删除执行记录
- [x] 支持检测 success 翻转
- [x] 支持检测 result JSON 结构变化
- [x] 支持检测 error_type 变化
- [x] 支持检测 duration 退化
- [x] 新增 `compare-sub-agent-executions` CLI
- [x] 新增 Sub-Agent execution comparison 测试

学到的关键点：

```text
计划稳定不等于执行稳定。
Sub-Agent 的执行结果还需要从成功率、错误类型、输出结构和耗时四个维度做回归检测。
这一步把 Sub-Agent 从“能执行”推进到“执行结果可审计、可回放、可比较”。
```

下一步学习：

- 做 Sub-Agent execution quality gate。
- 将 execution comparison 的 passed/failed 接入 CLI 退出码。
- 为 CI 或本地质量门禁预留接口。

<!-- roadmap-update-2026-06-25-sub-agent-execution-quality-gate -->

## 2026-06-25 路线同步：Sub-Agent Execution Quality Gate 已完成

本阶段新增完成能力：

- [x] `compare-sub-agent-executions` 默认作为质量门禁
- [x] `PASSED: True` 时命令退出码为 0
- [x] `PASSED: False` 时命令退出码为 1
- [x] 新增 `--allow-fail` 观察模式
- [x] 新增 CLI 门禁测试

学到的关键点：

```text
评估报告本身不是质量门禁。
只有当报告结果能影响进程退出码时，它才可以进入 CI、脚本和自动化回归流程。
```

下一步学习：

- 将 Sub-Agent execution quality gate 接入本地 quality gate 脚本。
- 暂不接 GitHub Actions，先保留本地可执行质量门禁。

<!-- roadmap-update-2026-06-25-local-quality-gate-sub-agent -->

## 2026-06-25 路线同步：本地 Quality Gate 接入 Sub-Agent Execution 已完成

本阶段新增完成能力：

- [x] 新增 `app/local_quality_gate.py`
- [x] 新增 `local-quality-gate` CLI
- [x] 默认支持本地 pytest 检查
- [x] 可选接入 Sub-Agent execution comparison
- [x] 任一检查失败时返回非 0 退出码
- [x] 支持 `--allow-fail` 观察模式
- [x] 新增本地 quality gate 测试

学到的关键点：

```text
单个质量检查只是局部能力。
本地 quality gate 是统一入口，用来把 pytest、评估回归、Sub-Agent execution comparison 等检查组合起来。
统一入口的价值是：开发者和 CI 都能复用同一套门禁语义。
```

当前边界：

```text
暂不修改 GitHub Actions。
暂不自动生成 Sub-Agent baseline/candidate trace。
暂不把在线 LLM 评估放进本地默认门禁。
```

下一步学习：

- 做 Sub-Agent execution baseline/candidate fixture。
- 让本地 quality gate 可以在离线环境中稳定跑 Sub-Agent execution comparison。

<!-- roadmap-update-2026-06-25-sub-agent-execution-fixtures -->

## 2026-06-25 路线同步：Sub-Agent Execution 离线 Fixture 已完成

本阶段新增完成能力：

- [x] 新增 `tests/fixtures/sub_agent_execution/baseline.jsonl`
- [x] 新增 `tests/fixtures/sub_agent_execution/candidate.jsonl`
- [x] 本地 quality gate 可使用 fixture 跑 Sub-Agent execution comparison
- [x] 不依赖真实工具执行
- [x] 不依赖在线 API
- [x] 新增 fixture 回归测试

学到的关键点：

```text
质量门禁不能依赖每次现场生成样本。
稳定 fixture 是离线回归测试的基础。
有了 baseline/candidate fixture，Sub-Agent execution comparison 才能稳定进入本地检查和后续 CI。
```

下一步学习：

- 将本地 quality gate 接入 CI。
- 只接入离线 fixture，不接入真实工具执行。

<!-- roadmap-update-2026-06-25-ci-local-quality-gate -->

## 2026-06-25 路线同步：CI 接入本地 Quality Gate 已完成

本阶段新增完成能力：

- [x] `.github/workflows/ci.yml` 接入 `local-quality-gate`
- [x] CI 使用 Sub-Agent execution baseline/candidate fixture
- [x] CI 不执行真实 Sub-Agent 工具
- [x] CI 不调用在线 API
- [x] `online-evaluation.yml` 保持不变

学到的关键点：

```text
CI 中只能放稳定、可重复、无外部依赖的质量门禁。
Sub-Agent execution comparison 通过离线 fixture 接入 CI，避免了真实工具、RAG API 或 LLM API 带来的不稳定性。
```

下一步学习：

- 进入 Sub-Agent 执行报告归档。
- 将 comparison/gate 输出保存到 data/reports，方便 CI artifact 查看。

<!-- roadmap-update-2026-06-25-sub-agent-gate-report-artifact -->

## 2026-06-25 路线同步：Sub-Agent Gate 报告归档已完成

本阶段新增完成能力：

- [x] `local-quality-gate` 支持 `--output`
- [x] 新增 JSON 报告保存能力
- [x] CI 将 Sub-Agent execution gate 报告写入 `data/reports/sub_agent_execution_gate.json`
- [x] CI artifact 会上传该报告
- [x] 新增报告保存测试

学到的关键点：

```text
质量门禁不只要通过或失败，还要留下可检查的结构化证据。
CI artifact 是排查质量门禁失败的入口，报告归档能减少只看日志定位问题的成本。
```

下一步学习：

- 做 Sub-Agent gate Markdown 报告。
- 让 artifact 同时包含机器可读 JSON 和人类可读 Markdown。

<!-- roadmap-update-2026-06-25-sub-agent-gate-markdown-report -->

## 2026-06-25 路线同步：Sub-Agent Gate Markdown 报告已完成

本阶段新增完成能力：

- [x] `local-quality-gate` 支持 `--markdown-output`
- [x] 新增 Markdown 报告渲染能力
- [x] CI 将 Markdown 报告写入 `data/reports/sub_agent_execution_gate.md`
- [x] CI artifact 同时包含 JSON 和 Markdown
- [x] 新增 Markdown 报告测试

学到的关键点：

```text
JSON 适合机器读取，Markdown 适合人查看。
CI artifact 同时保存两种格式，可以兼顾自动化回归和人工排查。
```

下一步学习：

- Sub-Agent 主线阶段性收尾。
- 汇总当前 Sub-Agent Harness 能力边界，并决定是否进入 Memory 或 Trace Replay 下一阶段。

<!-- roadmap-update-2026-06-25-sub-agent-phase-summary -->

## 2026-06-25 路线同步：Sub-Agent 主线阶段性收尾已完成

本阶段新增完成能力：

- [x] 新增 `docs/07-Sub-Agent阶段复盘.md`
- [x] 汇总 Sub-Agent Harness 已完成能力
- [x] 明确当前 Sub-Agent 边界
- [x] 明确后续未完成能力
- [x] 明确下一阶段建议

阶段结论：

```text
Sub-Agent 主线已经形成最小可审计 Harness：
Spec -> Permission -> Plan -> Dry-Run -> Execute -> Trace -> Comparison -> Quality Gate -> CI Artifact
```

当前暂不推进：

- 复杂多 Agent 协作
- 并行 Sub-Agent
- 自动任务拆解
- LangGraph 覆盖式重构
- 服务器部署

下一阶段学习：

- 进入 Trace Replay / Feedback 闭环。
- 暂不继续扩展复杂多 Agent 协作。
- 暂不进入服务器部署。

边界说明：

```text
LangGraph 后续只做旁路迁移，不覆盖现有手写 Agent Harness。
FastAPI、静态 Web 前端、stdio MCP Server、stdio MCP Client、MCP resource / prompt 能力、Dockerfile、docker-compose、Prometheus、Alertmanager 本机路由、外部通知路由本地可审计版本、K8s 基础 manifests、生产化基础字段、smoke test 计划 CLI 与执行记录模板 CLI、本机 PostgreSQL runtime smoke、Qdrant 最小后端、Vector DB 生产化治理报告、Qdrant backup retention policy CLI、Qdrant snapshot API runner 和 Windows Task Scheduler 本机实验已完成。
K8s 真实集群 smoke test 执行、cron / Kubernetes CronJob 调度证据、Qdrant 长期运行验证、Milvus backup / restore SOP、私有化部署、服务器长期运行和真实 Feishu / WeCom / email 通知提供方继续作为后续阶段。
```

<!-- roadmap-update-2026-06-25-trace-replay-feedback -->

## 2026-06-25 路线同步：Trace Replay / Feedback 闭环已完成

本阶段新增完成能力：

- [x] 通用 trace replay 归一化
- [x] 支持 Agent trace replay summary
- [x] 支持 Sub-Agent plan trace replay summary
- [x] 支持 Sub-Agent execution trace replay summary
- [x] trace replay issue 自动生成 feedback record
- [x] `replay-trace` CLI
- [x] `trace-feedback` CLI
- [x] `trace-feedback -> export-feedback-candidates` 端到端测试
- [x] `trace -> feedback -> candidate -> review -> draft -> validate -> export` 完整闭环测试

阶段链路：

```text
失败 trace
-> replay summary
-> feedback record
-> benchmark candidate
-> human review
-> benchmark draft
-> draft validation
-> validated benchmark draft export
```

学到的关键点：

```text
Agent 失败不能只停留在日志里。
失败 trace 要能转成 feedback。
feedback 不能直接进 benchmark，必须经过 candidate 和人工 review。
review accepted 后还只是 draft，必须补全字段并通过 validation。
只有 validated draft 才能进入正式回归评估资产。
```

当前边界：

- 不自动把失败 trace 写入正式 benchmark
- 不绕过人工 review
- 不自动猜测 benchmark 字段
- 不接数据库
- 不接服务器部署

下一步学习：

- 做 Trace Replay / Feedback 阶段复盘文档。
- 然后进入 Memory 阶段，做本地长期记忆的写入、检索、摘要和遗忘策略。

<!-- roadmap-update-2026-06-25-task-memory-export -->

## 2026-06-25 路线同步：Task Summary Memory Export 已完成

本阶段新增完成能力：

- [x] 从已完成 `DefenseTask` 提取 `summarize_training` 输出
- [x] 将训练总结写入 `training_summaries`
- [x] 将薄弱点写入 `weaknesses`
- [x] 新增 `export-task-memory` CLI
- [x] 保持显式导出，不在任务完成时自动污染长期记忆

阶段链路：

```text
completed task
-> summarize_training output
-> summary / weaknesses
-> long_term_memory.json
-> chat / Agent memory injection
```

学到的关键点：

```text
长期记忆不是日志。
不是所有任务输出都应该自动记住。
训练任务完成后，需要由用户显式确认再沉淀进 memory。
这样可以降低低质量总结、临时错误、调试样本污染长期上下文的风险。
```

当前 Memory 已完成：

- [x] Profile Memory
- [x] Weakness Memory
- [x] Training Summary Memory
- [x] Memory Retrieval
- [x] Memory Pruning
- [x] Chat Memory Injection
- [x] Task Summary Memory Export

下一步学习：

- 做 Memory 阶段复盘文档。
- 然后进入 Memory 质量治理：重复记忆检测、记忆压缩摘要、记忆命中审计。

<!-- roadmap-update-2026-06-25-memory-phase-summary -->

## 2026-06-25 路线同步：Memory 阶段复盘已完成

本阶段新增完成能力：

- [x] 新增 `docs/08-Memory阶段复盘.md`
- [x] 汇总 Profile Memory
- [x] 汇总 Weakness Memory
- [x] 汇总 Training Summary Memory
- [x] 汇总 Memory Retrieval
- [x] 汇总 Memory Pruning
- [x] 汇总 Chat Memory Injection
- [x] 汇总 Task Summary Memory Export

阶段结论：

```text
Memory 不是聊天历史，也不是日志。
Memory 是跨任务保留的长期上下文资产。
它必须可控写入、可检索、可裁剪、可审计。
```

下一步学习：

```text
Memory 质量治理
```

短期顺序：

- memory-audit
- duplicate report
- dry-run prune
- hit audit
- context report

暂不进入：

- 数据库 Memory
- 向量化 Memory
- 多用户 Memory
- 服务器部署

<!-- roadmap-update-2026-06-25-memory-quality-governance -->

## 2026-06-25 路线同步：Memory 质量治理已完成

本阶段新增完成能力：

- [x] `memory-audit`
- [x] duplicate weakness / summary 检测
- [x] empty profile / weakness / summary 检测
- [x] `memory-prune --dry-run`
- [x] `memory-hit-audit`
- [x] `memory-context-report`
- [x] Memory 相关 CLI 测试
- [x] 全量测试通过

阶段链路：

```text
long_term_memory.json
-> memory-audit
-> memory-prune --dry-run
-> memory-hit-audit
-> memory-context-report
```

学到的关键点：

```text
Memory 质量治理必须先只读审计，再预览修改，最后才允许写入。
长期记忆注入前必须能解释命中了哪些记忆，以及最终注入了什么上下文。
```

当前 Memory 主线已完成：

- [x] 写入
- [x] 检索
- [x] 注入
- [x] 裁剪
- [x] 任务总结沉淀
- [x] 质量审计
- [x] dry-run
- [x] 命中审计
- [x] context report

下一步学习：

- 将 `feat/memory-audit` 推送并合并。
- 合并后进入 LangGraph 旁路迁移前整理，保留现有手写 Agent Harness 作为学习对照。

<!-- roadmap-update-2026-06-26-langgraph-phase-summary -->

## 2026-06-26 路线同步：LangGraph 旁路迁移阶段已完成

本阶段新增完成能力：

- [x] `demo_task`：基础 StateGraph
- [x] `interrupt_demo`：人工输入中断
- [x] `checkpointer_demo`：checkpoint 状态检查
- [x] `persistent_checkpoint_demo`：checkpoint 快照保存
- [x] `conditional_demo`：条件路由
- [x] `evaluate_rewrite_demo`：评价与改写节点
- [x] `follow_up_demo`：追问链路与第二次 interrupt
- [x] `summary_demo`：完整训练总结节点
- [x] `parity_report`：LangGraph 与 Task Workflow Contract 对照
- [x] 新增 `docs/11-LangGraph阶段复盘.md`

阶段链路：

```text
Task Workflow Contract
-> LangGraph sidecar demos
-> interrupt / checkpoint / conditional routing
-> evaluate / rewrite / follow-up / summary
-> parity report
```

学到的关键点：

```text
LangGraph 是编排层，不是业务逻辑替代品。
旁路迁移比覆盖式重构更适合学习和验证。
迁移完成标准不是“能跑”，而是通过 parity report 证明与原工作流契约等价。
```

暂不进入：

- 覆盖替换 `app/task_*`
- 数据库 checkpoint
- 服务端部署
- Web UI

下一步学习：

```text
LangGraph 阶段收尾后，进入 Agent Harness 稳定性治理复盘：
工具超时、重试、结果长度限制、错误标准化、Sub-Agent 权限和执行审计。
```

<!-- roadmap-update-2026-06-26-agent-harness-stability-review -->

## 2026-06-26 路线同步：Agent Harness 稳定性治理复盘已完成

本阶段新增完成文档：

```text
docs/12-Agent-Harness稳定性治理复盘.md
```

已复盘能力：

- [x] 工具注册表
- [x] 工具白名单
- [x] 工具权限 metadata
- [x] 工具结果长度限制
- [x] 工具有限重试
- [x] 工具超时
- [x] 标准化错误返回
- [x] 工具调用 trace 审计

对应代码位置：

```text
app/tool_registry.py
app/tool_executor.py
app/agent.py
app/agent_models.py
```

阶段结论：

```text
Agent Harness 的核心不是能调用工具，而是能治理工具。
工具治理必须覆盖权限、失败、耗时、输出长度和审计记录。
```

下一步学习：

```text
Sub-Agent 权限边界和 dry-run 执行策略复盘：
明确计划生成、执行审批、权限边界、trace 记录和工具审计。
```

<!-- roadmap-update-2026-06-26-sub-agent-permission-review -->

## 2026-06-26 路线同步：Sub-Agent 权限与 Dry-Run 复盘已完成

本阶段新增完成文档：

```text
docs/13-Sub-Agent权限与Dry-Run复盘.md
```

已复盘能力：

- [x] Sub-Agent spec
- [x] allowed_tools 权限边界
- [x] input_fields / output_fields 契约
- [x] max_steps 边界
- [x] plan-first 执行策略
- [x] dry-run 预演
- [x] plan trace
- [x] execution trace
- [x] plan comparator
- [x] execution comparator

对应代码位置：

```text
app/sub_agent_specs.py
app/sub_agent_permissions.py
app/sub_agent_plan.py
app/sub_agent_dry_run.py
app/sub_agent_executor.py
app/sub_agent_plan_trace.py
app/sub_agent_execution_trace.py
app/sub_agent_plan_comparator.py
app/sub_agent_execution_comparator.py
```

阶段结论：

```text
Sub-Agent 的重点不是多一个 Agent，而是把角色、工具、输入输出和执行边界显式化。
dry-run 是执行前的安全闸门。
plan trace 审计计划，execution trace 审计真实执行。
```

下一步学习：

```text
Trace 回放与工具审计深化：
把 Agent trace、Sub-Agent plan trace 和 execution trace 串成更清晰的审计报告。
```

<!-- roadmap-update-2026-06-26-trace-audit-review -->

## 2026-06-26 路线同步：Trace 回放与工具审计复盘已完成

本阶段新增完成文档：

```text
docs/14-Trace回放与工具审计复盘.md
```

已复盘能力：

- [x] Agent trace
- [x] Task trace
- [x] Sub-Agent plan trace
- [x] Sub-Agent execution trace
- [x] Agent trace replay
- [x] Generic trace replay
- [x] Agent trace comparison
- [x] Sub-Agent plan comparison
- [x] Sub-Agent execution comparison
- [x] Trace feedback

对应代码位置：

```text
app/agent_trace_logger.py
app/agent_trace_analyzer.py
app/agent_trace_replayer.py
app/trace_replay.py
app/trace_feedback.py
app/task_trace_analyzer.py
app/sub_agent_plan_trace.py
app/sub_agent_execution_trace.py
app/sub_agent_plan_comparator.py
app/sub_agent_execution_comparator.py
```

阶段结论：

```text
Trace 是 Agent 工程化的事实来源。
Replay 解决可读性问题。
Comparison 解决回归检测问题。
Feedback 解决数据闭环问题。
Audit 解决风险识别问题。
```

下一步学习：

```text
Memory 污染治理复盘：
长期记忆写入、检索、注入、审计、裁剪和上下文压缩的风险边界。
```

<!-- roadmap-update-2026-06-26-memory-contamination-review -->

## 2026-06-26 路线同步：Memory 污染治理复盘已完成

本阶段新增完成文档：

```text
docs/15-Memory污染治理复盘.md
```

已复盘能力：

- [x] 长期记忆结构校验
- [x] profile 写入
- [x] weakness 写入
- [x] training summary 写入
- [x] 记忆去重
- [x] 记忆裁剪
- [x] `memory-prune --dry-run`
- [x] `memory-audit`
- [x] `memory-hit-audit`
- [x] `memory-context-report`
- [x] `--disable-memory`
- [x] `--disable-session-compaction`
- [x] session summary compaction

对应代码位置：

```text
app/long_term_memory.py
app/memory_auditor.py
app/conversation_memory.py
app/session_compactor.py
app/task_memory_exporter.py
```

阶段结论：

```text
Memory 的难点不是写入，而是防止污染。
长期记忆必须可审计、可预览、可裁剪、可禁用。
注入 prompt 前必须能回答：为什么这条记忆会被选中？
```

下一步学习：

```text
MCP 工具协议对照学习：
将当前本地 Tool Registry、Sub-Agent 权限和工具审计能力映射到 MCP 的工具发现、授权、调用和审计模型。
```

<!-- roadmap-update-2026-06-26-mcp-tool-protocol-review -->

## 2026-06-26 路线同步：MCP 工具协议对照学习已完成

本阶段新增完成文档：

```text
docs/16-MCP工具协议对照学习.md
```

已复盘映射：

- [x] Host
- [x] Client
- [x] Server
- [x] Tool
- [x] Tool Schema
- [x] Tool Metadata
- [x] Tool Invocation
- [x] Resource
- [x] Prompt
- [x] Audit
- [x] Permission
- [x] Sub-Agent allowed tools

对应代码位置：

```text
app/cli.py
app/agent.py
app/task_service.py
app/tools/
app/tool_registry.py
app/tool_executor.py
app/sub_agent_specs.py
app/sub_agent_permissions.py
app/*trace*.py
```

阶段结论：

```text
MCP 不是替代 Agent Harness，而是外部工具协议。
本地 Tool Registry 是接 MCP 前的治理基座。
远程工具必须先转换成本地可治理对象，再进入 Agent Loop。
```

下一步学习：

```text
项目阶段总复盘：
汇总本机学习版 Agent Harness 已完成能力、未完成边界、可展示命令、简历表达和服务器阶段学习计划。
```

<!-- roadmap-update-2026-06-26-local-agent-harness-phase-summary -->

## 2026-06-26 路线同步：本机学习版阶段总复盘已完成

本阶段新增完成文档：

```text
docs/17-本机学习版阶段总复盘.md
```

本机学习版已完成主线：

- [x] LLM 与 Prompt
- [x] RAG
- [x] Tool Calling 与 Agent Harness
- [x] Session 与 Memory
- [x] DefenseTask 可恢复任务流
- [x] Evaluation 与 Quality Gate
- [x] Trace 与 Feedback
- [x] Sub-Agent 本地学习版
- [x] LangGraph 旁路迁移
- [x] MCP 工具协议对照
- [x] 文档化复盘

阶段结论：

```text
本机学习版阶段已经完成。
后续不再继续堆本地功能。
下一阶段重点转向服务器化、真实服务接口、数据库、部署和真实 MCP 接入。
```

服务器笔记本阶段建议顺序：

```text
1. K8s 真实集群 smoke test 执行 / 生产化部署验证
2. cron / Kubernetes CronJob 调度证据和 Qdrant 长期运行验证
3. MilvusVectorStoreRepository / Milvus runtime benchmark
4. 服务器长期运行验证
5. 真实 Feishu / WeCom / email 通知提供方
6. 权限审批和 workspace 隔离
```

<!-- roadmap-update-2026-06-26-fastapi-docker-prometheus -->

## 2026-06-26 路线同步：FastAPI / Docker / Prometheus 本机验证已完成

本阶段已完成服务化与本机部署验证：

```text
FastAPI API
-> RAG Search API
-> DefenseTask API
-> Task answer / follow-up answer API
-> Task analysis / Markdown report API
-> request logging
-> JSON metrics
-> Prometheus text metrics
-> Dockerfile
-> docker-compose
-> Prometheus compose service
-> Docker build CI
-> GHCR image publish workflow
-> server runtime guide
```

已完成接口：

```text
GET  /health
GET  /version
GET  /metrics
GET  /metrics/prometheus
GET  /rag/status
POST /rag/search
POST /tasks
GET  /tasks/{task_id}
POST /tasks/{task_id}/steps/start
POST /tasks/{task_id}/steps/execute
POST /tasks/{task_id}/answer
POST /tasks/{task_id}/follow-up-answer
GET  /tasks/{task_id}/analysis
POST /tasks/{task_id}/report/export
```

已完成部署能力：

```text
Dockerfile
docker-compose.yml
observability/prometheus/prometheus.yml
docs/deployment/local-fastapi.md
docs/deployment/docker.md
docs/deployment/docker-ci.md
docs/deployment/server.md
```

当前边界：

```text
PostgreSQL repository、runtime integration 和本机 smoke test 已完成；默认后端仍是 json。
Qdrant 已有本地最小实现、benchmark 对比、backup / restore SOP 和生产化治理报告；Milvus 已完成本机 runtime benchmark，尚未做 Milvus backup / restore SOP。
Prometheus 告警规则已完成；Alertmanager 本机路由已完成；外部通知路由本地可审计版本已完成；K8s 基础 manifests、生产化基础字段、smoke test 计划 CLI 与执行记录模板 CLI 已完成；静态 Web 前端已完成；stdio MCP Server 已完成；stdio MCP Client 已完成；MCP resource / prompt 能力已完成；日志保留与查询文档已完成；API request Correlation ID 已完成；request -> task -> tool call 全链路 Correlation ID 已完成。
尚未提供真实 Feishu / WeCom / email 通知提供方。
K8s 真实集群 smoke test 执行和生产化部署验证已在本机 kind 集群完成。
```

下一阶段建议顺序：

```text
1. K8s 真实集群 smoke test 执行 / 生产化部署验证
2. cron / Kubernetes CronJob 调度证据和 Qdrant 长期运行验证
3. Milvus backup / restore SOP
4. 服务器长期运行验证
5. 真实 Feishu / WeCom / email 通知提供方
```

<!-- roadmap-update-2026-06-30-web-frontend-enhancements -->

## 2026-06-30 路线同步：Web 前端增强已完成

本阶段在已有 FastAPI 静态页面基础上补齐本机学习版操作面板。

已完成：

- [x] 文件上传 UI，对接 `POST /documents/upload`
- [x] SSE 输出测试面板，对接 `GET /stream/echo`
- [x] WebSocket 连接状态，对接 `/ws/tasks/{task_id}`
- [x] Trace 指标卡片：工具调用、成功调用、token、cost
- [x] 可点击步骤列表，查看单步详情
- [x] Markdown 报告导出后支持浏览器下载
- [x] `tests/test_api_frontend.py` 覆盖新增入口

当前边界：

```text
仍是静态 HTML/CSS/JS 学习版。
不引入 React/Vite。
不做登录鉴权。
不做图形化 trace 拓扑。
不做复杂前端状态管理。
```

下一步学习：

```text
K8s 生产化部署基础：
namespace / configmap / secret 模板
readiness / liveness
resource requests / limits
rollout / rollback SOP
```

<!-- roadmap-update-2026-06-30-k8s-production-basics -->

## 2026-06-30 路线同步：K8s 生产化基础字段已完成

本阶段在已有 `k8s/base` manifests 上补齐生产化基础字段，不做真实集群长期运行。

已完成：

- [x] API / Prometheus / Alertmanager Deployment 增加 `revisionHistoryLimit`
- [x] API / Prometheus / Alertmanager Deployment 增加 `progressDeadlineSeconds`
- [x] API / Prometheus / Alertmanager Deployment 增加 RollingUpdate 策略
- [x] API / Prometheus / Alertmanager 保留 readiness / liveness probe
- [x] API / Prometheus / Alertmanager 保留 resource requests / limits
- [x] API / Prometheus / Alertmanager 增加 restricted securityContext
- [x] API / Prometheus / Alertmanager 增加 PodDisruptionBudget
- [x] `docs/deployment/k8s.md` 增加 rollout / rollback SOP
- [x] `tests/test_k8s_manifests.py` 覆盖新增字段
- [x] `k8s-smoke-plan` CLI 生成真实集群验证步骤
- [x] `k8s-smoke-report-template` CLI 生成真实集群执行记录模板
- [x] `tests/test_k8s_smoke_plan.py` 与 `tests/test_k8s_smoke_cli.py` 覆盖计划和模板生成

当前边界：

```text
这是静态 manifest 生产化基础学习。
已提供 smoke test 计划生成和执行记录模板，但尚未做真实集群 apply / rollout status / rollback 验证。
尚未做 Ingress、TLS、HPA、NetworkPolicy、PVC、Helm chart。
API 仍保持 replicas=1，因为默认 JSON / emptyDir 后端不适合多副本共享状态。
```

下一步学习：

```text
如果继续 K8s：执行真实集群 smoke test，并将脱敏输出写入验证记录模板。
如果暂不接服务器：继续 cron / Kubernetes CronJob 调度证据，或进入 Milvus runtime benchmark。
```

<!-- roadmap-update-2026-06-30-vector-db-governance -->

## 2026-06-30 路线同步：Vector DB 生产化治理报告已完成

本阶段没有直接引入 Milvus runtime，也没有把默认向量库后端从 JSON 切到 Qdrant。
本阶段目标是先把生产化上线标准固化下来。

已完成：

- [x] `app/vector_db_governance.py`
- [x] `vector-db-governance-report` CLI
- [x] JSON / Qdrant / Milvus 角色划分
- [x] Qdrant promotion gates
- [x] Milvus 作为后续对比候选的边界说明
- [x] `tests/test_vector_db_governance.py`
- [x] `docs/deployment/qdrant.md` 更新生产化治理报告命令

当前边界：

```text
JSON 仍是默认向量库后端。
Qdrant 是当前项目主生产候选，已完成本地备份保留策略和手动 snapshot API runner，尚未做定时 snapshot / restore drill 自动调度。
Milvus 只作为未来对比候选，尚未实现 MilvusVectorStoreRepository。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 自动调度
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-async-task-api -->

## 2026-07-01 路线同步：AsyncTaskRunner FastAPI API 已完成

本阶段完成的是把内存型 `AsyncTaskRunner` 暴露为 FastAPI 后台任务 API，用于学习 HTTP 层如何创建、查询和取消长任务。

已完成：

- [x] `app/api/routes/async_tasks.py`
- [x] `POST /async-tasks`
- [x] `GET /async-tasks/{task_id}`
- [x] `DELETE /async-tasks/{task_id}`
- [x] demo sleep job
- [x] 依赖注入覆盖测试
- [x] `tests/test_api_async_tasks.py`

当前边界：

```text
当前只接入 fake long-running job。
任务状态保存在进程内存中，进程重启后会丢失。
尚未接入真实 DefenseTask 步骤执行。
尚未实现幂等请求和持久化恢复。
```

下一步学习：

```text
1. AsyncTaskRunner 并发限制
2. 异步 DefenseTask step execution API
3. 异步 LLM / 工具调用边界
```

<!-- roadmap-update-2026-07-01-async-task-concurrency-limit -->

## 2026-07-01 路线同步：AsyncTaskRunner 并发限制已完成

本阶段给内存型后台任务 runner 增加并发上限，避免 API 层无限创建运行中任务。

已完成：

- [x] `AsyncTaskRunner(max_concurrent_tasks=...)`
- [x] `asyncio.Semaphore` 控制同时运行任务数
- [x] 超出上限的任务保持 `pending`
- [x] 排队任务可取消并落到 `cancelled`
- [x] `ASYNC_TASK_MAX_CONCURRENT_TASKS` 环境变量
- [x] FastAPI 全局 runner 使用默认并发上限
- [x] 单元测试覆盖非法上限、排队、排队取消

当前边界：

```text
并发限制只作用于单进程内存型 AsyncTaskRunner。
多进程部署时，每个进程都有自己的 runner 和并发上限。
任务状态仍未持久化，进程重启会丢失。
尚未接入真实 DefenseTask 步骤执行。
```

下一步学习：

```text
1. 异步 DefenseTask step execution API
2. 异步 LLM / 工具调用边界
3. 幂等请求和后台任务持久化恢复
```

<!-- roadmap-update-2026-07-01-async-defense-task-step-api -->

## 2026-07-01 路线同步：异步 DefenseTask Step Execution API 已完成

本阶段把后台任务 API 从 demo sleep job 推进到真实 `DefenseTask` 当前步骤执行。

已完成：

- [x] `POST /tasks/{task_id}/steps/execute-async`
- [x] 路由层校验 `task_id` 是否存在
- [x] 后台执行复用 `execute_current_task_step`
- [x] 阻塞同步执行通过 `asyncio.to_thread` 隔离到线程
- [x] 后台任务结果通过 `/async-tasks/{async_task_id}` 查询
- [x] 后台失败记录为 async task `failed`
- [x] API 测试覆盖成功、失败和缺失任务

当前边界：

```text
当前只把现有同步 DefenseTask step execution 放入后台任务。
底层 RAG、LLM 和工具调用仍是同步函数。
后台任务状态仍在进程内存中。
尚未实现幂等请求，重复调用 execute-async 可能创建多个后台任务。
```

下一步学习：

```text
1. 异步 LLM / 工具调用边界
2. 后台任务幂等请求
3. 后台任务持久化恢复
```

<!-- roadmap-update-2026-07-01-async-llm-tool-boundary -->

## 2026-07-01 路线同步：异步 LLM / 工具调用边界已完成

本阶段不是把所有 SDK 替换为原生异步版本，而是先建立清晰的同步阻塞隔离边界。

已完成：

- [x] `app/async_boundary.py`
- [x] `run_sync_in_thread()`
- [x] `async_chat_with_llm()`
- [x] `execute_tool_call_async()`
- [x] `execute_tool_call_safely_async()`
- [x] `execute_task_step_background_job()` 改为复用统一异步边界
- [x] 单元测试覆盖线程隔离、LLM 包装、工具异步执行和安全失败包装

当前边界：

```text
底层 LLM SDK 仍是同步 OpenAI-compatible client。
底层工具函数仍是同步 Python 函数。
当前通过 asyncio.to_thread 隔离阻塞调用，避免阻塞 FastAPI 事件循环。
尚未切换到原生 async LLM SDK 或 async tool registry。
```

下一步学习：

```text
1. 后台任务幂等请求
2. 后台任务持久化恢复
3. 原生异步 LLM / 工具 SDK 调用
```

<!-- roadmap-update-2026-07-01-async-task-idempotency -->

## 2026-07-01 路线同步：后台任务幂等请求已完成

本阶段解决重复点击、HTTP 重试或网络抖动导致同一个 `DefenseTask` 当前步骤被重复创建后台任务的问题。

已完成：

- [x] `AsyncTaskRecord.idempotency_key`
- [x] `AsyncTaskRunner.create_task(..., idempotency_key=...)`
- [x] 同一 `idempotency_key` 返回已有后台任务记录
- [x] `POST /tasks/{task_id}/steps/execute-async` 使用 `task_id + current_step_id` 构造幂等 key
- [x] 同一当前步骤重复 `execute-async` 返回同一个 `async_task_id`
- [x] 测试覆盖 active / finished 幂等任务复用、空 key 拒绝和 API 重复请求

当前边界：

```text
幂等记录在本阶段仍保存在进程内存中。
服务进程重启后，async task 记录和幂等索引在本阶段仍会丢失。
失败任务重复请求也会返回同一个失败记录；显式重试策略后续单独设计。
```

下一步学习：

```text
1. 后台任务持久化恢复
2. 原生异步 LLM / 工具 SDK 调用
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-async-task-persistence -->

## 2026-07-01 路线同步：后台任务持久化状态恢复已完成

本阶段解决 FastAPI 后台任务记录只存在进程内存中的问题。现在后台任务状态会写入本地 JSON 文件，服务进程重启后仍可查询历史任务状态和幂等索引。

已完成：

- [x] `AsyncTaskRunner(storage_path=...)`
- [x] `AsyncTaskRecord.from_dict()`
- [x] 后台任务记录 JSON 落盘
- [x] completed / failed / cancelled 历史任务重启后可查询
- [x] `idempotency_key` 重启后可恢复查询
- [x] pending / running / cancelling 任务重启后恢复为 `failed`
- [x] 中断任务错误类型统一为 `TaskInterruptedError`
- [x] FastAPI 默认 runner 接入 `ASYNC_TASK_STORE_PATH`
- [x] `data/async_tasks/` 加入 `.gitignore`
- [x] 测试覆盖 completed、failed 和 interrupted 恢复语义

当前边界：

```text
恢复的是后台任务记录和审计状态，不恢复重启前正在运行的 coroutine。
本机学习版使用 JSON 文件存储，不是多实例分布式队列。
多进程或多副本部署仍需要 Redis / Postgres / Celery / Arq / Dramatiq 这类队列或任务表设计。
```

下一步学习：

```text
1. 原生异步 LLM / 工具 SDK 调用
2. K8s 真实集群 smoke test 执行 / 生产化部署验证
3. Qdrant cron / Kubernetes CronJob 长期调度证据
```

<!-- roadmap-update-2026-07-01-native-async-llm -->

## 2026-07-01 路线同步：原生异步 LLM SDK 调用已完成

本阶段把 `async_chat_with_llm()` 从 `asyncio.to_thread(chat_with_llm)` 线程隔离包装，升级为直接使用 OpenAI-compatible SDK 的 `AsyncOpenAI`。

已完成：

- [x] `get_async_llm_client()`
- [x] `async_chat_with_llm()` 直接 `await client.chat.completions.create(...)`
- [x] 同步 `chat_with_llm()` 保留，兼容现有同步调用方
- [x] 测试覆盖异步 client 参数传递和返回内容

当前边界：

```text
LLM chat 已使用原生异步 SDK。
stream_chat_with_llm() 仍是同步流式接口。
本阶段工具调用 async 边界仍通过线程隔离同步工具函数，尚未改成原生 async tool function。
```

下一步学习：

```text
1. 原生异步工具 SDK / async tool function 支持
2. K8s 真实集群 smoke test 执行 / 生产化部署验证
3. Qdrant cron / Kubernetes CronJob 长期调度证据
```

<!-- roadmap-update-2026-07-01-async-tool-functions -->

## 2026-07-01 路线同步：async tool function 执行支持已完成

本阶段把工具执行器从“所有工具都通过线程隔离执行”推进到“async 工具直接 await，同步工具继续线程隔离”的混合执行模型。

已完成：

- [x] `execute_tool_function_async_with_timeout()`
- [x] `execute_tool_function_async_with_retry()`
- [x] `execute_tool_call_async()` 可直接 await `async def` 工具函数
- [x] 同步工具在 async 入口中继续通过 `run_sync_in_thread()` 隔离
- [x] 同步 `execute_tool_call()` 明确拒绝 async 工具函数
- [x] async 工具超时使用 `asyncio.wait_for`
- [x] async safe wrapper 保留标准错误 JSON
- [x] 测试覆盖 async 工具成功、超时、错误包装和同步入口保护

当前边界：

```text
工具执行器已支持 async tool function。
现有业务工具是否真正异步，取决于它们内部依赖的 SDK / IO 库是否提供 async API。
没有强制把所有现有工具重写为 async，避免为“异步”而异步。
```

下一步学习：

```text
1. K8s 真实集群 smoke test 执行 / 生产化部署验证
2. Qdrant cron / Kubernetes CronJob 长期调度证据
3. 服务器长期运行验证
```

<!-- roadmap-update-2026-07-01-k8s-smoke-runner -->

## 2026-07-01 路线同步：K8s Smoke Runner CLI 已完成

本阶段把 K8s smoke test 从“计划和执行记录模板”推进到“可执行 runner”。runner 默认只运行 offline 步骤，避免误改集群；只有显式加 `--apply-cluster` 才执行 `kubectl apply`、rollout 和工作负载检查。

已完成：

- [x] `app/k8s_smoke_runner.py`
- [x] `k8s-smoke-run` CLI
- [x] 默认执行 offline validation：`kubectl kustomize` 和 `kubectl apply --dry-run=client`
- [x] `--apply-cluster` 执行 cluster 步骤
- [x] `--include-port-forward` 控制 port-forward 和 API health check
- [x] `--include-rollback` 控制 rollback，默认跳过
- [x] `--allow-fail` 支持采集失败证据
- [x] Markdown 执行报告输出
- [x] secret-like 输出脱敏
- [x] 单元测试覆盖 runner、CLI、失败退出和输出脱敏

当前边界：

```text
runner 已具备执行真实 kubectl 命令的能力。
当前提交不包含真实集群执行结果。
data/reports/ 下的真实执行报告默认不提交，除非后续整理为脱敏证据文档。
```

下一步学习：

```text
1. 使用真实 kubectl context 执行 k8s-smoke-run 并采集脱敏证据
2. Qdrant cron / Kubernetes CronJob 长期调度证据
3. 服务器长期运行验证
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-drill-plan -->

## 2026-07-01 路线同步：Qdrant Snapshot Drill Plan 已完成

本阶段开始把手动 snapshot API runner 组合成可调度的运维 drill。第一步只生成计划，不执行真实 API。

已完成：

- [x] `app/qdrant_snapshot_scheduler.py`
- [x] `qdrant-snapshot-drill-plan` CLI
- [x] drill step 建模：create snapshot、download snapshot、retention、restore drill、restored collection compare
- [x] 支持 `--apply-retention`
- [x] 支持 `--skip-restore-drill`
- [x] 支持 Markdown 输出
- [x] `tests/test_qdrant_snapshot_scheduler.py`
- [x] `docs/deployment/qdrant.md` 更新 drill plan 操作说明

当前边界：

```text
只生成 drill plan。
不调用 Qdrant snapshot API。
不下载 snapshot 文件。
不 restore collection。
不执行 retention 删除。
```

下一步学习：

```text
1. Qdrant snapshot drill 一次性 runner
2. Qdrant 定时 snapshot / restore drill 自动调度
3. MilvusVectorStoreRepository / Milvus runtime benchmark
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-drill-runner -->

## 2026-07-01 路线同步：Qdrant Snapshot Drill Runner 已完成

本阶段把 drill plan 推进为一次性显式 runner，但仍不创建系统级定时任务。

已完成：

- [x] `execute_qdrant_snapshot_drill()`
- [x] `render_qdrant_snapshot_drill_report()`
- [x] `qdrant-snapshot-drill-run` CLI
- [x] create snapshot
- [x] download snapshot
- [x] local retention policy
- [x] restore 到 disposable collection
- [x] restored collection compare hook
- [x] restore collection 显式确认保护
- [x] fake client 单元测试，不依赖真实 Qdrant 服务
- [x] `docs/deployment/qdrant.md` 更新 runner 操作说明

当前边界：

```text
这是一次性 runner。
不是后台常驻任务。
不创建 cron、Windows Task Scheduler 或 Kubernetes CronJob。
retention 默认 dry-run，只有 --apply-retention 才删除本地旧备份。
restore 必须确认 disposable collection。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 自动调度
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-schedule-config -->

## 2026-07-01 路线同步：Qdrant Snapshot Schedule Config 已完成

本阶段继续推进 Qdrant 定时 snapshot / restore drill 自动调度，但只完成调度配置预览，不安装真实定时任务。

已完成：

- [x] `QdrantSnapshotScheduleConfig`
- [x] `build_qdrant_snapshot_schedule_config()`
- [x] `render_qdrant_snapshot_schedule_config()`
- [x] `qdrant-snapshot-schedule-config` CLI
- [x] cron 配置预览
- [x] Windows Task Scheduler 命令预览
- [x] Kubernetes CronJob manifest 预览
- [x] 调度平台、cron 表达式、Windows 时间、restore collection 等参数校验
- [x] Markdown 输出
- [x] 单元测试覆盖 builder、renderer 和 CLI
- [x] `docs/deployment/qdrant.md` 更新 schedule config 操作说明

当前边界：

```text
这是调度配置预览。
不会写入 crontab。
不会创建 Windows scheduled task。
不会 kubectl apply Kubernetes CronJob。
不会实际启动后台定时任务。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 自动调度安装验证
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-schedule-install-plan -->

## 2026-07-01 路线同步：Qdrant Snapshot Schedule Install Plan 已完成

本阶段继续推进 Qdrant 定时 snapshot / restore drill 自动调度，但仍不直接修改本机或集群调度器。
本阶段目标是把调度配置预览转成可审查的安装命令，并加入 apply 安全闸门。

已完成：

- [x] `QdrantSnapshotScheduleInstallCommand`
- [x] `QdrantSnapshotScheduleInstallPlan`
- [x] `build_qdrant_snapshot_schedule_install_plan()`
- [x] `render_qdrant_snapshot_schedule_install_plan()`
- [x] `qdrant-snapshot-schedule-install-plan` CLI
- [x] cron install command 生成
- [x] Windows Task Scheduler install command 生成
- [x] Kubernetes CronJob apply command 生成
- [x] 默认 dry-run
- [x] `--apply` 安全闸门
- [x] `--confirm-task-name` 显式确认
- [x] 禁止 `--apply --platform all`
- [x] 单元测试覆盖 builder、renderer 和 CLI

当前边界：

```text
这是安装计划和命令生成器。
CLI 不直接执行安装命令。
不会写入 crontab。
不会创建 Windows scheduled task。
不会 kubectl apply Kubernetes CronJob。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 真实安装验证
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-schedule-verification-plan -->

## 2026-07-01 路线同步：Qdrant Snapshot Schedule Verification Plan 已完成

本阶段继续推进 Qdrant 定时 snapshot / restore drill 自动调度，但仍不直接查询或修改系统调度器。
本阶段目标是为真实安装后的验证和回滚准备可审查命令。

已完成：

- [x] `QdrantSnapshotScheduleVerificationCommand`
- [x] `QdrantSnapshotScheduleVerificationPlan`
- [x] `build_qdrant_snapshot_schedule_verification_plan()`
- [x] `render_qdrant_snapshot_schedule_verification_plan()`
- [x] `qdrant-snapshot-schedule-verify-plan` CLI
- [x] cron status / log / rollback 命令生成
- [x] Windows Task Scheduler status / log / rollback 命令生成
- [x] Kubernetes CronJob status / job / log / rollback 命令生成
- [x] 禁止 `--platform all` 生成验证计划
- [x] 单元测试覆盖 builder、renderer 和 CLI

当前边界：

```text
这是验证计划和回滚命令生成器。
CLI 不直接查询调度器。
CLI 不直接执行回滚。
真实调度安装后的 evidence collection 仍需人工执行命令并记录。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 真实安装证据记录模板
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-schedule-evidence-template -->

## 2026-07-01 路线同步：Qdrant Snapshot Schedule Evidence Template 已完成

本阶段继续推进 Qdrant 定时 snapshot / restore drill 自动调度，但仍不直接安装或查询系统调度器。
本阶段目标是为真实安装后的证据采集提供固定 Markdown 模板。

已完成：

- [x] `render_qdrant_snapshot_schedule_evidence_template()`
- [x] `qdrant-snapshot-schedule-evidence-template` CLI
- [x] pre-install manual drill 证据区
- [x] install command 证据区
- [x] status check 证据区
- [x] log check 证据区
- [x] rollback command 证据区
- [x] final decision 区
- [x] safety checklist
- [x] 禁止 `--platform all` 生成证据模板
- [x] 单元测试覆盖 renderer 和 CLI

当前边界：

```text
这是证据记录模板生成器。
CLI 不安装调度任务。
CLI 不查询调度器。
CLI 不验证粘贴的证据内容。
真实 evidence collection 仍需人工执行命令并脱敏记录。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 真实安装执行
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-qdrant-snapshot-schedule-install-executor -->

## 2026-07-01 路线同步：Qdrant Snapshot Schedule Install Executor 已完成

本阶段把调度安装从“命令预览”推进为“受保护的真实执行能力”。
该能力可以执行单平台调度安装命令，但要求显式确认任务名，并保留执行报告。

已完成：

- [x] `QdrantSnapshotScheduleInstallExecutionResult`
- [x] `QdrantSnapshotScheduleInstallExecutionReport`
- [x] `execute_qdrant_snapshot_schedule_install_plan()`
- [x] `run_schedule_install_command()`
- [x] `render_qdrant_snapshot_schedule_install_execution_report()`
- [x] `qdrant-snapshot-schedule-install-execute` CLI
- [x] 拒绝 dry-run plan 执行
- [x] 拒绝 `--platform all`
- [x] 要求 `--confirm-task-name`
- [x] 记录 return code / stdout / stderr / success
- [x] timeout 失败报告
- [x] fake runner 单元测试，不触碰真实系统调度器

当前边界：

```text
执行器已经具备真实安装命令执行能力。
测试不执行真实 cron / Task Scheduler / Kubernetes 修改。
真实启用后仍需运行 verification plan 并填写 evidence template。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 真实运行证据采集
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-07-01-qdrant-windows-scheduler-experiment -->

## 2026-07-01 路线同步：Qdrant Windows Task Scheduler 本机实验已完成

本阶段选择 Windows 本机平台先验证 Qdrant 定时 snapshot 运行链路。
验证对象是一次可回滚的 disposable scheduled task，不是长期生产任务。

已完成：

- [x] 启动本机 Qdrant Compose 服务
- [x] 手动执行 snapshot drill，并恢复到 disposable collection
- [x] 通过 `qdrant-snapshot-schedule-install-execute` 创建 Windows Task Scheduler 测试任务
- [x] 手动 `schtasks /Run` 触发测试任务
- [x] 验证 scheduled task 日志写入
- [x] 验证 snapshot create / download 在 scheduled task 中成功执行
- [x] 验证 `Last Result: 0`
- [x] 生成 evidence template
- [x] 使用 `schtasks /Delete` 回滚测试任务
- [x] 修复 Windows Task Scheduler `/TR` 261 字符限制导致的长命令失败
- [x] 修复项目路径包含空格时 `/TR` 嵌套引号失败
- [x] 修复 Windows PowerShell 5 读取无 BOM UTF-8 脚本导致中文路径乱码

当前实现策略：

```text
Windows scheduled task 不再直接执行长 runner 命令。
系统先生成一个短路径临时 .ps1 文件。
Task Scheduler action 使用 powershell.exe -File 调用该脚本。
.ps1 使用 UTF-8 with BOM 写入，保证 Windows PowerShell 5 可以正确读取中文路径。
```

当前边界：

```text
本阶段只验证 Windows 本机 Task Scheduler。
测试任务已经回滚删除。
data/reports/ 和 data/qdrant_backups/ 下的运行证据不提交到 Git，除非后续整理为脱敏报告。
cron、Kubernetes CronJob、长期运行和服务器常驻验证尚未完成。
```

下一步学习：

```text
1. Milvus runtime benchmark
2. K8s 真实集群 smoke test 执行 / 生产化部署验证
3. cron / Kubernetes CronJob 调度证据和长期运行验证
```

<!-- roadmap-update-2026-07-01-milvus-vector-store-repository-skeleton -->

## 2026-07-01 路线同步：MilvusVectorStoreRepository 骨架已完成

本阶段开始补齐第二个 Vector DB 后端。目标不是马上替换 Qdrant，而是验证现有 `VectorStoreRepository` 协议能否适配 Milvus。

已完成：

- [x] Milvus 环境变量配置
- [x] `MilvusVectorStoreRepository`
- [x] `create_milvus_client()` 懒加载真实 `pymilvus`
- [x] `parse_milvus_metric_type()`
- [x] `create_vector_store_repository("milvus", ...)`
- [x] save / search / delete / collection_exists 行为
- [x] fake-client 单元测试，不依赖真实 Milvus 服务

当前边界：

```text
Milvus repository 可以被实例化。
真实 pymilvus 只在实际连接 Milvus 时才需要。
本阶段没有启动 Milvus 服务。
本阶段没有跑 JSON / Qdrant / Milvus 三方 runtime benchmark。
```

下一步学习：

```text
1. Docker Compose Milvus 服务
2. Milvus import-vector-store CLI 或 repository runtime smoke
3. JSON / Qdrant / Milvus benchmark 对比报告
```

<!-- roadmap-update-2026-07-01-milvus-runtime-entry -->

## 2026-07-01 路线同步：Milvus Runtime Entry 已完成

本阶段把 Milvus 从 repository skeleton 推进到可本机 smoke 的运行入口。

已完成：

- [x] `docker-compose.yml` 新增 Milvus standalone 服务
- [x] `.env.example` 新增 Milvus URI、collection、vector size、metric 和端口配置
- [x] `pymilvus` 加入项目依赖锁
- [x] `import-vector-store-to-milvus` CLI
- [x] `compare-vector-store-backends --include-milvus`
- [x] benchmark 对比函数支持可选 Milvus repository
- [x] CLI 和 fake repository 单元测试

当前边界：

```text
Milvus 可以通过 Docker Compose 在本机启动。
Milvus 导入和三方 benchmark CLI 已接好。
本阶段没有提交真实 Milvus benchmark 结果。
Compose Milvus 用于本机 smoke，不代表生产部署拓扑。
```

下一步学习：

```text
1. 本机启动 Milvus
2. 导入 data/vector_store.json 到 Milvus
3. 运行 JSON / Qdrant / Milvus 三方 benchmark
4. 将结果写入 data/reports/ 并把脱敏结论同步到文档
```

<!-- roadmap-update-2026-07-01-milvus-runtime-benchmark -->

## 2026-07-01 路线同步：Milvus Runtime Benchmark 已完成

本阶段在 Windows 本机完成 Milvus 真实 runtime smoke 和三方检索 benchmark。

执行结果：

```text
Milvus 镜像通过 127.0.0.1:10808 代理拉取成功。
Milvus Compose standalone 服务启动成功，状态 healthy。
data/vector_store.json 导入 disposable collection thesis_chunks_milvus_smoke 成功。
JSON / Qdrant / Milvus 三方 benchmark 执行成功。
```

benchmark 摘要：

```text
JSON average score: 1.0
Qdrant average score: 1.0
Milvus average score: 1.0
Best repository: qdrant
Qdrant average duration: about 49 ms
JSON average duration: about 79 ms
Milvus average duration: about 1231 ms
Milvus latency was dominated by first-query warm-up; later queries were about 7-11 ms.
```

当前边界：

```text
完整 JSON benchmark report 保存在 data/reports/，默认不提交到 Git。
本次 Milvus collection 是 disposable smoke collection。
Milvus backup / restore SOP 已完成。
Milvus production deployment topology 尚未完成。
```

下一步学习：

```text
1. Milvus destructive operation guardrails
2. Milvus Backup Tool / 集群级 restore drill 边界学习
3. Vector DB runtime comparison documentation cleanup
```

<!-- roadmap-update-2026-07-01-milvus-backup-restore-sop -->

## 2026-07-01 路线同步：Milvus Backup / Restore SOP 已完成

本阶段补齐 Milvus 本机学习版的备份 / 恢复演练文档和 CLI 计划生成能力。

已完成：

- [x] `app/milvus_backup_restore_plan.py`
- [x] `milvus-backup-restore-plan` CLI
- [x] `milvus-restore-report-template` CLI
- [x] `.env.example` 增加 `MILVUS_BACKUP_DIR`
- [x] `docs/deployment/milvus-backup-restore.md`
- [x] `tests/test_milvus_backup_restore_plan.py`

当前边界：

```text
当前 Milvus 仍被视为可由 data/vector_store.json 重建的向量后端。
恢复优先走 JSON baseline -> disposable Milvus restore collection -> benchmark comparison。
volume tar.gz 只作为本机 standalone 学习备份，不作为生产集群备份方案。
不自动执行破坏性 volume restore。
```

下一步学习：

```text
1. Milvus Backup Tool / 集群级 restore drill 边界学习
2. Qdrant cron / Kubernetes CronJob 长期调度证据
3. K8s 真实集群 smoke test 执行
```

<!-- roadmap-update-2026-07-01-milvus-destructive-guardrails -->

## 2026-07-01 路线同步：Milvus Destructive Operation Guardrails 已完成

本阶段给 Milvus collection 删除操作补齐显式确认保护，避免误删活动 collection。

已完成：

- [x] `delete-milvus-collection` CLI
- [x] `--confirm-collection` 必填
- [x] confirmation 必须和 `--collection` 完全一致
- [x] repository 错误标准化输出
- [x] fake repository CLI 测试
- [x] `docs/deployment/milvus.md` 更新危险操作说明
- [x] `docs/deployment/milvus-backup-restore.md` 更新 restore smoke 后清理命令

当前边界：

```text
Milvus collection 删除已有显式确认保护。
仍不自动执行 volume restore 或生产 collection 切换。
Milvus Backup Tool / 集群级 restore drill 尚未接入。
```

下一步学习：

```text
1. Qdrant cron / Kubernetes CronJob 长期调度证据
2. K8s 真实集群 smoke test 执行
3. Milvus Backup Tool / 集群级 restore drill 边界学习
```

<!-- roadmap-update-2026-06-30-qdrant-snapshot-api-runner -->

## 2026-06-30 路线同步：Qdrant Snapshot API Runner 已完成

本阶段把离线 snapshot SOP 和 smoke plan 推进为可执行的手动 API runner。

已完成：

- [x] `app/qdrant_snapshot_client.py`
- [x] `qdrant-snapshot-create` CLI
- [x] `qdrant-snapshot-list` CLI
- [x] `qdrant-snapshot-download` CLI
- [x] `qdrant-snapshot-restore` CLI
- [x] restore 目标 collection 显式确认保护
- [x] fake HTTP client 单元测试，不依赖真实 Qdrant 服务
- [x] `docs/deployment/qdrant.md` 更新 snapshot API runner 操作说明

当前边界：

```text
这是手动 API runner，不是定时备份任务。
不会自动创建 cron、Windows Task Scheduler 或 Kubernetes CronJob。
restore smoke 仍需人工选择 disposable collection。
JSON 仍是本地 fallback 和 rebuild baseline。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 自动调度
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```
<!-- roadmap-update-2026-06-30-qdrant-snapshot-smoke-plan -->

## 2026-06-30 路线同步：Qdrant Snapshot Smoke Plan 已完成

本阶段完成的是 Qdrant snapshot 创建、下载、恢复和对比验证的离线执行计划，不直接调用 Qdrant API。

已完成：

- [x] `app/qdrant_snapshot_smoke_plan.py`
- [x] `qdrant-snapshot-smoke-plan` CLI
- [x] `qdrant-snapshot-smoke-report-template` CLI
- [x] create snapshot / list snapshots / download snapshot 步骤
- [x] restore 到 disposable collection 的步骤
- [x] restored collection 与 JSON baseline 对比步骤
- [x] retention dry-run 步骤
- [x] `tests/test_qdrant_snapshot_smoke_plan.py`
- [x] `docs/deployment/qdrant.md` 更新 snapshot smoke plan

当前边界：

```text
只生成执行计划和记录模板。
真实 Qdrant snapshot API 调用已由手动 CLI runner 承担。
不自动定时创建 snapshot 或执行 restore drill。
不删除或切换生产 collection。
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 自动调度
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```

<!-- roadmap-update-2026-06-30-qdrant-backup-retention -->

## 2026-06-30 路线同步：Qdrant 备份保留策略执行已完成

本阶段完成的是本地已下载 snapshot 文件的保留策略执行，不负责创建 Qdrant snapshot。

已完成：

- [x] `app/qdrant_backup_retention.py`
- [x] `qdrant-backup-retention` CLI
- [x] 默认 dry-run
- [x] 显式 `--apply` 才删除旧备份
- [x] `--keep-last` 保留最新 N 个备份
- [x] `--pattern` 支持指定备份文件 glob
- [x] retention Markdown report
- [x] `tests/test_qdrant_backup_retention.py`
- [x] `docs/deployment/qdrant.md` 更新 retention SOP

当前边界：

```text
只管理 data/qdrant_backups/ 等本地目录中已经下载的 snapshot 文件。
不自动调用 Qdrant create snapshot API。
不创建 cron、Windows Task Scheduler 或 Kubernetes CronJob。
```

<!-- roadmap-update-2026-07-02-qdrant-k8s-cronjob-multi-cycle -->

## 2026-07-02 路线同步：Qdrant Kubernetes CronJob Multi-Cycle Observe 已完成

本阶段将 Qdrant Kubernetes CronJob 从“一次自然调度周期”推进到“多个自然调度周期”的本机 kind 集群验证。
该阶段验证的是 CronJob 不依赖 `kubectl create job` 手动触发，也能连续由 Kubernetes controller 按 cron schedule 创建多个 Job，并且每个 Job 都能访问集群内 Qdrant 完成 snapshot create / download。

已完成：

- [x] `qdrant-k8s-cronjob-multi-cycle-observe` CLI
- [x] `execute_qdrant_k8s_cronjob_multi_cycle_observe`
- [x] 多周期 scheduled Job 发现逻辑
- [x] CronJob ownerReference / label 识别
- [x] 每个 scheduled Job 的 wait / inspect / pod / logs 证据采集
- [x] 可选 `--cleanup-jobs`
- [x] 可选 `--cleanup-cronjob`
- [x] Markdown evidence report
- [x] 本机 kind 集群真实验证两个自然调度周期

本机验证结果：

```text
qdrant-k8s-cronjob-multi-cycle-observe --expected-cycles 2

Overall status: passed
Observed scheduled Jobs: 2
Job 1: Complete, pod Completed, snapshot create/download completed
Job 2: Complete, pod Completed, snapshot create/download completed
CronJob ownerReference detected
Scheduled Jobs deleted
CronJob deleted
```

当前边界：

```text
这是本机 kind 集群多周期调度证据。
它证明 Kubernetes CronJob controller 可以连续调度并成功执行 snapshot drill。
它不等于服务器多小时或多天长期运行验证。
服务器长期运行仍需要更长时间窗口、失败告警、日志保留和真实通知通道。
```

下一步学习：

```text
1. 整理本机部署 / K8s / Qdrant 证据索引和运行命令索引
2. 服务器长期运行前置检查
3. 服务器长期运行验证
```

下一步学习：

```text
1. Qdrant 定时 snapshot / restore drill 自动调度
2. MilvusVectorStoreRepository / Milvus runtime benchmark
3. K8s 真实集群 smoke test 执行 / 生产化部署验证
```
<!-- roadmap-update-2026-07-01-k8s-kind-smoke-evidence -->

## 2026-07-01 路线同步：K8s Kind Smoke Evidence 已完成

本阶段使用本机 `kind-thesis-defense-agent` context 完成真实 Kubernetes 集群 smoke 验证。
原始执行报告保存在 `data/reports/k8s_smoke_run.md`，该目录不提交到 Git。

已验证：

- [x] `kubectl kustomize k8s/base`
- [x] `kubectl apply --dry-run=client --validate=false -k k8s/base`
- [x] `kubectl apply -k k8s/base`
- [x] API Deployment rollout 成功
- [x] Prometheus Deployment rollout 成功
- [x] Alertmanager Deployment rollout 成功
- [x] API `/health` 返回 ok
- [x] Prometheus target `http://api:8000/metrics/prometheus` 为 `up`
- [x] Alertmanager ready/status 正常

当前边界：

```text
这是本机 kind 集群验证，不代表服务器长期运行。
没有提交原始 smoke report、kubeconfig、密钥或完整运行日志。
下一阶段转向 cron / Kubernetes CronJob 调度证据和 Qdrant 长期运行验证。
```

下一步学习：

```text
1. Qdrant cron / Kubernetes CronJob 长期调度证据
2. 服务器长期运行验证
```

<!-- roadmap-update-2026-07-01-qdrant-kubernetes-cronjob-manifest -->

## 2026-07-01 路线同步：Qdrant Kubernetes CronJob Manifest 已完成

本阶段把 Qdrant snapshot drill 的 Kubernetes 调度从 Markdown 预览推进到可直接交给 `kubectl` 的 CronJob YAML manifest。
该阶段验证的是 manifest 生成和 Kubernetes client-side dry-run，不代表 CronJob 已经在集群内长期运行。

已完成：

- [x] `app/qdrant_snapshot_cronjob_manifest.py`
- [x] `qdrant-snapshot-cronjob-manifest` CLI
- [x] ConfigMap / Secret envFrom 引用可配置
- [x] CronJob `concurrencyPolicy: Forbid`
- [x] Job history / deadline / backoff / TTL 字段
- [x] non-root `securityContext`
- [x] container resources request / limit
- [x] `kubectl apply --dry-run=client --validate=false -f data/reports/qdrant_snapshot_cronjob.yaml`
- [x] 单元测试覆盖 manifest 渲染、CLI 输出、文件写入和参数校验

验证结果：

```text
cronjob.batch/thesis-defense-qdrant-snapshot-drill created (dry run)
uv run pytest -q: 1182 passed, 1 warning
```

当前边界：

```text
这是 manifest 渲染和 client-side dry-run 验证。
当前 kind 集群已补齐 Qdrant StatefulSet / Service / PVC / PDB，并完成一次运行验证。
CronJob 尚未作为长期任务 apply 到集群。
真实调度证据仍需 Qdrant 在集群内可达后再采集。
```

下一步学习：

```text
1. 为 kind / K8s 环境补齐 Qdrant 服务可达性方案
2. 将 CronJob apply 到测试 namespace 并手动触发 Job
3. 采集 Job 状态、日志、snapshot 产物和失败可见性证据
4. 再进入长期周期运行观察
```

<!-- roadmap-update-2026-07-01-qdrant-k8s-service-runtime -->

## 2026-07-01 路线同步：Qdrant Kubernetes StatefulSet / Service Runtime 已完成

本阶段为本机 kind / Kubernetes 环境补齐 Qdrant 集群内可达性。
目标不是启用长期 CronJob，而是先让 Qdrant 在 namespace 内以稳定 DNS、持久化卷和受保护 workload 的方式运行。

已完成：

- [x] `k8s/base/qdrant-statefulset.yaml`
- [x] `k8s/base/qdrant-service.yaml`
- [x] `k8s/base/qdrant-pod-disruption-budget.yaml`
- [x] Qdrant `ClusterIP` Service 暴露 HTTP 6333 和 gRPC 6334
- [x] Qdrant `StatefulSet` 挂载 `volumeClaimTemplates`
- [x] Qdrant readiness / liveness probes
- [x] Qdrant resources request / limit
- [x] Qdrant PDB `minAvailable: 1`
- [x] API ConfigMap 增加集群内 `QDRANT_URL=http://qdrant:6333`
- [x] K8s smoke plan 增加 `rollout_qdrant`
- [x] `kubectl apply --dry-run=client --validate=false -k k8s/base`
- [x] 本机 kind 集群 `kubectl apply -k k8s/base`
- [x] `kubectl rollout status statefulset/qdrant -n thesis-defense-agent`
- [x] Qdrant Pod Running、PVC Bound、Service endpoints 可见
- [x] Port-forward 验证 `/readyz` 返回 200
- [x] `k8s-smoke-run --apply-cluster` 覆盖 Qdrant rollout 和 workload inspect

当前边界：

```text
这是本机 kind 集群的一次性 runtime validation。
Qdrant StatefulSet / Service 已可被同 namespace 内 CronJob 使用。
CronJob manual Job smoke 已完成。
周期运行证据尚未采集。
```

下一步学习：

```text
1. 观察 CronJob 至少一个自然调度周期
2. 采集 scheduled Job 状态、日志、snapshot 产物和失败可见性证据
3. 验证 CronJob 回滚和清理命令
4. 再决定是否保留长期运行任务
```

<!-- roadmap-update-2026-07-01-qdrant-k8s-cronjob-manual-smoke -->

## 2026-07-01 路线同步：Qdrant Kubernetes CronJob Manual Job Smoke 已完成

本阶段将 Qdrant CronJob 从 manifest dry-run 推进到本机 kind 集群中的一次性 Job 运行证据。
该阶段验证的是 CronJob 能被 apply、能手动触发 Job、Job 能访问集群内 Qdrant 并完成 snapshot create / download。

已完成：

- [x] `app/qdrant_k8s_cronjob_smoke.py`
- [x] `qdrant-k8s-cronjob-smoke-run` CLI
- [x] CronJob YAML 生成后直接 apply
- [x] `kubectl create job --from=cronjob/...` 手动触发
- [x] `kubectl wait --for=condition=complete` 等待 Job 完成
- [x] CronJob / Job / Pod / logs 证据采集
- [x] 可选 `--cleanup-job`
- [x] 可选 `--cleanup-cronjob`
- [x] 可选 `--manifest-output`
- [x] Markdown smoke report 输出
- [x] 本机 kind 集群 smoke run 通过

本机验证结果：

```text
qdrant-k8s-cronjob-smoke-run --namespace thesis-defense-agent --cleanup-job --cleanup-cronjob

Overall status: passed
CronJob created
Manual Job created
Manual Job condition complete
Job Pod status Completed
Job logs include Qdrant Snapshot Drill Report
Snapshot create completed
Snapshot download completed
Retention dry-run completed
Manual Job deleted
CronJob deleted
```

当前边界：

```text
这是手动触发 Job 的 smoke evidence。
默认不执行 restore drill，也不执行 JSON baseline compare。
原始报告保存在 data/reports/，不提交到 Git。
这还不是 CronJob 自然调度周期的长期运行证据。
```

下一步学习：

```text
1. 保留 CronJob 至少一个自然调度周期
2. 采集 scheduled Job 状态、日志和 snapshot 产物
3. 验证失败可见性和回滚清理命令
4. 再进入跨平台 cron / 服务器长期运行验证
```
