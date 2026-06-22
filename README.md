# Thesis Defense Agent

[![CI](https://github.com/buan496/thesis-defense-agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/buan496/thesis-defense-agent/actions/workflows/ci.yml)

## 项目目标

本项目目标是从零搭建一个面向答辩学生本人的论文答辩训练 Agent。通过完整实现 LLM 调用、Prompt Engineering、RAG、工具调用、会话记忆、评估闭环、API 服务和工程化部署，系统性掌握 AI Agent 从原型到可交付产品的核心能力。

项目不仅用于完成论文答辩训练工具本身，也作为个人 AI Agent 工程能力训练项目，目标是逐步达到并超越企业级 AI Agent / RAG / AIOps 工程岗位所要求的能力水平。

## 能力对标

本项目将逐步对标以下工程能力：

- Agent 工程化：Agent Harness、Session、Memory、Tool、Skill、Workspace
- RAG 落地：文档解析、文本切分、Embedding、向量检索、上下文构建、答案溯源
- LLM 评估：LLM as Judge、人工评分、测试样例、Trace 分析、反馈闭环
- 工具治理：工具注册、工具调用边界、错误处理、调用日志
- 后端工程：FastAPI、配置管理、pytest、Git、部署文档
- 私有化意识：本地文档处理、API Key 管理、可替换模型、数据不外泄设计
- 长任务稳定性：异常处理、状态保存、会话记录、可恢复执行

## 第一版目标功能

1. 读取论文文本内容
2. 对论文进行文本切分和结构化处理
3. 构建论文知识库检索能力
4. 基于论文内容生成答辩问题
5. 模拟评委追问
6. 对学生回答进行评分和反馈
7. 将口语化回答改写为答辩表达
8. 保存每轮训练记录
9. 支持命令行交互式模拟答辩

## 当前已实现功能

1. 使用 uv 管理 Python 项目和依赖
2. 使用 `.env` 管理 DeepSeek 和 Embedding API 配置
3. 使用 OpenAI SDK 以 OpenAI-compatible 方式调用 DeepSeek 模型
4. 生成中文论文答辩问题
5. 评价学生回答
6. 根据学生回答生成追问
7. 将学生回答改写为更适合答辩的表达
8. 支持一轮命令行模拟答辩交互
9. 将训练记录保存为 Markdown 文件
10. 支持读取本地 `.txt` 论文文本
11. 支持按段落和字符窗口进行文本切分
12. 支持 chunk metadata，包括 `id`、`text`、`source`、`length`
13. 支持真实 Embedding API 生成向量
14. 支持内存向量库和余弦相似度检索
15. 支持将向量库保存和加载为 JSON 文件
16. 支持 PDF 论文读取、无效 Unicode 清理、目录过滤和 PDF 换行归一化
17. 支持向量库 metadata、构建参数校验、断点恢复和增量跳过
18. 支持 query embedding cache，减少重复评估时的 API 调用
19. 支持 RAG benchmark，统计 Top-K 召回关键词覆盖率
20. 支持基于检索上下文生成答辩问题和基于论文片段回答问题
21. 支持 Tool Schema、工具注册、工具执行器和工具白名单
22. 支持 `search_thesis` 和 `create_defense_questions` 两类 Agent 工具
23. 支持 Agent Loop、多步工具调用、最大步数限制和工具异常恢复
24. 支持 Agent tool trace，记录工具名称、参数、结果、成功状态和耗时
25. 支持 Agent Session，保存多轮消息历史并支持恢复会话
26. 支持短期记忆窗口，限制历史轮数和历史字符数
27. 支持 chat CLI，包含 session id、历史窗口、预算上限和预算预检参数
28. 支持 token usage、cost estimate，并将本轮 token / cost 写入 session metadata
29. 支持 Agent trace JSONL 持久化和 trace 分析
30. 支持 Agent routing、task completion、faithfulness 和稳定性评估
31. 支持评估报告生成、回归对比、指标下降检测、预测翻转检测和稳定性退化检测
32. 支持可恢复 DefenseTask 工作流，覆盖检索、生成问题、提交回答、评价、改写、追问、追问评价和训练总结
33. 支持任务级 resume、trace 汇总和 Markdown 训练报告导出
34. 使用 pytest 覆盖文本切分、文档读取、JSON 清洗、向量检索、RAG、Agent、Session、Trace、预算控制、Task 工作流和评估逻辑

## 当前技术栈

- Python
- uv
- python-dotenv
- OpenAI SDK
- DeepSeek API
- SiliconFlow Embedding API
- BAAI/bge-m3
- pytest
- Markdown / JSON 本地文件存储

## 质量保障

项目使用 pytest、评估 benchmark 和 GitHub Actions 组成多层质量门禁：

- `280` 个离线单元测试覆盖 Agent、工具调用、RAG、Session、Memory、Trace、预算控制、Task 工作流和评估模块
- Retrieval benchmark 检查 RAG Top-K 召回效果
- Agent routing benchmark 检查工具选择、参数生成和任务完成
- Faithfulness benchmark 检查 LLM Judge 的语义判断
- 多轮稳定性评估统计一致率、全票一致率和多数投票准确率
- 评估报告回归对比检测指标下降、预测翻转和稳定性退化
- GitHub Actions 在 Push 和 Pull Request 时自动运行离线质量门禁
- `main` 分支要求 `Offline tests and quality gate` 检查通过后才能合并
- 在线评估仅允许手动触发，并通过 GitHub Secret 使用模型 API

本地运行离线测试：

```powershell
uv sync --frozen --all-groups
uv run --frozen pytest
```

比较两份评估报告：

```powershell
python -m app.cli compare-evaluation-reports `
  --baseline data/reports/baseline.json `
  --current data/reports/current.json `
  --fail-on-regression `
  --markdown-output data/reports/comparison.md
```

## 计划引入的技术栈

- OpenAI Agents SDK
- LangChain / LangGraph
- LlamaIndex
- Qdrant 或 Milvus
- FastAPI
- Streamlit 或 Gradio
- SQLite / PostgreSQL
- Langfuse 或其他 Trace / Observability 工具
- MCP 工具接入
- Docker / K8s 部署

## 目录结构

```text
app/        项目核心逻辑，包括配置、LLM 调用、RAG、评价、追问、会话保存等
data/       本地数据，包括论文文本、训练记录、向量库缓存等
docs/       项目说明、设计文档、学习笔记
notebooks/  实验性代码，例如文档切分、embedding、检索效果分析
scripts/    命令行入口和一次性测试脚本
tests/      pytest 自动化测试
```

## 核心模块

```text
app/config.py             读取环境变量和模型配置
app/llm.py                封装 LLM 客户端和通用调用函数
app/prompts.py            存放系统提示词
app/document_loader.py    读取本地文本文件
app/pdf_loader.py         读取 PDF 论文文本
app/document_cleaner.py   清洗 PDF 文本、目录和非法 Unicode
app/text_splitter.py      文本切分和 chunk metadata 构建
app/embeddings.py         真实 embedding 调用
app/embedding_cache.py    query embedding 缓存
app/vector_store.py       点积、向量长度、余弦相似度、内存向量检索
app/vector_store_io.py    向量库 JSON 保存与加载
app/vector_store_builder.py      构建 PDF 向量库，支持断点恢复
app/vector_store_metadata.py     保存向量库构建参数和元信息
app/rag.py                RAG 上下文拼接和基于上下文回答
app/retrieval_evaluator.py       RAG 检索 benchmark
app/defense_questions.py  生成答辩问题，支持 JSON 结构化输出
app/evaluation.py         评价学生回答
app/follow_up.py          生成追问
app/answer_rewrite.py     改写学生回答
app/mock_defense.py       组织一轮模拟答辩流程
app/session_logger.py     保存训练记录
app/agent.py              手写 Agent Harness、工具调用循环和 token / cost 统计
app/agent_models.py       AgentResult、ToolTrace、TokenUsage、CostEstimate 数据结构
app/tool_executor.py      工具调用分发与白名单执行
app/session_models.py     AgentSession 和答辩训练记录模型
app/session_store.py      Agent 会话 JSON 保存与加载
app/session_service.py    chat 会话创建、恢复、预算控制和 metadata 写入
app/conversation_memory.py        短期消息窗口选择
app/agent_trace_logger.py         Agent trace JSONL 持久化
app/agent_trace_analyzer.py       Trace 统计分析
app/cost_estimator.py             LLM 成本估算
app/budget_guard.py               调用后成本上限检查
app/preflight_budget.py           调用前预算预估
app/agent_routing_evaluator.py    Agent 工具路由评估
app/faithfulness_evaluator.py     Faithfulness Judge
app/evaluation_report.py          评估报告生成
app/evaluation_report_comparator.py 评估报告回归对比
app/task_models.py          DefenseTask 和 TaskStep 数据结构
app/task_store.py           可恢复任务 JSON 保存与加载
app/task_runner.py          任务步骤状态流转
app/task_service.py         任务创建、推进、提交回答和执行服务
app/task_executor.py        执行 retrieve/generate/evaluate/rewrite/follow-up/summary 节点
app/task_resume.py          任务中断后的恢复状态判断
app/task_trace_analyzer.py  任务级 trace、耗时、token 和 cost 汇总
app/task_markdown_exporter.py  任务训练记录 Markdown 导出
app/cli.py                统一命令行入口
```

## 环境配置

创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048
LLM_INPUT_PRICE_PER_1M_TOKENS=0
LLM_OUTPUT_PRICE_PER_1M_TOKENS=0
LLM_PRICE_CURRENCY=CNY

EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

RAG_TOP_K=3
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=100
RAG_MIN_CHUNK_SIZE=30
RAG_VECTOR_STORE_PATH=data/vector_store.json
RAG_VECTOR_STORE_META_PATH=data/vector_store_meta.json
QUERY_EMBEDDING_CACHE_PATH=data/query_embedding_cache.json
AGENT_TRACE_PATH=data/traces/agent_trace.jsonl
```

`.env` 保存真实密钥，不提交到 Git；`.env.example` 保存配置模板，可以提交。

## 安装依赖

```powershell
uv sync
```

如果还没有创建虚拟环境：

```powershell
uv venv
.venv\Scripts\activate
uv sync
```

## 运行方式

构建 PDF 向量库：

```powershell
python -m app.cli build-store --file data/thesis.pdf
```

运行 RAG 召回评估：

```powershell
python -m app.cli evaluate-rag --min-score 0.9
```

运行一轮命令行模拟答辩：

```powershell
python -m app.cli mock-defense --topic 系统架构
```

运行多轮 chat 会话：

```powershell
python -m app.cli chat --message "请记住，我的论文研究方向是中英双语语音识别。"
```

创建并推进可恢复答辩任务：

```powershell
python -m app.cli create-task --topic 系统架构
python -m app.cli start-task-step --task-id <TASK_ID> --input '{\"topic\":\"系统架构\"}'
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli submit-task-answer --task-id <TASK_ID> --answer "系统架构拆分为多个模块，主要是为了降低耦合，并方便定位问题。"
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli submit-follow-up-answer --task-id <TASK_ID> --answer "如果音频读取失败，可以优先检查特征处理模块；如果损失维度不对，可以检查数据集构建和输出头。"
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli show-task --task-id <TASK_ID>
python -m app.cli analyze-task --task-id <TASK_ID>
python -m app.cli export-task-markdown --task-id <TASK_ID>
```

说明：PowerShell 会处理命令行引号，JSON 参数里的双引号需要写成 `\"`，否则 Python 收到的可能会变成 `{topic:系统架构}` 这类非法 JSON。

运行 RAG 检索测试：

```powershell
python -m scripts.test_retrieval
```

运行 RAG 问答测试：

```powershell
python -m scripts.test_rag_answer
```

运行自动化测试：

```powershell
uv run pytest
```

## 当前学习重点

当前项目已经从 RAG 原型阶段进入 Agent Harness 与 Session / Memory 工程化阶段，重点包括：

1. 手写 Agent Loop，而不是只依赖框架
2. Tool Schema、工具白名单、工具执行和工具轨迹
3. Session 创建、恢复、消息历史和短期记忆窗口
4. token usage、cost estimate、预算上限和预算预检
5. Agent trace 持久化、trace 分析和工具耗时统计
6. RAG / Agent / Faithfulness / Stability 评估
7. CI 离线质量门禁和评估报告回归对比
8. 将模拟答辩流程升级为可恢复、可审计的任务型 Agent

## 下一步计划

1. 增强任务报告可读性，补充更细粒度的薄弱点和下一轮训练建议结构化字段
2. 增加工具超时、工具重试和工具结果长度限制
3. 增加长期记忆，沉淀学生论文方向、常错点和薄弱模块
4. 增加混合检索 BM25 + Vector、reranker 和 query rewrite
5. 增加 FastAPI 后端接口
6. 增加 Web 页面或 Streamlit / Gradio 界面
7. 后续迁移到 LangGraph、MCP 和 Sub-Agent 协作

## 学习记录

- 2026-05-23：创建项目目录，确定第一版目标和技术栈。
- 2026-05-23：使用 uv 初始化项目，创建虚拟环境，并添加 OpenAI SDK 依赖。
- 2026-05-23：完成第一个 DeepSeek LLM 调用脚本，验证环境变量和模型 API 可用。
- 2026-05-27：实现答辩问题生成、回答评价、追问生成和回答改写。
- 2026-05-27：实现命令行模拟答辩流程，并将训练记录保存为 Markdown 文件。
- 2026-05-28：实现文本读取、段落切分、chunk metadata 和 pytest 测试。
- 2026-06-01：实现真实 embedding 调用、内存向量检索和 RAG 问答原型。
- 2026-06-05：实现 PDF 读取、文档清洗、向量库 metadata、断点恢复和 RAG 召回评估。
- 2026-06-09：实现 Agent 工具调用、Tool Schema、Agent Loop、工具轨迹和工具耗时统计。
- 2026-06-10：实现 Agent routing、task completion、faithfulness 和稳定性评估。
- 2026-06-12：实现评估报告回归对比和 GitHub Actions 离线质量门禁。
- 2026-06-17：实现 chat session、短期记忆窗口、token / cost 统计、预算预检和 session metadata 成本审计。
- 2026-06-17：实现 DefenseTask / TaskStep、任务存储、状态推进、Task Service 和 Task CLI。
- 2026-06-22：实现完整可恢复答辩任务流，支持追问、追问评价、训练总结、任务 trace 汇总和 Markdown 报告导出。
