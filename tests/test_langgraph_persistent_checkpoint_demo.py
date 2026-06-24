import json

import pytest

from app.langgraph_workflow.persistent_checkpoint_demo import (
    build_checkpoint_snapshot,
    load_checkpoint_snapshot,
    run_persistent_checkpoint_demo,
    save_checkpoint_snapshot,
    summarize_checkpoint_snapshot,
)


def fake_embedding(text: str) -> list[float]:
    if "architecture" in text.lower() or "system" in text.lower():
        return [1.0, 0.0]

    return [0.0, 1.0]


def build_test_vector_store(tmp_path):
    vector_store_path = tmp_path / "vector_store.json"
    store = [
        {
            "id": 0,
            "text": "The system architecture contains retrieval and question generation.",
            "source": "test",
            "embedding": [1.0, 0.0],
        }
    ]
    vector_store_path.write_text(
        json.dumps(store, ensure_ascii=False),
        encoding="utf-8",
    )
    return vector_store_path


def build_report():
    return {
        "thread_id": "thread-1",
        "checkpointer_type": "InMemorySaver",
        "interrupted_checkpoint": {
            "thread_id": "thread-1",
            "checkpoint_id": "checkpoint-1",
            "next": ["answer_interrupt"],
            "values": {
                "topic": "system architecture",
                "question": "How is the system designed?",
            },
            "interrupts": [
                {
                    "type": "answer_required",
                    "question": "How is the system designed?",
                }
            ],
            "has_pending_interrupt": True,
        },
        "resumed_checkpoint": {
            "thread_id": "thread-1",
            "checkpoint_id": "checkpoint-2",
            "next": [],
            "values": {
                "topic": "system architecture",
                "question": "How is the system designed?",
                "answer": "The system is modular.",
            },
            "interrupts": [],
            "has_pending_interrupt": False,
        },
    }


def test_build_checkpoint_snapshot():
    snapshot = build_checkpoint_snapshot(build_report())

    assert snapshot["thread_id"] == "thread-1"
    assert snapshot["checkpointer_type"] == "InMemorySaver"
    assert snapshot["has_resumed"] is True
    assert snapshot["created_at"]


def test_save_and_load_checkpoint_snapshot(tmp_path):
    snapshot = build_checkpoint_snapshot(build_report())
    output_path = tmp_path / "snapshot.json"

    saved_path = save_checkpoint_snapshot(
        snapshot,
        str(output_path),
    )
    loaded = load_checkpoint_snapshot(saved_path)

    assert loaded["thread_id"] == "thread-1"
    assert loaded["interrupted_checkpoint"]["next"] == ["answer_interrupt"]
    assert loaded["resumed_checkpoint"]["next"] == []


def test_load_checkpoint_snapshot_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_checkpoint_snapshot(str(tmp_path / "missing.json"))


def test_summarize_checkpoint_snapshot():
    snapshot = build_checkpoint_snapshot(build_report())

    summary = summarize_checkpoint_snapshot(snapshot)

    assert summary["thread_id"] == "thread-1"
    assert summary["interrupted_next"] == ["answer_interrupt"]
    assert summary["interrupted_has_pending_interrupt"] is True
    assert summary["has_resumed"] is True
    assert summary["resumed_next"] == []
    assert summary["resumed_has_pending_interrupt"] is False
    assert summary["resumed_value_keys"] == [
        "answer",
        "question",
        "topic",
    ]


def test_run_persistent_checkpoint_demo(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    output_path = tmp_path / "checkpoints" / "thread-1.json"

    result = run_persistent_checkpoint_demo(
        topic="system architecture",
        thread_id="thread-1",
        output_path=str(output_path),
        answer="The system is modular.",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert result["snapshot_path"] == str(output_path)
    assert output_path.exists()
    assert result["summary"]["has_resumed"] is True
    assert "answer" in result["summary"]["resumed_value_keys"]
    assert "question" in result["summary"]["resumed_value_keys"]
    assert "topic" in result["summary"]["resumed_value_keys"]
