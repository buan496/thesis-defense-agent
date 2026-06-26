from pathlib import Path

from fastapi import APIRouter


router = APIRouter(prefix="/rag", tags=["rag"])


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
