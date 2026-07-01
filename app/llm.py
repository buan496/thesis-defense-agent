from collections.abc import Iterator

from app.config import (
    DEEPSEEK_API_KEY,
    DEEPSEEK_BASE_URL,
    DEEPSEEK_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
)
from app.prompts import DEFENSE_ASSISTANT_SYSTEM_PROMPT
from openai import AsyncOpenAI, OpenAI


def get_llm_client():
    client = OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    return client, DEEPSEEK_MODEL


def get_async_llm_client():
    client = AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
    )

    return client, DEEPSEEK_MODEL


def _build_chat_messages(user_message: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": DEFENSE_ASSISTANT_SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_message,
        },
    ]


def chat_with_llm(user_message: str) -> str:
    client, model = get_llm_client()

    response = client.chat.completions.create(
        model=model,
        messages=_build_chat_messages(user_message),
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    return response.choices[0].message.content


async def async_chat_with_llm(user_message: str) -> str:
    client, model = get_async_llm_client()

    response = await client.chat.completions.create(
        model=model,
        messages=_build_chat_messages(user_message),
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    return response.choices[0].message.content


def stream_chat_with_llm(user_message: str) -> Iterator[str]:
    client, model = get_llm_client()

    stream = client.chat.completions.create(
        model=model,
        messages=_build_chat_messages(user_message),
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        stream=True,
    )

    for chunk in stream:
        if not chunk.choices:
            continue

        delta = chunk.choices[0].delta
        content = getattr(delta, "content", None)

        if content:
            yield content
