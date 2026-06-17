from app.session_models import AgentSession


def test_agent_session_generates_unique_ids():
    first_session = AgentSession()
    second_session = AgentSession()

    assert first_session.session_id
    assert second_session.session_id
    assert first_session.session_id != second_session.session_id


def test_agent_session_has_creation_time():
    session = AgentSession()

    assert session.created_at
    assert "+00:00" in session.created_at


def test_agent_session_add_message():
    session = AgentSession()

    message = session.add_message(
        role="user",
        content="系统架构包含哪些模块？",
    )

    assert message == {
        "role": "user",
        "content": "系统架构包含哪些模块？",
    }
    assert session.messages == [message]


def test_agent_sessions_do_not_share_message_lists():
    first_session = AgentSession()
    second_session = AgentSession()

    first_session.add_message(
        role="user",
        content="第一条消息",
    )

    assert len(first_session.messages) == 1
    assert second_session.messages == []


def test_agent_session_metadata():
    session = AgentSession(
        metadata={
            "user_id": "student-001",
            "thesis_path": "data/thesis.pdf",
        }
    )

    assert session.metadata["user_id"] == "student-001"
    assert session.metadata["thesis_path"] == "data/thesis.pdf"