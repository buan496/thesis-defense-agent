from app.memory_auditor import (
    audit_long_term_memory,
    find_duplicate_memory_items,
    find_empty_memory_items,
    find_empty_profile_fields,
)


def test_audit_long_term_memory_passes_clean_memory():
    report = audit_long_term_memory(
        {
            "profile": {
                "thesis_direction": "bilingual speech recognition",
            },
            "weaknesses": [
                {"weakness": "回答缺少模块案例"},
            ],
            "training_summaries": [
                {"summary": "下一轮练习系统架构。"},
            ],
            "metadata": {},
        }
    )

    assert report["passed"] is True
    assert report["profile_count"] == 1
    assert report["weakness_count"] == 1
    assert report["summary_count"] == 1
    assert report["issue_count"] == 0
    assert report["recommendations"] == []


def test_audit_long_term_memory_detects_duplicates_and_empty_items():
    report = audit_long_term_memory(
        {
            "profile": {
                "thesis_direction": " ",
            },
            "weaknesses": [
                {"weakness": "回答缺少模块案例"},
                {"weakness": "回答缺少模块案例"},
                {"weakness": ""},
            ],
            "training_summaries": [
                {"summary": "练习系统架构"},
                {"summary": "练习系统架构"},
                {"summary": None},
            ],
            "metadata": {},
        }
    )

    assert report["passed"] is False
    assert report["duplicate_weakness_count"] == 1
    assert report["duplicate_summary_count"] == 1
    assert report["empty_profile_field_count"] == 1
    assert report["empty_weakness_count"] == 1
    assert report["empty_summary_count"] == 1
    assert report["issue_count"] == 5
    assert report["empty_profile_fields"] == ["thesis_direction"]
    assert report["duplicate_weaknesses"][0]["indexes"] == [0, 1]
    assert report["duplicate_summaries"][0]["indexes"] == [0, 1]
    assert report["empty_weaknesses"] == [{"index": 2, "value": ""}]
    assert report["empty_summaries"] == [{"index": 2, "value": None}]
    assert "Run memory-prune" in report["recommendations"][0]


def test_find_duplicate_memory_items_ignores_empty_values():
    duplicates = find_duplicate_memory_items(
        [
            {"weakness": ""},
            {"weakness": "  "},
            {"weakness": "same"},
            {"weakness": "same"},
        ],
        key_name="weakness",
    )

    assert len(duplicates) == 1
    assert duplicates[0]["normalized_value"] == "same"
    assert duplicates[0]["count"] == 2


def test_find_empty_profile_fields():
    assert find_empty_profile_fields(
        {
            "valid": "value",
            "blank": " ",
            "missing": None,
        }
    ) == ["blank", "missing"]


def test_find_empty_memory_items():
    assert find_empty_memory_items(
        [
            {"summary": "valid"},
            {"summary": ""},
            {"summary": None},
            {},
        ],
        key_name="summary",
    ) == [
        {"index": 1, "value": ""},
        {"index": 2, "value": None},
        {"index": 3, "value": None},
    ]
