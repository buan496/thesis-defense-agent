from app.memory_auditor import (
    audit_long_term_memory,
    audit_memory_hits,
    build_memory_context_report,
    count_non_empty_lines,
    find_duplicate_memory_items,
    find_empty_memory_items,
    find_empty_profile_fields,
    rank_memory_hits,
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


def test_audit_memory_hits():
    report = audit_memory_hits(
        memory={
            "profile": {},
            "weaknesses": [
                {"weakness": "回答缺少实验指标"},
                {"weakness": "系统架构回答缺少模块案例"},
            ],
            "training_summaries": [
                {
                    "topic": "实验验证",
                    "summary": "下一轮练习指标设计。",
                },
                {
                    "topic": "系统架构",
                    "summary": "下一轮练习模块边界。",
                },
            ],
            "metadata": {},
        },
        query="系统架构",
        max_weaknesses=1,
        max_summaries=1,
    )

    assert report["query"] == "系统架构"
    assert report["weakness_hit_count"] == 1
    assert report["summary_hit_count"] == 1
    assert report["weakness_hits"][0]["index"] == 1
    assert report["weakness_hits"][0]["text"] == "系统架构回答缺少模块案例"
    assert report["summary_hits"][0]["index"] == 1
    assert report["summary_hits"][0]["text"] == "下一轮练习模块边界。"


def test_audit_memory_hits_rejects_invalid_arguments():
    memory = {
        "profile": {},
        "weaknesses": [],
        "training_summaries": [],
        "metadata": {},
    }

    try:
        audit_memory_hits(memory, query=" ")
    except ValueError as error:
        assert "query" in str(error)
    else:
        raise AssertionError("empty query should fail")

    try:
        audit_memory_hits(memory, query="系统架构", max_weaknesses=-1)
    except ValueError as error:
        assert "max_weaknesses" in str(error)
    else:
        raise AssertionError("negative max_weaknesses should fail")


def test_rank_memory_hits_returns_empty_when_no_match():
    hits = rank_memory_hits(
        items=[{"weakness": "实验指标"}],
        query="系统架构",
        max_items=5,
        key_name="weakness",
    )

    assert hits == []


def test_build_memory_context_report():
    report = build_memory_context_report(
        memory={
            "profile": {
                "thesis_direction": "bilingual ASR",
            },
            "weaknesses": [
                {"weakness": "回答缺少实验指标"},
                {"weakness": "系统架构回答缺少模块案例"},
            ],
            "training_summaries": [
                {
                    "topic": "系统架构",
                    "summary": "下一轮练习模块边界。",
                },
            ],
            "metadata": {},
        },
        query="系统架构",
        max_weaknesses=1,
        max_summaries=1,
    )

    assert report["query"] == "系统架构"
    assert report["max_weaknesses"] == 1
    assert report["max_summaries"] == 1
    assert report["is_empty"] is False
    assert report["context_character_count"] == len(report["context"])
    assert "Long-term memory:" in report["context"]
    assert "- thesis_direction: bilingual ASR" in report["context"]
    assert "系统架构回答缺少模块案例" in report["context"]
    assert "回答缺少实验指标" not in report["context"]
    assert "系统架构: 下一轮练习模块边界。" in report["context"]


def test_build_memory_context_report_handles_empty_memory():
    report = build_memory_context_report(
        memory={
            "profile": {},
            "weaknesses": [],
            "training_summaries": [],
            "metadata": {},
        }
    )

    assert report["context"] == ""
    assert report["context_character_count"] == 0
    assert report["line_count"] == 0
    assert report["is_empty"] is True


def test_count_non_empty_lines():
    assert count_non_empty_lines("a\n\n b \n") == 2
