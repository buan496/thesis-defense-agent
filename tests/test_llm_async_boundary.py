import asyncio
from types import SimpleNamespace

from app import llm


class FakeAsyncCompletions:
    def __init__(self):
        self.kwargs = None

    async def create(self, **kwargs):
        self.kwargs = kwargs
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content="answer:hello"),
                )
            ]
        )


class FakeAsyncClient:
    def __init__(self):
        self.completions = FakeAsyncCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_async_chat_with_llm_uses_async_client(monkeypatch):
    fake_client = FakeAsyncClient()

    monkeypatch.setattr(
        llm,
        "get_async_llm_client",
        lambda: (fake_client, "fake-model"),
    )

    async def scenario():
        result = await llm.async_chat_with_llm("hello")

        assert result == "answer:hello"
        assert fake_client.completions.kwargs["model"] == "fake-model"
        assert fake_client.completions.kwargs["temperature"] == llm.LLM_TEMPERATURE
        assert fake_client.completions.kwargs["max_tokens"] == llm.LLM_MAX_TOKENS
        assert fake_client.completions.kwargs["messages"][1] == {
            "role": "user",
            "content": "hello",
        }

    asyncio.run(scenario())
