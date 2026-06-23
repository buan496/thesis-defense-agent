import json
from pathlib import Path


REQUIRED_FIELDS_BY_TYPE = {
    "rag_retrieval": {
        "query": str,
        "expected_keywords": list,
    },
    "faithfulness": {
        "question": str,
        "evidence": str,
        "answer": str,
        "expected_passed": bool,
    },
    "agent_routing": {
        "user_message": str,
        "expected_tools": list,
        "expected_arguments": dict,
        "expected_answer_contains": list,
    },
    "manual": {
        "notes": str,
    },
}


def load_benchmark_draft(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"benchmark draft file not found: {file_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def validate_benchmark_draft(draft: dict) -> dict:
    item_results = [
        validate_benchmark_draft_item(item)
        for item in draft.get("items", [])
    ]
    invalid_items = [
        item_result
        for item_result in item_results
        if not item_result["passed"]
    ]

    return {
        "item_count": len(item_results),
        "valid_count": len(item_results) - len(invalid_items),
        "invalid_count": len(invalid_items),
        "passed": len(invalid_items) == 0,
        "items": item_results,
    }


def validate_benchmark_draft_item(item: dict) -> dict:
    draft_id = item.get("draft_id")
    benchmark_type = item.get("benchmark_type")
    draft_fields = item.get("draft_fields", {})
    errors = []

    required_fields = REQUIRED_FIELDS_BY_TYPE.get(benchmark_type)

    if required_fields is None:
        errors.append(f"unknown benchmark_type: {benchmark_type}")
    elif not isinstance(draft_fields, dict):
        errors.append("draft_fields must be an object")
    else:
        errors.extend(
            validate_required_fields(
                draft_fields,
                required_fields,
            )
        )

    return {
        "draft_id": draft_id,
        "benchmark_type": benchmark_type,
        "passed": len(errors) == 0,
        "errors": errors,
    }


def validate_required_fields(
    draft_fields: dict,
    required_fields: dict[str, type],
) -> list[str]:
    errors = []

    for field_name, expected_type in required_fields.items():
        if field_name not in draft_fields:
            errors.append(f"missing field: {field_name}")
            continue

        value = draft_fields[field_name]

        if not isinstance(value, expected_type):
            errors.append(
                f"field {field_name} must be {expected_type.__name__}"
            )
            continue

        if is_empty_value(value):
            errors.append(f"field {field_name} must not be empty")

    return errors


def is_empty_value(value) -> bool:
    if isinstance(value, str):
        return not value.strip()

    if isinstance(value, list):
        return len(value) == 0

    if value is None:
        return True

    return False
