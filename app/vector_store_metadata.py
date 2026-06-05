import json
from datetime import datetime
from pathlib import Path


def save_vector_store_metadata(
        file_path: str,
        source_file: str,
        embedding_model: str,
        chunk_size: int,
        overlap: int,
        min_chunk_size: int,
    ) -> None:
    metadata = {
        "source_file": source_file,
        "embedding_model": embedding_model,
        "chunk_size": chunk_size,
        "overlap": overlap,
        "min_chunk_size": min_chunk_size,
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(metadata, ensure_ascii=False, indent=2)
    path.write_text(json_text, encoding="utf-8")


def load_vector_store_metadata(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"向量库元信息文件不存在：{file_path}")

    json_text = path.read_text(encoding="utf-8")
    return json.loads(json_text)

def is_vector_store_metadata_match(
        metadata: dict,
        source_file: str,
        embedding_model: str,
        chunk_size: int,
        overlap: int,
        min_chunk_size: int,
    ) -> bool:
    return (
            metadata.get("source_file") == source_file
            and metadata.get("embedding_model") == embedding_model
            and metadata.get("chunk_size") == chunk_size
            and metadata.get("overlap") == overlap
            and metadata.get("min_chunk_size") == min_chunk_size
        )