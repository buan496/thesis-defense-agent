import json
from pathlib import Path


def save_vector_store(store: list[dict], file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    json_text = json.dumps(store, ensure_ascii=False, indent=2)

    path.write_text(json_text, encoding="utf-8")


def load_vector_store(file_path: str) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"向量库文件不存在：{file_path}")

    json_text = path.read_text(encoding="utf-8")

    return json.loads(json_text)