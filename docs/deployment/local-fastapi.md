# FastAPI 本地服务化运行说明

## 定位

当前 FastAPI 层是本机服务化学习版本，目标是把已有 CLI / Agent Harness 能力逐步暴露成 HTTP API。

本阶段只覆盖本地开发与接口验证，不代表生产部署完成。

## 启动前提

确认依赖已安装：

```powershell
uv sync
```

确认测试通过：

```powershell
uv run pytest -q
```

如果需要调用真实 RAG 搜索，需要先准备：

```text
data/vector_store.json
data/vector_store_meta.json
.env 中的 EMBEDDING_API_KEY / EMBEDDING_BASE_URL / EMBEDDING_MODEL
```

## 启动服务

```powershell
uv run uvicorn app.api.main:app --reload
```

默认访问地址：

```text
http://127.0.0.1:8000
```

Swagger 文档：

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON：

```text
http://127.0.0.1:8000/openapi.json
```

## 当前 API

### 基础状态

```text
GET /health
GET /version
```

示例：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Invoke-RestMethod http://127.0.0.1:8000/version
```

### Document Upload

```text
POST /documents/upload
```

Example:

```powershell
curl.exe -F "file=@data/thesis.pdf" http://127.0.0.1:8000/documents/upload
```

Current behavior:

- accepts `.pdf`, `.txt`, and `.md`
- saves uploaded files under `data/uploads/`
- returns document id, stored path, original filename, suffix, content type, and size
- rejects empty files
- rejects unsupported suffixes
- rejects files larger than `DOCUMENT_UPLOAD_MAX_BYTES`

### SSE Streaming

```text
GET /stream/echo
GET /stream/chat
```

Echo example:

```powershell
curl.exe -N "http://127.0.0.1:8000/stream/echo?message=hello-agent&chunk_size=3"
```

LLM streaming example:

```powershell
curl.exe -N "http://127.0.0.1:8000/stream/chat?message=请简要说明你的系统架构"
```

Current behavior:

- returns `text/event-stream`
- `/stream/echo` emits `chunk` events for local text chunks
- `/stream/chat` emits `chunk` events from the LLM streaming response
- emits a final `done` event
- emits an `error` event if the LLM stream fails after streaming starts
- rejects blank messages
- validates `chunk_size`

### WebSocket Task Control

```text
WS /ws/tasks/{task_id}
```

Supported client messages:

```json
{"type": "ping"}
{"type": "start_next_step", "input": {"topic": "系统架构"}}
{"type": "execute_current_step"}
{"type": "submit_answer", "answer": "模块化便于定位问题"}
{"type": "submit_follow_up_answer", "answer": "可以结合特征处理模块说明排错过程"}
{"type": "analyze_task"}
```

Possible server messages:

```json
{"type": "connected", "task_id": "..."}
{"type": "pong", "task_id": "..."}
{"type": "step_started", "task": {}, "step": {}, "path": "..."}
{"type": "step_completed", "task": {}, "step": {}, "path": "..."}
{"type": "answer_submitted", "task": {}, "step": {}, "path": "..."}
{"type": "follow_up_answer_submitted", "task": {}, "step": {}, "path": "..."}
{"type": "task_analysis", "analysis": {}}
{"type": "error", "message": "..."}
```

Current scope:

- provides a bidirectional control channel for `DefenseTask`
- reuses the existing task service layer
- does not replace the HTTP Task API
- does not include browser UI yet

### Async Task API

当前已暴露后台任务 API，用于验证长任务生命周期：

```text
POST   /async-tasks
GET    /async-tasks/{task_id}
DELETE /async-tasks/{task_id}
```

创建后台任务：

```powershell
curl.exe -X POST http://127.0.0.1:8000/async-tasks `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"demo\",\"delay_seconds\":1,\"result\":\"ok\"}"
```

查询后台任务：

```powershell
curl.exe http://127.0.0.1:8000/async-tasks/<TASK_ID>
```

取消后台任务：

```powershell
curl.exe -X DELETE http://127.0.0.1:8000/async-tasks/<TASK_ID>
```

Current scope:

- uses `AsyncTaskRunner`
- limits concurrently running tasks with `ASYNC_TASK_MAX_CONCURRENT_TASKS`
- persists task records to `ASYNC_TASK_STORE_PATH`
- demo job only sleeps and returns a configured result
- validates task creation, status query, completion and cancellation
- restores completed / failed / cancelled task records after process restart
- marks unfinished tasks as `TaskInterruptedError` after process restart
- does not execute real `DefenseTask` steps yet
- does not implement cross-process queue sharing or idempotency yet

### RAG 状态与检索

```text
GET  /rag/status
POST /rag/search
```

RAG 状态：

```powershell
Invoke-RestMethod http://127.0.0.1:8000/rag/status
```

RAG 搜索：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/rag/search `
  -ContentType "application/json" `
  -Body '{"query":"系统架构包括哪些模块？","top_k":3}'
```

