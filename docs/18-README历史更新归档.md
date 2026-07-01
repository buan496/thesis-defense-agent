# README 历史更新归档

本文从 README 迁移而来，用于保存阶段性更新记录。README 首页只保留项目入口、运行方式和当前状态。

## 2026-07-01 Update: Qdrant Snapshot Schedule Config

项目新增 Qdrant snapshot drill 的调度配置预览生成器：

```text
qdrant-snapshot-schedule-config
```

生成全部平台的调度预览：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-config
```

生成 Kubernetes CronJob 预览：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-config `
  --platform kubernetes_cronjob `
  --namespace thesis-defense `
  --image ghcr.io/buan496/thesis-defense-agent:latest
```

当前边界：

```text
该命令只生成 cron、Windows Task Scheduler 和 Kubernetes CronJob 预览。
不会安装 cron。
不会创建 Windows scheduled task。
不会 apply Kubernetes CronJob。
真实定时任务安装仍是后续生产化验证内容。
```

<!-- docs-update-2026-07-01-qdrant-snapshot-schedule-install-plan -->


## 2026-07-01 Update: Qdrant Snapshot Schedule Install Plan

项目新增 Qdrant snapshot drill 的调度安装计划生成器：

```text
qdrant-snapshot-schedule-install-plan
```

生成 dry-run 安装计划：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-plan
```

生成单平台 apply 模式安装命令预览：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-plan `
  --platform cron `
  --task-name thesis-defense-qdrant-snapshot-drill `
  --confirm-task-name thesis-defense-qdrant-snapshot-drill `
  --apply
```

当前边界：

```text
默认 dry-run。
--apply 必须配合 --confirm-task-name。
--apply 不能用于 --platform all。
CLI 只渲染安装命令，不直接执行系统修改。
```

<!-- docs-update-2026-07-01-qdrant-snapshot-schedule-verification-plan -->


## 2026-07-01 Update: Qdrant Snapshot Schedule Verification Plan

项目新增 Qdrant snapshot drill 调度验证计划生成器：

```text
qdrant-snapshot-schedule-verify-plan
```

生成 cron 验证计划：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-verify-plan `
  --platform cron
```

生成 Kubernetes CronJob 验证计划：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-verify-plan `
  --platform kubernetes_cronjob `
  --task-name thesis-defense-qdrant-snapshot-drill `
  --namespace thesis-defense
```

当前边界：

```text
该命令生成状态检查、日志检查和回滚命令。
不会直接查询系统调度器或 Kubernetes。
不会执行回滚。
真实安装后的证据采集仍需人工执行命令并记录。
```

<!-- docs-update-2026-07-01-qdrant-snapshot-schedule-evidence-template -->


## 2026-07-01 Update: Qdrant Snapshot Schedule Evidence Template

项目新增 Qdrant snapshot drill 调度证据记录模板：

```text
qdrant-snapshot-schedule-evidence-template
```

生成 cron 证据模板：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-evidence-template `
  --platform cron `
  --environment local-cron `
  --operator "<your-name>"
```

保存 Markdown：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-evidence-template `
  --platform cron `
  --output data/reports/qdrant_snapshot_schedule_evidence.md
```

当前边界：

```text
该命令只生成证据记录模板。
不会安装调度任务。
不会查询调度器。
不会验证粘贴的证据内容。
真实命令输出需要人工脱敏后写入模板。
```

<!-- docs-update-2026-07-01-qdrant-snapshot-schedule-install-executor -->


## 2026-07-01 Update: Qdrant Snapshot Schedule Install Executor

项目新增受保护的 Qdrant snapshot drill 调度安装执行器：

```text
qdrant-snapshot-schedule-install-execute
```

示例：

```powershell
uv run python -m app.cli qdrant-snapshot-schedule-install-execute `
  --platform cron `
  --task-name thesis-defense-qdrant-snapshot-drill `
  --confirm-task-name thesis-defense-qdrant-snapshot-drill
