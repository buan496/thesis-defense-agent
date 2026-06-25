from typing import Any

from app.long_term_memory import (
    normalize_memory_text,
    validate_long_term_memory,
)


def audit_long_term_memory(
    memory: dict[str, Any],
) -> dict[str, Any]:
    validate_long_term_memory(memory)

    duplicate_weaknesses = find_duplicate_memory_items(
        memory["weaknesses"],
        key_name="weakness",
    )
    duplicate_summaries = find_duplicate_memory_items(
        memory["training_summaries"],
        key_name="summary",
    )
    empty_profile_fields = find_empty_profile_fields(memory["profile"])
    empty_weaknesses = find_empty_memory_items(
        memory["weaknesses"],
        key_name="weakness",
    )
    empty_summaries = find_empty_memory_items(
        memory["training_summaries"],
        key_name="summary",
    )

    issue_count = (
        len(duplicate_weaknesses)
        + len(duplicate_summaries)
        + len(empty_profile_fields)
        + len(empty_weaknesses)
        + len(empty_summaries)
    )

    return {
        "profile_count": len(memory["profile"]),
        "weakness_count": len(memory["weaknesses"]),
        "summary_count": len(memory["training_summaries"]),
        "duplicate_weakness_count": len(duplicate_weaknesses),
        "duplicate_summary_count": len(duplicate_summaries),
        "empty_profile_field_count": len(empty_profile_fields),
        "empty_weakness_count": len(empty_weaknesses),
        "empty_summary_count": len(empty_summaries),
        "issue_count": issue_count,
        "passed": issue_count == 0,
        "duplicate_weaknesses": duplicate_weaknesses,
        "duplicate_summaries": duplicate_summaries,
        "empty_profile_fields": empty_profile_fields,
        "empty_weaknesses": empty_weaknesses,
        "empty_summaries": empty_summaries,
        "recommendations": build_memory_audit_recommendations(
            duplicate_weaknesses=duplicate_weaknesses,
            duplicate_summaries=duplicate_summaries,
            empty_profile_fields=empty_profile_fields,
            empty_weaknesses=empty_weaknesses,
            empty_summaries=empty_summaries,
        ),
    }


def find_duplicate_memory_items(
    items: list[dict[str, Any]],
    key_name: str,
) -> list[dict[str, Any]]:
    groups: dict[str, list[int]] = {}

    for index, item in enumerate(items):
        value = item.get(key_name, "")
        normalized_value = normalize_memory_text(str(value))

        if not normalized_value:
            continue

        groups.setdefault(normalized_value, []).append(index)

    duplicates = []

    for normalized_value, indexes in sorted(groups.items()):
        if len(indexes) <= 1:
            continue

        duplicates.append(
            {
                "normalized_value": normalized_value,
                "indexes": indexes,
                "count": len(indexes),
                "values": [
                    items[index].get(key_name, "")
                    for index in indexes
                ],
            }
        )

    return duplicates


def find_empty_profile_fields(
    profile: dict[str, Any],
) -> list[str]:
    empty_fields = []

    for key, value in profile.items():
        if value is None:
            empty_fields.append(key)
            continue

        if isinstance(value, str) and not value.strip():
            empty_fields.append(key)

    return sorted(empty_fields)


def find_empty_memory_items(
    items: list[dict[str, Any]],
    key_name: str,
) -> list[dict[str, Any]]:
    empty_items = []

    for index, item in enumerate(items):
        value = item.get(key_name)

        if value is None:
            empty_items.append({"index": index, "value": value})
            continue

        if isinstance(value, str) and not value.strip():
            empty_items.append({"index": index, "value": value})

    return empty_items


def build_memory_audit_recommendations(
    duplicate_weaknesses: list[dict[str, Any]],
    duplicate_summaries: list[dict[str, Any]],
    empty_profile_fields: list[str],
    empty_weaknesses: list[dict[str, Any]],
    empty_summaries: list[dict[str, Any]],
) -> list[str]:
    recommendations = []

    if duplicate_weaknesses or duplicate_summaries:
        recommendations.append(
            "Run memory-prune to deduplicate repeated memory items."
        )

    if empty_profile_fields:
        recommendations.append(
            "Remove or rewrite empty profile fields."
        )

    if empty_weaknesses or empty_summaries:
        recommendations.append(
            "Remove empty weakness or summary records before injecting memory."
        )

    return recommendations
