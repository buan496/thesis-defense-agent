import json
import re

from copy import deepcopy
from pathlib import Path
from typing import Any

from app.config import LONG_TERM_MEMORY_PATH
from app.task_models import current_time

MEMORY_STOPWORDS = {
    "a",
    "an",
    "and",
    "answer",
    "answers",
    "are",
    "can",
    "do",
    "does",
    "for",
    "how",
    "i",
    "is",
    "my",
    "of",
    "question",
    "questions",
    "should",
    "the",
    "to",
    "what",
    "when",
    "where",
    "why",
}


def create_empty_long_term_memory() -> dict[str, Any]:
    return {
        "profile": {},
        "weaknesses": [],
        "training_summaries": [],
        "metadata": {
            "created_at": current_time(),
            "updated_at": current_time(),
        },
    }


def load_long_term_memory(
    path: str | Path = LONG_TERM_MEMORY_PATH,
) -> dict[str, Any]:
    memory_path = Path(path)

    if not memory_path.exists():
        return create_empty_long_term_memory()

    try:
        memory = json.loads(
            memory_path.read_text(encoding="utf-8")
        )
    except json.JSONDecodeError as error:
        raise ValueError(
            f"long term memory file is not valid JSON: {memory_path}"
        ) from error

    validate_long_term_memory(memory)
    return memory