说明：

- `/rag/status` 只检查向量库文件和元信息文件是否存在。
- `/rag/search` 会加载本地向量库，并调用 embedding 函数生成 query embedding。
- 如果向量库不存在，接口返回 `503`。
- 如果 query 为空，接口返回 `422`。

### Task State API

当前已暴露 `DefenseTask` 的核心 HTTP 操作：

```text
POST /tasks
GET  /tasks/{task_id}
POST /tasks/{task_id}/steps/start
POST /tasks/{task_id}/steps/execute
POST /tasks/{task_id}/steps/execute-async
POST /tasks/{task_id}/answer
POST /tasks/{task_id}/follow-up-answer
GET  /tasks/{task_id}/analysis
POST /tasks/{task_id}/report/export
```

创建任务：

```powershell
$task = Invoke-RestMethod `
  -Method Post `
  -Uri http://127.0.0.1:8000/tasks `
  -ContentType "application/json" `
  -Body '{"topic":"系统架构"}'

$taskId = $task.task.task_id
$taskId
```

查询任务：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId"
```

启动下一步：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tasks/$taskId/steps/start" `
  -ContentType "application/json" `
  -Body '{"input":{"topic":"系统架构"}}'
```

执行当前自动步骤：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tasks/$taskId/steps/execute"
```

后台执行当前自动步骤：

```powershell
$asyncExecution = Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tasks/$taskId/steps/execute-async"

$asyncTaskId = $asyncExecution.async_task.task_id
$asyncTaskId
```

查询后台执行结果：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/async-tasks/$asyncTaskId"
```

提交学生回答：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tasks/$taskId/answer" `
  -ContentType "application/json" `
  -Body '{"answer":"模块化设计便于定位问题和降低耦合。"}'
```

提交追问回答：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tasks/$taskId/follow-up-answer" `
  -ContentType "application/json" `
  -Body '{"answer":"例如特征处理模块负责音频读取和对数梅尔特征提取。"}'
```

查看任务分析：

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/tasks/$taskId/analysis"
```

导出 Markdown 报告：

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/tasks/$taskId/report/export"
```

## Task API 推荐调用顺序

完整任务流仍然沿用现有 Task State 设计：

```text
POST /tasks
-> POST /tasks/{task_id}/steps/start
-> POST /tasks/{task_id}/steps/execute 或 POST /tasks/{task_id}/steps/execute-async
-> 重复 start / execute，直到 wait_for_answer
-> POST /tasks/{task_id}/answer
-> 重复 start / execute，直到 wait_for_follow_up_answer
-> POST /tasks/{task_id}/follow-up-answer
-> 重复 start / execute，直到 summarize_training completed
-> GET /tasks/{task_id}/analysis
-> POST /tasks/{task_id}/report/export
```

注意：

- `steps/start` 只创建下一步，不执行。
- `steps/execute` 只执行当前自动步骤。
- `steps/execute-async` 会创建后台任务，步骤结果需要通过 `/async-tasks/{async_task_id}` 查询。
- `steps/execute-async` 对同一个 `task_id + current_step_id` 是幂等的，重复请求返回同一个后台任务。
- 人工输入步骤必须通过 `answer` 或 `follow-up-answer` 提交。
- 如果当前步骤类型不匹配，接口会返回 `400`。

## 当前边界

当前 FastAPI 层仍是本机学习版：

- 未实现鉴权。
- 未实现用户 / Workspace 隔离。
- 默认仍使用 JSON 本地存储，PostgreSQL 需要显式配置。
- 默认 RAG 仍使用本地向量库，Qdrant / Milvus 需要显式配置和导入。
- 后台任务状态和幂等索引会写入 `ASYNC_TASK_STORE_PATH`。
- 进程重启后可以查询历史任务状态。
- 重启前仍在 pending / running / cancelling 的任务会恢复为 `TaskInterruptedError`，不会继续执行原 coroutine。
- 当前 `execute-async` 只是把同步 DefenseTask 执行放到后台线程，不代表底层 LLM / 工具调用已经原生异步。
- 日志、metrics、Docker、Compose、K8s manifest 已有本机学习版配置，但仍未完成生产级鉴权、配额和多实例队列治理。

后续生产化仍需补齐：

```text
鉴权 / 用户隔离
多实例任务调度
异步 LLM / 工具调用
服务器长期运行证据
```
