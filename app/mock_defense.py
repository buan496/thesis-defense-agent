from app.answer_rewrite import rewrite_answer
from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.evaluation import evaluate_answer
from app.follow_up import generate_follow_up_question
from app.rag_question_generator import generate_rag_defense_questions_with_context
from app.session_logger import save_session_markdown
from app.session_models import DefenseSession
from app.vector_store_io import load_vector_store


def run_mock_defense(training_query: str | None = None):
    store = load_vector_store(RAG_VECTOR_STORE_PATH)

    if training_query is None:
        training_query = input("\n【请输入本轮训练方向】：")

    questions, retrieved_context = generate_rag_defense_questions_with_context(
        training_query,
        store,
        top_k=RAG_TOP_K,
    )

    question = questions[0]
    print("【答辩问题】：")
    print(question)

    student_answer = input("\n【请输入学生的回答】：")

    evaluation = evaluate_answer(question, student_answer)
    print("\n【评估】：")
    print(evaluation)

    rewritten_answer = rewrite_answer(question, student_answer)
    print("\n【改写后的回答】：")
    print(rewritten_answer)

    follow_up_question = generate_follow_up_question(question, student_answer)
    print("\n【追问】：")
    print(follow_up_question)

    follow_up_answer = input("\n【请输入学生的追问回答】：")
    follow_up_evaluation = evaluate_answer(follow_up_question, follow_up_answer)
    print("\n【评估】：")
    print(follow_up_evaluation)

    session = DefenseSession(
        training_query=training_query,
        retrieved_context=retrieved_context,
        question=question,
        student_answer=student_answer,
        evaluation=evaluation,
        rewritten_answer=rewritten_answer,
        follow_up_question=follow_up_question,
        follow_up_answer=follow_up_answer,
        follow_up_evaluation=follow_up_evaluation,
    )
    session_path = save_session_markdown(session)
    print(f"\n【记录已保存】：{session_path}")
