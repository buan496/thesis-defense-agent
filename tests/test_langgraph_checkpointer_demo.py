import json

from app.langgraph_workflow.checkpointer_demo import (
    build_checkpointer_demo_graph,
    inspect_checkpoint_state,
    run_checkpointer_demo,
)
from app.langgraph_workflow.interrupt_demo import (
    resume_interrupt_demo,
    start_interrupt_demo,
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


def test_build_checkpointer_demo_graph_returns_graph_and_checkpointer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    graph, checkpointer = build_checkpointer_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert graph is not None
    assert type(checkpointer).__name__ == "InMemorySaver"


def test_inspect_checkpoint_state_before_and_after_resume(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph, _ = build_checkpointer_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    start_interrupt_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )
    interrupted_checkpoint = inspect_checkpoint_state(
        graph=graph,
        thread_id="thread-1",
    )

    assert interrupted_checkpoint["thread_id"] == "thread-1"
    assert interrupted_checkpoint["checkpoint_id"]
    assert interrupted_checkpoint["next"] == ["answer_interrupt"]
    assert interrupted_checkpoint["has_pending_interrupt"] is True
    assert interrupted_checkpoint["interrupts"][0]["type"] == "answer_required"
    assert interrupted_checkpoint["values"]["question"] == (
        "How is the system architecture designed?"
    )

    resume_interrupt_demo(
        graph=graph,
        thread_id="thread-1",
        answer="The system is modular.",
    )
    resumed_checkpoint = inspect_checkpoint_state(
        graph=graph,
        thread_id="thread-1",
    )

    assert resumed_checkpoint["checkpoint_id"]
    assert resumed_checkpoint["checkpoint_id"] != (
        interrupted_checkpoint["checkpoint_id"]
    )
    assert resumed_checkpoint["next"] == []
    assert resumed_checkpoint["has_pending_interrupt"] is False
    assert resumed_checkpoint["values"]["answer"] == "The system is modular."


def test_run_checkpointer_demo_without_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_checkpointer_demo(
        topic="system architecture",
        thread_id="thread-1",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert report["thread_id"] == "thread-1"
    assert report["checkpointer_type"] == "InMemorySaver"
    assert report["interrupt_payload"]["type"] == "answer_required"
    assert report["interrupted_checkpoint"]["has_pending_interrupt"] is True
    assert report["resumed_result"] is None
    assert report["resumed_checkpoint"] is None


def test_run_checkpointer_demo_with_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_checkpointer_demo(
        topic="system architecture",
        thread_id="thread-1",
        answer="The system is modular.",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert report["resumed_result"]["answer"] == "The system is modular."
    assert report["resumed_checkpoint"]["next"] == []
    assert report["resumed_checkpoint"]["has_pending_interrupt"] is False
