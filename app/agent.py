import time

from collections.abc import Callable
from typing import Any

from app.config import LLM_MAX_TOKENS, LLM_TEMPERATURE
from app.llm import get_llm_client
from app.tools import DEFENSE_QUESTION_TOOL, THESIS_SEARCH_TOOL
from app.tool_executor import execute_tool_call
from app.agent_models import AgentResult, ToolTrace ,TokenUsage
from app.session_models import AgentSession
from app.conversation_memory import select_context_messages

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

def extract_token_usage(response) -> TokenUsage:
    usage = getattr(response, "usage", None)

    if usage is None:
        return TokenUsage()

    return TokenUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(usage, "total_tokens", 0) or 0,
    )


def extract_assistant_message(response):
    choices = getattr(response, "choices", None)

    if choices:
        return response.choices[0].message

    return response

def run_agent(
        user_message: str,
        max_steps: int = 5,
        max_history_turns: int = 6,
        max_history_characters: int = 12000,
        session: AgentSession | None = None,
        llm_call: Callable[[list[dict]], Any] | None = None,
        tool_executor: Callable[[Any], str] = execute_tool_call,
    ) -> AgentResult:
    
    if session is None:
        session = AgentSession()
    
    tool_traces = []
    
    token_usage = TokenUsage()
    
    if llm_call is None:
        client, model = get_llm_client()

        def llm_call(messages: list[dict]):
            return client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto",
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )

    session.add_message(
        role="user",
        content=user_message,
    )

    context_messages = select_context_messages(
        messages=session.messages,
        max_turns=max_history_turns,
        max_characters=max_history_characters,
    )

    messages = [
        {
            "role": "system",
            "content": AGENT_SYSTEM_PROMPT,
        },
        *context_messages,
    ]


    for step in range(1,max_steps + 1):
        llm_response = llm_call(messages)
        token_usage.add(extract_token_usage(llm_response))
        assistant_message = extract_assistant_message(llm_response)

        if not assistant_message.tool_calls:
            final_output = assistant_message.content or ""

            session.add_message(
                role="assistant",
                content=final_output,
            )

            return AgentResult(
                final_output=final_output,
                steps=step,
                tool_traces=tool_traces,
                token_usage=token_usage,
            )

        assistant_message_data = assistant_message.model_dump(
            exclude_none=True
        )

        messages.append(assistant_message_data)
        session.messages.append(assistant_message_data)
        

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

            tool_message = {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            }

            messages.append(tool_message)
            session.messages.append(tool_message)

    raise RuntimeError(
        f"Agent 执行超过最大步数：{max_steps}"
    )
