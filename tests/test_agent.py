from types import SimpleNamespace
import pytest
from app.agent import run_agent


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