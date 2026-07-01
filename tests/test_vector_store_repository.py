import pytest

from app import cli
from app.vector_store import build_vector_store
from app.vector_store_repository import (
    JsonVectorStoreRepository,
    MilvusVectorStoreRepository,
    QdrantVectorStoreRepository,
    create_vector_store_repository,
    parse_milvus_metric_type,
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
        self.deleted_collections = []
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

    def delete_collection(self, collection_name):
        self.deleted_collections.append(collection_name)
        self._collection_exists = False
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


def test_qdrant_vector_store_repository_reports_collection_exists():
    client = FakeQdrantClient(collection_exists=True)
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    assert repository.collection_exists() is True


def test_qdrant_vector_store_repository_delete_existing_collection():
    client = FakeQdrantClient(collection_exists=True)
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    deleted = repository.delete_collection()

    assert deleted is True
    assert client.deleted_collections == ["test_chunks"]
    assert repository.collection_exists() is False


def test_qdrant_vector_store_repository_delete_missing_collection():
    client = FakeQdrantClient(collection_exists=False)
    repository = QdrantVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    deleted = repository.delete_collection()

    assert deleted is False
    assert client.deleted_collections == []


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


class FakeMilvusClient:
    def __init__(self, collection_exists=False):
        self._collection_exists = collection_exists
        self.created_collections = []
        self.dropped_collections = []
        self.inserts = []
        self.searches = []

    def has_collection(self, collection_name):
        return self._collection_exists

    def create_collection(
        self,
        collection_name,
        dimension,
        metric_type,
    ):
        self.created_collections.append(
            {
                "collection_name": collection_name,
                "dimension": dimension,
                "metric_type": metric_type,
            }
        )
        self._collection_exists = True

    def drop_collection(self, collection_name):
        self.dropped_collections.append(collection_name)
        self._collection_exists = False

    def insert(self, collection_name, data):
        self.inserts.append(
            {
                "collection_name": collection_name,
                "data": data,
            }
        )

    def search(
        self,
        collection_name,
        data,
        limit,
        output_fields,
    ):
        self.searches.append(
            {
                "collection_name": collection_name,
                "data": data,
                "limit": limit,
                "output_fields": output_fields,
            }
        )
        return [
            [
                {
                    "id": 1,
                    "distance": 0.93,
                    "entity": {
                        "id": 1,
                        "text": "论文系统",
                        "source": "data/thesis.txt",
                    },
                }
            ]
        ]


def test_milvus_vector_store_repository_save_creates_collection_and_inserts():
    client = FakeMilvusClient(collection_exists=False)
    repository = MilvusVectorStoreRepository(
        uri="http://127.0.0.1:19530",
        collection_name="test_chunks",
        vector_size=3,
        metric_type="COSINE",
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
    assert client.created_collections == [
        {
            "collection_name": "test_chunks",
            "dimension": 3,
            "metric_type": "COSINE",
        }
    ]
    assert client.inserts == [
        {
            "collection_name": "test_chunks",
            "data": [
                {
                    "id": 1,
                    "text": "论文系统",
                    "source": "data/thesis.txt",
                    "length": 4,
                    "vector": [0.1, 0.2, 0.3],
                }
            ],
        }
    ]


def test_milvus_vector_store_repository_save_skips_create_when_exists():
    client = FakeMilvusClient(collection_exists=True)
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    repository.save([])

    assert client.created_collections == []
    assert client.inserts == []


def test_milvus_vector_store_repository_search():
    client = FakeMilvusClient(collection_exists=True)
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    results = repository.search(
        query="论文系统",
        top_k=1,
        embedding_fn=lambda text: [0.1, 0.2, 0.3],
    )

    assert client.searches == [
        {
            "collection_name": "test_chunks",
            "data": [[0.1, 0.2, 0.3]],
            "limit": 1,
            "output_fields": ["id", "text", "source", "length"],
        }
    ]
    assert results == [
        {
            "id": 1,
            "text": "论文系统",
            "source": "data/thesis.txt",
            "score": 0.93,
        }
    ]


def test_milvus_vector_store_repository_reports_collection_exists():
    client = FakeMilvusClient(collection_exists=True)
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    assert repository.collection_exists() is True


def test_milvus_vector_store_repository_delete_existing_collection():
    client = FakeMilvusClient(collection_exists=True)
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    deleted = repository.delete_collection()

    assert deleted is True
    assert client.dropped_collections == ["test_chunks"]
    assert repository.collection_exists() is False


def test_milvus_vector_store_repository_delete_missing_collection():
    client = FakeMilvusClient(collection_exists=False)
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=client,
    )

    deleted = repository.delete_collection()

    assert deleted is False
    assert client.dropped_collections == []


def test_milvus_vector_store_repository_load_is_not_supported():
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=FakeMilvusClient(collection_exists=True),
    )

    with pytest.raises(NotImplementedError, match="does not support full load"):
        repository.load()


