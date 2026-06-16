import json

from typing import Any


DEFAULT_CHARACTERS_PER_TOKEN = 4


def estimate_text_tokens(
    text: str,
    characters_per_token: int = DEFAULT_CHARACTERS_PER_TOKEN,
) -> int:
    if characters_per_token <= 0:
        raise ValueError("characters_per_token 必须大于 0")

    if not text:
        return 0

    return (len(text) + characters_per_token - 1) // characters_per_token


def estimate_message_tokens(
    message: dict[str, Any],
    characters_per_token: int = DEFAULT_CHARACTERS_PER_TOKEN,
) -> int:
    serialized_message = json.dumps(
        message,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return estimate_text_tokens(
        serialized_message,
        characters_per_token=characters_per_token,
    )


def estimate_messages_tokens(
    messages: list[dict[str, Any]],
    characters_per_token: int = DEFAULT_CHARACTERS_PER_TOKEN,
) -> int:
    return sum(
        estimate_message_tokens(
            message,
            characters_per_token=characters_per_token,
        )
        for message in messages
    )