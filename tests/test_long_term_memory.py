import json

import pytest

from app.long_term_memory import (
    add_training_summary,
    add_weakness,
    build_long_term_memory_context,
    calculate_memory_relevance_score,
    create_empty_long_term_memory,
    load_long_term_memory,
    prune_long_term_memory,
    save_long_term_memory,
    select_relevant_memory_items,
    update_memory_profile,
    validate_long_term_memory,
)


def test_create_empty_long_term_memory():
    memory = create_empty_long_term_memory()

    assert memory["profile"] == {}
    assert memory["weaknesses"] == []
    assert memory["training_summaries"] == []
    assert memory["metadata"]["created_at"]
    assert memory["metadata"]["updated_at"]


def test_load_missing_long_term_memory_returns_empty_memory(tmp_path):
    memory = load_long_term_memory(
        tmp_path / "missing.json",
    )

    assert memory["profile"] == {}
    assert memory["weaknesses"] == []
    assert memory["training_summaries"] == []


def test_save_and_load_long_term_memory(tmp_path):
    memory = create_empty_long_term_memory()
    memory = update_memory_profile(
        memory,
        thesis_direction="bilingual speech recognition",
    )
    memory = add_weakness(
        memory,
        "answers about system architecture lack module examples",
        source_task_id="task-001",
    )
    memory = add_training_summary(
        memory,
        "practice engineering debugging examples next time",
        task_id="task-001",
        topic="system architecture",
    )

    memory_path = save_long_term_memory(
        memory,
        path=tmp_path / "memory.json",
    )

    loaded_memory = load_long_term_memory(memory_path)

    assert loaded_memory["profile"]["thesis_direction"] == (
        "bilingual speech recognition"
    )
    assert loaded_memory["weaknesses"][0]["weakness"] == (
        "answers about system architecture lack module examples"
    )
    assert loaded_memory["training_summaries"][0]["summary"] == (
        "practice engineering debugging examples next time"
    )


def test_update_memory_profile_ignores_empty_values():
    memory = create_empty_long_term_memory()

    updated_memory = update_memory_profile(
        memory,
        thesis_direction="bilingual speech recognition",
        empty_field="   ",
        none_field=None,
    )

    assert updated_memory["profile"] == {
        "thesis_direction": "bilingual speech recognition",
    }
    assert memory["profile"] == {}


def test_add_weakness_rejects_empty_text():
    memory = create_empty_long_term_memory()

    with pytest.raises(ValueError, match="weakness cannot be empty"):
        add_weakness(memory, "   ")


def test_add_training_summary_rejects_empty_text():
    memory = create_empty_long_term_memory()

    with pytest.raises(ValueError, match="summary cannot be empty"):
        add_training_summary(memory, "   ")


def test_build_long_term_memory_context():
    memory = create_empty_long_term_memory()
    memory = update_memory_profile(
        memory,
        thesis_direction="bilingual speech recognition",
    )
    memory = add_weakness(memory, "system architecture answer is too vague")
    memory = add_weakness(memory, "experiment validation answer lacks metrics")
    memory = add_training_summary(
        memory,
        "practice tradeoffs in modular design",
        topic="system architecture",
    )

    context = build_long_term_memory_context(
        memory,
        max_weaknesses=1,
        max_summaries=1,
    )

    assert "Long-term memory:" in context
    assert "- thesis_direction: bilingual speech recognition" in context
    assert "experiment validation answer lacks metrics" in context
    assert "system architecture answer is too vague" not in context
    assert (
        "system architecture: practice tradeoffs in modular design"
        in context
    )


def test_build_long_term_memory_context_respects_zero_limits():
    memory = create_empty_long_term_memory()
    memory = add_weakness(memory, "weakness should be hidden")
    memory = add_training_summary(memory, "summary should be hidden")

    context = build_long_term_memory_context(
        memory,
        max_weaknesses=0,
        max_summaries=0,
    )

    assert context == ""


def test_build_long_term_memory_context_prefers_relevant_weaknesses():
    memory = create_empty_long_term_memory()
    memory = add_weakness(memory, "answer lacks experiment metrics")
    memory = add_weakness(memory, "system architecture needs module examples")

    context = build_long_term_memory_context(
        memory,
        query="system architecture",
        max_weaknesses=1,
        max_summaries=0,
    )

    assert "system architecture needs module examples" in context
    assert "answer lacks experiment metrics" not in context


def test_build_long_term_memory_context_prefers_relevant_summaries():
    memory = create_empty_long_term_memory()
    memory = add_training_summary(
        memory,
        "practice validation metrics",
        topic="experiment validation",
    )
    memory = add_training_summary(
        memory,
        "practice module boundaries",
        topic="system architecture",
    )

    context = build_long_term_memory_context(
        memory,
        query="system architecture",
        max_weaknesses=0,
        max_summaries=1,
    )

    assert "system architecture: practice module boundaries" in context
    assert "experiment validation: practice validation metrics" not in context


