from app.embedding_cache import get_cached_embedding


def test_get_cached_embedding_hit():
    cache = {
        "问题1": [0.1, 0.2, 0.3],
    }

    assert get_cached_embedding("问题1", cache) == [0.1, 0.2, 0.3]


def test_get_cached_embedding_miss():
    cache = {
        "问题1": [0.1, 0.2, 0.3],
    }

    assert get_cached_embedding("问题2", cache) is None