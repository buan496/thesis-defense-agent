import pytest

from app import cli
from app.vector_store import build_vector_store
from app.vector_store_repository import (
    JsonVectorStoreRepository,
    QdrantVectorStoreRepository,
    create_vector_store_repository,
    parse_qdrant_distance,
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


class FakeQdrantPoint:
    def __init__(self, point_id, score, payload):
        self.id = point_id
        self.score = score
        self.payload = payload


class FakeQdrantQueryResponse:
    def __init__(self, points):
        self.points = points


class FakeQdrantClient:
    def __init__(self, collection_exists=False):
        self._collection_exists = collection_exists
        self.created_collections = []
        self.upserts = []
        self.queries = []

    def collection_exists(self, collection_name):
        return self._collection_exists

    def create_collection(self, collection_name, vectors_config):
        self.created_collections.append(
            {
                "collection_name": collection_name,
                "vectors_config": vectors_config,
            }
        )
        self._collection_exists = True
        return True

    def upsert(self, collection_name, points, wait=True):
        self.upserts.append(
            {
                "collection_name": collection_name,
                "points": points,
                "wait": wait,
            }
        )

    def query_points(
        self,
        collection_name,
        query,
        limit,
        with_payload,
        with_vectors,
    ):
        self.queries.append(
            {
                "collection_name": collection_name,
                "query": query,
                "limit": limit,
                "with_payload": with_payload,
                "with_vectors": with_vectors,
            }
        )

        return FakeQdrantQueryResponse(
            [
                FakeQdrantPoint(
                    point_id=1,
                    score=0.91,
                    payload={
                        "id": 1,
                        "text": "论文系统",
                        "source": "data/thesis.txt",
                    },
                )
            ]
        )


def test_qdrant_vector_store_repository_save_creates_collection_and_upserts():
    client = FakeQdrantClient(collection_exists=False)
    repository = QdrantVectorStoreRepository(
        url="http://127.0.0.1:6333",
        collection_name="test_chunks",
        vector_size=3,
        distance="Cosine",
        client=client,
    )
    store = [
        {
            "id": 1,
            "text": "论文系统",
            "source": "data/thesis.txt",
            "length": 4,
            "embedding": [0.1, 0.2, 0.3],
        }
    ]

    saved_identifier = repository.save(store)

    assert saved_identifier == "test_chunks"
    assert client.created_collections[0]["collection_name"] == "test_chunks"
    assert client.created_collections[0]["vectors_config"].size == 3
    assert client.upserts[0]["collection_name"] == "test_chunks"
    assert client.upserts[0]["wait"] is True
    point = client.upserts[0]["points"][0]
    assert point.id == 1
    assert point.vector == [0.1, 0.2, 0.3]
    assert point.payload == {
        "id": 1,
        "text": "论文系统",
        "source": "data/thesis.txt",
        "length": 4,
    }


def test_qdrant_vector_store_repository_save_skips_create_when_exists():
    client = FakeQdrantClient(collection_exists=True)
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    repository.save([])

    assert client.created_collections == []
    assert client.upserts == []


def test_qdrant_vector_store_repository_search():
    client = FakeQdrantClient(collection_exists=True)
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    results = repository.search(
        query="论文系统",
        top_k=1,
        embedding_fn=lambda text: [0.1, 0.2, 0.3],
    )

    assert client.queries == [
        {
            "collection_name": "test_chunks",
            "query": [0.1, 0.2, 0.3],
            "limit": 1,
            "with_payload": True,
            "with_vectors": False,
        }
    ]
    assert results == [
        {
            "id": 1,
            "text": "论文系统",
            "source": "data/thesis.txt",
            "score": 0.91,
        }
    ]


def test_qdrant_vector_store_repository_load_is_not_supported():
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=FakeQdrantClient(collection_exists=True),
    )

    with pytest.raises(NotImplementedError, match="does not support full load"):
        repository.load()


def test_qdrant_vector_store_repository_requires_valid_collection_name():
    with pytest.raises(ValueError, match="collection_name is required"):
        QdrantVectorStoreRepository(
            collection_name=" ",
            vector_size=3,
            client=FakeQdrantClient(collection_exists=True),
        )


