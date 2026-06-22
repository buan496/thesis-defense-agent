import pytest

from app.session_compactor import (
    SESSION_SUMMARY_METADATA_KEY,
    build_extractive_session_summary,
    compact_agent_session,
    merge_session_summaries,
)
from app.session_models import AgentSession


def build_session_with_turns(turn_count: int) -> AgentSession:
    session = AgentSession(session_id="compact-session")

    for index in range(turn_count):
        session.add_message(
            role="user",
            content=f"user message {index}",
        )
        session.add_message(
            role="assistant",
            content=f"assistant answer {index}",
        )

    return session


def test_build_extractive_session_summary_uses_user_and_assistant_messages():
    summary = build_extractive_session_summary(
        [
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "tool", "content": "tool result"},
        ],
        max_characters=200,
    )

    assert "user: hello" in summary
    assert "assistant: hi" in summary
    assert "system prompt" not in summary
    assert "tool result" not in summary


def test_build_extractive_session_summary_truncates_from_left():
    summary = build_extractive_session_summary(
        [
            {"role": "user", "content": "old " * 20},
            {"role": "assistant", "content": "recent answer"},
        ],
        max_characters=30,
    )

    assert len(summary) <= 30
    assert "recent answer" in summary


def test_merge_session_summaries_keeps_existing_and_new_summary():
    merged = merge_session_summaries(
        existing_summary="old summary",
        new_summary="new summary",
        max_characters=100,
    )

    assert "old summary" in merged
    assert "new summary" in merged


def test_compact_agent_session_keeps_recent_turns_and_writes_summary():
    session = build_session_with_turns(4)

    compacted_session = compact_agent_session(
        session,
        keep_recent_turns=2,
        max_summary_characters=500,
    )

    assert compacted_session is not session
    assert len(compacted_session.messages) == 4
    assert compacted_session.messages[0]["content"] == "user message 2"
    assert compacted_session.messages[-1]["content"] == "assistant answer 3"

    summary = compacted_session.metadata[SESSION_SUMMARY_METADATA_KEY]
    assert "user message 0" in summary
    assert "assistant answer 1" in summary
    assert compacted_session.metadata["compacted_turn_count"] == 2
    assert compacted_session.metadata["retained_turn_count"] == 2


def test_compact_agent_session_merges_existing_summary():
    session = build_session_with_turns(3)
    session.metadata[SESSION_SUMMARY_METADATA_KEY] = "previous summary"

    compacted_session = compact_agent_session(
        session,
        keep_recent_turns=1,
        max_summary_characters=500,
    )

    summary = compacted_session.metadata[SESSION_SUMMARY_METADATA_KEY]

    assert "previous summary" in summary
    assert "user message 0" in summary
    assert "assistant answer 1" in summary


def test_compact_agent_session_returns_original_when_no_compaction_needed():
    session = build_session_with_turns(2)

    compacted_session = compact_agent_session(
        session,
        keep_recent_turns=2,
        max_summary_characters=500,
    )

    assert compacted_session is session


def test_compact_agent_session_rejects_invalid_limits():
    session = build_session_with_turns(1)

    with pytest.raises(ValueError, match="keep_recent_turns"):
        compact_agent_session(
            session,
            keep_recent_turns=0,
            max_summary_characters=500,
        )

    with pytest.raises(ValueError, match="max_summary_characters"):
        compact_agent_session(
            session,
            keep_recent_turns=1,
            max_summary_characters=0,
        )
