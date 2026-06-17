import pytest

from app.token_estimator import (
    estimate_message_tokens,
    estimate_messages_tokens,
    estimate_text_tokens,
)


def test_estimate_text_tokens_empty_text():
    assert estimate_text_tokens("") == 0


def test_estimate_text_tokens_rounds_up():
    assert estimate_text_tokens("abcd") == 1
    assert estimate_text_tokens("abcde") == 2


def test_estimate_text_tokens_uses_custom_ratio():
    assert estimate_text_tokens(
        "abcdef",
        characters_per_token=3,
    ) == 2


def test_estimate_text_tokens_rejects_invalid_ratio():
    with pytest.raises(
        ValueError,
        match="characters_per_token 必须大于 0",
    ):
        estimate_text_tokens(
            "abc",
            characters_per_token=0,
        )


def test_estimate_message_tokens_includes_tool_calls():
    normal_message = {
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
                        '{"query": "系统架构和训练流程"}'
                    ),
                },
            }
        ],
    }

    assert estimate_message_tokens(tool_message) > (
        estimate_message_tokens(normal_message)
    )


def test_estimate_messages_tokens_sums_messages():
    messages = [
        {
            "role": "user",
            "content": "abcd",
        },
        {
            "role": "assistant",
            "content": "efgh",
        },
    ]

    expected = sum(
        estimate_message_tokens(message)
        for message in messages
    )

    assert estimate_messages_tokens(messages) == expected