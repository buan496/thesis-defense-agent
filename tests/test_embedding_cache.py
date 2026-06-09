from app.embedding_cache import get_cached_embedding, load_embedding_cache


def test_get_cached_embedding_hit():
    cache = {
        "embedding_model": "test-model",
        "items": {
            "问题1": [0.1, 0.2, 0.3],
        },
    }

    assert get_cached_embedding("问题1", cache) == [0.1, 0.2, 0.3]


def test_get_cached_embedding_miss():
    cache = {
        "embedding_model": "test-model",
        "items": {
            "问题1": [0.1, 0.2, 0.3],
        },
    }

    assert get_cached_embedding("问题2", cache) is None


def test_load_embedding_cache_model_mismatch(tmp_path):
    cache_path = tmp_path / "cache.json"
    cache_path.write_text(
        """
        {
          "embedding_model": "old-model",
          "items": {
            "问题1": [0.1, 0.2]
          }
        }
        """,
        encoding="utf-8",
    )

    cache = load_embedding_cache(
        str(cache_path),
        embedding_model="new-model",
    )

    assert cache == {
        "embedding_model": "new-model",
        "items": {},
    }