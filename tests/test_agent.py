from types import SimpleNamespace

import pytest

from app.agent import run_agent
from app.session_models import AgentSession
from app.conversation_memory import count_message_characters
class FakeMessage:
    def __init__(self, content="", tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

    def model_dump(self, exclude_none=True):
        return {
            "role": "assistant",
            "content": self.content,
            "tool_calls": [
                {
                    "id": tool_call.id,
                    "type": "function",
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in self.tool_calls
            ],
        }


def test_run_agent_executes_tool_then_returns_answer():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(
            name="search_thesis",
            arguments='{"query": "系统架构"}',
        ),
    )

    responses = [
        FakeMessage(tool_calls=[tool_call]),
        FakeMessage(
            content="系统架构包括特征处理和模型训练模块。",
            tool_calls=None,
        ),
    ]

    def fake_llm_call(messages):
        return responses.pop(0)

    def fake_tool_executor(received_tool_call):
        assert received_tool_call.function.name == "search_thesis"
        return '{"text": "系统架构包括特征处理和模型训练模块。"}'

    result = run_agent(
        user_message="论文的系统架构包括什么？",
        llm_call=fake_llm_call,
        tool_executor=fake_tool_executor,
    )

    assert result.final_output == "系统架构包括特征处理和模型训练模块。"
    assert result.steps == 2
    assert len(result.tool_traces) == 1
    assert result.tool_traces[0].tool_name == "search_thesis"
    assert result.tool_traces[0].success is True
    assert result.tool_traces[0].duration_ms >= 0


def test_run_agent_recovers_from_tool_error():
    tool_call = SimpleNamespace(
        id="call_1",
        function=SimpleNamespace(
            name="search_thesis",
            arguments='{"query": "系统架构"}',
        ),
    )

    responses = [
        FakeMessage(tool_calls=[tool_call]),
        FakeMessage(
            content="论文检索暂时失败，请稍后重试。",
            tool_calls=None,
        ),
    ]

    def fake_llm_call(messages):
        return responses.pop(0)

    def failing_tool_executor(received_tool_call):
        raise RuntimeError("向量库不可用")

    result = run_agent(
        user_message="请检索论文中的系统架构。",
        llm_call=fake_llm_call,
        tool_executor=failing_tool_executor,
    )

    assert result.final_output == "论文检索暂时失败，请稍后重试。"
    assert result.steps == 2
    assert len(result.tool_traces) == 1

    trace = result.tool_traces[0]

    assert trace.success is False
    assert trace.tool_name == "search_thesis"
    assert "RuntimeError" in trace.result
    assert "向量库不可用" in trace.result
    assert trace.duration_ms >= 0


def test_run_agent_stops_after_max_steps():
    call_count = {"value": 0}

    def fake_llm_call(messages):
        call_count["value"] += 1

        tool_call = SimpleNamespace(
            id=f"call_{call_count['value']}",
            function=SimpleNamespace(
                name="search_thesis",
                arguments='{"query": "继续检索"}',
            ),
        )

        return FakeMessage(tool_calls=[tool_call])

    def fake_tool_executor(tool_call):
        return '{"text": "检索结果"}'

    with pytest.raises(
        RuntimeError,
        match="Agent 执行超过最大步数",
    ):
        run_agent(
            user_message="不断检索论文。",
            max_steps=2,
            llm_call=fake_llm_call,
            tool_executor=fake_tool_executor,
        )

    assert call_count["value"] == 2
    
    
def test_run_agent_returns_direct_answer_without_tool():
    def fake_llm_call(messages):
        return FakeMessage(
            content="你好，我可以帮助你准备论文答辩。",
            tool_calls=None,
        )

    def tool_executor_should_not_run(tool_call):
        raise AssertionError("不应该执行工具")

    result = run_agent(
        user_message="你好",
        llm_call=fake_llm_call,
        tool_executor=tool_executor_should_not_run,
    )

    assert result.final_output == "你好，我可以帮助你准备论文答辩。"
    assert result.steps == 1
    assert result.tool_traces == []


def test_run_agent_chains_search_and_question_generation_tools():
    search_tool_call = SimpleNamespace(
        id="call_search",
        function=SimpleNamespace(
            name="search_thesis",
            arguments='{"query": "系统架构"}',
        ),
    )
    question_tool_call = SimpleNamespace(
        id="call_questions",
        function=SimpleNamespace(
            name="create_defense_questions",
            arguments='{"context": "系统包括特征处理、模型训练和推理模块。"}',
        ),
    )

    responses = [
        FakeMessage(tool_calls=[search_tool_call]),
        FakeMessage(tool_calls=[question_tool_call]),
        FakeMessage(
            content="答辩问题：系统各模块之间是如何协作的？",
            tool_calls=None,
        ),
    ]
    executed_tools = []

    def fake_llm_call(messages):
        return responses.pop(0)

    def fake_tool_executor(tool_call):
        executed_tools.append(tool_call.function.name)

        if tool_call.function.name == "search_thesis":
            return (
                '{"text": "系统包括特征处理、模型训练和推理模块。"}'
            )

        if tool_call.function.name == "create_defense_questions":
            return '["系统各模块之间是如何协作的？"]'

        raise AssertionError("执行了未预期的工具")

    result = run_agent(
        user_message="请根据论文中的系统架构生成答辩问题。",
        llm_call=fake_llm_call,
        tool_executor=fake_tool_executor,
    )

    assert result.final_output == "答辩问题：系统各模块之间是如何协作的？"
    assert result.steps == 3
    assert executed_tools == [
        "search_thesis",
        "create_defense_questions",
    ]
    assert len(result.tool_traces) == 2
    assert result.tool_traces[0].tool_name == "search_thesis"
    assert result.tool_traces[1].tool_name == "create_defense_questions"
    assert all(trace.success for trace in result.tool_traces)


def test_run_agent_stores_conversation_in_session():
    session = AgentSession(session_id="session-memory-test")

    def fake_llm_call(messages):
        return FakeMessage(
            content="第一轮回答",
            tool_calls=None,
        )

    result = run_agent(
        user_message="第一轮问题",
        session=session,
        llm_call=fake_llm_call,
    )

    assert result.final_output == "第一轮回答"
    assert session.messages == [
        {
            "role": "user",
            "content": "第一轮问题",
        },
        {
            "role": "assistant",
            "content": "第一轮回答",
        },
    ]


def test_run_agent_uses_previous_session_messages():
    session = AgentSession(session_id="session-history-test")

    session.add_message(
        role="user",
        content="我的论文研究语音识别。",
    )
    session.add_message(
        role="assistant",
        content="好的，我已经记住了。",
    )

    received_messages = []

    def fake_llm_call(messages):
        received_messages.extend(messages)

        return FakeMessage(
            content="你的论文研究方向是语音识别。",
            tool_calls=None,
        )

    run_agent(
        user_message="我的论文研究方向是什么？",
        session=session,
        llm_call=fake_llm_call,
    )

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

    assert session.messages[-1] == {
        "role": "assistant",
        "content": "你的论文研究方向是语音识别。",
    }


def test_run_agent_stores_tool_messages_in_session():
    session = AgentSession(session_id="session-tool-test")

    tool_call = SimpleNamespace(
        id="call_session_tool",
        function=SimpleNamespace(
            name="search_thesis",
            arguments='{"query": "系统架构"}',
        ),
    )

    responses = [
        FakeMessage(
            content="",
            tool_calls=[tool_call],
        ),
        FakeMessage(
            content="系统包括特征处理和模型训练模块。",
            tool_calls=None,
        ),
    ]

    def fake_llm_call(messages):
        return responses.pop(0)

    def fake_tool_executor(received_tool_call):
        return '{"text": "系统包括特征处理和模型训练模块。"}'

    run_agent(
        user_message="系统架构包括什么？",
        session=session,
        llm_call=fake_llm_call,
        tool_executor=fake_tool_executor,
    )

    roles = [
        message["role"]
        for message in session.messages
    ]

    assert roles == [
        "user",
        "assistant",
        "tool",
        "assistant",
    ]

    assert session.messages[2]["tool_call_id"] == (
        "call_session_tool"
    )
    
def test_run_agent_limits_llm_context_but_keeps_full_session():
    session = AgentSession(
        session_id="limited-history-session",
    )

    for turn_number in range(1, 4):
        session.add_message(
            role="user",
            content=f"第{turn_number}轮问题",
        )
        session.add_message(
            role="assistant",
            content=f"第{turn_number}轮回答",
        )

    received_messages = []

    def fake_llm_call(messages):
        received_messages.extend(messages)

        return FakeMessage(
            content="第四轮回答",
            tool_calls=None,
        )

    run_agent(
        user_message="第四轮问题",
        session=session,
        max_history_turns=2,
        llm_call=fake_llm_call,
    )

    assert received_messages[0]["role"] == "system"

    assert received_messages[1:] == [
        {
            "role": "user",
            "content": "第3轮问题",
        },
        {
            "role": "assistant",
            "content": "第3轮回答",
        },
        {
            "role": "user",
            "content": "第四轮问题",
        },
    ]

    assert len(session.messages) == 8

    assert session.messages[0] == {
        "role": "user",
        "content": "第1轮问题",
    }

    assert session.messages[-1] == {
        "role": "assistant",
        "content": "第四轮回答",
    }
    
def test_run_agent_limits_context_by_character_budget():
    session = AgentSession(
        session_id="character-budget-session",
    )

    session.add_message(
        role="user",
        content="很长的旧问题" * 100,
    )
    session.add_message(
        role="assistant",
        content="很长的旧回答" * 100,
    )
    session.add_message(
        role="user",
        content="较新的问题",
    )
    session.add_message(
        role="assistant",
        content="较新的回答",
    )

    received_messages = []

    def fake_llm_call(messages):
        received_messages.extend(messages)

        return FakeMessage(
            content="最新回答",
            tool_calls=None,
        )

    current_user_message = {
        "role": "user",
        "content": "最新问题",
    }

    recent_messages = [
        {
            "role": "user",
            "content": "较新的问题",
        },
        {
            "role": "assistant",
            "content": "较新的回答",
        },
        current_user_message,
    ]

    character_budget = sum(
        count_message_characters(message)
        for message in recent_messages
    )

    run_agent(
        user_message="最新问题",
        session=session,
        max_history_turns=10,
        max_history_characters=character_budget,
        llm_call=fake_llm_call,
    )

    assert received_messages[0]["role"] == "system"
    assert received_messages[1:] == recent_messages

    assert session.messages[0]["content"].startswith(
        "很长的旧问题"
    )
    assert session.messages[-1] == {
        "role": "assistant",
        "content": "最新回答",
    }
    
    
class FakeResponse:
    def __init__(
        self,
        message,
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    ):
        self.choices = [
            SimpleNamespace(message=message)
        ]

        self.usage = SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )


