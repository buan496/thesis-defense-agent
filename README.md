# Thesis Defense Agent

[![CI](https://github.com/buan496/thesis-defense-agent/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/buan496/thesis-defense-agent/actions/workflows/ci.yml)

## 项目目标

本项目目标是从零搭建一个面向学生本人的论文答辩训练 Agent。它不仅用于生成答辩问题、模拟评委追问、评价学生回答和保存训练记录，也作为一个 AI Agent 工程能力训练项目。

长期目标保持不变：通过完整实现 LLM 调用、Prompt Engineering、RAG、Tool Calling、Agent Harness、Session / Memory、Trace、评估闭环和工程化质量门禁，系统性掌握 AI Agent 从原型到可交付产品的核心能力。

项目能力对标方向：

- Agent 工程化：Agent Harness、Session、Memory、Tool、Skill、Workspace、Task State
- RAG 落地：文档解析、文本切分、Embedding、向量检索、溯源、benchmark
- LLM 评估：LLM-as-Judge、faithfulness、稳定性评估、回归对比、CI 质量门禁
- 工具治理：工具注册、白名单、错误标准化、重试、超时、长度限制、trace 审计
- 长任务稳定性：checkpoint、断点恢复、可恢复任务流、任务级 trace 汇总
- 私有化意识：本地文件存储、密钥不入库、可替换模型、服务器部署后移

## 当前状态

当前项目已经完成本机学习版 Agent Harness 的完整闭环：

```text
PDF / TXT 论文
→ 清洗与切分
→ Embedding
→ 向量库
→ RAG 检索与溯源
→ Tool Calling
→ Agent Loop
→ Session / Memory
→ 可恢复 DefenseTask
→ 评价 / 改写 / 追问 / 总结
→ Trace / benchmark / CI
```

最新本地测试基线：

```text
371 passed
```

## 已实现能力

### LLM 与 Prompt

- 使用 `.env` 管理 DeepSeek 与 Embedding API 配置
- 使用 OpenAI-compatible SDK 调用国内模型
- 支持 system / user message、temperature、max tokens
- 支持结构化 JSON 输出、输出清洗和异常处理
- 支持 token usage、cost estimate、调用后预算上限和调用前预算预检

### RAG

- 支持读取本地 TXT 和 PDF 论文
- 支持 PDF 文本清洗、目录过滤、无效 Unicode 清理和换行归一化
- 支持按段落和字符窗口切分 chunk
- 支持 chunk metadata：`id`、`text`、`source`、`length`
- 支持真实 Embedding API
- 支持内存向量库、余弦相似度检索、JSON 持久化
- 支持向量库 metadata、参数一致性检查、断点恢复和增量跳过
- 支持 query embedding cache，减少重复评估时的 API 调用
- 支持 RAG benchmark，统计 Top-K 召回关键字覆盖率
- 支持 BM25 关键词检索、Vector 语义检索和 Hybrid 融合检索
- 支持检索器对比和 Hybrid 权重扫描，用 benchmark 自动选择检索参数

### Tool Calling 与 Agent Harness

- 支持 Tool Schema、工具注册表、工具白名单
- 支持 `search_thesis`、`create_defense_questions`、`evaluate_student_answer`、`generate_follow_up`、`query_training_record`
- 支持手写 Agent Loop、多步工具调用、最大步数限制
- 支持工具异常恢复、工具成功 / 失败记录、工具耗时统计
- 支持工具结果长度限制、工具重试、工具超时和标准化错误
- 支持 Agent trace JSONL 持久化和 trace 分析

### Session 与 Memory

- 支持 Agent Session 创建、保存和恢复
- 支持多轮消息历史和短期记忆窗口
- 支持历史轮数限制和历史字符预算
- 支持 token / cost 写入 session metadata
- 支持长期记忆 `long_term_memory.json`
- 支持记录用户论文方向、常见薄弱点、训练总结
- 支持按当前问题检索相关记忆
- 支持 `memory-show`、`memory-set-profile`、`memory-add-weakness`、`memory-add-summary`、`memory-prune`
- 支持长期记忆注入开关和注入条数控制
- 支持 Session 上下文压缩摘要，将旧对话压入 `conversation_summary`

### 可恢复任务型 Agent

完整任务流：

```text
retrieve_context
→ generate_question
→ wait_for_answer
→ evaluate_answer
→ rewrite_answer
→ generate_follow_up
→ wait_for_follow_up_answer
→ evaluate_follow_up_answer
→ summarize_training
```

已支持：

- `DefenseTask / TaskStep`
- 任务 JSON 保存和加载
- `create-task`
- `start-task-step`
- `execute-task-step`
- `submit-task-answer`
- `submit-follow-up-answer`
- `resume-task`
- `analyze-task`
- `show-task`
- `export-task-markdown`
- 每步输入、输出、证据、工具调用、耗时、token、cost 写入任务记录
- 任务总结自动写入长期记忆

### 评估与质量门禁

- pytest 覆盖 RAG、Agent、Tool、Session、Memory、Task、Trace、预算控制和评估逻辑
- Retrieval benchmark
- Agent routing benchmark
- Task completion evaluation
- Faithfulness benchmark
- 多轮稳定性评估
- 评估报告生成
- 评估报告回归对比
- 指标下降、预测翻转和稳定性退化检测
- GitHub Actions 离线质量门禁

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
- GitHub Actions

## 暂缓范围

以下内容不在当前本机继续推进，会放到另一台服务器笔记本学习：

- FastAPI 服务化
- Web 前端
- Docker
- PostgreSQL
- Qdrant / Milvus
- Prometheus
- K8s
- 私有化部署
- 服务器环境变量和密钥管理

LangGraph 后续只做旁路迁移，不覆盖当前手写实现。会新增独立目录和独立 CLI，用于和当前 `app/agent.py`、`app/task_*` 对照学习。

## 安装

```powershell
uv sync
```

如果还没有虚拟环境：

```powershell
uv venv
.venv\Scripts\activate
uv sync
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

TOOL_RESULT_MAX_CHARACTERS=6000
TOOL_MAX_RETRIES=2
TOOL_TIMEOUT_SECONDS=30

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
LONG_TERM_MEMORY_PATH=data/long_term_memory.json
```

`.env` 保存真实密钥，不提交到 Git；`.env.example` 保存模板，可以提交。

## 常用命令

构建 PDF 向量库：

```powershell
python -m app.cli build-store --file data/thesis.pdf
```

运行 RAG 召回评估：

```powershell
python -m app.cli evaluate-rag --min-score 0.9
```

运行多轮 chat：

```powershell
python -m app.cli chat --message "请记住，我的论文研究方向是中英双语语音识别。"
```

带 memory 控制运行 chat：

```powershell
python -m app.cli chat `
  --message "我该如何回答系统架构相关问题？" `
  --max-memory-weaknesses 2 `
  --max-memory-summaries 1
```

关闭长期记忆：

```powershell
python -m app.cli chat --message "测试本轮不注入长期记忆" --disable-memory
```

关闭 Session 压缩：

```powershell
python -m app.cli chat --message "测试本轮不压缩 session" --disable-session-compaction
```

查看长期记忆：

```powershell
python -m app.cli memory-show
```

写入长期记忆：

```powershell
python -m app.cli memory-set-profile --key thesis_direction --value "中英双语语音识别"
python -m app.cli memory-add-weakness --text "系统架构回答缺少模块例子"
python -m app.cli memory-add-summary --topic "系统架构" --summary "下一轮需要练习模块边界和排错案例。"
```

裁剪长期记忆：

```powershell
python -m app.cli memory-prune --max-weaknesses 20 --max-summaries 10
```

运行完整任务流：

```powershell
python -m app.cli create-task --topic 系统架构
python -m app.cli start-task-step --task-id <TASK_ID> --input '{\"topic\":\"系统架构\"}'
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli submit-task-answer --task-id <TASK_ID> --answer "系统按职责拆成多个模块，方便定位问题和维护。"
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli submit-follow-up-answer --task-id <TASK_ID> --answer "例如音频读不进来先查特征处理，损失维度不对先查数据集和输出头。"
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli start-task-step --task-id <TASK_ID>
python -m app.cli execute-task-step --task-id <TASK_ID>
python -m app.cli analyze-task --task-id <TASK_ID>
python -m app.cli export-task-markdown --task-id <TASK_ID>
```

PowerShell 里 JSON 参数的双引号需要写成 `\"`，否则 Python 收到的可能不是合法 JSON。

运行测试：

```powershell
uv run pytest -q
```

## 核心模块

```text
app/config.py                    环境变量和模型配置
app/llm.py                       LLM 客户端封装
app/document_loader.py           TXT 文档读取
app/pdf_loader.py                PDF 文档读取
app/document_cleaner.py          文档清洗
app/text_splitter.py             文本切分和 chunk metadata
app/embeddings.py                Embedding 调用
app/embedding_cache.py           Query embedding 缓存
app/vector_store.py              向量检索
app/vector_store_io.py           向量库保存和加载
app/vector_store_builder.py      PDF 向量库构建，支持断点恢复
app/rag.py                       RAG 上下文拼接和问答
app/retrieval_evaluator.py       RAG benchmark
app/tools/                       Agent 工具定义和实现
app/tool_executor.py             工具分发、白名单、重试、超时和错误标准化
app/agent.py                     手写 Agent Harness
app/session_models.py            AgentSession 数据结构
app/session_store.py             Session 保存和加载
app/session_service.py           Chat session 服务层
app/session_compactor.py         Session 摘要压缩
app/long_term_memory.py          长期记忆
app/conversation_memory.py       短期上下文窗口选择
app/task_models.py               DefenseTask / TaskStep
app/task_store.py                Task JSON 保存和加载
app/task_executor.py             Task 节点执行
app/task_service.py              Task 服务层
app/task_resume.py               Task 恢复判断
app/task_trace_analyzer.py       Task trace 汇总
app/task_markdown_exporter.py    Task Markdown 报告导出
app/faithfulness_evaluator.py    Faithfulness Judge
app/evaluation_report.py         评估报告生成
app/evaluation_report_comparator.py 评估报告回归对比
app/cli.py                       统一 CLI
```

## 下一步学习

当前 Session / Memory 主线已经完成到本机学习版闭环，Trace 回放与反馈闭环也已完成，BM25 + Vector 混合检索和权重扫描也已接入。下一步按路线进入：

1. reranker 与 query rewrite
2. LangGraph 旁路迁移，不覆盖现有手写 Harness

服务化、Docker、数据库和服务器部署继续后移到另一台服务器笔记本。
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
432 passed
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
