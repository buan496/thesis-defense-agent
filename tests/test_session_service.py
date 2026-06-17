import pytest

from app.session_models import AgentSession
from app.session_service import run_agent_session
from app.session_store import (
    load_agent_session,
    save_agent_session,
)
from app.agent_models import CostEstimate
from app.budget_guard import BudgetExceededError ,PreflightBudgetExceededError


class FakeMessage:
    def __init__(
        self,
        content: str = "",
        tool_calls=None,
    ):
        self.content = content
        self.tool_calls = tool_calls

class FakeResponse:
    def __init__(
        self,
        message,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    ):
        self.choices = [
            type("Choice", (), {"message": message})()
        ]

        self.usage = type(
            "Usage",
            (),
            {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            },
        )()

def test_run_agent_session_creates_and_saves_new_session(
    tmp_path,
):
    def fake_llm_call(messages):
        return FakeMessage(
            content="你好，我可以帮助你准备答辩。",
            tool_calls=None,
        )

    result, session, session_path = run_agent_session(
        user_message="你好",
        directory=tmp_path,
        llm_call=fake_llm_call,
    )

    assert result.final_output == (
        "你好，我可以帮助你准备答辩。"
    )

    assert session.session_id
    assert session_path.exists()
    assert session_path.name == f"{session.session_id}.json"

    loaded_session = load_agent_session(
        session_id=session.session_id,
        directory=tmp_path,
    )

    assert loaded_session == session


def test_run_agent_session_resumes_existing_session(
    tmp_path,
):
    original_session = AgentSession(
        session_id="resume-session",
    )

    original_session.add_message(
        role="user",
        content="我的论文研究语音识别。",
    )
    original_session.add_message(
        role="assistant",
        content="好的，我已经记住了。",
    )

    save_agent_session(
        session=original_session,
        directory=tmp_path,
    )

    received_messages = []

    def fake_llm_call(messages):
        received_messages.extend(messages)

        return FakeMessage(
            content="你的论文研究方向是语音识别。",
            tool_calls=None,
        )

    result, session, session_path = run_agent_session(
        user_message="我的论文研究方向是什么？",
        session_id="resume-session",
        directory=tmp_path,
        llm_call=fake_llm_call,
    )

    assert result.final_output == (
        "你的论文研究方向是语音识别。"
    )

    assert session.session_id == "resume-session"
    assert session_path.name == "resume-session.json"

    assert received_messages[0]["role"] == "system"

    assert received_messages[1:] == [
        {
            "role": "user",
            "content": "我的论文研究语音识别。",
        },
        {
            "role": "assistant",
            "content": "好的，我已经记住了。",
        },
        {
            "role": "user",
            "content": "我的论文研究方向是什么？",
        },
    ]

    saved_session = load_agent_session(
        session_id="resume-session",
        directory=tmp_path,
    )

    assert saved_session.messages[-1] == {
        "role": "assistant",
        "content": "你的论文研究方向是语音识别。",
    }


def test_run_agent_session_rejects_missing_session(
    tmp_path,
):
    def fake_llm_call(messages):
        raise AssertionError("不应该调用模型")

    with pytest.raises(
        FileNotFoundError,
        match="Agent 会话文件不存在",
    ):
        run_agent_session(
            user_message="继续对话",
            session_id="missing-session",
            directory=tmp_path,
            llm_call=fake_llm_call,
        )


def test_failed_agent_run_does_not_overwrite_session(
    tmp_path,
):
    original_session = AgentSession(
        session_id="protected-session",
    )

    original_session.add_message(
        role="user",
        content="已经保存的问题",
    )
    original_session.add_message(
        role="assistant",
        content="已经保存的回答",
    )

    save_agent_session(
        session=original_session,
        directory=tmp_path,
    )

    def failing_llm_call(messages):
        raise RuntimeError("模拟模型调用失败")

    with pytest.raises(
        RuntimeError,
        match="模拟模型调用失败",
    ):
        run_agent_session(
            user_message="这条消息不应该保存",
            session_id="protected-session",
            directory=tmp_path,
            llm_call=failing_llm_call,
        )

    loaded_session = load_agent_session(
        session_id="protected-session",
        directory=tmp_path,
    )

    assert loaded_session == original_session
    assert len(loaded_session.messages) == 2


