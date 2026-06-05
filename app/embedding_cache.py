import json
from pathlib import Path


def load_embedding_cache(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        return {}

    return json.loads(path.read_text(encoding="utf-8"))


def save_embedding_cache(file_path: str, cache: dict) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(cache, ensure_ascii=False),
        encoding="utf-8",
    )


def get_cached_embedding(
    text: str,
    cache: dict,
) -> list[float] | None:
    return cache.get(text)