from app.defense_questions import generate_defense_questions_json

thesis_summary = """
本文研究基于大语言模型的论文答辩训练系统，目标是帮助学生模拟评委提问、生成追问并提供反馈。
"""

questions = generate_defense_questions_json(thesis_summary)

print(questions)
print(questions[0])