def test_run_agent_session_does_not_save_when_cost_exceeded(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.session_service.LLM_INPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )
    monkeypatch.setattr(
        "app.session_service.LLM_OUTPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )
    monkeypatch.setattr(
        "app.agent.LLM_INPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )
    monkeypatch.setattr(
        "app.agent.LLM_OUTPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )

    original_session = AgentSession(
        session_id="cost-protected-session",
    )

    original_session.add_message(
        role="user",
        content="已经保存的问题",
    )
    original_session.add_message(
        role="assistant",
        content="已经保存的回答",
    )

    save_agent_session(
        session=original_session,
        directory=tmp_path,
    )

    def fake_llm_call(messages):
        return FakeResponse(
            message=FakeMessage(
                content="这是一条超预算回答",
                tool_calls=None,
            ),
            prompt_tokens=1_000_000,
            completion_tokens=1_000_000,
            total_tokens=2_000_000,
        )

    with pytest.raises(BudgetExceededError):
        run_agent_session(
            user_message="这条消息不应该保存",
            session_id="cost-protected-session",
            directory=tmp_path,
            max_run_cost=0.0,
            llm_call=fake_llm_call,
        )

    loaded_session = load_agent_session(
        session_id="cost-protected-session",
        directory=tmp_path,
    )

    assert loaded_session == original_session
    
def test_run_agent_session_preflight_budget_blocks_llm_call(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.session_service.LLM_INPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )
    monkeypatch.setattr(
        "app.session_service.LLM_OUTPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )

    def llm_call_should_not_run(messages):
        raise AssertionError("预算预检失败时不应调用模型")

    with pytest.raises(PreflightBudgetExceededError):
        run_agent_session(
            user_message="这是一个很长的问题" * 1000,
            directory=tmp_path,
            preflight_max_run_cost=0.0,
            llm_call=llm_call_should_not_run,
        )

    assert list(tmp_path.iterdir()) == []
    
def test_run_agent_session_runs_when_preflight_budget_passes(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "app.session_service.LLM_INPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )
    monkeypatch.setattr(
        "app.session_service.LLM_OUTPUT_PRICE_PER_1M_TOKENS",
        1.0,
    )

    def fake_llm_call(messages):
        return FakeMessage(
            content="预算通过后的回答",
            tool_calls=None,
        )

    result, session, session_path = run_agent_session(
        user_message="短问题",
        directory=tmp_path,
        preflight_max_run_cost=1.0,
        llm_call=fake_llm_call,
    )

    assert result.final_output == "预算通过后的回答"
    assert session_path.exists()

    user_messages = [
        message
        for message in session.messages
        if message["role"] == "user"
    ]

    assert len(user_messages) == 1


def test_run_agent_session_saves_token_usage_and_cost_metadata(
    tmp_path,
):
    def fake_llm_call(messages):
        return FakeResponse(
            message=FakeMessage(
                content="带成本统计的回答",
                tool_calls=None,
            ),
            prompt_tokens=100,
            completion_tokens=20,
            total_tokens=120,
        )

    result, session, session_path = run_agent_session(
        user_message="测试成本记录",
        directory=tmp_path,
        llm_call=fake_llm_call,
    )

    expected_token_usage = {
        "prompt_tokens": result.token_usage.prompt_tokens,
        "completion_tokens": result.token_usage.completion_tokens,
        "total_tokens": result.token_usage.total_tokens,
    }
    expected_cost_estimate = {
        "input_cost": result.cost_estimate.input_cost,
        "output_cost": result.cost_estimate.output_cost,
        "total_cost": result.cost_estimate.total_cost,
        "currency": result.cost_estimate.currency,
    }

    assert session.metadata["last_token_usage"] == (
        expected_token_usage
    )
    assert session.metadata["last_cost_estimate"] == (
        expected_cost_estimate
    )

    saved_session = load_agent_session(
        session_id=session.session_id,
        directory=tmp_path,
    )

    assert session_path.exists()
    assert saved_session.metadata["last_token_usage"] == (
        expected_token_usage
    )
    assert saved_session.metadata["last_cost_estimate"] == (
        expected_cost_estimate
    )
