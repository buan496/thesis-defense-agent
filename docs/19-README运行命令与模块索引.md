# README 运行命令与模块索引

本文从 README 拆出，保存较长的能力清单、环境变量示例、命令大全和模块索引。README 首页只保留快速入口。

## 已实现能力

### LLM 与 Prompt

- 使用 `.env` 管理 DeepSeek 与 Embedding API 配置
- 使用 OpenAI-compatible SDK 调用国内模型
- 支持 system / user message、temperature、max tokens
- 支持结构化 JSON 输出、输出清洗和异常处理
- 支持 token usage、cost estimate、调用后预算上限和调用前预算预检

### RAG

- 支持读取本地 TXT 和 PDF 论文
- 支持通过 FastAPI 上传 `.pdf`、`.txt`、`.md` 文档并安全落盘
- 支持 PDF 文本清洗、目录过滤、无效 Unicode 清理和换行归一化
- 支持按段落和字符窗口切分 chunk
- 支持 chunk metadata：`id`、`text`、`source`、`length`
- 支持真实 Embedding API
- 支持内存向量库、余弦相似度检索、JSON 持久化
- 支持向量库 repository 抽象，当前默认实现为 JSON 后端
- 支持向量库 metadata、参数一致性检查、断点恢复和增量跳过
- 支持 query embedding cache，减少重复评估时的 API 调用
- 支持 RAG benchmark，统计 Top-K 召回关键字覆盖率
- 支持 JSON 与 Qdrant 向量库后端 benchmark 对比，记录质量和延迟差异
- 支持 Vector DB 生产化治理报告，明确 JSON / Qdrant / Milvus 的角色、风险和上线门禁
- 支持 Milvus collection 删除显式确认保护
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
- 已完成 Agent Harness 稳定性治理复盘，覆盖权限、超时、重试、长度限制、错误标准化和 trace 审计
- 已完成 Sub-Agent 权限与 dry-run 复盘，覆盖角色边界、工具授权、执行计划、plan trace、execution trace 和回归对比
- 已完成 MCP 工具协议对照学习，明确 Tool Registry、Tool Schema、Tool Metadata、权限控制、调用执行、资源暴露和审计链路的映射关系

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
- 已完成 Memory 污染治理复盘，覆盖记忆写入、去重裁剪、命中审计、注入预览、禁用开关和上下文压缩风险边界

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
- 已完成 Trace 回放与工具审计复盘，覆盖 Agent trace、Task trace、Sub-Agent plan trace、execution trace、replay、comparison 和 feedback


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
ASYNC_TASK_MAX_CONCURRENT_TASKS=4

EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3

RAG_TOP_K=3
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=100
RAG_MIN_CHUNK_SIZE=30
RAG_VECTOR_STORE_PATH=data/vector_store.json
RAG_VECTOR_STORE_META_PATH=data/vector_store_meta.json
VECTOR_STORE_BACKEND=json
QDRANT_URL=http://127.0.0.1:6333
QDRANT_COLLECTION=thesis_chunks
QDRANT_VECTOR_SIZE=1024
QDRANT_DISTANCE=Cosine
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334
QDRANT_API_KEY=
QDRANT_BACKUP_DIR=data/qdrant_backups
MILVUS_URI=http://127.0.0.1:19530
MILVUS_TOKEN=
MILVUS_COLLECTION=thesis_chunks
MILVUS_VECTOR_SIZE=1024
MILVUS_METRIC_TYPE=COSINE
MILVUS_BACKUP_DIR=data/milvus_backups
MILVUS_PORT=19530
MILVUS_METRICS_PORT=9091
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

启动 FastAPI 本地服务：

```powershell
uv run uvicorn app.api.main:app --reload
```

服务文档：

```text
http://127.0.0.1:8000/docs
docs/deployment/local-fastapi.md
```

创建异步后台任务：

```powershell
curl.exe -X POST http://127.0.0.1:8000/async-tasks `
  -H "Content-Type: application/json" `
  -d "{\"name\":\"demo\",\"delay_seconds\":1,\"result\":\"ok\"}"
```

查询异步后台任务：

```powershell
curl.exe http://127.0.0.1:8000/async-tasks/<TASK_ID>
```

取消异步后台任务：

```powershell
curl.exe -X DELETE http://127.0.0.1:8000/async-tasks/<TASK_ID>
```

后台执行当前答辩任务步骤：

```powershell
curl.exe -X POST http://127.0.0.1:8000/tasks/<TASK_ID>/steps/execute-async
```

同一个 `task_id + current_step_id` 重复调用会返回同一个后台任务。

查询后台执行结果：

```powershell
curl.exe http://127.0.0.1:8000/async-tasks/<ASYNC_TASK_ID>
```

上传论文文档：

```powershell
curl.exe -F "file=@data/thesis.pdf" http://127.0.0.1:8000/documents/upload
```

验证 SSE 流式输出：

```powershell
curl.exe -N "http://127.0.0.1:8000/stream/echo?message=hello-agent&chunk_size=3"
```

验证真实 LLM SSE 流式输出：

```powershell
curl.exe -N "http://127.0.0.1:8000/stream/chat?message=请简要说明你的系统架构"
```

WebSocket 任务控制通道：

```text
ws://127.0.0.1:8000/ws/tasks/<TASK_ID>
```

构建本地 FastAPI Docker 镜像：

```powershell
docker build -t thesis-defense-agent:local .
```

Docker 说明：

```text
docs/deployment/docker.md
```

服务器长期运行说明：

```text
docs/deployment/server.md
```

关闭 Session 压缩：

```powershell
python -m app.cli chat --message "测试本轮不压缩 session" --disable-session-compaction
```

查看长期记忆：

```powershell
python -m app.cli memory-show
```

删除 disposable Milvus collection：

```powershell
uv run python -m app.cli delete-milvus-collection `
  --uri http://127.0.0.1:19530 `
  --collection thesis_chunks_restore `
  --confirm-collection thesis_chunks_restore
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
app/vector_store_repository.py   向量库后端抽象和 JSON 实现
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
docs/07-Sub-Agent阶段复盘.md     Sub-Agent 本地学习版 Harness、dry-run、plan replay 和执行边界
docs/08-Memory阶段复盘.md        长期记忆、记忆注入、记忆审计和上下文压缩复盘
docs/09-Task工作流契约.md        手写 Task State 与 LangGraph 旁路迁移的工作流契约
docs/10-LangGraph旁路迁移.md     LangGraph 旁路迁移过程记录
docs/11-LangGraph阶段复盘.md     LangGraph 旁路迁移阶段总结和 parity report
docs/12-Agent-Harness稳定性治理复盘.md 工具权限、超时、重试、结果限制、错误标准化和 trace 审计复盘
docs/13-Sub-Agent权限与Dry-Run复盘.md Sub-Agent 角色边界、dry-run、计划审计、执行审计和回归对比复盘
docs/14-Trace回放与工具审计复盘.md Agent trace、Task trace、Sub-Agent trace、回放、对比、反馈和审计复盘
docs/15-Memory污染治理复盘.md 长期记忆写入、裁剪、命中审计、注入预览和污染风险治理复盘
docs/16-MCP工具协议对照学习.md 当前本地 Tool Harness 与 MCP 工具发现、调用、授权、资源和审计模型对照
docs/17-本机学习版阶段总复盘.md 本机学习版 Agent Harness 完成能力、边界、展示命令、简历表达和服务器阶段计划
```