def test_qdrant_vector_store_repository_requires_positive_vector_size():
    with pytest.raises(ValueError, match="vector_size must be greater than 0"):
        QdrantVectorStoreRepository(
            collection_name="test_chunks",
            vector_size=0,
            client=FakeQdrantClient(collection_exists=True),
        )


def test_qdrant_vector_store_repository_requires_embedding_list():
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=FakeQdrantClient(collection_exists=True),
    )

    with pytest.raises(ValueError, match="embedding must be a list"):
        repository.save(
            [
                {
                    "id": 1,
                    "text": "论文系统",
                    "source": "data/thesis.txt",
                    "embedding": "not-a-list",
                }
            ]
        )


def test_create_vector_store_repository_qdrant():
    repository = create_vector_store_repository(
        backend="qdrant",
        vector_store_path="ignored.json",
    )

    assert isinstance(repository, QdrantVectorStoreRepository)


def test_import_vector_store_to_qdrant_cli(
    monkeypatch,
    capsys,
    tmp_path,
):
    source_path = tmp_path / "vector_store.json"
    JsonVectorStoreRepository(source_path).save(
        [
            {
                "id": 1,
                "text": "论文系统",
                "source": "data/thesis.txt",
                "embedding": [0.1, 0.2, 0.3],
            }
        ]
    )
    created_repositories = []

    class FakeQdrantVectorStoreRepository:
        def __init__(
            self,
            url,
            collection_name,
            vector_size,
            distance,
            api_key,
        ):
            created_repositories.append(
                {
                    "url": url,
                    "collection_name": collection_name,
                    "vector_size": vector_size,
                    "distance": distance,
                    "api_key": api_key,
                    "saved_store": None,
                }
            )

        def save(self, store):
            created_repositories[-1]["saved_store"] = store
            return created_repositories[-1]["collection_name"]

    monkeypatch.setattr(
        cli,
        "QdrantVectorStoreRepository",
        FakeQdrantVectorStoreRepository,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "import-vector-store-to-qdrant",
            "--source",
            str(source_path),
            "--url",
            "http://127.0.0.1:6333",
            "--collection",
            "test_chunks",
            "--vector-size",
            "3",
            "--distance",
            "Cosine",
            "--api-key",
            "secret",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "QDRANT VECTOR STORE IMPORT" in output
    assert "COLLECTION: test_chunks" in output
    assert "IMPORTED COUNT: 1" in output
    assert created_repositories == [
        {
            "url": "http://127.0.0.1:6333",
            "collection_name": "test_chunks",
            "vector_size": 3,
            "distance": "Cosine",
            "api_key": "secret",
            "saved_store": [
                {
                    "id": 1,
                    "text": "论文系统",
                    "source": "data/thesis.txt",
                    "embedding": [0.1, 0.2, 0.3],
                }
            ],
        }
    ]


def test_create_vector_store_repository_rejects_unknown_backend(tmp_path):
    with pytest.raises(ValueError, match="Unsupported VECTOR_STORE_BACKEND"):
        create_vector_store_repository(
            backend="unknown",
            vector_store_path=tmp_path / "vector_store.json",
        )


@pytest.mark.parametrize("backend", ["milvus"])
def test_create_vector_store_repository_marks_external_backends_pending(
    tmp_path,
    backend,
):
    with pytest.raises(NotImplementedError, match=backend):
        create_vector_store_repository(
            backend=backend,
            vector_store_path=tmp_path / "vector_store.json",
        )


def test_parse_qdrant_distance_accepts_supported_values():
    assert str(parse_qdrant_distance("Cosine")) == "Cosine"
    assert str(parse_qdrant_distance("Dot")) == "Dot"
    assert str(parse_qdrant_distance("Euclid")) == "Euclid"
    assert str(parse_qdrant_distance("Euclidean")) == "Euclid"
    assert str(parse_qdrant_distance("Manhattan")) == "Manhattan"


def test_parse_qdrant_distance_rejects_unknown_value():
    with pytest.raises(ValueError, match="Unsupported QDRANT_DISTANCE"):
        parse_qdrant_distance("unknown")
