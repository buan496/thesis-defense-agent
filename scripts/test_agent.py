from app.agent import run_agent
from app.agent_trace_logger import save_agent_trace


user_message = "请根据论文中的系统架构生成5个答辩问题。"

result = run_agent(user_message)

print("最终回答：")
print(result.final_output)

print("\n执行步数：", result.steps)

print("\n工具调用轨迹：")
trace_path = save_agent_trace(
    user_message=user_message,
    result=result,
)

print("\nTRACE SAVED:", trace_path)
for trace in result.tool_traces:
    print("STEP:", trace.step)
    print("TOOL:", trace.tool_name)
    print("ARGUMENTS:", trace.arguments)
    print("-" * 40)
    print("SUCCESS:", trace.success)
    print("DURATION_MS:", round(trace.duration_ms, 2))
    
print("\nToken 使用量：")
print("PROMPT TOKENS:", result.token_usage.prompt_tokens)
print("COMPLETION TOKENS:", result.token_usage.completion_tokens)
print("TOTAL TOKENS:", result.token_usage.total_tokens)

print("\n成本估算：")
print("INPUT COST:", round(result.cost_estimate.input_cost, 6))
print("OUTPUT COST:", round(result.cost_estimate.output_cost, 6))
print("TOTAL COST:", round(result.cost_estimate.total_cost, 6))
print("CURRENCY:", result.cost_estimate.currency)

def test_run_agent_can_skip_appending_user_message():
    session = AgentSession(
        session_id="pre-appended-user-session",
    )

    session.add_message(
        role="user",
        content="已经提前加入的问题",
    )

    received_messages = []

    def fake_llm_call(messages):
        received_messages.extend(messages)

        return FakeMessage(
            content="回答",
            tool_calls=None,
        )

    run_agent(
        user_message="已经提前加入的问题",
        session=session,
        append_user_message=False,
        llm_call=fake_llm_call,
    )

    assert received_messages[1:] == [
        {
            "role": "user",
            "content": "已经提前加入的问题",
        },
    ]

    user_messages = [
        message
        for message in session.messages
        if message["role"] == "user"
    ]

    assert len(user_messages) == 1