def test_milvus_vector_store_repository_requires_valid_collection_name():
    with pytest.raises(ValueError, match="collection_name is required"):
        MilvusVectorStoreRepository(
            collection_name=" ",
            vector_size=3,
            client=FakeMilvusClient(collection_exists=True),
        )


def test_milvus_vector_store_repository_requires_positive_vector_size():
    with pytest.raises(ValueError, match="vector_size must be greater than 0"):
        MilvusVectorStoreRepository(
            collection_name="test_chunks",
            vector_size=0,
            client=FakeMilvusClient(collection_exists=True),
        )


def test_milvus_vector_store_repository_requires_embedding_list():
    repository = MilvusVectorStoreRepository(
        collection_name="test_chunks",
        vector_size=3,
        client=FakeMilvusClient(collection_exists=True),
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


def test_create_vector_store_repository_milvus():
    repository = create_vector_store_repository(
        backend="milvus",
        vector_store_path="ignored.json",
    )

    assert isinstance(repository, MilvusVectorStoreRepository)


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


def test_import_vector_store_to_milvus_cli(
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

    class FakeMilvusVectorStoreRepository:
        def __init__(
            self,
            uri,
            collection_name,
            vector_size,
            metric_type,
            token,
        ):
            created_repositories.append(
                {
                    "uri": uri,
                    "collection_name": collection_name,
                    "vector_size": vector_size,
                    "metric_type": metric_type,
                    "token": token,
                    "saved_store": None,
                }
            )

        def save(self, store):
            created_repositories[-1]["saved_store"] = store
            return created_repositories[-1]["collection_name"]

    monkeypatch.setattr(
        cli,
        "MilvusVectorStoreRepository",
        FakeMilvusVectorStoreRepository,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "import-vector-store-to-milvus",
            "--source",
            str(source_path),
            "--uri",
            "http://127.0.0.1:19530",
            "--collection",
            "test_chunks",
            "--vector-size",
            "3",
            "--metric-type",
            "COSINE",
            "--token",
            "secret",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "MILVUS VECTOR STORE IMPORT" in output
    assert "COLLECTION: test_chunks" in output
    assert "IMPORTED COUNT: 1" in output
    assert created_repositories == [
        {
            "uri": "http://127.0.0.1:19530",
            "collection_name": "test_chunks",
            "vector_size": 3,
            "metric_type": "COSINE",
            "token": "secret",
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


def test_delete_qdrant_collection_cli(
    monkeypatch,
    capsys,
):
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
                    "deleted": False,
                }
            )

        def delete_collection(self):
            created_repositories[-1]["deleted"] = True
            return True

    monkeypatch.setattr(
        cli,
        "QdrantVectorStoreRepository",
        FakeQdrantVectorStoreRepository,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "delete-qdrant-collection",
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
            "--confirm-collection",
            "test_chunks",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "QDRANT COLLECTION DELETE" in output
    assert "COLLECTION: test_chunks" in output
    assert "DELETED: True" in output
    assert created_repositories == [
        {
            "url": "http://127.0.0.1:6333",
            "collection_name": "test_chunks",
            "vector_size": 3,
            "distance": "Cosine",
            "api_key": "secret",
            "deleted": True,
        }
    ]


def test_delete_qdrant_collection_cli_requires_matching_confirmation(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "delete-qdrant-collection",
            "--collection",
            "test_chunks",
            "--confirm-collection",
            "wrong_chunks",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "QDRANT DELETE ERROR" in output
    assert "must exactly match" in output


def test_delete_milvus_collection_cli(
    monkeypatch,
    capsys,
):
    created_repositories = []

    class FakeMilvusVectorStoreRepository:
        def __init__(
            self,
            uri,
            collection_name,
            vector_size,
            metric_type,
            token,
        ):
            created_repositories.append(
                {
                    "uri": uri,
                    "collection_name": collection_name,
                    "vector_size": vector_size,
                    "metric_type": metric_type,
                    "token": token,
                    "deleted": False,
                }
            )

        def delete_collection(self):
            created_repositories[-1]["deleted"] = True
            return True

    monkeypatch.setattr(
        cli,
        "MilvusVectorStoreRepository",
        FakeMilvusVectorStoreRepository,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "delete-milvus-collection",
            "--uri",
            "http://127.0.0.1:19530",
            "--collection",
            "test_chunks_restore",
            "--vector-size",
            "3",
            "--metric-type",
            "COSINE",
            "--token",
            "secret",
            "--confirm-collection",
            "test_chunks_restore",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "MILVUS COLLECTION DELETE" in output
    assert "COLLECTION: test_chunks_restore" in output
    assert "DELETED: True" in output
    assert created_repositories == [
        {
            "uri": "http://127.0.0.1:19530",
            "collection_name": "test_chunks_restore",
            "vector_size": 3,
            "metric_type": "COSINE",
            "token": "secret",
            "deleted": True,
        }
    ]


def test_delete_milvus_collection_cli_requires_matching_confirmation(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "delete-milvus-collection",
            "--collection",
            "test_chunks_restore",
            "--confirm-collection",
            "wrong_chunks",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "MILVUS DELETE ERROR" in output
    assert "must exactly match" in output


def test_delete_milvus_collection_cli_reports_repository_error(
    monkeypatch,
    capsys,
):
    class FailingMilvusVectorStoreRepository:
        def __init__(
            self,
            uri,
            collection_name,
            vector_size,
            metric_type,
            token,
        ):
            pass

        def delete_collection(self):
            raise RuntimeError("milvus unavailable")

    monkeypatch.setattr(
        cli,
        "MilvusVectorStoreRepository",
        FailingMilvusVectorStoreRepository,
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "app.cli",
            "delete-milvus-collection",
            "--collection",
            "test_chunks_restore",
            "--confirm-collection",
            "test_chunks_restore",
        ],
    )

    with pytest.raises(SystemExit) as error:
        cli.main()

    output = capsys.readouterr().out

    assert error.value.code == 1
    assert "MILVUS DELETE ERROR: milvus unavailable" in output


def test_create_vector_store_repository_rejects_unknown_backend(tmp_path):
    with pytest.raises(ValueError, match="Unsupported VECTOR_STORE_BACKEND"):
        create_vector_store_repository(
            backend="unknown",
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


def test_parse_milvus_metric_type_accepts_supported_values():
    assert parse_milvus_metric_type("cosine") == "COSINE"
    assert parse_milvus_metric_type("IP") == "IP"
    assert parse_milvus_metric_type("l2") == "L2"


def test_parse_milvus_metric_type_rejects_unknown_value():
    with pytest.raises(ValueError, match="Unsupported MILVUS_METRIC_TYPE"):
        parse_milvus_metric_type("unknown")
