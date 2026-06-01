# Thesis Defense Agent

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
16. 使用 pytest 覆盖文本切分、文档读取、JSON 清洗和向量相关逻辑

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
app/text_splitter.py      文本切分和 chunk metadata 构建
app/embeddings.py         fake embedding 和真实 embedding 调用
app/vector_store.py       点积、向量长度、余弦相似度、内存向量检索
app/vector_store_io.py    向量库 JSON 保存与加载
app/rag.py                RAG 上下文拼接和基于上下文回答
app/defense_questions.py  生成答辩问题，支持 JSON 结构化输出
app/evaluation.py         评价学生回答
app/follow_up.py          生成追问
app/answer_rewrite.py     改写学生回答
app/mock_defense.py       组织一轮模拟答辩流程
app/session_logger.py     保存训练记录
```

## 环境配置

创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash

LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048

EMBEDDING_API_KEY=your_embedding_api_key_here
EMBEDDING_BASE_URL=https://api.siliconflow.cn/v1
EMBEDDING_MODEL=BAAI/bge-m3
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

运行一轮命令行模拟答辩：

```powershell
python -m scripts.run_mock_defense
```

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

当前项目已经进入 RAG 基础阶段，重点包括：

1. 文档读取
2. 文本切分
3. chunk metadata
4. embedding
5. 向量相似度
6. 内存向量库
7. 向量库持久化
8. 检索结果拼接为上下文
9. 基于上下文生成回答

## 下一步计划

1. 优化真实 embedding 检索效果
2. 增加向量库缓存复用，避免重复调用 embedding API
3. 支持从 PDF 中提取论文文本
4. 增加文档清洗，过滤封面、目录、页眉页脚等低价值内容
5. 增加基于论文原文的答辩问题生成
6. 增加答案引用来源和 chunk 溯源
7. 引入更正式的向量数据库，如 Qdrant 或 Milvus
8. 增加 FastAPI 后端接口
9. 增加 Web 页面或 Streamlit / Gradio 界面
10. 引入 Agent 框架、工具调用、Session / Memory 和多 Agent 协作

## 学习记录

- 2026-05-23：创建项目目录，确定第一版目标和技术栈。
- 2026-05-23：使用 uv 初始化项目，创建虚拟环境，并添加 OpenAI SDK 依赖。
- 2026-05-23：完成第一个 DeepSeek LLM 调用脚本，验证环境变量和模型 API 可用。
- 2026-05-27：实现答辩问题生成、回答评价、追问生成和回答改写。
- 2026-05-27：实现命令行模拟答辩流程，并将训练记录保存为 Markdown 文件。
- 2026-05-28：实现文本读取、段落切分、chunk metadata 和 pytest 测试。
- 2026-06-01：实现真实 embedding 调用、内存向量检索和 RAG 问答原型。
