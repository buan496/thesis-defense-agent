import json

import pytest

from app.langgraph_workflow.interrupt_demo import (
    answer_interrupt_node,
    build_interrupt_demo_graph,
    build_thread_config,
    get_interrupt_payload,
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


def test_build_thread_config():
    assert build_thread_config("thread-1") == {
        "configurable": {
            "thread_id": "thread-1",
        }
    }


def test_build_thread_config_rejects_empty_thread_id():
    with pytest.raises(ValueError):
        build_thread_config(" ")


def test_answer_interrupt_node_requires_question():
    with pytest.raises(ValueError):
        answer_interrupt_node({})


def test_interrupt_demo_pauses_and_resumes(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_interrupt_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    interrupted_result = start_interrupt_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )
    interrupt_payload = get_interrupt_payload(interrupted_result)

    assert interrupt_payload == {
        "type": "answer_required",
        "question": "How is the system architecture designed?",
        "message": "Please provide the student's answer to resume.",
    }
    assert interrupted_result["topic"] == "system architecture"
    assert interrupted_result["question"] == (
        "How is the system architecture designed?"
    )
    assert "answer" not in interrupted_result

    resumed_result = resume_interrupt_demo(
        graph=graph,
        thread_id="thread-1",
        answer="The modules are separated by responsibility.",
    )

    assert resumed_result["answer"] == (
        "The modules are separated by responsibility."
    )
    assert resumed_result["status"] == "answer_received"
    assert resumed_result["current_node"] == "answer_interrupt"
    assert resumed_result["needs_human_input"] is False


def test_start_interrupt_demo_rejects_empty_topic(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_interrupt_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    with pytest.raises(ValueError):
        start_interrupt_demo(
            graph=graph,
            topic=" ",
            thread_id="thread-1",
        )


def test_resume_interrupt_demo_rejects_empty_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_interrupt_demo_graph(
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

    with pytest.raises(ValueError):
        resume_interrupt_demo(
            graph=graph,
            thread_id="thread-1",
            answer=" ",
        )


def test_get_interrupt_payload_returns_none_without_interrupt():
    assert get_interrupt_payload({"status": "answer_received"}) is None
