
# thesis defense agent
## 项目目标
通过写一个论文答辩agent，学会agent开发的所有能力
## 第一版功能
1. 读取论文内容
2. 基于论文生成答辩问题
3. 模拟评委追问
4. 对我的回答进行评分
5. 总结薄弱点并保存复盘记录
## 技术栈
- python
- OpenAI Agents SDK
- LangChain / LangGraph
- LlamaIndex
- Qdrant
- FastAPI
- Streamlit 或 Gradio
- SQLite
## 目录结构
app/:主程序代码，后面放agent，rag，api，配置等
data/:本地数据，例如论文pdf，解析后的文本，向量库临时文件
docs/:项目说明，设计文档，学习笔记
notebooks/:实验性代码，例如设计文档切分，embedding，检索效果
scripts/:一次性脚本，例如解析论文，导入数据，初始化向量库
tests/:测试代码
## 学习记录
- 2026-05-23：创建项目目录，确定第一版目标和技术栈。
- 2026-05-23：使用 uv 初始化项目，创建虚拟环境，并添加 openai 依赖
- 2026-05-23：完成第一个 DeepSeek LLM 调用脚本，验证环境变量和模型 API 可用。
- 2026-05-27：实现 generate_defense_questions，用论文简介生成答辩问题。