def save_long_term_memory(
    memory: dict[str, Any],
    path: str | Path = LONG_TERM_MEMORY_PATH,
) -> Path:
    validate_long_term_memory(memory)

    memory_copy = deepcopy(memory)
    memory_copy.setdefault("metadata", {})
    memory_copy["metadata"]["updated_at"] = current_time()

    memory_path = Path(path)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = memory_path.with_suffix(
        memory_path.suffix + ".tmp"
    )

    try:
        temporary_path.write_text(
            json.dumps(
                memory_copy,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary_path.replace(memory_path)
    finally:
        if temporary_path.exists():
            temporary_path.unlink()

    return memory_path


def validate_long_term_memory(memory: dict[str, Any]) -> None:
    required_fields = {
        "profile",
        "weaknesses",
        "training_summaries",
        "metadata",
    }

    missing_fields = required_fields - memory.keys()

    if missing_fields:
        raise ValueError(
            f"long term memory missing fields: {sorted(missing_fields)}"
        )

    if not isinstance(memory["profile"], dict):
        raise ValueError("profile must be a dictionary")

    if not isinstance(memory["weaknesses"], list):
        raise ValueError("weaknesses must be a list")

    if not isinstance(memory["training_summaries"], list):
        raise ValueError("training_summaries must be a list")

    if not isinstance(memory["metadata"], dict):
        raise ValueError("metadata must be a dictionary")


def update_memory_profile(
    memory: dict[str, Any],
    **fields: str | None,
) -> dict[str, Any]:
    validate_long_term_memory(memory)

    updated_memory = deepcopy(memory)

    for key, value in fields.items():
        if value is not None and value.strip():
            updated_memory["profile"][key] = value.strip()

    updated_memory["metadata"]["updated_at"] = current_time()
    return updated_memory


def add_weakness(
    memory: dict[str, Any],
    weakness: str,
    source_task_id: str | None = None,
) -> dict[str, Any]:
    validate_long_term_memory(memory)

    if not weakness.strip():
        raise ValueError("weakness cannot be empty")

    updated_memory = deepcopy(memory)
    item = {
        "weakness": weakness.strip(),
        "created_at": current_time(),
    }

    if source_task_id:
        item["source_task_id"] = source_task_id

    updated_memory["weaknesses"].append(item)
    updated_memory["metadata"]["updated_at"] = current_time()
    return updated_memory


def add_training_summary(
    memory: dict[str, Any],
    summary: str,
    task_id: str | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    validate_long_term_memory(memory)

    if not summary.strip():
        raise ValueError("summary cannot be empty")

    updated_memory = deepcopy(memory)
    item = {
        "summary": summary.strip(),
        "created_at": current_time(),
    }

    if task_id:
        item["task_id"] = task_id

    if topic:
        item["topic"] = topic

    updated_memory["training_summaries"].append(item)
    updated_memory["metadata"]["updated_at"] = current_time()
    return updated_memory


def prune_long_term_memory(
    memory: dict[str, Any],
    max_weaknesses: int,
    max_summaries: int,
    deduplicate: bool = True,
) -> dict[str, Any]:
    validate_long_term_memory(memory)

    if max_weaknesses < 0:
        raise ValueError("max_weaknesses must be greater than or equal to 0")

    if max_summaries < 0:
        raise ValueError("max_summaries must be greater than or equal to 0")

    updated_memory = deepcopy(memory)

    weaknesses = updated_memory["weaknesses"]
    summaries = updated_memory["training_summaries"]

    if deduplicate:
        weaknesses = deduplicate_memory_items(
            weaknesses,
            key_name="weakness",
        )
        summaries = deduplicate_memory_items(
            summaries,
            key_name="summary",
        )

    updated_memory["weaknesses"] = keep_recent_memory_items(
        weaknesses,
        max_weaknesses,
    )
    updated_memory["training_summaries"] = keep_recent_memory_items(
        summaries,
        max_summaries,
    )
    updated_memory["metadata"]["updated_at"] = current_time()

    return updated_memory


def keep_recent_memory_items(
    items: list[dict[str, Any]],
    max_items: int,
) -> list[dict[str, Any]]:
    if max_items == 0:
        return []

    return items[-max_items:]


def deduplicate_memory_items(
    items: list[dict[str, Any]],
    key_name: str,
) -> list[dict[str, Any]]:
    seen_values = set()
    deduplicated_reversed = []

    for item in reversed(items):
        value = item.get(key_name, "")
        normalized_value = normalize_memory_text(value)

        if not normalized_value:
            deduplicated_reversed.append(item)
            continue

        if normalized_value in seen_values:
            continue

        seen_values.add(normalized_value)
        deduplicated_reversed.append(item)

    return list(reversed(deduplicated_reversed))


def build_long_term_memory_context(
    memory: dict[str, Any],
    max_weaknesses: int = 5,
    max_summaries: int = 3,
    query: str | None = None,
) -> str:
    validate_long_term_memory(memory)

    if max_weaknesses < 0:
        raise ValueError("max_weaknesses must be greater than or equal to 0")

    if max_summaries < 0:
        raise ValueError("max_summaries must be greater than or equal to 0")

    lines = ["Long-term memory:"]
    profile = memory["profile"]

    if profile:
        lines.append("Profile:")

        for key, value in profile.items():
            lines.append(f"- {key}: {value}")

    weaknesses = select_relevant_memory_items(
        items=memory["weaknesses"],
        query=query,
        max_items=max_weaknesses,
        text_builder=lambda item: item.get("weakness", ""),
    )

    if weaknesses:
        lines.append("Weaknesses:")

        for item in weaknesses:
            lines.append(f"- {item['weakness']}")

    summaries = select_relevant_memory_items(
        items=memory["training_summaries"],
        query=query,
        max_items=max_summaries,
        text_builder=lambda item: (
            f"{item.get('topic', '')} {item.get('summary', '')}"
        ),
    )

    if summaries:
        lines.append("Recent training summaries:")

        for item in summaries:
            topic = item.get("topic")
            prefix = f"{topic}: " if topic else ""
            lines.append(f"- {prefix}{item['summary']}")

    if len(lines) == 1:
        return ""

    return "\n".join(lines)


def select_relevant_memory_items(
    items: list[dict[str, Any]],
    query: str | None,
    max_items: int,
    text_builder,
) -> list[dict[str, Any]]:
    if max_items < 0:
        raise ValueError("max_items must be greater than or equal to 0")

    if max_items == 0 or not items:
        return []

    if query is None or not query.strip():
        return items[-max_items:]

    scored_items = []

    for index, item in enumerate(items):
        text = text_builder(item)
        score = calculate_memory_relevance_score(
            query=query,
            text=text,
        )

        if score > 0:
            scored_items.append((score, index, item))

    if not scored_items:
        return items[-max_items:]

    ranked_items = sorted(
        scored_items,
        key=lambda scored_item: (
            scored_item[0],
            scored_item[1],
        ),
        reverse=True,
    )

    selected_items = [
        item
        for _, _, item in ranked_items[:max_items]
    ]

    return selected_items


def calculate_memory_relevance_score(
    query: str,
    text: str,
) -> int:
    normalized_query = normalize_memory_text(query)
    normalized_text = normalize_memory_text(text)

    if not normalized_query or not normalized_text:
        return 0

    score = 0

    if normalized_query in normalized_text:
        score += 5

    query_terms = extract_memory_terms(normalized_query)

    for term in query_terms:
        if term in normalized_text:
            score += 1

    return score


def extract_memory_terms(text: str) -> list[str]:
    terms = [
        term
        for term in re.split(r"\s+", text)
        if len(term) >= 2 and term not in MEMORY_STOPWORDS
    ]

    if terms:
        return terms

    if len(text) >= 2:
        return [text]

    return []


def normalize_memory_text(text: str) -> str:
    normalized = re.sub(
        r"[^0-9a-zA-Z\u4e00-\u9fff]+",
        " ",
        text.lower(),
    )

    return re.sub(r"\s+", " ", normalized).strip()
