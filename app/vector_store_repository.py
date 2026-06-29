from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from app.config import (
    QDRANT_API_KEY,
    QDRANT_COLLECTION,
    QDRANT_DISTANCE,
    QDRANT_URL,
    QDRANT_VECTOR_SIZE,
)
from app.vector_store import create_fake_embedding, search_vector_store
from app.vector_store_io import load_vector_store, save_vector_store


class VectorStoreRepository(Protocol):
    def save(self, store: list[dict]) -> str:
        ...

    def load(self) -> list[dict]:
        ...

    def search(
        self,
        query: str,
        top_k: int,
        embedding_fn: Callable[[str], list[float]],
    ) -> list[dict]:
        ...


class JsonVectorStoreRepository:
    def __init__(self, file_path: str | Path):
        self.file_path = str(file_path)

    def save(self, store: list[dict]) -> str:
        save_vector_store(store, self.file_path)
        return self.file_path

    def load(self) -> list[dict]:
        return load_vector_store(self.file_path)

    def search(
        self,
        query: str,
        top_k: int,
        embedding_fn: Callable[[str], list[float]] = create_fake_embedding,
    ) -> list[dict]:
        return search_vector_store(
            query=query,
            store=self.load(),
            top_k=top_k,
            embedding_fn=embedding_fn,
        )


class QdrantVectorStoreRepository:
    def __init__(
        self,
        url: str = QDRANT_URL,
        collection_name: str = QDRANT_COLLECTION,
        vector_size: int = QDRANT_VECTOR_SIZE,
        distance: str = QDRANT_DISTANCE,
        api_key: str = QDRANT_API_KEY,
        client=None,
    ):
        if not collection_name.strip():
            raise ValueError("collection_name is required")

        if vector_size <= 0:
            raise ValueError("vector_size must be greater than 0")

        self.url = url
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.distance = distance
        self.api_key = api_key
        self.client = client or create_qdrant_client(
            url=url,
            api_key=api_key,
        )

    def save(self, store: list[dict]) -> str:
        self.ensure_collection()

        if not store:
            return self.collection_name

        self.client.upsert(
            collection_name=self.collection_name,
            points=[
                self._build_point(item)
                for item in store
            ],
            wait=True,
        )

        return self.collection_name

    def load(self) -> list[dict]:
        raise NotImplementedError(
            "QdrantVectorStoreRepository does not support full load(). "
            "Use search() for retrieval."
        )

    def search(
        self,
        query: str,
        top_k: int,
        embedding_fn: Callable[[str], list[float]],
    ) -> list[dict]:
        self.ensure_collection()
        query_embedding = embedding_fn(query)
        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k,
            with_payload=True,
            with_vectors=False,
        )

        return [
            self._point_to_result(point)
            for point in response.points
        ]

    def ensure_collection(self) -> None:
        if self.client.collection_exists(self.collection_name):
            return

        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=create_qdrant_vector_params(
                vector_size=self.vector_size,
                distance=self.distance,
            ),
        )

    def _build_point(self, item: dict):
        embedding = item.get("embedding")

        if not isinstance(embedding, list):
            raise ValueError("vector store item embedding must be a list")

        payload = {
            "id": item["id"],
            "text": item["text"],
            "source": item["source"],
        }

        if "length" in item:
            payload["length"] = item["length"]

        from qdrant_client import models

        return models.PointStruct(
            id=item["id"],
            vector=embedding,
            payload=payload,
        )

    def _point_to_result(self, point) -> dict:
        payload = point.payload or {}

        return {
            "id": payload.get("id", point.id),
            "text": payload.get("text", ""),
            "source": payload.get("source", ""),
            "score": point.score,
        }


def create_qdrant_client(
    url: str = QDRANT_URL,
    api_key: str = QDRANT_API_KEY,
):
    from qdrant_client import QdrantClient

    return QdrantClient(
        url=url,
        api_key=api_key or None,
    )


def create_qdrant_vector_params(
    vector_size: int = QDRANT_VECTOR_SIZE,
    distance: str = QDRANT_DISTANCE,
):
    from qdrant_client import models

    return models.VectorParams(
        size=vector_size,
        distance=parse_qdrant_distance(distance),
    )


def parse_qdrant_distance(distance: str):
    from qdrant_client import models

    normalized_distance = distance.strip().lower()
    mapping = {
        "cosine": models.Distance.COSINE,
        "dot": models.Distance.DOT,
        "euclid": models.Distance.EUCLID,
        "euclidean": models.Distance.EUCLID,
        "manhattan": models.Distance.MANHATTAN,
    }

    if normalized_distance not in mapping:
        raise ValueError(
            "Unsupported QDRANT_DISTANCE. Expected Cosine, Dot, Euclid, "
            f"or Manhattan, got: {distance}"
        )

    return mapping[normalized_distance]


def create_vector_store_repository(
    backend: str,
    vector_store_path: str | Path,
) -> VectorStoreRepository:
    normalized_backend = backend.strip().lower()

    if normalized_backend == "json":
        return JsonVectorStoreRepository(vector_store_path)

    if normalized_backend == "qdrant":
        return QdrantVectorStoreRepository()

    if normalized_backend == "milvus":
        raise NotImplementedError(
            f"{normalized_backend} vector store repository is not implemented"
        )

    raise ValueError(
        "Unsupported VECTOR_STORE_BACKEND. Expected 'json', 'qdrant', "
        f"or 'milvus', got: {backend}"
    )
