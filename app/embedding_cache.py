import json
from pathlib import Path


def load_embedding_cache(file_path: str,
        embedding_model: str,
        ) -> dict:
    path = Path(file_path)

    empty_cache = {
            "embedding_model": embedding_model,
            "items": {},
        }
    
    if not path.exists():
        return empty_cache

    cache = json.loads(path.read_text(encoding="utf-8"))

    if cache.get("embedding_model") != embedding_model:
        return empty_cache

    if not isinstance(cache.get("items"), dict):
        return empty_cache

    return cache

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
    return cache["items"].get(text)