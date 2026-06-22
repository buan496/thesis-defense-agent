import json
import time
from types import SimpleNamespace

import pytest

from app.tool_executor import (
    TOOL_REGISTRY,
    build_tool_error_result,
    execute_tool_function_with_retry,
    execute_tool_function_with_timeout,
    execute_tool_call,
    execute_tool_call_safely,
    limit_tool_result_text,
)


def create_tool_call(name: str, arguments: str):
    return SimpleNamespace(
        function=SimpleNamespace(
            name=name,
            arguments=arguments,
        )
    )


def test_execute_tool_call_rejects_unknown_tool():
    tool_call = create_tool_call(
        name="delete_all_files",
        arguments="{}",
    )

    with pytest.raises(ValueError, match="未知工具"):
        execute_tool_call(tool_call)


def test_execute_tool_call_rejects_invalid_json():
    tool_call = create_tool_call(
        name="search_thesis",
        arguments="{invalid json}",
    )

    with pytest.raises(ValueError, match="工具参数不是合法 JSON"):
        execute_tool_call(tool_call)


def test_tool_registry_contains_defense_question_tool():
    assert "create_defense_questions" in TOOL_REGISTRY


def test_tool_registry_contains_answer_evaluation_tool():
    assert "evaluate_student_answer" in TOOL_REGISTRY


def test_tool_registry_contains_follow_up_tool():
    assert "generate_follow_up" in TOOL_REGISTRY


def test_tool_registry_contains_training_record_tool():
    assert "query_training_record" in TOOL_REGISTRY


def test_limit_tool_result_text_keeps_short_text():
    text = '{"result": "short"}'

    limited_text = limit_tool_result_text(
        text,
        max_characters=100,
    )

    assert limited_text == text


def test_limit_tool_result_text_truncates_long_text_as_json():
    text = "a" * 20

    limited_text = limit_tool_result_text(
        text,
        max_characters=5,
    )

    data = json.loads(limited_text)

    assert data["truncated"] is True
    assert data["original_characters"] == 20
    assert data["max_characters"] == 5
    assert data["content"] == "aaaaa"


def test_limit_tool_result_text_rejects_invalid_max_characters():
    with pytest.raises(ValueError):
        limit_tool_result_text(
            "abc",
            max_characters=0,
        )


def test_execute_tool_call_limits_long_tool_result(monkeypatch):
    def fake_tool():
        return {"text": "a" * 50}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "fake_tool",
        fake_tool,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_RESULT_MAX_CHARACTERS",
        10,
    )

    tool_call = create_tool_call(
        name="fake_tool",
        arguments="{}",
    )

    result_text = execute_tool_call(tool_call)
    data = json.loads(result_text)

    assert data["truncated"] is True
    assert data["original_characters"] > 10
    assert data["max_characters"] == 10
    assert len(data["content"]) == 10


def test_execute_tool_function_with_retry_returns_on_first_success():
    calls = []

    def fake_tool():
        calls.append("called")
        return {"ok": True}

    result = execute_tool_function_with_retry(
        fake_tool,
        arguments={},
        max_retries=2,
    )

    assert result == {"ok": True}
    assert calls == ["called"]


def test_execute_tool_function_with_retry_recovers_from_temporary_failure():
    calls = []

    def flaky_tool():
        calls.append("called")
        if len(calls) == 1:
            raise RuntimeError("temporary failure")
        return {"ok": True}

    result = execute_tool_function_with_retry(
        flaky_tool,
        arguments={},
        max_retries=2,
    )

    assert result == {"ok": True}
    assert calls == ["called", "called"]


def test_execute_tool_function_with_retry_raises_last_error():
    calls = []

    def broken_tool():
        calls.append("called")
        raise RuntimeError(f"failure {len(calls)}")

    with pytest.raises(RuntimeError, match="failure 3"):
        execute_tool_function_with_retry(
            broken_tool,
            arguments={},
            max_retries=2,
        )

    assert calls == ["called", "called", "called"]


def test_execute_tool_function_with_retry_rejects_invalid_retry_count():
    with pytest.raises(ValueError):
        execute_tool_function_with_retry(
            lambda: {"ok": True},
            arguments={},
            max_retries=-1,
        )


