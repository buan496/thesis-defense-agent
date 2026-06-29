import pytest
from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes.stream import format_sse_event, split_text_chunks


client = TestClient(app)


def test_format_sse_event_with_event_name():
    event = format_sse_event(
        {
            "text": "hello",
        },
        event="chunk",
    )

    assert event == 'event: chunk\ndata: {"text": "hello"}\n\n'


def test_split_text_chunks_splits_by_chunk_size():
    assert split_text_chunks("abcdef", 2) == ["ab", "cd", "ef"]
    assert split_text_chunks("abcde", 2) == ["ab", "cd", "e"]


def test_split_text_chunks_rejects_invalid_chunk_size():
    with pytest.raises(ValueError):
        split_text_chunks("abc", 0)


def test_stream_echo_returns_sse_chunks():
    response = client.get(
        "/stream/echo",
        params={
            "message": "abcdef",
            "chunk_size": 2,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    body = response.text

    assert 'event: chunk\ndata: {"index": 0, "text": "ab"}' in body
    assert 'event: chunk\ndata: {"index": 1, "text": "cd"}' in body
    assert 'event: chunk\ndata: {"index": 2, "text": "ef"}' in body
    assert 'event: done\ndata: {"chunk_count": 3}' in body


def test_stream_echo_rejects_blank_message():
    response = client.get(
        "/stream/echo",
        params={
            "message": "   ",
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "message must not be empty"


def test_stream_echo_rejects_invalid_chunk_size():
    response = client.get(
        "/stream/echo",
        params={
            "message": "abcdef",
            "chunk_size": 0,
        },
    )

    assert response.status_code == 422
