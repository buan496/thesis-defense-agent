import pytest

from app.tools.follow_up_generation import generate_follow_up


def test_generate_follow_up():
    received = {}

    def fake_generator(
        question: str,
        student_answer: str,
        evaluation: str | None = None,
        rewritten_answer: str | None = None,
    ) -> str:
        received["question"] = question
        received["student_answer"] = student_answer
        received["evaluation"] = evaluation
        received["rewritten_answer"] = rewritten_answer
        return "请进一步说明模块拆分如何帮助定位故障？"

    result = generate_follow_up(
        question="系统架构为什么要拆分模块？",
        student_answer="方便管理和定位问题。",
        evaluation="回答过于简略。",
        rewritten_answer="模块化可以降低耦合并提升可维护性。",
        generator_fn=fake_generator,
    )

    assert received == {
        "question": "系统架构为什么要拆分模块？",
        "student_answer": "方便管理和定位问题。",
        "evaluation": "回答过于简略。",
        "rewritten_answer": "模块化可以降低耦合并提升可维护性。",
    }
    assert result == "请进一步说明模块拆分如何帮助定位故障？"


def test_generate_follow_up_rejects_empty_question():
    with pytest.raises(ValueError, match="question 不能为空"):
        generate_follow_up(
            question="   ",
            student_answer="方便定位问题。",
        )


def test_generate_follow_up_rejects_empty_student_answer():
    with pytest.raises(ValueError, match="student_answer 不能为空"):
        generate_follow_up(
            question="系统架构为什么要拆分模块？",
            student_answer="   ",
        )
