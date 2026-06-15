import pytest

from app.conversation_memory import select_recent_turns


def test_select_recent_turns_keeps_all_messages_when_under_limit():
    messages = [
        {
            "role": "user",
            "content": "第一轮问题",
        },
        {
            "role": "assistant",
            "content": "第一轮回答",
        },
    ]

    selected = select_recent_turns(
        messages=messages,
        max_turns=2,
    )

    assert selected == messages
    assert selected is not messages


def test_select_recent_turns_keeps_latest_user_turns():
    messages = [
        {
            "role": "user",
            "content": "第一轮问题",
        },
        {
            "role": "assistant",
            "content": "第一轮回答",
        },
        {
            "role": "user",
            "content": "第二轮问题",
        },
        {
            "role": "assistant",
            "content": "第二轮回答",
        },
        {
            "role": "user",
            "content": "第三轮问题",
        },
        {
            "role": "assistant",
            "content": "第三轮回答",
        },
    ]

    selected = select_recent_turns(
        messages=messages,
        max_turns=2,
    )

    assert selected == [
        {
            "role": "user",
            "content": "第二轮问题",
        },
        {
            "role": "assistant",
            "content": "第二轮回答",
        },
        {
            "role": "user",
            "content": "第三轮问题",
        },
        {
            "role": "assistant",
            "content": "第三轮回答",
        },
    ]


def test_select_recent_turns_preserves_tool_call_chain():
    messages = [
        {
            "role": "user",
            "content": "旧问题",
        },
        {
            "role": "assistant",
            "content": "旧回答",
        },
        {
            "role": "user",
            "content": "系统架构包括什么？",
        },
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_thesis",
                        "arguments": (
                            '{"query": "系统架构"}'
                        ),
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": (
                '{"text": "系统包含特征处理模块。"}'
            ),
        },
        {
            "role": "assistant",
            "content": "系统包含特征处理模块。",
        },
    ]

    selected = select_recent_turns(
        messages=messages,
        max_turns=1,
    )

    assert [message["role"] for message in selected] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]

    assert selected[0]["content"] == (
        "系统架构包括什么？"
    )

    assert selected[2]["tool_call_id"] == "call_1"


@pytest.mark.parametrize(
    "max_turns",
    [
        0,
        -1,
        -10,
    ],
)
def test_select_recent_turns_rejects_invalid_limit(
    max_turns,
):
    with pytest.raises(
        ValueError,
        match="max_turns 必须大于 0",
    ):
        select_recent_turns(
            messages=[],
            max_turns=max_turns,
        )