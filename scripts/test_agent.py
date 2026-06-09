from app.agent import run_agent


result = run_agent(
    "请根据我的论文说明系统架构包含哪些模块。"
)

print("最终回答：")
print(result.final_output)

print("\n执行步数：", result.steps)

print("\n工具调用轨迹：")
for trace in result.tool_traces:
    print("STEP:", trace.step)
    print("TOOL:", trace.tool_name)
    print("ARGUMENTS:", trace.arguments)
    print("-" * 40)
    print("SUCCESS:", trace.success)