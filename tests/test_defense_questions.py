from types import SimpleNamespace

from app.defense_questions import (
    _clean_json_text,
    generate_questions_from_context_with_audit,
)


def test_clean_json_text_plain_json():
    text = '{"questions": ["问题1"]}'
    expected = '{"questions": ["问题1"]}'
    assert _clean_json_text(text) == expected


def test_clean_json_text_markdown_json_block():
    text = '''```json
{"questions": ["问题1"]}
```'''
    expected = '{"questions": ["问题1"]}'
    assert _clean_json_text(text) == expected


def test_clean_json_text_extra_text():
    text = '''下面是 JSON：
{"questions": ["问题1"]}
希望对你有帮助'''
    expected = '{"questions": ["问题1"]}'
    assert _clean_json_text(text) == expected
    
def test_clean_json_text_keeps_chinese_quotes_inside_string():
    text = '''{
  "questions": [
    "请解释“语言嵌入”在模型中的作用？"
  ]
}'''

    cleaned = _clean_json_text(text)

    assert "“语言嵌入”" in cleaned


def test_generate_questions_from_context_with_audit(monkeypatch):
    fake_response = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='{"questions": ["系统架构如何划分模块？"]}',
                ),
            ),
        ],
        usage=SimpleNamespace(
            prompt_tokens=10,
            completion_tokens=5,
            total_tokens=15,
        ),
    )

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["messages"][0]["role"] == "user"
            assert "论文片段" in kwargs["messages"][0]["content"]

            return fake_response

    fake_client = SimpleNamespace(
        chat=SimpleNamespace(
            completions=FakeCompletions(),
        ),
    )

    monkeypatch.setattr(
        "app.defense_questions.get_llm_client",
        lambda: (fake_client, "fake-model"),
    )

    result = generate_questions_from_context_with_audit(
        "系统架构包括特征处理模块。",
    )

    assert result["questions"] == ["系统架构如何划分模块？"]
    assert result["token_usage"] == {
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15,
    }
    assert result["cost_estimate"]["currency"] == "CNY"
