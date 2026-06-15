from typing import Any


def select_recent_turns(
    messages: list[dict[str, Any]],
    max_turns: int,
) -> list[dict[str, Any]]:
    if max_turns <= 0:
        raise ValueError("max_turns 必须大于 0")

    user_message_indices = [
        index
        for index, message in enumerate(messages)
        if message.get("role") == "user"
    ]

    if len(user_message_indices) <= max_turns:
        return list(messages)

    start_index = user_message_indices[-max_turns]

    return list(messages[start_index:])