def test_run_agent_collects_token_usage_from_response():
    def fake_llm_call(messages):
        return FakeResponse(
            message=FakeMessage(
                content="测试回答",
                tool_calls=None,
            ),
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        )

    result = run_agent(
        user_message="测试问题",
        llm_call=fake_llm_call,
    )

    assert result.final_output == "测试回答"
    assert result.token_usage.prompt_tokens == 10
    assert result.token_usage.completion_tokens == 5
    assert result.token_usage.total_tokens == 15
    assert result.cost_estimate.currency == "CNY"


def test_run_agent_accumulates_token_usage_across_steps():
    tool_call = SimpleNamespace(
        id="call_usage",
        function=SimpleNamespace(
            name="search_thesis",
            arguments='{"query": "系统架构"}',
        ),
    )

    responses = [
        FakeResponse(
            message=FakeMessage(
                content="",
                tool_calls=[tool_call],
            ),
            prompt_tokens=20,
            completion_tokens=3,
            total_tokens=23,
        ),
        FakeResponse(
            message=FakeMessage(
                content="系统包括特征处理模块。",
                tool_calls=None,
            ),
            prompt_tokens=30,
            completion_tokens=8,
            total_tokens=38,
        ),
    ]

    def fake_llm_call(messages):
        return responses.pop(0)

    def fake_tool_executor(received_tool_call):
        return '{"text": "系统包括特征处理模块。"}'

    result = run_agent(
        user_message="系统架构包括什么？",
        llm_call=fake_llm_call,
        tool_executor=fake_tool_executor,
    )

    assert result.final_output == "系统包括特征处理模块。"
    assert result.steps == 2
    assert result.token_usage.prompt_tokens == 50
    assert result.token_usage.completion_tokens == 11
    assert result.token_usage.total_tokens == 61


def test_run_agent_defaults_token_usage_to_zero_for_message_only_fake():
    def fake_llm_call(messages):
        return FakeMessage(
            content="没有 usage 的回答",
            tool_calls=None,
        )

    result = run_agent(
        user_message="测试问题",
        llm_call=fake_llm_call,
    )

    assert result.final_output == "没有 usage 的回答"
    assert result.token_usage.prompt_tokens == 0
    assert result.token_usage.completion_tokens == 0
    assert result.token_usage.total_tokens == 0
    
def test_run_agent_returns_cost_estimate():
    def fake_llm_call(messages):
        return FakeResponse(
            message=FakeMessage(
                content="成本测试回答",
                tool_calls=None,
            ),
            prompt_tokens=1000,
            completion_tokens=500,
            total_tokens=1500,
        )

    result = run_agent(
        user_message="测试成本结构",
        llm_call=fake_llm_call,
    )

    assert result.cost_estimate.input_cost >= 0
    assert result.cost_estimate.output_cost >= 0
    assert result.cost_estimate.total_cost >= 0
    assert result.cost_estimate.currency