def test_execute_tool_call_retries_tool_function(monkeypatch):
    calls = []

    def flaky_tool():
        calls.append("called")
        if len(calls) == 1:
            raise RuntimeError("temporary failure")
        return {"ok": True}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "flaky_tool",
        flaky_tool,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_MAX_RETRIES",
        1,
    )

    tool_call = create_tool_call(
        name="flaky_tool",
        arguments="{}",
    )

    result_text = execute_tool_call(tool_call)

    assert json.loads(result_text) == {"ok": True}
    assert calls == ["called", "called"]


def test_execute_tool_function_with_timeout_returns_fast_result():
    def fake_tool(value):
        return {"value": value}

    result = execute_tool_function_with_timeout(
        fake_tool,
        arguments={"value": "ok"},
        timeout_seconds=1,
    )

    assert result == {"value": "ok"}


def test_execute_tool_function_with_timeout_rejects_invalid_timeout():
    with pytest.raises(ValueError):
        execute_tool_function_with_timeout(
            lambda: {"ok": True},
            arguments={},
            timeout_seconds=0,
        )


def test_execute_tool_function_with_timeout_raises_timeout():
    def slow_tool():
        time.sleep(0.2)
        return {"ok": True}

    with pytest.raises(TimeoutError, match="timed out"):
        execute_tool_function_with_timeout(
            slow_tool,
            arguments={},
            timeout_seconds=0.01,
        )


def test_execute_tool_function_with_retry_retries_timeout():
    calls = []

    def sometimes_slow_tool():
        calls.append("called")
        if len(calls) == 1:
            time.sleep(0.2)
        return {"ok": True}

    result = execute_tool_function_with_retry(
        sometimes_slow_tool,
        arguments={},
        max_retries=1,
        timeout_seconds=0.05,
    )

    assert result == {"ok": True}
    assert calls == ["called", "called"]


def test_execute_tool_call_passes_timeout_to_tool_function(monkeypatch):
    def slow_tool():
        time.sleep(0.2)
        return {"ok": True}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "slow_tool",
        slow_tool,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_MAX_RETRIES",
        0,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_TIMEOUT_SECONDS",
        0.01,
    )

    tool_call = create_tool_call(
        name="slow_tool",
        arguments="{}",
    )

    with pytest.raises(TimeoutError, match="timed out"):
        execute_tool_call(tool_call)


def test_build_tool_error_result_returns_standard_json():
    result_text = build_tool_error_result(
        RuntimeError("工具失败"),
        tool_name="search_thesis",
    )

    data = json.loads(result_text)

    assert data == {
        "success": False,
        "error_type": "RuntimeError",
        "message": "工具失败",
        "tool_name": "search_thesis",
    }


def test_execute_tool_call_safely_returns_successful_result(monkeypatch):
    def fake_tool():
        return {"ok": True}

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "safe_success_tool",
        fake_tool,
    )

    tool_call = create_tool_call(
        name="safe_success_tool",
        arguments="{}",
    )

    result_text = execute_tool_call_safely(tool_call)

    assert json.loads(result_text) == {"ok": True}


def test_execute_tool_call_safely_wraps_tool_error(monkeypatch):
    def broken_tool():
        raise RuntimeError("工具临时不可用")

    monkeypatch.setitem(
        TOOL_REGISTRY,
        "broken_tool",
        broken_tool,
    )
    monkeypatch.setattr(
        "app.tool_executor.TOOL_MAX_RETRIES",
        0,
    )

    tool_call = create_tool_call(
        name="broken_tool",
        arguments="{}",
    )

    result_text = execute_tool_call_safely(tool_call)
    data = json.loads(result_text)

    assert data["success"] is False
    assert data["error_type"] == "RuntimeError"
    assert data["message"] == "工具临时不可用"
    assert data["tool_name"] == "broken_tool"


def test_execute_tool_call_safely_wraps_unknown_tool_error():
    tool_call = create_tool_call(
        name="unknown_tool",
        arguments="{}",
    )

    result_text = execute_tool_call_safely(tool_call)
    data = json.loads(result_text)

    assert data["success"] is False
    assert data["error_type"] == "ValueError"
    assert "未知工具" in data["message"]
    assert data["tool_name"] == "unknown_tool"


def test_execute_tool_call_safely_wraps_invalid_json_error():
    tool_call = create_tool_call(
        name="search_thesis",
        arguments="{invalid json}",
    )

    result_text = execute_tool_call_safely(tool_call)
    data = json.loads(result_text)

    assert data["success"] is False
    assert data["error_type"] == "ValueError"
    assert "工具参数不是合法 JSON" in data["message"]
    assert data["tool_name"] == "search_thesis"
