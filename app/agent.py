import time

from collections.abc import Callable
from typing import Any

from app.config import LLM_MAX_TOKENS, LLM_TEMPERATURE
from app.llm import get_llm_client
from app.tools import DEFENSE_QUESTION_TOOL, THESIS_SEARCH_TOOL
from app.tool_executor import execute_tool_call
from app.agent_models import AgentResult, ToolTrace

AGENT_TOOLS = [
    THESIS_SEARCH_TOOL,
    DEFENSE_QUESTION_TOOL,
]

AGENT_SYSTEM_PROMPT = """
你是论文答辩助手。

工具使用规则：
1. 普通问候不需要调用工具。
2. 回答论文事实问题时，调用 search_thesis。
3. 根据论文生成答辩问题时，必须先调用 search_thesis。
4. 获得论文片段后，将片段作为 context 调用 create_defense_questions。
5. 不得编造论文中不存在的信息。
"""


def request_tool_call(user_message: str):
    client, model = get_llm_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": AGENT_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        tools=AGENT_TOOLS,
        tool_choice="auto",
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    return response.choices[0].message

def run_agent(
        user_message: str,
        max_steps: int = 5,
        llm_call: Callable[[list[dict]], Any] | None = None,
        tool_executor: Callable[[Any], str] = execute_tool_call,
    ) -> AgentResult:
    
    tool_traces = []
    
    if llm_call is None:
        client, model = get_llm_client()

        def llm_call(messages: list[dict]):
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )

            return response.choices[0].message

    messages = [
        {
            "role": "system",
            "content": AGENT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]


    for step in range(1,max_steps + 1):
        assistant_message = llm_call(messages)

        if not assistant_message.tool_calls:
            return AgentResult(
                final_output=assistant_message.content or "",
                steps=step,
                tool_traces=tool_traces,
            )

        messages.append(
            assistant_message.model_dump(exclude_none=True)
        )
        

        for tool_call in assistant_message.tool_calls:
            start_time = time.perf_counter()
            try:
                tool_result = tool_executor(tool_call)
                tool_success = True
            except Exception as error:
                tool_result = f"{type(error).__name__}: {error}"
                tool_success = False
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            tool_traces.append(
                ToolTrace(
                    step=step,
                    tool_name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    result=tool_result,
                    success=tool_success,
                    duration_ms=duration_ms,
                )
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result,
                }
            )

    raise RuntimeError(
        f"Agent 执行超过最大步数：{max_steps}"
    )
