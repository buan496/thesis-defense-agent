from collections.abc import Callable

from app.evaluation import evaluate_answer


def evaluate_student_answer(
    question: str,
    student_answer: str,
    evaluator_fn: Callable[[str, str], str] = evaluate_answer,
) -> str:
    if not question.strip():
        raise ValueError("question 不能为空")

    if not student_answer.strip():
        raise ValueError("student_answer 不能为空")

    return evaluator_fn(question, student_answer)
