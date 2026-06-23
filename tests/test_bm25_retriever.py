from app.bm25_retriever import (
    bm25_score,
    build_bm25_index,
    search_bm25,
    tokenize_for_bm25,
)


def test_tokenize_for_bm25_handles_chinese_and_english():
    assert tokenize_for_bm25("LAConformer 系统架构 2026") == [
        "laconformer",
        "系",
        "统",
        "架",
        "构",
        "2026",
    ]


def test_bm25_score_returns_zero_without_match():
    score = bm25_score(
        query_tokens=["系统"],
        document_tokens=["天气"],
        document_frequencies={"系统": 1},
        document_count=2,
        average_document_length=1,
    )

    assert score == 0


def test_search_bm25_ranks_keyword_match_first():
    store = [
        {
            "id": 0,
            "text": "系统架构包括特征处理模块和模型模块",
            "source": "a.txt",
            "embedding": [1, 0],
        },
        {
            "id": 1,
            "text": "天气很好适合散步",
            "source": "a.txt",
            "embedding": [0, 1],
        },
    ]

    results = search_bm25("系统架构", store, top_k=2)

    assert results[0]["id"] == 0
    assert results[0]["score"] > results[1]["score"]


def test_build_bm25_index_handles_empty_store():
    index = build_bm25_index([])

    assert index["document_count"] == 0
    assert index["average_document_length"] == 0
    assert index["document_frequencies"] == {}
