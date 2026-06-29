from types import SimpleNamespace

from app import llm


class FakeCompletions:
    def __init__(self):
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs

        return [
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="第一段"),
                    )
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content=None),
                    )
                ]
            ),
            SimpleNamespace(choices=[]),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        delta=SimpleNamespace(content="第二段"),
                    )
                ]
            ),
        ]


class FakeClient:
    def __init__(self):
        self.completions = FakeCompletions()
        self.chat = SimpleNamespace(completions=self.completions)


def test_stream_chat_with_llm_yields_delta_content(monkeypatch):
    fake_client = FakeClient()

    monkeypatch.setattr(
        llm,
        "get_llm_client",
        lambda: (fake_client, "fake-model"),
    )

    chunks = list(llm.stream_chat_with_llm("系统架构"))

    assert chunks == ["第一段", "第二段"]
    assert fake_client.completions.kwargs["model"] == "fake-model"
    assert fake_client.completions.kwargs["stream"] is True
    assert fake_client.completions.kwargs["messages"][1] == {
        "role": "user",
        "content": "系统架构",
    }
