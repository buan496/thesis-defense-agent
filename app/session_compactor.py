from copy import deepcopy
from typing import Any

from app.conversation_memory import split_messages_into_turns
from app.session_models import AgentSession

SESSION_SUMMARY_METADATA_KEY = "conversation_summary"


def build_extractive_session_summary(
    messages: list[dict[str, Any]],
    max_characters: int,
) -> str:
    if max_characters <= 0:
        raise ValueError("max_characters must be greater than 0")

    lines = []

    for message in messages:
        role = message.get("role", "unknown")
        content = str(message.get("content", "")).strip()

        if not content:
            continue

        if role not in {"user", "assistant"}:
            continue

        lines.append(f"{role}: {content}")

    summary = "\n".join(lines).strip()

    if len(summary) <= max_characters:
        return summary

    return summary[-max_characters:].lstrip()


def merge_session_summaries(
    existing_summary: str,
    new_summary: str,
    max_characters: int,
) -> str:
    if max_characters <= 0:
        raise ValueError("max_characters must be greater than 0")

    parts = [
        part.strip()
        for part in [existing_summary, new_summary]
        if part and part.strip()
    ]

    merged_summary = "\n".join(parts)

    if len(merged_summary) <= max_characters:
        return merged_summary

    return merged_summary[-max_characters:].lstrip()


def compact_agent_session(
    session: AgentSession,
    keep_recent_turns: int,
    max_summary_characters: int,
) -> AgentSession:
    if keep_recent_turns <= 0:
        raise ValueError("keep_recent_turns must be greater than 0")

    if max_summary_characters <= 0:
        raise ValueError("max_summary_characters must be greater than 0")

    turns = split_messages_into_turns(session.messages)

    if len(turns) <= keep_recent_turns:
        return session

    compacted_session = deepcopy(session)
    old_turns = turns[:-keep_recent_turns]
    recent_turns = turns[-keep_recent_turns:]

    old_messages = [
        message
        for turn in old_turns
        for message in turn
    ]
    recent_messages = [
        message
        for turn in recent_turns
        for message in turn
    ]

    existing_summary = str(
        compacted_session.metadata.get(
            SESSION_SUMMARY_METADATA_KEY,
            "",
        )
    )
    new_summary = build_extractive_session_summary(
        old_messages,
        max_characters=max_summary_characters,
    )
    merged_summary = merge_session_summaries(
        existing_summary=existing_summary,
        new_summary=new_summary,
        max_characters=max_summary_characters,
    )

    if merged_summary:
        compacted_session.metadata[SESSION_SUMMARY_METADATA_KEY] = merged_summary

    compacted_session.metadata["compacted_turn_count"] = (
        compacted_session.metadata.get("compacted_turn_count", 0)
        + len(old_turns)
    )
    compacted_session.metadata["retained_turn_count"] = len(recent_turns)
    compacted_session.messages = recent_messages

    return compacted_session
