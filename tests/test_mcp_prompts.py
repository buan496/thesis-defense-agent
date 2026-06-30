import pytest

from app.mcp_prompts import (
    get_mcp_prompt,
    list_mcp_prompt_schemas,
)


def test_list_mcp_prompt_schemas_includes_training_prompts():
    prompts = list_mcp_prompt_schemas()
    names = [prompt["name"] for prompt in prompts]

    assert "defense_question_prompt" in names
    assert "answer_evaluation_prompt" in names
    assert "follow_up_prompt" in names


def test_get_defense_question_prompt():
    result = get_mcp_prompt(
        "defense_question_prompt",
        {
            "thesis_context": "系统架构包括特征处理和模型训练。",
        },
    )

    assert result["messages"][0]["role"] == "user"
    assert "生成 5 个中文论文答辩问题" in result["messages"][0]["content"]["text"]
    assert "系统架构包括特征处理和模型训练" in result["messages"][0]["content"]["text"]


def test_get_answer_evaluation_prompt():
    result = get_mcp_prompt(
        "answer_evaluation_prompt",
        {
            "question": "系统架构如何设计？",
            "student_answer": "分模块。",
        },
    )

    text = result["messages"][0]["content"]["text"]
    assert "严禁编造实验数据" in text
    assert "系统架构如何设计？" in text
    assert "分模块。" in text


def test_get_follow_up_prompt_with_optional_evaluation():
    result = get_mcp_prompt(
        "follow_up_prompt",
        {
            "question": "系统架构如何设计？",
            "student_answer": "分模块。",
            "evaluation": "回答较笼统。",
        },
    )

    text = result["messages"][0]["content"]["text"]
    assert "生成 1 个有针对性的中文追问" in text
    assert "回答较笼统" in text


def test_get_mcp_prompt_rejects_missing_required_argument():
    with pytest.raises(ValueError, match="missing required prompt argument"):
        get_mcp_prompt("defense_question_prompt", {})


def test_get_mcp_prompt_rejects_unknown_prompt():
    with pytest.raises(ValueError, match="unknown prompt name"):
        get_mcp_prompt("missing_prompt", {})
