from app.mock_defense import run_mock_defense
thesis_summary = """本文研究基于大语言模型的论文答辩训练系统，目标是帮助学生模拟评委提问、生成追问并提供反馈。
系统通过读取论文内容，提取研究主题、方法和创新点，再生成针对性的答辩问题。"""

run_mock_defense(thesis_summary)