def test_build_long_term_memory_context_falls_back_to_recent_items():
    memory = create_empty_long_term_memory()
    memory = add_weakness(memory, "old weakness")
    memory = add_weakness(memory, "recent weakness")

    context = build_long_term_memory_context(
        memory,
        query="unrelated query",
        max_weaknesses=1,
        max_summaries=0,
    )

    assert "recent weakness" in context
    assert "old weakness" not in context


def test_select_relevant_memory_items_rejects_negative_limit():
    with pytest.raises(ValueError, match="max_items"):
        select_relevant_memory_items(
            items=[],
            query="system architecture",
            max_items=-1,
            text_builder=lambda item: item["text"],
        )


def test_calculate_memory_relevance_score():
    score = calculate_memory_relevance_score(
        query="system architecture",
        text="system architecture needs module examples",
    )

    unrelated_score = calculate_memory_relevance_score(
        query="system architecture",
        text="experiment validation needs metrics",
    )

    assert score > unrelated_score
    assert unrelated_score == 0


def test_prune_long_term_memory_keeps_recent_items():
    memory = create_empty_long_term_memory()
    memory = add_weakness(memory, "old weakness")
    memory = add_weakness(memory, "middle weakness")
    memory = add_weakness(memory, "recent weakness")
    memory = add_training_summary(memory, "old summary")
    memory = add_training_summary(memory, "recent summary")

    pruned_memory = prune_long_term_memory(
        memory,
        max_weaknesses=2,
        max_summaries=1,
    )

    assert [
        item["weakness"] for item in pruned_memory["weaknesses"]
    ] == [
        "middle weakness",
        "recent weakness",
    ]
    assert [
        item["summary"] for item in pruned_memory["training_summaries"]
    ] == [
        "recent summary",
    ]


def test_prune_long_term_memory_deduplicates_and_keeps_newest():
    memory = create_empty_long_term_memory()
    memory = add_weakness(memory, "duplicate weakness", source_task_id="old")
    memory = add_weakness(memory, "other weakness")
    memory = add_weakness(memory, "duplicate weakness", source_task_id="new")
    memory = add_training_summary(memory, "duplicate summary", task_id="old")
    memory = add_training_summary(memory, "duplicate summary", task_id="new")

    pruned_memory = prune_long_term_memory(
        memory,
        max_weaknesses=5,
        max_summaries=5,
    )

    assert [
        item["weakness"] for item in pruned_memory["weaknesses"]
    ] == [
        "other weakness",
        "duplicate weakness",
    ]
    assert pruned_memory["weaknesses"][-1]["source_task_id"] == "new"
    assert len(pruned_memory["training_summaries"]) == 1
    assert pruned_memory["training_summaries"][0]["task_id"] == "new"


def test_prune_long_term_memory_can_clear_lists():
    memory = create_empty_long_term_memory()
    memory = add_weakness(memory, "weakness")
    memory = add_training_summary(memory, "summary")

    pruned_memory = prune_long_term_memory(
        memory,
        max_weaknesses=0,
        max_summaries=0,
    )

    assert pruned_memory["weaknesses"] == []
    assert pruned_memory["training_summaries"] == []


def test_prune_long_term_memory_rejects_negative_limits():
    memory = create_empty_long_term_memory()

    with pytest.raises(ValueError, match="max_weaknesses"):
        prune_long_term_memory(
            memory,
            max_weaknesses=-1,
            max_summaries=1,
        )

    with pytest.raises(ValueError, match="max_summaries"):
        prune_long_term_memory(
            memory,
            max_weaknesses=1,
            max_summaries=-1,
        )


def test_build_long_term_memory_context_returns_empty_string_for_empty_memory():
    memory = create_empty_long_term_memory()

    assert build_long_term_memory_context(memory) == ""


def test_build_long_term_memory_context_rejects_invalid_limits():
    memory = create_empty_long_term_memory()

    with pytest.raises(ValueError):
        build_long_term_memory_context(
            memory,
            max_weaknesses=-1,
        )

    with pytest.raises(ValueError):
        build_long_term_memory_context(
            memory,
            max_summaries=-1,
        )


def test_validate_long_term_memory_rejects_missing_fields():
    with pytest.raises(ValueError, match="long term memory missing fields"):
        validate_long_term_memory({})


def test_load_long_term_memory_rejects_invalid_json(tmp_path):
    memory_path = tmp_path / "broken.json"
    memory_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not valid JSON"):
        load_long_term_memory(memory_path)


def test_load_long_term_memory_rejects_invalid_schema(tmp_path):
    memory_path = tmp_path / "invalid.json"
    memory_path.write_text(
        json.dumps(
            {
                "profile": [],
                "weaknesses": [],
                "training_summaries": [],
                "metadata": {},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="profile must be a dictionary"):
        load_long_term_memory(memory_path)
