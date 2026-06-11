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