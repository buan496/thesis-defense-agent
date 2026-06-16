import json

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


def count_message_characters(
    message: dict[str, Any],
) -> int:
    serialized_message = json.dumps(
        message,
        ensure_ascii=False,
        separators=(",", ":"),
    )

    return len(serialized_message)


def split_messages_into_turns(
    messages: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    turns: list[list[dict[str, Any]]] = []
    current_turn: list[dict[str, Any]] = []

    for message in messages:
        if message.get("role") == "user":
            if current_turn:
                turns.append(current_turn)

            current_turn = [message]
        else:
            current_turn.append(message)

    if current_turn:
        turns.append(current_turn)

    return turns


def select_context_messages(
    messages: list[dict[str, Any]],
    max_turns: int,
    max_characters: int,
) -> list[dict[str, Any]]:
    if max_characters <= 0:
        raise ValueError("max_characters 必须大于 0")

    recent_messages = select_recent_turns(
        messages=messages,
        max_turns=max_turns,
    )

    turns = split_messages_into_turns(recent_messages)

    if not turns:
        return []

    selected_turns: list[list[dict[str, Any]]] = []
    used_characters = 0

    for turn in reversed(turns):
        turn_characters = sum(
            count_message_characters(message)
            for message in turn
        )

        if selected_turns and (
            used_characters + turn_characters
            > max_characters
        ):
            break

        selected_turns.append(turn)
        used_characters += turn_characters

    selected_turns.reverse()

    return [
        message
        for turn in selected_turns
        for message in turn
    ]