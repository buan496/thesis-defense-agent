from collections.abc import Callable

from app.follow_up import generate_follow_up_question


def generate_follow_up(
    question: str,
    student_answer: str,
    evaluation: str | None = None,
    rewritten_answer: str | None = None,
    generator_fn: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
) -> str:
    if not question.strip():
        raise ValueError("question 不能为空")

    if not student_answer.strip():
        raise ValueError("student_answer 不能为空")

    return generator_fn(
        question,
        student_answer,
        evaluation,
        rewritten_answer,
    )
