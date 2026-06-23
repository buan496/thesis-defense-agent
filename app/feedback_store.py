import json
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def create_feedback_record(
    source_type: str,
    source_id: str,
    rating: int,
    comment: str,
    tags: list[str] | None = None,
    metadata: dict | None = None,
) -> dict:
    if not source_type.strip():
        raise ValueError("source_type must not be empty")

    if not source_id.strip():
        raise ValueError("source_id must not be empty")

    if rating < 1 or rating > 5:
        raise ValueError("rating must be between 1 and 5")

    if not comment.strip():
        raise ValueError("comment must not be empty")

    return {
        "id": uuid4().hex,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_type": source_type,
        "source_id": source_id,
        "rating": rating,
        "comment": comment,
        "tags": tags or [],
        "metadata": metadata or {},
    }


def save_feedback_record(
    file_path: str,
    feedback_record: dict,
) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                feedback_record,
                ensure_ascii=False,
            )
        )
        file.write("\n")

    return str(path)


def load_feedback_records(file_path: str) -> list[dict]:
    path = Path(file_path)

    if not path.exists():
        return []

    records = []

    with path.open(encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()

            if not line:
                continue

            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"line {line_number} is not valid JSON"
                ) from error

    return records


def summarize_feedback_records(records: list[dict]) -> dict:
    if not records:
        return {
            "count": 0,
            "average_rating": 0,
            "source_type_counts": {},
            "tag_counts": {},
        }

    source_type_counts = {}
    tag_counts = {}
    rating_sum = 0

    for record in records:
        rating_sum += record.get("rating", 0)

        source_type = record.get("source_type", "unknown")
        source_type_counts[source_type] = (
            source_type_counts.get(source_type, 0) + 1
        )

        for tag in record.get("tags", []):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    return {
        "count": len(records),
        "average_rating": rating_sum / len(records),
        "source_type_counts": source_type_counts,
        "tag_counts": tag_counts,
    }
