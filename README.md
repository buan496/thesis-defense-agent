# Thesis Defense Agent

[![CI](https://github.com/buan496/thesis-defense-agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/buan496/thesis-defense-agent/actions/workflows/ci.yml)
[![Docker Build](https://github.com/buan496/thesis-defense-agent/actions/workflows/docker-build.yml/badge.svg?branch=main)](https://github.com/buan496/thesis-defense-agent/actions/workflows/docker-build.yml)

## 项目目标

本项目是一个面向学生本人使用的论文答辩训练 Agent，同时也是一个 AI Agent 工程化学习项目。

它的产品目标是帮助学生完成论文答辩训练：生成答辩问题、模拟评委追问、评价回答、改写回答、保存训练记录和沉淀长期薄弱点。

它的工程目标是系统性掌握 AI Agent 从原型到可交付产品的核心能力：

- Agent Harness：Tool Calling、Agent Loop、Session、Memory、Task State、Trace
- RAG：文档解析、Embedding、向量检索、溯源、benchmark、检索策略评估
- 评估闭环：LLM-as-Judge、faithfulness、稳定性评估、回归对比、CI 质量门禁
- 工具治理：工具注册、白名单、错误标准化、重试、超时、结果长度限制
- 长任务稳定性：checkpoint、断点恢复、可恢复任务流、任务级 trace 汇总
- 交付能力：FastAPI、Docker、PostgreSQL、Qdrant、Milvus、Prometheus、K8s 基础配置

## 当前状态

当前项目已经完成本机学习版 Agent Harness 的主要闭环：

```text
PDF / TXT 论文
-> 文档清洗与切分
-> Embedding
-> JSON / Qdrant / Milvus 向量库
-> RAG 检索与溯源
-> Tool Calling
-> Agent Loop
-> Session / Memory
-> 可恢复 DefenseTask
-> 评价 / 改写 / 追问 / 总结
-> Trace / benchmark / CI
-> FastAPI / SSE / WebSocket
-> Docker / GHCR / Prometheus
-> PostgreSQL / Qdrant / Milvus 后端验证
-> K8s manifests / smoke plan / report template
```

最新主线能力包括：

- 可恢复答辩训练流：`retrieve_context -> generate_question -> wait_for_answer -> evaluate_answer -> rewrite_answer -> generate_follow_up -> wait_for_follow_up_answer -> evaluate_follow_up_answer -> summarize_training`
- RAG 检索治理：BM25、Vector、Hybrid、reranker、query rewrite、multi-query、benchmark 对比
- Agent 治理：工具权限、超时、重试、错误标准化、trace 审计、Sub-Agent dry-run 和 replay
- Memory 治理：长期记忆、薄弱点记录、训练总结沉淀、记忆注入和污染治理
- 存储治理：JSON 默认后端、PostgreSQL runtime smoke、Qdrant benchmark 与 snapshot SOP、Milvus runtime benchmark 与 backup / restore SOP
- 交付基础：FastAPI、静态 Web、Docker Compose、GHCR、Prometheus、Alertmanager、K8s manifests

当前测试基线见 [当前进度](docs/01-当前进度.md)。

## 快速开始

安装依赖：

```powershell
uv sync
```

复制环境变量模板：

```powershell
Copy-Item .env.example .env
```

至少需要配置：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
EMBEDDING_API_KEY=your_embedding_api_key_here
```

运行测试：

```powershell
uv run pytest -q
```

启动本机 API：

```powershell
uv run uvicorn app.api.main:app --reload
```

Docker Compose 启动基础服务：

```powershell
docker compose up -d api prometheus alertmanager postgres qdrant milvus
```

## 常用入口

构建 PDF 向量库：

```powershell
uv run python -m app.cli build-store --file data/thesis.pdf
```

运行 RAG 评估：

```powershell
uv run python -m app.cli evaluate-rag
```

创建并推进答辩训练任务：

```powershell
uv run python -m app.cli create-task --topic 系统架构
uv run python -m app.cli resume-task --task-id <TASK_ID>
uv run python -m app.cli analyze-task --task-id <TASK_ID>
uv run python -m app.cli export-task-markdown --task-id <TASK_ID>
```

运行本地质量门禁：

```powershell
uv run python -m app.cli local-quality-gate
```

生成 Milvus 备份 / 恢复计划：

```powershell
uv run python -m app.cli milvus-backup-restore-plan
```

完整命令列表和模块索引见 [README 运行命令与模块索引](docs/19-README运行命令与模块索引.md)。

## 技术栈

核心开发：

- Python
- uv
- pytest
- FastAPI
- Pydantic
- OpenAI-compatible SDK
- DeepSeek API
- SiliconFlow Embedding API
- BAAI/bge-m3

Agent 与 RAG：

- Tool Calling
- 手写 Agent Harness
- LangGraph 旁路迁移
- JSON vector store
- Qdrant
- Milvus
- BM25 / Hybrid retrieval / reranker / query rewrite

交付与观测：

- Docker
- Docker Compose
- GitHub Actions
- GHCR
- PostgreSQL
- Prometheus
- Alertmanager
- Kubernetes manifests

## 文档索引

项目状态与学习路线：

- [当前进度](docs/01-当前进度.md)
- [Agent 完整学习路线](docs/02-Agent完整学习路线.md)
- [知识索引](docs/03-知识索引.md)
- [README 运行命令与模块索引](docs/19-README运行命令与模块索引.md)
- [README 历史更新归档](docs/18-README历史更新归档.md)

阶段复盘：

- [Task State 工作流复盘](docs/05-Task-State工作流复盘.md)
- [MCP 与 Sub-Agent 前置概念](docs/06-MCP与Sub-Agent前置概念.md)
- [Sub-Agent 阶段复盘](docs/07-Sub-Agent阶段复盘.md)
- [Memory 阶段复盘](docs/08-Memory阶段复盘.md)
- [LangGraph 旁路迁移](docs/10-LangGraph旁路迁移.md)
- [本机学习版阶段总复盘](docs/17-本机学习版阶段总复盘.md)

部署与运维：

- [Docker](docs/deployment/docker.md)
- [Docker CI](docs/deployment/docker-ci.md)
- [FastAPI 本机服务](docs/deployment/local-fastapi.md)
- [PostgreSQL](docs/deployment/postgresql.md)
- [Qdrant](docs/deployment/qdrant.md)
- [Milvus](docs/deployment/milvus.md)
- [Milvus Backup / Restore](docs/deployment/milvus-backup-restore.md)
- [Prometheus](docs/deployment/prometheus.md)
- [Alertmanager](docs/deployment/alertmanager.md)
- [Kubernetes](docs/deployment/k8s.md)

## 当前边界

已经完成：

- 本机学习版 Agent Harness 闭环
- RAG 与检索策略 benchmark
- Tool Calling 与工具治理
- Task State 可恢复任务流
- Session / Memory / Trace / Feedback
- FastAPI / Docker / PostgreSQL / Qdrant / Milvus 本机验证
- Milvus destructive operation guardrails
- Prometheus / Alertmanager / K8s manifests 基础交付能力

仍待推进：

- Qdrant cron / Kubernetes CronJob 长期调度证据
- K8s 真实集群 smoke test
- 真实 Feishu / WeCom / email 通知提供方
- 服务器长期运行验证
- 用户认证和更完整的 Trace 查看器
- Langfuse 或等价可观测平台接入

README 只保留项目入口信息；阶段更新、命令大全和实现细节统一放入 `docs/`。
