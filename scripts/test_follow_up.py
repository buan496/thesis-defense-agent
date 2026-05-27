from app.follow_up import generate_follow_up_question

question = "您的系统最核心的创新点是什么？"
student_answer = "我的系统主要是使用大语言模型帮助学生生成问题，并且可以模拟老师继续追问。"
follow_up_questions = generate_follow_up_question(question, student_answer)
print(follow_up_questions)