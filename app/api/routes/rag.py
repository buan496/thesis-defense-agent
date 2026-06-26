from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.vector_store import search_vector_store
from app.vector_store_io import load_vector_store


router = APIRouter(prefix="/rag", tags=["rag"])


class RagSearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=3, ge=1, le=10)


class RagSearchResult(BaseModel):
    id: int
    text: str
    source: str
    score: float


class RagSearchResponse(BaseModel):
    query: str
    top_k: int
    results: list[RagSearchResult]


def get_vector_store_path() -> str:
    return "data/vector_store.json"


def get_embedding_function() -> Callable[[str], list[float]]:
    # Import lazily so lightweight API endpoints do not require LLM/API config.
    from app.embeddings import create_embedding

    return create_embedding


@router.get("/status")
def rag_status() -> dict[str, object]:
    vector_store_path = Path("data/vector_store.json")
    metadata_path = Path("data/vector_store_meta.json")

    return {
        "vector_store_path": str(vector_store_path),
        "vector_store_exists": vector_store_path.exists(),
        "metadata_path": str(metadata_path),
        "metadata_exists": metadata_path.exists(),
    }


@router.post("/search")
def rag_search(
    request: RagSearchRequest,
    vector_store_path: str = Depends(get_vector_store_path),
    embedding_fn: Callable[[str], list[float]] = Depends(
        get_embedding_function
    ),
) -> RagSearchResponse:
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=422,
            detail="query must not be empty",
        )

    try:
        store = load_vector_store(vector_store_path)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    results = search_vector_store(
        query=query,
        store=store,
        top_k=request.top_k,
        embedding_fn=embedding_fn,
    )

    return RagSearchResponse(
        query=query,
        top_k=request.top_k,
        results=[
            RagSearchResult(
                id=result["id"],
                text=result["text"],
                source=result["source"],
                score=result["score"],
            )
            for result in results
        ],
    )
