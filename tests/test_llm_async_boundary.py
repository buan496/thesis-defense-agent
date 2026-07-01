import asyncio

from app import llm


def test_async_chat_with_llm_wraps_sync_chat(monkeypatch):
    calls = []

    def fake_chat_with_llm(user_message: str) -> str:
        calls.append(user_message)
        return f"answer:{user_message}"

    monkeypatch.setattr(
        llm,
        "chat_with_llm",
        fake_chat_with_llm,
    )

    async def scenario():
        result = await llm.async_chat_with_llm("hello")

        assert result == "answer:hello"
        assert calls == ["hello"]

    asyncio.run(scenario())
