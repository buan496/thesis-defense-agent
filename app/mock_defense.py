from app.defense_questions import generate_defense_questions
from app.follow_up import generate_follow_up_question   
from app.evaluation import evaluate_answer
from app.answer_rewrite import rewrite_answer
from app.session_logger import save_session_markdown
from app.defense_questions import generate_defense_questions_json

def run_mock_defense(thesis_summary):
    # 生成答辩问题
    questions = generate_defense_questions_json(thesis_summary)
    question = questions[0]  # 选择第一个问题进行模拟答辩
    print("【答辩问题】：")
    print(question)
    # 模拟学生回答
    student_answer = input("\n【请输入学生的回答】：")
     # 评估学生回答
    evaluation = evaluate_answer(question, student_answer)
    print("\n【评估】：")
    print(evaluation)
    # 改写后的答辩回答
    rewritten_answer = rewrite_answer(question, student_answer)
    print("\n【改写后的回答】：")
    print(rewritten_answer)
    # 生成追问
    follow_up_question = generate_follow_up_question(question, student_answer)
    print("\n【追问】：")
    print(follow_up_question)
    # 评估学生回答
    follow_up_answer = input("\n【请输入学生的追问回答】：")
    follow_up_evaluation = evaluate_answer(follow_up_question, follow_up_answer)
    print("\n【评估】：")
    print(follow_up_evaluation)


    session_path = save_session_markdown(
    question,
    student_answer,
    evaluation,
    rewritten_answer,
    follow_up_question,
    follow_up_answer,
    follow_up_evaluation,
)

    print(f"\n【记录已保存】：{session_path}")