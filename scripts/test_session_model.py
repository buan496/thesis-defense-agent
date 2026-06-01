from app.session_models import DefenseSession

session = DefenseSession(
    training_query="系统架构",
    retrieved_context="论文片段",
    question="答辩问题",
    student_answer="学生回答",
    evaluation="评价",
    rewritten_answer="改写回答",
    follow_up_question="追问",
    follow_up_answer="追问回答",
    follow_up_evaluation="追问评价",
)

print(session.training_query)
print(session.question)
print(session.student_answer)