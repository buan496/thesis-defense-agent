import pytest

from app.vector_store import build_vector_store
from app.vector_store_repository import (
    JsonVectorStoreRepository,
    create_vector_store_repository,
)


def test_json_vector_store_repository_save_and_load(tmp_path):
    repository = JsonVectorStoreRepository(tmp_path / "vector_store.json")
    store = [
        {
            "id": 0,
            "text": "论文系统",
            "source": "data/thesis.txt",
            "embedding": [1.0, 2.0, 3.0],
        }
    ]

    saved_path = repository.save(store)
    loaded = repository.load()

    assert saved_path == str(tmp_path / "vector_store.json")
    assert loaded == store


def test_json_vector_store_repository_search(tmp_path):
    repository = JsonVectorStoreRepository(tmp_path / "vector_store.json")
    chunks = [
        {"id": 0, "text": "论文答辩系统", "source": "a.txt"},
        {"id": 1, "text": "天气很好", "source": "a.txt"},
    ]
    repository.save(build_vector_store(chunks))

    results = repository.search("论文系统", top_k=1)

    assert len(results) == 1
    assert results[0]["id"] == 0


def test_create_vector_store_repository_json(tmp_path):
    repository = create_vector_store_repository(
        backend="json",
        vector_store_path=tmp_path / "vector_store.json",
    )

    assert isinstance(repository, JsonVectorStoreRepository)


def test_create_vector_store_repository_rejects_unknown_backend(tmp_path):
    with pytest.raises(ValueError, match="Unsupported VECTOR_STORE_BACKEND"):
        create_vector_store_repository(
            backend="unknown",
            vector_store_path=tmp_path / "vector_store.json",
        )


@pytest.mark.parametrize("backend", ["qdrant", "milvus"])
def test_create_vector_store_repository_marks_external_backends_pending(
    tmp_path,
    backend,
):
    with pytest.raises(NotImplementedError, match=backend):
        create_vector_store_repository(
            backend=backend,
            vector_store_path=tmp_path / "vector_store.json",
        )
