import pytest
from app.vector_store import (
    dot_product,
    vector_norm,
    cosine_similarity,
    build_vector_store,
    search_vector_store,
)


def test_dot_product():
    assert dot_product([1, 2, 3], [4, 5, 6]) == 32


def test_dot_product_length_mismatch():
    with pytest.raises(ValueError):
        dot_product([1, 2], [1, 2, 3])
        
        
def test_vector_norm():
    assert vector_norm([3, 4]) == 5
    
    
def test_cosine_similarity_same_direction():
    assert cosine_similarity([1, 0], [2, 0]) == 1


def test_cosine_similarity_orthogonal():
    assert cosine_similarity([1, 0], [0, 1]) == 0


def test_cosine_similarity_zero_vector():
    with pytest.raises(ValueError):
        cosine_similarity([0, 0], [1, 2])
        
def test_build_vector_store():
    chunks = [
        {"id": 0, "text": "论文系统", "source": "a.txt"},
    ]

    store = build_vector_store(chunks)

    assert store[0]["id"] == 0
    assert store[0]["text"] == "论文系统"
    assert store[0]["source"] == "a.txt"
    assert "embedding" in store[0]


def test_search_vector_store():
    chunks = [
        {"id": 0, "text": "论文答辩系统", "source": "a.txt"},
        {"id": 1, "text": "天气很好", "source": "a.txt"},
    ]

    store = build_vector_store(chunks)

    results = search_vector_store("论文系统", store, top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == 0


