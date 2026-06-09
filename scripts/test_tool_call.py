from app.agent import request_tool_call
from app.tool_executor import execute_tool_call


message = request_tool_call(
    "请根据我的论文说明系统架构包含哪些模块。"
)

if not message.tool_calls:
    print("模型没有调用工具")
    print("模型回答：", message.content)
else:
    for tool_call in message.tool_calls:
        print("工具名称：", tool_call.function.name)
        print("工具参数：", tool_call.function.arguments)

        tool_result = execute_tool_call(tool_call)

        print("工具执行结果：")
        print(tool_result)
        