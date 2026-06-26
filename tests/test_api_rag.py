import json

from fastapi.testclient import TestClient

from app.api.main import app
from app.api.routes import rag


client = TestClient(app)


def fake_embedding(text: str) -> list[float]:
    if "architecture" in text or "架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


def clear_overrides():
    app.dependency_overrides.clear()


def test_rag_search_returns_ranked_results(tmp_path):
    store_path = tmp_path / "vector_store.json"
    store_path.write_text(
        json.dumps(
            [
                {
                    "id": 1,
                    "text": "系统架构包括特征处理和模型训练模块。",
                    "source": "thesis.pdf",
                    "embedding": [1.0, 0.0],
                },
                {
                    "id": 2,
                    "text": "论文使用了语音识别数据集。",
                    "source": "thesis.pdf",
                    "embedding": [0.0, 1.0],
                },
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    app.dependency_overrides[rag.get_vector_store_path] = lambda: str(
        store_path
    )
    app.dependency_overrides[rag.get_embedding_function] = lambda: (
        fake_embedding
    )

    try:
        response = client.post(
            "/rag/search",
            json={
                "query": "系统架构",
                "top_k": 1,
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "系统架构"
    assert body["top_k"] == 1
    assert len(body["results"]) == 1
    assert body["results"][0]["id"] == 1
    assert body["results"][0]["source"] == "thesis.pdf"
    assert body["results"][0]["score"] == 1.0


def test_rag_search_rejects_blank_query():
    response = client.post(
        "/rag/search",
        json={
            "query": "   ",
            "top_k": 1,
        },
    )

    assert response.status_code == 422


def test_rag_search_returns_503_when_vector_store_missing(tmp_path):
    missing_path = tmp_path / "missing.json"

    app.dependency_overrides[rag.get_vector_store_path] = lambda: str(
        missing_path
    )
    app.dependency_overrides[rag.get_embedding_function] = lambda: (
        fake_embedding
    )

    try:
        response = client.post(
            "/rag/search",
            json={
                "query": "系统架构",
                "top_k": 1,
            },
        )
    finally:
        clear_overrides()

    assert response.status_code == 503
    assert "detail" in response.json()