```

当前边界：

```text
这是第一个可以真实执行调度安装命令的 CLI。
必须显式传入 --confirm-task-name。
底层拒绝 --platform all。
执行报告会记录 return code、stdout、stderr 和 success。
真实启用前应先生成 install plan、verification plan 和 evidence template。
```

<!-- docs-update-2026-07-01-qdrant-windows-scheduler-experiment -->


## 2026-07-01 Update: Qdrant Windows Scheduler Experiment

本机 Windows Task Scheduler 实验已完成。

验证范围：

```text
创建测试计划任务
手动触发 schtasks /Run
Qdrant snapshot 创建
snapshot 下载到 data/qdrant_backups
retention dry-run
写入调度日志
删除测试计划任务
```

本次实验修复了 Windows 平台两个真实问题：

```text
1. schtasks /TR 参数有 261 字符限制，长命令不能直接放进 /TR。
2. Windows PowerShell 5 读取无 BOM UTF-8 脚本时会导致中文路径乱码。
```

当前实现：

```text
Windows Task Scheduler 动作调用临时目录下的 .ps1 文件。
.ps1 文件使用 UTF-8 with BOM 写入。
测试任务已回滚删除。
```

<!-- docs-update-2026-06-29-postgres-compose -->


## 2026-06-29 Update: PostgreSQL Compose Service

This project includes a local PostgreSQL service in `docker-compose.yml`.
PostgreSQL is available for local integration testing and optional runtime
storage through `STORAGE_BACKEND=postgres`.

Current boundary:

```text
STORAGE_BACKEND=json remains the default.
Task, session, and trace runtime can use PostgreSQL when STORAGE_BACKEND=postgres
and DATABASE_URL are explicitly configured.
```

Local PostgreSQL check:

```powershell
docker compose up -d postgres
docker compose ps postgres
docker compose exec postgres pg_isready -U thesis_agent -d thesis_defense_agent
docker compose down
```

<!-- docs-update-2026-06-29-postgres-migrations -->


## 2026-06-29 Update: PostgreSQL Schema Migrations

PostgreSQL schema migration assets are now available under:

```text
db/migrations/postgres/
```

Current migration:

```text
001_initial_schema.sql
```

It defines durable storage tables for task, session, trace, feedback, and
benchmark candidate records. The application default remains JSON / JSONL
storage, but PostgreSQL repositories can use this schema when explicitly
selected.

Inspect the migration plan without connecting to PostgreSQL:

```powershell
uv run python -m app.cli postgres-migrations
```

Apply pending migrations against a configured PostgreSQL database:

```powershell
uv run python -m app.cli run-postgres-migrations
```

The migration runner records applied versions in `schema_migrations` and
rejects checksum drift. It prepares the database schema for the PostgreSQL task,
session, and trace repositories.

<!-- docs-update-2026-06-29-postgres-task-repository -->


## 2026-06-29 Update: PostgresTaskRepository

`PostgresTaskRepository` is now implemented as a PostgreSQL-backed task storage
adapter. It supports saving and loading `DefenseTask` records through the same
repository interface used by the JSON implementation.

Current boundary:

```text
The repository implementation exists and is covered by fake-connection tests.
Task runtime can use it when STORAGE_BACKEND=postgres.
JSON remains the default backend.
```

<!-- docs-update-2026-06-29-repository-factory -->


## 2026-06-29 Update: Repository Factory

The project now includes a repository factory that can construct storage
repositories from configuration:

```text
STORAGE_BACKEND=json      -> JsonTaskRepository / JsonSessionRepository / JsonlTraceRepository
STORAGE_BACKEND=postgres  -> PostgresTaskRepository / PostgresSessionRepository / PostgresTraceRepository
```

Inspect the selected repository classes:

```powershell
uv run python -m app.cli show-repositories
```

Current boundary:

```text
json remains the default backend.
The factory can create PostgreSQL repositories for task, session, and trace runtime
paths when STORAGE_BACKEND=postgres.
```

<!-- docs-update-2026-06-29-postgres-json-import -->


## 2026-06-29 Update: JSON-to-PostgreSQL Import

The project now includes explicit import tooling for moving local JSON / JSONL
storage into PostgreSQL repositories:

```powershell
uv run python -m app.cli import-json-to-postgres --dry-run
uv run python -m app.cli import-json-to-postgres
```

The import command supports task, session, and trace records. It reports source
and imported counts, and it does not print the full `DATABASE_URL`.

Current boundary:

```text
Import is an explicit operational command.
Runtime storage still defaults to JSON / JSONL unless STORAGE_BACKEND=postgres
is explicitly configured.
```

<!-- docs-update-2026-06-29-task-runtime-repository-pilot -->


## 2026-06-29 Update: Task Runtime Repository Pilot

Task workflow commands now use the repository abstraction at runtime. The CLI
creates a task repository from `STORAGE_BACKEND` through the repository factory
and injects it into task service functions.

Covered task commands:

```text
create-task
start-task-step
complete-task-step
execute-task-step
submit-task-answer
submit-follow-up-answer
resume-task
analyze-task
export-task-markdown
export-task-memory
show-task
```

Current boundary:

```text
STORAGE_BACKEND=json remains the default.
Task runtime can use the selected task repository.
Session and trace runtime can also use selected repositories.
```

<!-- docs-update-2026-06-29-session-runtime-repository-integration -->


## 2026-06-29 Update: Session Runtime Repository Integration

Chat session runtime now uses the repository abstraction. The CLI creates a
session repository from `STORAGE_BACKEND` through the repository factory and
injects it into `run_agent_session`.

Covered session path:

```text
chat
session creation
session resume
session metadata updates
session compaction persistence
```

Current boundary:

```text
STORAGE_BACKEND=json remains the default.
Task and session runtime can use selected repositories.
Trace runtime can use selected repositories.
```

<!-- docs-update-2026-06-29-trace-runtime-repository-integration -->


## 2026-06-29 Update: Trace Runtime Repository Integration

Trace runtime now uses the repository abstraction for Agent trace replay and
analysis, generic trace replay, and Sub-Agent plan / execution trace save and
analysis paths.

Covered trace paths:

```text
Agent trace save / load / analyze / replay
generic trace replay
Sub-Agent plan trace save / load / analyze
Sub-Agent execution trace save / load / analyze
```

Current boundary:

```text
STORAGE_BACKEND=json remains the default.
Task, session, and trace runtime can use selected repositories.
Compare commands that intentionally compare two explicit files still keep
file-path semantics.
```

<!-- docs-update-2026-06-29-postgres-trace-repository -->


## 2026-06-29 Update: PostgresTraceRepository

`PostgresTraceRepository` is now implemented as a PostgreSQL-backed append-only
trace storage adapter. It stores the original trace record as JSONB while also
filling query columns such as `source_type`, `source_id`, `event_type`, and
`success`.

Current boundary:

```text
The repository implementation exists and is covered by fake-connection tests.
Trace runtime can use it when STORAGE_BACKEND=postgres.
JSONL remains the default trace backend.
```

<!-- docs-update-2026-06-29-postgres-session-repository -->


## 2026-06-29 Update: PostgresSessionRepository

`PostgresSessionRepository` is now implemented as a PostgreSQL-backed Agent
session storage adapter. It saves the complete `AgentSession` payload to JSONB
and restores it through the same repository interface used by the JSON
implementation.

Current boundary:

```text
The repository implementation exists and is covered by fake-connection tests.
Session runtime can use it when STORAGE_BACKEND=postgres.
JSON remains the default session backend.
```

最新本地测试基线：

```text
1115 passed, 1 warning
```

本机学习版阶段已完成，阶段总复盘见：

```text
docs/17-本机学习版阶段总复盘.md
```


## 2026-06-30 Update: External Notification Routing

项目新增本地可审计的通知路由层：

```text
app/notification_models.py
app/notification_channels.py
app/notification_router.py
app/alert_notification_adapter.py
docs/deployment/notifications.md
```

告警链路现在是：

```text
Prometheus alert rule
-> Alertmanager route
-> POST /alerts/alertmanager
-> NotificationEvent
-> NotificationRouter
-> JsonlNotificationChannel
-> data/notifications/notifications.jsonl
```

当前支持：

```text
severity-based target routing
local JSONL notification audit
console notification channel
in-memory deduplication
delivery result reporting
```

当前边界：

```text
不包含 Feishu / WeCom / email provider。
不包含跨进程去重、silence 管理、升级策略或外部密钥配置。
```


## 2026-06-29 Update: Prometheus Alert Rules

项目现在从“能暴露指标”推进到“能发现常见异常”：

```text
observability/prometheus/alert_rules.yml
docs/deployment/prometheus.md
```

已定义告警：

```text
ThesisDefenseAgentApiDown
ThesisDefenseAgentHigh5xxRate
ThesisDefenseAgentHighAverageLatency
```

当前边界：

```text
Prometheus 会加载本地 alert rules。
Prometheus 会把告警发送到本地 Alertmanager。
Alertmanager 会把告警 webhook 发送到 FastAPI 的 `/alerts/alertmanager`。
尚未接邮件、飞书、企业微信、on-call routing 或生产 SLO。
```


## 2026-06-30 Update: Alertmanager Local Routing

项目现在从“能发现常见异常”推进到“能完成本机告警路由”：

```text
observability/alertmanager/alertmanager.yml
observability/prometheus/prometheus.yml
app/api/routes/alerts.py
docs/deployment/alertmanager.md
```

已完成链路：

```text
Prometheus alert rule
-> Alertmanager route
-> local-webhook receiver
-> POST /alerts/alertmanager
```

本机启动：

```powershell
docker compose up -d api alertmanager prometheus
```

边界：

```text
本阶段只做本机 webhook 接收和路由验证。
暂未接邮件、飞书、企业微信、PagerDuty 或生产 on-call。
```


## 2026-06-30 Update: Kubernetes Base Manifests

项目现在新增学习版 K8s manifests：

```text
k8s/base/
docs/deployment/k8s.md
```

已完成资源：

```text
Namespace
API Deployment / Service / ConfigMap / Secret example
Prometheus Deployment / Service / ConfigMap
Alertmanager Deployment / Service / ConfigMap
PodDisruptionBudget
```

本阶段只做无状态服务的基础对象映射：

```text
docker-compose service
-> Deployment
-> Service
-> ConfigMap
-> Secret example
-> readiness / liveness
-> resource requests / limits
-> rolling update strategy
-> PodDisruptionBudget
```

边界：

```text
已完成本机学习版 K8s 生产化基础字段。
尚未做 Ingress、TLS、HPA、NetworkPolicy、PVC、PostgreSQL StatefulSet、Qdrant StatefulSet、Helm chart 或真实集群 smoke test。
```


## 2026-06-30 Update: Kubernetes Production Basics

K8s base manifests 已补齐生产化基础字段：

```text
Docker image non-root runtime user
revisionHistoryLimit
progressDeadlineSeconds
RollingUpdate maxUnavailable=0 maxSurge=1
readinessProbe / livenessProbe
resource requests / limits
restricted securityContext
PodDisruptionBudget minAvailable=1
rollout / rollback SOP
```

相关文件：

```text
Dockerfile
k8s/base/*deployment.yaml
k8s/base/*pod-disruption-budget.yaml
docs/deployment/k8s.md
tests/test_k8s_manifests.py
tests/test_dockerfile.py
```

当前边界：

```text
这是静态 manifest 生产化基础学习，不等于真实集群生产运行。
API 仍保持 replicas=1，因为默认 JSON / emptyDir 后端不适合多副本共享状态。
```


## 2026-06-30 Update: Kubernetes Smoke Test Plan

项目新增 K8s smoke test 计划生成器和执行报告模板：

```text
app/k8s_smoke_plan.py
tests/test_k8s_smoke_plan.py
tests/test_k8s_smoke_cli.py
```

生成 smoke test SOP：

```powershell
uv run python -m app.cli k8s-smoke-plan
```

保存为 Markdown：

```powershell
uv run python -m app.cli k8s-smoke-plan `
  --output data/reports/k8s_smoke_plan.md
```

生成真实集群执行记录模板：

```powershell
uv run python -m app.cli k8s-smoke-report-template `
  --environment kind-local `
  --operator "<your-name>" `
  --output data/reports/k8s_smoke_report.md
```

当前边界：

```text
该命令只生成可审计执行计划和执行记录模板，不会自动 kubectl apply。
真实集群 apply / rollout / port-forward / rollback 验证仍需在有集群时手动执行。
```


## 2026-06-30 Update: Static Web Frontend

项目新增第一版 Web 前端：

```text
app/api/routes/frontend.py
app/api/static/index.html
app/api/static/styles.css
app/api/static/app.js
docs/deployment/web-frontend.md
```

访问入口：

```text
http://127.0.0.1:8000/
```

已支持：

```text
创建任务
加载任务
开始下一步
执行当前自动步骤
提交学生回答
提交追问回答
查看 Trace 汇总
导出 Markdown 报告
```

边界：

```text
当前是静态 HTML/CSS/JS 学习版，已包含文件上传 UI、SSE 输出测试、WebSocket 状态展示、Trace 指标卡片、步骤详情查看和 Markdown 报告下载。
仍不包含 React/Vite、登录鉴权、会话列表、图形化 trace 拓扑或复杂前端状态管理。
```


## 2026-06-30 Update: Web Frontend Enhancements

静态 Web 前端已从最小 Task 控制台增强为本机学习版操作面板。

新增能力：

```text
文件上传 UI -> POST /documents/upload
SSE 流式输出测试 -> GET /stream/echo
WebSocket 连接状态 -> /ws/tasks/{task_id}
Task Trace 指标卡片 -> tool calls / token / cost
可点击步骤列表 -> 查看单步输入输出与状态
Markdown 报告下载 -> 浏览器本地下载
```

相关文件：

```text
app/api/static/index.html
app/api/static/app.js
app/api/static/styles.css
tests/test_api_frontend.py
```

验证基线：

```text
uv run pytest tests/test_api_frontend.py -q
uv run pytest -q
```


## 2026-06-30 Update: MCP Stdio Server

项目新增最小 stdio MCP Server：

```text
app/mcp_server.py
docs/deployment/mcp-server.md
```

支持方法：

```text
initialize
notifications/initialized
tools/list
tools/call
```

运行：

```powershell
uv run python -m app.mcp_server
```

边界：

```text
当前是本地 stdio JSON-RPC MCP Server，不包含远程 HTTP transport、认证、resource/list、prompt/list 或生产部署。
```


## 2026-06-30 Update: MCP Stdio Client

项目新增最小 stdio MCP Client：

```text
app/mcp_client.py
docs/deployment/mcp-client.md
```

支持能力：

```text
JSON-RPC request / response
initialize handshake
notifications/initialized
tools/list
tools/call
stdio process transport
client-side MCP error handling
```

当前边界：

```text
尚未支持多 MCP Server 管理、远程 HTTP transport、认证或将外部 MCP 工具自动注册进 Agent Tool Registry。
```


## 2026-06-30 Update: MCP Resources and Prompts

项目新增 MCP resource / prompt 本地学习版能力：

```text
app/mcp_resources.py
app/mcp_prompts.py
docs/deployment/mcp-resources-prompts.md
```

新增 MCP Server 方法：

```text
resources/list
resources/read
prompts/list
prompts/get
```

新增 MCP Client 方法：

```text
list_resources()
read_resource(uri)
list_prompts()
get_prompt(name, arguments=None)
```

当前边界：

```text
Resource 只提供上下文。
Prompt 只提供模板。
Tool 才执行动作。
尚未做远程 MCP transport、多 Server 聚合、resource subscription 或 prompt marketplace。
```


## 2026-06-29 Update: Logging Retention and Query Guide

项目现在明确了本机 / Docker / 服务器风格运行时的日志查看和保留方式：

```text
docs/deployment/logging.md
```

当前已完成：

```text
API structured request logs
X-Correlation-ID response header
correlation_id in API request logs
correlation_id in DefenseTask metadata
correlation_id in TaskStep input/output
correlation_id in task tool traces
Docker Compose json-file log rotation
DOCKER_LOG_MAX_SIZE / DOCKER_LOG_MAX_FILE
Docker logs query commands
Agent trace analyze / replay commands
```

当前边界：

```text
尚未接 Loki / Elasticsearch。
尚未做 log-based alerting。
Agent 非任务型 trace 的 correlation_id 贯穿仍可继续扩展。
```


## 2026-06-29 Update: Vector Store Repository Abstraction

RAG 向量库现在开始从“直接读写 JSON 文件”过渡到 repository 抽象：

```text
VECTOR_STORE_BACKEND=json -> JsonVectorStoreRepository
VECTOR_STORE_BACKEND=qdrant -> QdrantVectorStoreRepository
VECTOR_STORE_BACKEND=milvus -> MilvusVectorStoreRepository
```

已接入路径：

```text
PDF vector store builder
Task retrieve_context step
Retrieval evaluator load path
```

当前边界：

```text
JSON 仍是默认向量库后端。
Qdrant 已有最小 repository 实现和 benchmark 对比入口。
Milvus 已有 repository、Compose 服务、导入 CLI、可选 benchmark 入口和本机 runtime benchmark 结果。
```


## 2026-06-29 Update: Qdrant Compose Service

项目现在增加了本地 Qdrant Compose 服务和配置骨架：

```text
docker-compose.yml -> qdrant service
qdrant/qdrant:v1.18.2
qdrant_data volume -> /qdrant/storage
QDRANT_URL / QDRANT_COLLECTION / QDRANT_VECTOR_SIZE / QDRANT_DISTANCE
```

本地启动：

```powershell
docker compose up -d qdrant
docker compose ps qdrant
Invoke-RestMethod http://127.0.0.1:6333
```

当前边界：

```text
VECTOR_STORE_BACKEND=json 仍是默认值。
Qdrant 服务和配置已准备。
QdrantVectorStoreRepository 已有最小实现。
运行时默认检索仍走 JSON 向量库，只有显式设置 VECTOR_STORE_BACKEND=qdrant 时才使用 Qdrant。
```

说明文档：

```text
docs/deployment/qdrant.md
```


## 2026-06-29 Update: QdrantVectorStoreRepository

项目已增加 Qdrant 向量库后端的最小实现：

```text
Qdrant collection ensure/create
JSON vector store items upsert into Qdrant
Qdrant query_points search
import-vector-store-to-qdrant CLI
delete-qdrant-collection CLI with explicit confirmation
Qdrant snapshot backup/restore SOP
```

导入现有 JSON 向量库到 Qdrant：

```powershell
docker compose up -d qdrant

uv run python -m app.cli import-vector-store-to-qdrant `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine
```

当前边界：

```text
VECTOR_STORE_BACKEND=json 仍是默认值。
Task retrieve_context 已可通过 VECTOR_STORE_BACKEND=qdrant 使用 Qdrant。
RAG benchmark 已支持对比 Qdrant 与 JSON 后端。
```

对比 JSON 与 Qdrant 后端：

```powershell
docker compose up -d qdrant

uv run python -m app.cli compare-vector-store-backends `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine
```

删除 Qdrant collection 必须显式确认 collection 名称：

```powershell
uv run python -m app.cli delete-qdrant-collection `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --distance Cosine `
  --confirm-collection thesis_chunks
```

Qdrant snapshot 备份与恢复流程已文档化：

```text
docs/deployment/qdrant.md
```


## 2026-07-01 Update: Milvus Vector Store Runtime Entry

项目新增 Milvus 本机验证入口：

```text
docker-compose.yml -> milvus service
MilvusVectorStoreRepository
import-vector-store-to-milvus CLI
compare-vector-store-backends --include-milvus
```

本机启动 Milvus：

```powershell
docker compose up -d milvus
docker compose ps milvus
```

导入现有 JSON 向量库：

```powershell
uv run python -m app.cli import-vector-store-to-milvus `
  --source data/vector_store.json `
  --uri http://127.0.0.1:19530 `
  --collection thesis_chunks `
  --vector-size 1024 `
  --metric-type COSINE
```

对比 JSON、Qdrant 和 Milvus：

```powershell
docker compose up -d qdrant milvus

uv run python -m app.cli compare-vector-store-backends `
  --source data/vector_store.json `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --include-milvus `
  --milvus-uri http://127.0.0.1:19530 `
  --milvus-collection thesis_chunks `
  --output data/reports/vector_store_backend_comparison_with_milvus.json
```

本机 benchmark 结果：

```text
JSON average score: 1.0
Qdrant average score: 1.0
Milvus average score: 1.0
Best repository: qdrant
Qdrant average duration: about 49 ms
JSON average duration: about 79 ms
Milvus average duration: about 1231 ms, dominated by first-query warm-up
```

生成 Milvus 备份 / 恢复计划：

```powershell
uv run python -m app.cli milvus-backup-restore-plan
```

生成 Milvus 恢复执行记录模板：

```powershell
uv run python -m app.cli milvus-restore-report-template `
  --environment local-milvus `
  --operator "<your-name>"
```

当前边界：

```text
Milvus repository 和 CLI 入口已完成。
Compose 服务用于本机 smoke，不代表生产部署形态。
完整 benchmark JSON 报告保存在 data/reports/，默认不提交到 Git。
Milvus backup / restore SOP 已完成。
milvus-backup-restore-plan 和 milvus-restore-report-template 已接入 CLI。
```

当前边界：

```text
已有手动 snapshot backup / restore SOP。
尚未做定时备份、保留策略清理和自动恢复演练。
```


## 2026-06-30 Update: Vector DB Governance Report

项目新增离线 Vector DB 生产化治理报告：

```text
app/vector_db_governance.py
tests/test_vector_db_governance.py
docs/deployment/qdrant.md
```

生成默认 Qdrant 生产化治理报告：

```powershell
uv run python -m app.cli vector-db-governance-report
```

保存报告：

```powershell
uv run python -m app.cli vector-db-governance-report `
  --output data/reports/vector_db_governance.md
```

生成 Milvus 作为目标后端的对比报告：

```powershell
uv run python -m app.cli vector-db-governance-report `
  --target-backend milvus `
  --output data/reports/vector_db_governance_milvus.md
```

当前结论：

```text
JSON 仍作为本地 fallback 和 rebuild baseline。
Qdrant 是当前项目的主生产候选。
Milvus repository 已实现，仍作为后续 runtime benchmark 对比候选。
```

下一步边界：

```text
Qdrant 已有手动 snapshot API runner，还缺定时 snapshot / restore drill 自动调度。
Milvus 已有本机 backup / restore SOP，仍缺 Milvus Backup Tool 集成和集群级 restore drill。
```


## 2026-06-30 Update: Qdrant Backup Retention

项目新增本地 Qdrant 备份保留策略执行器：

```text
app/qdrant_backup_retention.py
tests/test_qdrant_backup_retention.py
```

默认 dry-run，不删除文件：

```powershell
New-Item -ItemType Directory -Force data/qdrant_backups

uv run python -m app.cli qdrant-backup-retention `
  --backup-dir data/qdrant_backups `
  --keep-last 5
```

显式执行删除：

```powershell
uv run python -m app.cli qdrant-backup-retention `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --apply
```

当前边界：

```text
该命令只管理已经下载到本地目录的 snapshot 文件。
Qdrant snapshot 创建 / 列表 / 下载 / 恢复可通过手动 CLI runner 执行。
尚未接入 cron、Windows Task Scheduler 或 Kubernetes CronJob。
```


## 2026-06-30 Update: Qdrant Snapshot Smoke Plan

项目新增离线 Qdrant snapshot smoke 计划和执行记录模板：

```text
app/qdrant_snapshot_smoke_plan.py
tests/test_qdrant_snapshot_smoke_plan.py
```

生成计划：

```powershell
uv run python -m app.cli qdrant-snapshot-smoke-plan
```

生成执行记录模板：

```powershell
uv run python -m app.cli qdrant-snapshot-smoke-report-template `
  --environment local-compose `
  --operator "<your-name>" `
  --output data/reports/qdrant_snapshot_smoke_report.md
```

计划覆盖：

```text
create snapshot
list snapshot
download snapshot
restore into disposable collection
compare restored collection
retention dry-run
```

当前边界：

```text
该能力只生成 smoke test 计划和执行记录模板。
真实 Qdrant snapshot API 调用已由手动 CLI runner 承担。
不会自动定时创建 snapshot，也不会自动 restore 或删除 collection。
```


## 2026-06-30 Update: Qdrant Snapshot API Runner

项目新增 Qdrant collection snapshot API runner：

```text
app/qdrant_snapshot_client.py
tests/test_qdrant_snapshot_client.py
```

支持命令：

```powershell
uv run python -m app.cli qdrant-snapshot-create `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks

uv run python -m app.cli qdrant-snapshot-list `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks

uv run python -m app.cli qdrant-snapshot-download `
  --url http://127.0.0.1:6333 `
  --collection thesis_chunks `
  --snapshot-name <snapshot_name> `
  --backup-dir data/qdrant_backups

uv run python -m app.cli qdrant-snapshot-restore `
  --url http://127.0.0.1:6333 `
  --restore-collection thesis_chunks_restore `
  --confirm-restore-collection thesis_chunks_restore `
  --snapshot-path data/qdrant_backups/<snapshot_name>
```

当前边界：

```text
该能力是手动 API runner，不是定时任务。
restore 必须显式确认目标 collection。
snapshot 文件仍保存到 data/qdrant_backups/，不提交到 Git。
尚未接入 cron、Windows Task Scheduler 或 Kubernetes CronJob。
```


## 2026-07-01 Update: Qdrant Snapshot Drill Plan

项目新增 Qdrant snapshot drill 计划生成器：

```text
app/qdrant_snapshot_scheduler.py
tests/test_qdrant_snapshot_scheduler.py
```

生成计划：

```powershell
uv run python -m app.cli qdrant-snapshot-drill-plan
```

保存计划：

```powershell
uv run python -m app.cli qdrant-snapshot-drill-plan `
  --output data/reports/qdrant_snapshot_drill_plan.md
```

当前边界：

```text
该能力只生成计划，不调用 Qdrant API。
不会创建 snapshot、下载文件、restore collection 或删除旧备份。
下一步才实现一次性 runner，再考虑 cron / Task Scheduler / Kubernetes CronJob。
```


## 2026-07-01 Update: Qdrant Snapshot Drill Runner

项目新增一次性 Qdrant snapshot drill runner：

```text
qdrant-snapshot-drill-run
```

它把已有能力串成一条显式运维链路：

```text
create snapshot
-> download snapshot
-> retention policy
-> optional restore into disposable collection
-> optional restored-collection benchmark comparison
-> Markdown report
```

示例：

```powershell
uv run python -m app.cli qdrant-snapshot-drill-run `
  --collection thesis_chunks `
  --restore-collection thesis_chunks_restore `
  --confirm-restore-collection thesis_chunks_restore `
  --backup-dir data/qdrant_backups `
  --keep-last 5 `
  --skip-compare
```

当前边界：

```text
这是一次性显式 runner，不是后台定时任务。
restore 必须显式确认目标 collection。
retention 默认 dry-run，只有传入 --apply-retention 才删除旧备份。
尚未创建 cron、Windows Task Scheduler 或 Kubernetes CronJob。
```

### LangGraph 旁路 Demo

完整命令见 `docs/11-LangGraph阶段复盘.md`。常用命令：

```powershell
uv run python -m app.cli graph-summary-demo `
  --topic "系统架构" `
  --thread-id "thread-1" `
  --answer "系统按职责拆分模块，便于定位问题。" `
  --follow-up-answer "这样可以把音频读取、数据集、输出头和服务接口的问题分别定位。"

uv run python -m app.cli graph-task-parity
```

说明：

- `graph-summary-demo` 覆盖从检索、生成问题、等待回答、评价、改写、追问到训练总结的完整旁路链路。
- `graph-task-parity` 将 LangGraph 节点与手写 `DefenseTask` 节点做顺序对齐检查。
- 旁路实现只用于学习对照，不覆盖 `app/task_*` 和 `app/agent.py`。
<!-- docs-update-2026-06-23-feedback-loop -->


## 2026-06-23 更新：Trace 回放与反馈驱动 Benchmark 闭环

当前本机学习版 Agent Harness 已补齐一条完整的数据闭环：

```text
Agent Trace
→ Trace 回放
→ Trace 对比
→ 用户反馈记录
→ Benchmark 候选集导出
→ 人工复核候选样本
→ Accepted Candidate 导出为 Benchmark Draft
→ Draft 字段校验
→ Validated Draft 转成正式 Benchmark 草稿文件
```

最新本地测试基线：

```text
738 passed
```

<!-- docs-update-2026-06-23-hybrid-retrieval -->


## 2026-06-23 更新：BM25 + Vector 混合检索与权重扫描

当前 RAG 链路已从单一路径向量检索扩展为三种检索模式：

```text
vector：语义检索，适合改写后的自然语言问题
bm25：关键词检索，适合模块名、数据集名、算法名等精确术语
hybrid：融合 vector 与 bm25，兼顾语义理解和关键词命中
```

新增命令：

```powershell
python -m app.cli compare-retrievers --output data/reports/retriever_comparison.json

python -m app.cli scan-hybrid-weights `
  --weights "1:0,0.9:0.1,0.8:0.2,0.7:0.3,0.6:0.4,0.5:0.5,0.4:0.6,0.3:0.7,0.2:0.8,0.1:0.9,0:1" `
  --output data/reports/hybrid_weight_scan.json
```

本步骤学习重点：

- 不凭感觉选择 Hybrid 权重。
- 使用 RAG benchmark 自动扫描 `vector_weight` 与 `bm25_weight`。
- 对比 `AVERAGE SCORE`、`MISSING` 和不同 Top-K 下的表现。
- 若多个权重得分相同，优先选择更稳妥的默认值，例如 `vector_weight=0.7`、`bm25_weight=0.3`。

<!-- docs-update-2026-06-23-reranker -->


## 2026-06-23 更新：规则版 Reranker 与 Benchmark 对比

当前已新增规则版 reranker，用于在第一阶段检索后进行二次排序：

```text
query
→ hybrid 检索召回候选 chunk
→ reranker 根据关键词命中、章节特征、短文本惩罚重新排序
→ 截取最终 top_k 进入 RAG 评分或回答生成
```

新增命令示例：

```powershell
python -m app.cli evaluate-rag `
  --retriever hybrid `
  --vector-weight 0.7 `
  --bm25-weight 0.3 `
  --rerank `
  --rerank-candidate-multiplier 3
```

本轮真实 benchmark 对比：

```text
hybrid no rerank: average_score = 0.8667
hybrid rerank x3: average_score = 0.8333
hybrid rerank x5: average_score = 0.8333
```

结论：

- 当前规则版 reranker 没有提升这份 benchmark，反而降低了平均分。
- 主要原因是规则打分偏向中文关键词命中，对 `LanguageAwareFrontend`、`BiLSTM` 等英文术语混合问题不够友好。
- 当前默认 RAG 检索不启用 reranker，保留 `--rerank` 作为实验开关。
- reranker 的价值不是“加上就更好”，而是必须通过 benchmark 验证是否真的改善召回质量。

<!-- docs-update-2026-06-23-query-rewrite -->


## 2026-06-23 更新：规则版 Query Rewrite 与 Benchmark 对比

当前已新增规则版 query rewrite，用于在检索前改写用户问题：

```text
用户原始问题
→ 按规则补充论文中的关键术语
→ 使用改写后的 query 执行 hybrid 检索
→ 保留原 query 和 rewritten query 进入评估报告
```

新增命令示例：

```powershell
python -m app.cli evaluate-rag `
  --retriever hybrid `
  --vector-weight 0.7 `
  --bm25-weight 0.3 `
  --rewrite-query
```

本轮真实 benchmark 对比：

```text
hybrid no query rewrite: average_score = 0.8667
hybrid with query rewrite: average_score = 1.0
hybrid with query rewrite + rerank x3: average_score = 0.925
```

结论：

- 规则版 query rewrite 对当前 benchmark 有明显正收益。
- 它主要修复了“语言感知前端”问题中英文术语召回不足的问题。
- 当前推荐默认实验策略是：`hybrid + query rewrite`。
- 当前不推荐默认叠加规则版 reranker，因为 `rewrite + rerank` 会从 `1.0` 降到 `0.925`。
- query rewrite 改变的是“拿什么去搜”，reranker 改变的是“搜到后怎么排”。两者都必须单独做 benchmark 对比。

<!-- docs-update-2026-06-23-multi-query -->


## 2026-06-23 更新：Multi-Query Retrieval 与 Benchmark 对比

当前已新增规则版 multi-query retrieval，用于为同一个用户问题生成多个检索视角：

```text
用户原始问题
→ 生成多个 search query
→ 分别执行检索
→ 合并去重候选结果
→ 按分数截取最终 top_k
```

新增命令示例：

```powershell
python -m app.cli evaluate-rag `
  --retriever hybrid `
  --vector-weight 0.7 `
  --bm25-weight 0.3 `
  --multi-query
```

本轮真实 benchmark 结果：

```text
hybrid + multi-query: average_score = 1.0
```

结论：

- multi-query retrieval 对当前 benchmark 能达到满分召回。
- 它解决的是“同一个问题可以从多个检索角度表达”的问题。
- 与 query rewrite 不同，query rewrite 生成一个增强后的 query，multi-query 会保留多个 query 并合并检索结果。
- 当前已验证 `hybrid + multi-query` 可用，后续可以继续对比 `hybrid + query rewrite`、`hybrid + query rewrite + multi-query` 的成本和稳定性。

<!-- docs-update-2026-06-23-model-reranker -->


## 2026-06-23 更新：LLM 模型版 Reranker 与 Benchmark 对比

当前已新增 LLM 模型版 reranker，用于在第一阶段召回之后，让模型对 `query + candidate chunk` 进行相关性评分：

```text
query
→ hybrid / vector / bm25 召回候选 chunk
→ LLM reranker 对每个候选 chunk 输出 0~1 相关性分数
→ 按模型分数重新排序
→ 截取最终 top_k
```

新增命令示例：

```powershell
python -m app.cli evaluate-rag `
  --retriever hybrid `
  --vector-weight 0.7 `
  --bm25-weight 0.3 `
  --model-rerank `
  --model-rerank-candidate-multiplier 2
```

本轮真实 benchmark 结果：

```text
hybrid + model reranker x2: average_score = 0.9667
missing: 卷积层
```

结论：

- 模型版 reranker 工程链路已经跑通。
- 当前 benchmark 上，模型版 reranker 没有超过 `hybrid + query rewrite` 或 `hybrid + multi-query`。
- 模型版 reranker 调用成本明显更高，因为每个候选 chunk 都需要一次 LLM 评分。
- 当前不建议默认启用 `--model-rerank`，保留为实验开关。
- 本阶段学到的关键点是：更“智能”的排序器不一定更适合当前数据，必须用 benchmark 和成本一起验证。

<!-- docs-update-2026-06-23-llm-query-rewrite -->


## 2026-06-23 更新：LLM Query Rewrite 与 Benchmark 对比

当前已新增 LLM query rewrite，用于让模型根据用户问题生成更适合检索的 query：

```text
用户原始问题
→ LLM 生成检索 query
→ 使用生成后的 query 执行 RAG 检索
→ 在报告中保留原始 query 与 rewritten query
```

新增命令示例：

```powershell
python -m app.cli evaluate-rag `
  --retriever hybrid `
  --vector-weight 0.7 `
  --bm25-weight 0.3 `
  --llm-rewrite-query
```

本轮真实 benchmark 对比：

```text
hybrid + LLM query rewrite: average_score = 0.8333
hybrid + LLM query rewrite + multi-query: average_score = 1.0
```

结论：

- LLM query rewrite 单独使用时不稳定，本轮把 `LanguageAwareFrontend / BiLSTM / 卷积层` 等关键术语改丢，导致召回下降。
- LLM query rewrite + multi-query 可以恢复到满分召回，因为 multi-query 会补充关键检索视角。
- 组合策略的成本更高，本轮出现 5 次 LLM rewrite 调用和 10 次 query embedding miss。
- 当前仍不建议默认启用 LLM query rewrite，保留为实验开关。
- 本阶段学到的关键点是：LLM 参与检索前处理并不天然更好，必须同时评估召回、missing keywords、cache hits / misses 和调用成本。

<!-- docs-update-2026-06-23-retrieval-strategy-comparison -->


## 2026-06-23 更新：检索策略组合对比

当前已新增统一的检索策略组合对比命令：

```powershell
python -m app.cli compare-retrieval-strategies `
  --output data/reports/retrieval_strategy_comparison.json
```

默认对比不额外调用 LLM 的低成本组合：

```text
hybrid
hybrid + query rewrite
hybrid + multi-query
hybrid + query rewrite + multi-query
hybrid + reranker
```

如需把 LLM query rewrite 和模型版 reranker 纳入扫描，可显式增加：

```powershell
python -m app.cli compare-retrieval-strategies `
  --include-expensive `
  --output data/reports/retrieval_strategy_comparison_expensive.json
```

本轮真实 benchmark 结果：

```text
hybrid: average_score = 0.8667
hybrid + query rewrite: average_score = 1.0
hybrid + multi-query: average_score = 1.0
hybrid + query rewrite + multi-query: average_score = 0.925
hybrid + reranker: average_score = 0.8333
```

结论：

- 当前推荐低成本默认策略是 `hybrid + query rewrite`。
- `hybrid + multi-query` 同样达到满分，但会产生更多 query embedding 检索成本。
- `query rewrite + multi-query` 在当前规则下没有继续提升，反而出现训练流程类关键词遗漏。
- reranker 在当前 benchmark 上继续下降，因此只保留为实验开关。
- 本阶段学到的关键点是：检索组件不是叠得越多越好，必须用同一份 benchmark 扫描组合收益、缺失关键词和调用成本。

### Trace 回放与对比

```powershell
python -m app.cli replay-agent-trace

python -m app.cli compare-agent-traces `
  --baseline-file data/traces/agent_trace.jsonl `
  --current-file data/traces/agent_trace.jsonl `
  --baseline-line-number 1 `
  --current-line-number 2
```

Trace 对比会检查工具调用顺序、工具成功 / 失败序列、失败工具数、最终回答是否变空，以及 token、cost、duration 的变化。

### Feedback → Benchmark 数据闭环

记录反馈：

```powershell
python -m app.cli record-feedback `
  --source-type agent_trace `
  --source-id line:1 `
  --rating 2 `
  --comment "工具选择不稳定，需要加入回归样本" `
  --tag needs_benchmark `
  --tag routing_error
```

查看反馈统计：

```powershell
python -m app.cli summarize-feedback
```

导出候选样本：

```powershell
python -m app.cli export-feedback-candidates `
  --feedback-file data/feedback/feedback.jsonl `
  --output data/benchmark_candidates/candidates.json `
  --max-rating 2 `
  --tag needs_benchmark
```

人工复核候选样本：

```powershell
python -m app.cli review-benchmark-candidate `
  --file data/benchmark_candidates/candidates.json `
  --candidate-id feedback-xxx `
  --status accepted `
  --reviewer buan496 `
  --reason "适合作为工具路由回归样本"

python -m app.cli summarize-benchmark-candidates `
  --file data/benchmark_candidates/candidates.json
```

导出 benchmark draft：

```powershell
python -m app.cli export-benchmark-draft `
  --candidate-file data/benchmark_candidates/candidates.json `
  --output data/benchmark_candidates/benchmark_draft.json
```

校验 benchmark draft：

```powershell
python -m app.cli validate-benchmark-draft `
  --file data/benchmark_candidates/benchmark_draft.json `
  --fail-on-error
```

将校验通过的 draft 转成正式 benchmark 格式的新文件：

```powershell
python -m app.cli export-validated-benchmark-draft `
  --draft-file data/benchmark_candidates/benchmark_draft.json `
  --output-directory data/benchmark_candidates
```

可能生成：

```text
rag_benchmark_draft.json
faithfulness_benchmark_draft.json
agent_routing_benchmark_draft.json
manual_benchmark_draft.json
```

这些文件仍然是草稿，不会覆盖现有正式 benchmark。正式合并前需要人工检查。

<!-- docs-update-2026-06-24-tool-registry-metadata -->


## 2026-06-24 更新：Tool Registry 元信息增强

本阶段新增工具治理能力：

- 新增 `app/tool_registry.py`
- 新增 `ToolMetadata` 和 `RegisteredTool`
- 将工具函数、OpenAI Tool Schema、工程治理元信息统一注册
- `tool_executor.py` 从注册表构建工具函数白名单
- 新增 `list-tools` CLI，用于查看工具可发现性与治理参数

查看工具注册表：

```powershell
uv run python -m app.cli list-tools
```

这一步区分了两个概念：

```text
Tool Schema：给 LLM 看的函数调用格式，描述参数怎么传。
Tool Metadata：给工程系统看的治理信息，描述权限、owner、enabled、timeout、retry、结果长度限制等。
```

这一步是 MCP / Sub-Agent 的前置基础：MCP 本质上也需要把外部能力标准化为可发现、可描述、可调用、可治理的工具。

<!-- docs-update-2026-06-24-tool-execution-governance -->


## 2026-06-24 更新：工具执行治理强约束

本阶段把 `ToolMetadata` 从展示信息接入执行链路：

- 执行工具前会读取注册表中的 metadata
- `enabled=False` 的工具会被拒绝执行
- 非白名单 permission 会被拒绝执行
- 每个工具可以使用自己的 `timeout_seconds`
- 每个工具可以使用自己的 `retry_count`
- 每个工具可以使用自己的 `result_max_characters`
- 旧的 `TOOL_REGISTRY` fake tool 注入仍保留，用于测试和临时实验

这一步的意义：

```text
工具治理不能只停留在文档和展示层。
真正的 Agent Harness 必须在执行器入口处做强约束。
否则模型或上层代码仍可能绕过工具注册表，直接调用不该调用的能力。
```

<!-- docs-update-2026-06-24-sub-agent-specs -->


## 2026-06-24 更新：本地 SubAgentSpec 规格定义

本阶段新增本地 Sub-Agent 规格层：

- 新增 `app/sub_agent_specs.py`
- 新增 `SubAgentSpec`
- 定义候选子 Agent：
  - `retrieval_agent`
  - `defense_question_agent`
  - `answer_evaluation_agent`
  - `follow_up_agent`
  - `training_record_agent`
- 每个规格声明：
  - `role`
  - `description`
  - `allowed_tools`
  - `input_fields`
  - `output_fields`
  - `max_steps`
- 新增 `list-sub-agents` CLI

查看本地 Sub-Agent 规格：

```powershell
uv run python -m app.cli list-sub-agents
```

当前边界：

```text
SubAgentSpec 只定义子 Agent 能做什么。
当前还不做真实多 Agent 调度。
当前还不让 Sub-Agent 自动调用工具。
```

<!-- docs-update-2026-06-24-sub-agent-permission-guard -->


## 2026-06-24 更新：本地 Sub-Agent 工具权限校验

本阶段新增子 Agent 级工具权限边界：

- 新增 `app/sub_agent_permissions.py`
- 新增 `SubAgentToolPermissionResult`
- 新增 `check_sub_agent_tool_permission()`
- 新增 `can_sub_agent_use_tool()`
- 新增 `validate_sub_agent_tool_call()`
- 新增 `check-sub-agent-tool` CLI

手动检查某个子 Agent 是否允许调用某个工具：

```powershell
uv run python -m app.cli check-sub-agent-tool `
  --sub-agent retrieval_agent `
  --tool search_thesis
```

这一步的意义：

```text
ToolMetadata 解决单个工具能不能被执行。
SubAgentSpec.allowed_tools 解决某个子 Agent 能不能调用某个工具。
多 Agent 系统必须先有权限边界，再考虑自动调度。
```

<!-- docs-update-2026-06-24-sub-agent-execution-plan -->


## 2026-06-24 更新：本地 Sub-Agent 执行计划对象

本阶段新增本地 Sub-Agent 计划层：

- 新增 `app/sub_agent_plan.py`
- 新增 `SubAgentExecutionPlan`
- 新增 `create_sub_agent_execution_plan()`
- 新增 `validate_sub_agent_plan_input()`
- 新增 `plan-sub-agent-call` CLI

生成一个只规划、不执行的 Sub-Agent 工具调用计划：

```powershell
uv run python -m app.cli plan-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --arguments '{"query":"系统架构"}'
```

当前边界：

```text
计划对象只描述谁准备用什么工具、输入是什么、预期输出是什么。
它不执行工具。
它不调用 LLM。
它不做多 Agent 自动调度。
```

这一步的意义：

```text
先有计划，再有执行。
多 Agent 调度前必须先把 role、tool、arguments、expected output 和 max_steps 固化为可审计对象。
```

<!-- docs-update-2026-06-24-sub-agent-plan-powershell-arguments -->


## 2026-06-24 补充：Sub-Agent Plan 的 PowerShell 友好参数

`plan-sub-agent-call` 支持两种传参方式：

JSON 方式：

```powershell
uv run python -m app.cli plan-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --arguments '{"query":"系统架构"}'
```

PowerShell 更推荐 KEY=VALUE 方式，避免 JSON 引号被 shell 吃掉：

```powershell
uv run python -m app.cli plan-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --argument query=系统架构
```

<!-- docs-update-2026-06-24-sub-agent-plan-trace -->


## 2026-06-24 更新：Sub-Agent Plan Trace / Audit 记录

本阶段新增 Sub-Agent 计划审计能力：

- 新增 `app/sub_agent_plan_trace.py`
- 新增 `save_sub_agent_plan_trace()`
- 新增 `load_sub_agent_plan_traces()`
- 新增 `summarize_sub_agent_plan_traces()`
- `plan-sub-agent-call` 支持 `--save-trace`
- 新增 `analyze-sub-agent-plans` CLI

保存计划 trace：

```powershell
uv run python -m app.cli plan-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --argument query=系统架构 `
  --save-trace
```

分析计划 trace：

```powershell
uv run python -m app.cli analyze-sub-agent-plans
```

这一步的意义：

```text
Sub-Agent 还没有真正执行工具之前，计划本身就应该可以被审计。
先记录 plan，再执行 plan，后续才能做 trace replay、权限审计和回归对比。
```

<!-- docs-update-2026-06-24-sub-agent-dry-run -->


## 2026-06-24 更新：单步 Sub-Agent Dry-Run

本阶段新增 Sub-Agent dry-run 能力：

- 新增 `app/sub_agent_dry_run.py`
- 新增 `SubAgentDryRunReport`
- 新增 `dry_run_sub_agent_tool_call()`
- 新增 `dry-run-sub-agent-call` CLI
- dry-run 会生成执行计划、校验工具权限、可选保存 trace，但不会执行真实工具

普通 dry-run：

```powershell
uv run python -m app.cli dry-run-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --argument query=系统架构
```

保存 dry-run trace：

```powershell
uv run python -m app.cli dry-run-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --argument query=系统架构 `
  --save-trace
```

这一步的意义：

```text
dry-run 是真实执行前的安全演练。
它让系统先回答“谁要调用什么工具、参数是什么、权限是否允许、计划是否可审计”，再决定是否进入真实执行。
```

<!-- docs-update-2026-06-24-sub-agent-plan-comparison -->


## 2026-06-24 更新：Sub-Agent Plan Replay / Comparison

本阶段新增 Sub-Agent 计划级回归对比能力：

- 新增 `app/sub_agent_plan_comparator.py`
- 新增 `compare_sub_agent_plan_records()`
- 新增 `compare-sub-agent-plans` CLI
- 支持比较两份 Sub-Agent plan trace
- 自动检测新增、删除、字段变化和稳定计划数量

对比两份 trace：

```powershell
uv run python -m app.cli compare-sub-agent-plans `
  --baseline data/traces/sub_agent_plan_baseline.jsonl `
  --candidate data/traces/sub_agent_plan_candidate.jsonl
```

当前比较策略：

```text
忽略 plan_id 和 created_at，因为它们每次生成都会变化。
以 sub_agent_name + tool_name + tool_arguments 作为计划身份。
对 role、expected_output_fields、max_steps、status 做稳定性对比。
```

这一步的意义：

```text
在真正执行 Sub-Agent 前，先保证“计划”本身可以做回归检测。
如果某次改动让同样输入生成了不同计划，系统应该能提前发现。
```

<!-- docs-update-2026-06-24-sub-agent-single-step-executor -->


## 2026-06-24 更新：最小真实 Sub-Agent Executor

本阶段新增单步 Sub-Agent 执行能力：

- 新增 `app/sub_agent_executor.py`
- 新增 `app/sub_agent_execution_trace.py`
- 新增 `execute_sub_agent_tool_call()`
- 新增 `execute-sub-agent-call` CLI
- 新增 `analyze-sub-agent-executions` CLI
- 执行前复用 permission guard 与 execution plan
- 执行过程复用统一工具执行器的 timeout、retry、结果截断和错误标准化能力

执行一次允许的 Sub-Agent 工具调用：

```powershell
uv run python -m app.cli execute-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --argument query=系统架构
```

保存执行 trace：

```powershell
uv run python -m app.cli execute-sub-agent-call `
  --sub-agent retrieval_agent `
  --tool search_thesis `
  --argument query=系统架构 `
  --save-trace
```

分析执行 trace：

```powershell
uv run python -m app.cli analyze-sub-agent-executions
```

当前边界：

```text
只执行一个 Sub-Agent。
只执行一个工具。
只执行一步。
不做 LLM 自动调度。
不做并行。
不替换现有 app/agent.py 或 app/task_* 工作流。
```

<!-- docs-update-2026-06-25-sub-agent-execution-comparison -->


## 2026-06-25 更新：Sub-Agent Execution Replay / Comparison

本阶段新增 Sub-Agent 执行级回归对比能力：

- 新增 `app/sub_agent_execution_comparator.py`
- 新增 `compare_sub_agent_execution_records()`
- 新增 `compare-sub-agent-executions` CLI
- 支持比较两份 Sub-Agent execution trace
- 支持检测执行新增、删除、成功状态变化、错误类型变化、结果结构变化和耗时退化

对比两份 execution trace：

```powershell
uv run python -m app.cli compare-sub-agent-executions `
  --baseline data/traces/sub_agent_execution_baseline.jsonl `
  --candidate data/traces/sub_agent_execution_candidate.jsonl
```

设置耗时退化阈值：

```powershell
uv run python -m app.cli compare-sub-agent-executions `
  --baseline data/traces/sub_agent_execution_baseline.jsonl `
  --candidate data/traces/sub_agent_execution_candidate.jsonl `
  --max-duration-ratio 2.0
```

当前比较策略：

```text
以 sub_agent_name + tool_name + tool_arguments 作为执行身份。
比较 success、result JSON 是否有效、result JSON key 集合、error_type。
当 candidate duration 超过 baseline duration 的指定倍数时，标记为耗时退化。
```

<!-- docs-update-2026-06-25-sub-agent-execution-quality-gate -->


## 2026-06-25 更新：Sub-Agent Execution Quality Gate

`compare-sub-agent-executions` 现在默认作为质量门禁执行：

```text
PASSED: True  -> 退出码 0
PASSED: False -> 退出码 1
```

默认门禁模式：

```powershell
uv run python -m app.cli compare-sub-agent-executions `
  --baseline data/traces/sub_agent_execution_baseline.jsonl `
  --candidate data/traces/sub_agent_execution_candidate.jsonl
```

只查看报告、不让命令失败：

```powershell
uv run python -m app.cli compare-sub-agent-executions `
  --baseline data/traces/sub_agent_execution_baseline.jsonl `
  --candidate data/traces/sub_agent_execution_candidate.jsonl `
  --allow-fail
```

这一步的意义：

```text
比较报告如果不能影响退出码，就很难进入 CI 或自动化质量门禁。
将 Sub-Agent execution comparison 转成可失败命令后，后续可以直接接入本地检查和 GitHub Actions。
```

<!-- docs-update-2026-06-25-local-quality-gate-sub-agent -->


## 2026-06-25 更新：本地 Quality Gate 接入 Sub-Agent Execution

本阶段新增本地质量门禁入口：

- 新增 `app/local_quality_gate.py`
- 新增 `local-quality-gate` CLI
- 默认执行 `uv run pytest -q`
- 可选接入 Sub-Agent execution comparison
- 任一检查失败时，命令退出码为 1

默认本地质量门禁：

```powershell
uv run python -m app.cli local-quality-gate
```

接入 Sub-Agent execution comparison：

```powershell
uv run python -m app.cli local-quality-gate `
  --sub-agent-execution-baseline data/traces/sub_agent_execution_baseline.jsonl `
  --sub-agent-execution-candidate data/traces/sub_agent_execution_candidate.jsonl
```

只查看报告、不让命令失败：

```powershell
uv run python -m app.cli local-quality-gate `
  --sub-agent-execution-baseline data/traces/sub_agent_execution_baseline.jsonl `
  --sub-agent-execution-candidate data/traces/sub_agent_execution_candidate.jsonl `
  --allow-fail
```

当前边界：

```text
本阶段只接入本地质量门禁。
暂不修改 GitHub Actions。
Sub-Agent execution trace 仍由调用方显式提供，不自动生成 baseline/candidate。
```

<!-- docs-update-2026-06-25-sub-agent-execution-fixtures -->


## 2026-06-25 更新：Sub-Agent Execution 离线 Fixture

本阶段新增稳定的 Sub-Agent execution comparison fixture：

- `tests/fixtures/sub_agent_execution/baseline.jsonl`
- `tests/fixtures/sub_agent_execution/candidate.jsonl`

用途：

```text
在不调用真实工具、不访问在线 API 的情况下，验证 local-quality-gate 可以稳定执行 Sub-Agent execution comparison。
```

离线验证命令：

```powershell
uv run python -m app.cli local-quality-gate `
  --skip-pytest `
  --sub-agent-execution-baseline tests/fixtures/sub_agent_execution/baseline.jsonl `
  --sub-agent-execution-candidate tests/fixtures/sub_agent_execution/candidate.jsonl
```

预期结果：

```text
LOCAL QUALITY GATE
PASSED: True
CHECK: sub_agent_execution_comparison
PASSED: True
```

<!-- docs-update-2026-06-25-ci-local-quality-gate -->


## 2026-06-25 更新：CI 接入本地 Quality Gate

CI 的离线质量门禁现在包含 Sub-Agent execution comparison：

```text
pytest
offline regression quality gate
Sub-Agent execution quality gate
```

GitHub Actions 使用离线 fixture：

```text
tests/fixtures/sub_agent_execution/baseline.jsonl
tests/fixtures/sub_agent_execution/candidate.jsonl
```

CI 执行命令：

```bash
uv run --frozen python -m app.cli local-quality-gate \
  --skip-pytest \
  --sub-agent-execution-baseline tests/fixtures/sub_agent_execution/baseline.jsonl \
  --sub-agent-execution-candidate tests/fixtures/sub_agent_execution/candidate.jsonl
```

边界：

```text
CI 只使用离线 fixture。
CI 不执行真实 Sub-Agent 工具。
CI 不调用在线 LLM/API。
online-evaluation workflow 保持不变。
```

<!-- docs-update-2026-06-25-sub-agent-gate-report-artifact -->


## 2026-06-25 更新：Sub-Agent Gate 报告归档

`local-quality-gate` 支持输出 JSON 报告：

```powershell
uv run python -m app.cli local-quality-gate `
  --skip-pytest `
  --sub-agent-execution-baseline tests/fixtures/sub_agent_execution/baseline.jsonl `
  --sub-agent-execution-candidate tests/fixtures/sub_agent_execution/candidate.jsonl `
  --output data/reports/sub_agent_execution_gate.json
```

CI 中会把报告写入：

```text
data/reports/sub_agent_execution_gate.json
```

该文件会随 `offline-quality-reports` artifact 上传，便于查看 Sub-Agent gate 的结构化结果。

<!-- docs-update-2026-06-25-sub-agent-gate-markdown-report -->


## 2026-06-25 更新：Sub-Agent Gate Markdown 报告

`local-quality-gate` 支持输出 Markdown 报告：

```powershell
uv run python -m app.cli local-quality-gate `
  --skip-pytest `
  --sub-agent-execution-baseline tests/fixtures/sub_agent_execution/baseline.jsonl `
  --sub-agent-execution-candidate tests/fixtures/sub_agent_execution/candidate.jsonl `
  --output data/reports/sub_agent_execution_gate.json `
  --markdown-output data/reports/sub_agent_execution_gate.md
```

CI 中会同时输出：

```text
data/reports/sub_agent_execution_gate.json
data/reports/sub_agent_execution_gate.md
```

JSON 用于机器读取，Markdown 用于人工快速查看。

<!-- docs-update-2026-06-25-sub-agent-phase-summary -->


## 2026-06-25 更新：Sub-Agent 阶段复盘

新增阶段复盘文档：

```text
docs/07-Sub-Agent阶段复盘.md
```

该文档总结：

- 当前 Sub-Agent Harness 已完成能力
- 当前明确边界
- 已学到的核心概念
- 未完成能力
- 下一阶段建议

阶段结论：

```text
Sub-Agent 主线已经完成本地学习版最小可审计 Harness。
下一阶段建议进入 Trace Replay / Feedback 闭环，而不是继续堆更多工具。
```

<!-- docs-update-2026-06-25-trace-replay-feedback -->


## 2026-06-25 更新：Trace Replay / Feedback 闭环

本阶段新增一条从失败 trace 到 benchmark 草稿的本地闭环：

```text
trace replay
-> feedback record
-> benchmark candidate
-> human review
-> benchmark draft
-> draft validation
-> validated benchmark draft export
```

新增能力：

- 通用 JSONL trace replay 归一化
- Agent / Sub-Agent plan / Sub-Agent execution trace 汇总
- trace replay issue 自动转 feedback record
- trace feedback 写入 `feedback.jsonl`
- feedback 导出 benchmark candidate
- candidate 人工 review 后导出 benchmark draft
- benchmark draft 校验
- validated draft 导出为正式 benchmark 草稿文件

核心命令：

```powershell
uv run python -m app.cli replay-trace `
  --file data/traces/agent_trace.jsonl `
  --source-type agent

uv run python -m app.cli trace-feedback `
  --file data/traces/agent_trace.jsonl `
  --source-type agent `
  --feedback-file data/feedback.jsonl

uv run python -m app.cli export-feedback-candidates `
  --feedback-file data/feedback.jsonl `
  --output data/reports/feedback_candidates.json

uv run python -m app.cli review-benchmark-candidate `
  --file data/reports/feedback_candidates.json `
  --candidate-id <CANDIDATE_ID> `
  --status accepted `
  --reviewer buan496 `
  --reason "适合作为回归样本"

uv run python -m app.cli export-benchmark-draft `
  --candidate-file data/reports/feedback_candidates.json `
  --output data/reports/benchmark_draft.json

uv run python -m app.cli validate-benchmark-draft `
  --file data/reports/benchmark_draft.json `
  --fail-on-error

uv run python -m app.cli export-validated-benchmark-draft `
  --draft-file data/reports/benchmark_draft.json `
  --output-directory data/reports/validated_benchmarks
```

边界：

```text
失败 trace 不会直接进入正式 benchmark。
必须经过 feedback、candidate、human review、draft、validation。
当前只完成本地学习版数据治理闭环，不接服务器和数据库。
```

<!-- docs-update-2026-06-25-task-memory-export -->


## 2026-06-25 更新：Task 训练总结沉淀到长期记忆

本阶段新增显式任务记忆导出能力：

```text
completed DefenseTask
-> summarize_training step
-> summary / weaknesses
-> long_term_memory.json
```

核心命令：

```powershell
uv run python -m app.cli export-task-memory `
  --task-id <TASK_ID> `
  --directory data/defense_tasks `
  --memory-path data/long_term_memory.json
```

设计边界：

```text
只允许已完成任务导出。
必须存在已完成的 summarize_training 步骤。
不会在任务完成时自动写入 memory。
采用显式命令沉淀，避免长期记忆被低质量内容污染。
```

该能力与已有 chat memory injection 形成闭环：

```text
训练任务总结
-> 长期记忆
-> 下一轮 chat / Agent 上下文检索
```

<!-- docs-update-2026-06-25-memory-phase-summary -->


## 2026-06-25 更新：Memory 阶段复盘

新增阶段复盘文档：

```text
docs/08-Memory阶段复盘.md
```

该文档总结：

- Profile Memory
- Weakness Memory
- Training Summary Memory
- Memory Retrieval
- Memory Pruning
- Chat Memory Injection
- Task Summary Memory Export

阶段结论：

```text
Memory 不是聊天历史，也不是日志。
Memory 是经过筛选、可检索、可裁剪、可显式沉淀的长期上下文资产。
```

下一阶段建议：

```text
Memory 质量治理
-> memory audit
-> duplicate report
-> dry-run prune
-> hit audit
-> context report
```

<!-- docs-update-2026-06-25-memory-quality-governance -->


## 2026-06-25 更新：Memory 质量治理

本阶段新增本地长期记忆质量治理能力：

```text
memory-audit
-> memory-prune --dry-run
-> memory-hit-audit
-> memory-context-report
```

核心命令：

```powershell
uv run python -m app.cli memory-audit `
  --path data/long_term_memory.json

uv run python -m app.cli memory-prune `
  --max-weaknesses 20 `
  --max-summaries 10 `
  --dry-run `
  --path data/long_term_memory.json

uv run python -m app.cli memory-hit-audit `
  --query "系统架构" `
  --max-weaknesses 5 `
  --max-summaries 3 `
  --path data/long_term_memory.json

uv run python -m app.cli memory-context-report `
  --query "系统架构" `
  --max-weaknesses 5 `
  --max-summaries 3 `
  --path data/long_term_memory.json
```

能力边界：

```text
memory-audit 只读，不修改文件。
memory-prune --dry-run 只预览裁剪结果，不写入。
memory-hit-audit 解释哪些 memory 被 query 命中。
memory-context-report 展示最终注入 prompt 的 memory context。
```

阶段结论：

```text
长期记忆必须可审计、可预览、可解释。
不能只做写入和检索，也要能检查污染、重复、命中和最终注入内容。
```

<!-- docs-update-2026-06-26-langgraph-phase-summary -->


## 2026-06-26 更新：LangGraph 旁路迁移阶段复盘

新增阶段复盘文档：

```text
docs/11-LangGraph阶段复盘.md
```

本阶段完成的 LangGraph 旁路能力：

```text
demo_task
interrupt_demo
checkpointer_demo
persistent_checkpoint_demo
conditional_demo
evaluate_rewrite_demo
follow_up_demo
summary_demo
parity_report
```

阶段结论：

```text
LangGraph 是编排层，不是业务逻辑替代品。
迁移前必须有 Task Workflow Contract。
迁移后必须有 Parity Report。
旁路迁移优先于覆盖式重构。
```

