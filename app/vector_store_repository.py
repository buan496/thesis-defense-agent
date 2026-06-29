from collections.abc import Callable
from pathlib import Path
from typing import Protocol

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


def create_vector_store_repository(
    backend: str,
    vector_store_path: str | Path,
) -> VectorStoreRepository:
    normalized_backend = backend.strip().lower()

    if normalized_backend == "json":
        return JsonVectorStoreRepository(vector_store_path)

    if normalized_backend in {"qdrant", "milvus"}:
        raise NotImplementedError(
            f"{normalized_backend} vector store repository is not implemented"
        )

    raise ValueError(
        "Unsupported VECTOR_STORE_BACKEND. Expected 'json', 'qdrant', "
        f"or 'milvus', got: {backend}"
    )
