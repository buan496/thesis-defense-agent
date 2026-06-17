import pytest

from app.conversation_memory import (
    count_message_characters,
    select_context_messages,
    select_recent_turns,
    split_messages_into_turns,
)


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
        
def test_count_message_characters_includes_tool_arguments():
    short_message = {
        "role": "assistant",
        "content": "",
    }

    tool_message = {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "search_thesis",
                    "arguments": (
                        '{"query": "系统架构和模型训练流程"}'
                    ),
                },
            }
        ],
    }

    assert count_message_characters(tool_message) > (
        count_message_characters(short_message)
    )


def test_split_messages_into_turns():
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
            "tool_calls": [],
        },
        {
            "role": "tool",
            "content": "工具结果",
        },
        {
            "role": "assistant",
            "content": "第二轮回答",
        },
    ]

    turns = split_messages_into_turns(messages)

    assert len(turns) == 2

    assert [message["role"] for message in turns[0]] == [
        "user",
        "assistant",
    ]

    assert [message["role"] for message in turns[1]] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]


def test_select_context_messages_respects_character_budget():
    messages = [
        {
            "role": "user",
            "content": "第一轮问题" * 20,
        },
        {
            "role": "assistant",
            "content": "第一轮回答" * 20,
        },
        {
            "role": "user",
            "content": "第二轮问题",
        },
        {
            "role": "assistant",
            "content": "第二轮回答",
        },
    ]

    second_turn = messages[2:]

    second_turn_characters = sum(
        count_message_characters(message)
        for message in second_turn
    )

    selected = select_context_messages(
        messages=messages,
        max_turns=10,
        max_characters=second_turn_characters,
    )

    assert selected == second_turn


def test_select_context_messages_keeps_latest_turn_when_over_budget():
    messages = [
        {
            "role": "user",
            "content": "这是一个很长的最新问题" * 20,
        },
        {
            "role": "assistant",
            "content": "这是一个很长的最新回答" * 20,
        },
    ]

    selected = select_context_messages(
        messages=messages,
        max_turns=6,
        max_characters=1,
    )

    assert selected == messages


def test_select_context_messages_preserves_complete_tool_turn():
    messages = [
        {
            "role": "user",
            "content": "旧问题" * 50,
        },
        {
            "role": "assistant",
            "content": "旧回答" * 50,
        },
        {
            "role": "user",
            "content": "查询系统架构",
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
            "content": "系统包含特征处理和训练模块。",
        },
        {
            "role": "assistant",
            "content": "系统包含特征处理和训练模块。",
        },
    ]

    latest_turn = messages[2:]

    latest_turn_characters = sum(
        count_message_characters(message)
        for message in latest_turn
    )

    selected = select_context_messages(
        messages=messages,
        max_turns=6,
        max_characters=latest_turn_characters,
    )

    assert [message["role"] for message in selected] == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]

    assert selected == latest_turn


@pytest.mark.parametrize(
    "max_characters",
    [
        0,
        -1,
        -100,
    ],
)
def test_select_context_messages_rejects_invalid_character_budget(
    max_characters,
):
    with pytest.raises(
        ValueError,
        match="max_characters 必须大于 0",
    ):
        select_context_messages(
            messages=[],
            max_turns=6,
            max_characters=max_characters,
        )