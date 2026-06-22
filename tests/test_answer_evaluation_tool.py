import pytest

from app.tools.answer_evaluation import evaluate_student_answer


def test_evaluate_student_answer():
    received = {}

    def fake_evaluator(question: str, student_answer: str) -> str:
        received["question"] = question
        received["student_answer"] = student_answer
        return "评分：7/10。回答基本正确，但需要补充细节。"

    result = evaluate_student_answer(
        question="系统架构包括哪些模块？",
        student_answer="包括特征处理和模型训练模块。",
        evaluator_fn=fake_evaluator,
    )

    assert received == {
        "question": "系统架构包括哪些模块？",
        "student_answer": "包括特征处理和模型训练模块。",
    }
    assert result == "评分：7/10。回答基本正确，但需要补充细节。"


def test_evaluate_student_answer_rejects_empty_question():
    with pytest.raises(ValueError, match="question 不能为空"):
        evaluate_student_answer(
            question="   ",
            student_answer="包括特征处理模块。",
        )


def test_evaluate_student_answer_rejects_empty_student_answer():
    with pytest.raises(ValueError, match="student_answer 不能为空"):
        evaluate_student_answer(
            question="系统架构包括哪些模块？",
            student_answer="   ",
        )
