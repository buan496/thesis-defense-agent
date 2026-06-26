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
738 passed
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
- 支持规则版 reranker，并可用 benchmark 对比 rerank 前后效果
- 支持 LLM 模型版 reranker，并可用 benchmark 对比模型重排前后效果
- 支持规则版 query rewrite，并可用 benchmark 对比改写前后效果
- 支持 LLM query rewrite，并可用 benchmark 对比模型改写前后效果
- 支持 multi-query retrieval，为同一问题生成多个检索 query 后合并结果，提高召回稳定性
- 支持检索策略组合对比，统一扫描 `hybrid`、`query rewrite`、`multi-query`、`reranker` 等组合并选择默认策略

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
- LangGraph
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

LangGraph 已完成旁路迁移学习版闭环，并保留在 `app/langgraph_workflow/`。它只用于和当前 `app/agent.py`、`app/task_*` 对照学习，不覆盖当前手写实现。数据库级 checkpointer、服务器部署和跨进程恢复继续后移到服务器/数据库阶段。

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
app/tool_registry.py             工具元信息注册表和可发现性管理
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
app/langgraph_workflow/          LangGraph 旁路学习 demo，不覆盖手写 Task State
app/faithfulness_evaluator.py    Faithfulness Judge
app/evaluation_report.py         评估报告生成
app/evaluation_report_comparator.py 评估报告回归对比
app/cli.py                       统一 CLI
docs/05-Task-State工作流复盘.md   Task State 状态机、节点、边和 LangGraph 旁路迁移前复盘
docs/06-MCP与Sub-Agent前置概念.md MCP / Sub-Agent 概念映射和后续学习边界
```

## 下一步学习

当前本机学习版已经完成到以下主线：

```text
RAG / 检索策略评估
Tool Calling / Tool Registry / 工具执行治理
Agent Loop / Trace / Feedback / Benchmark
Session / Memory / Memory 质量治理
DefenseTask 可恢复任务流
Sub-Agent 本地学习版 Harness
LangGraph 旁路迁移与 parity report
CI / Local Quality Gate
```

LangGraph 旁路迁移当前已完成完整对照链路：

```text
retrieve_context
-> generate_question
-> answer_interrupt
-> evaluate_answer
-> rewrite_answer
-> generate_follow_up
-> follow_up_interrupt
-> evaluate_follow_up_answer
-> summarize_training
-> parity_report
```

下一步按路线进入：

1. Agent Harness 稳定性治理复盘：工具超时、重试、结果长度限制、错误标准化、权限和审计。
2. 对 README 和学习路线做周期性同步，避免文档落后于代码。
3. 服务化、Docker、数据库和服务器部署继续后移到另一台服务器笔记本。

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
