import pytest

from app.tools.defense_question import create_defense_questions


def test_create_defense_questions():
    received_context = {"value": None}

    def fake_generator(context: str) -> list[str]:
        received_context["value"] = context
        return [
            "系统采用了哪些核心技术？",
            "系统如何验证实验效果？",
        ]

    questions = create_defense_questions(
        context="论文实现了一个语音识别系统。",
        generator_fn=fake_generator,
    )

    assert received_context["value"] == "论文实现了一个语音识别系统。"
    assert len(questions) == 2
    assert questions[0] == "系统采用了哪些核心技术？"


def test_create_defense_questions_rejects_empty_context():
    with pytest.raises(ValueError, match="context 不能为空"):
        create_defense_questions(context="   ")


def test_create_defense_questions_rejects_long_context():
    with pytest.raises(
        ValueError,
        match="context 长度不能超过 12000 个字符",
    ):
        create_defense_questions(context="a" * 12001)