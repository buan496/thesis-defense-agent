import json

import pytest

from app.tools.thesis_search import search_thesis


def fake_embedding(text: str) -> list[float]:
    if "架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


def test_search_thesis(tmp_path):
    store_path = tmp_path / "vector_store.json"

    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理和模型训练模块。",
            "source": "test.pdf",
            "embedding": [1.0, 0.0],
        },
        {
            "id": 1,
            "text": "论文使用了语音数据集。",
            "source": "test.pdf",
            "embedding": [0.0, 1.0],
        },
    ]

    store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )

    results = search_thesis(
        query="系统架构",
        top_k=1,
        vector_store_path=str(store_path),
        embedding_fn=fake_embedding,
    )

    assert len(results) == 1
    assert results[0]["id"] == 0
    assert "系统架构" in results[0]["text"]


def test_search_thesis_empty_query():
    with pytest.raises(ValueError):
        search_thesis(query="   ")