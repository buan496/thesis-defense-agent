import json

import pytest

from app.langgraph_workflow.conditional_demo import (
    build_conditional_demo_graph,
    finalize_answer_node,
    route_by_answer,
    run_conditional_demo,
    start_conditional_demo,
)
from app.langgraph_workflow.interrupt_demo import get_interrupt_payload


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


def test_route_by_answer():
    assert route_by_answer({"answer": "The system is modular."}) == "finalize"
    assert route_by_answer({"answer": " "}) == "answer_interrupt"
    assert route_by_answer({}) == "answer_interrupt"


def test_finalize_answer_node_requires_answer():
    with pytest.raises(ValueError):
        finalize_answer_node({})


def test_finalize_answer_node():
    output = finalize_answer_node(
        {
            "answer": "The system is modular.",
        }
    )

    assert output == {
        "status": "completed",
        "current_node": "finalize",
        "needs_human_input": False,
    }


def test_conditional_demo_skips_interrupt_when_answer_exists(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_conditional_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    result = start_conditional_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
        answer="The system is modular.",
    )

    assert get_interrupt_payload(result) is None
    assert result["answer"] == "The system is modular."
    assert result["status"] == "completed"
    assert result["current_node"] == "finalize"
    assert result["needs_human_input"] is False


def test_conditional_demo_interrupts_without_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_conditional_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    result = start_conditional_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )
    interrupt_payload = get_interrupt_payload(result)

    assert interrupt_payload["type"] == "answer_required"
    assert interrupt_payload["question"] == (
        "How is the system architecture designed?"
    )
    assert "answer" not in result


def test_run_conditional_demo_with_existing_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_conditional_demo(
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

    assert report["route"] == "finalize"
    assert report["interrupt_payload"] is None
    assert report["first_result"]["status"] == "completed"
    assert report["resumed_result"] is None


def test_run_conditional_demo_with_resume_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_conditional_demo(
        topic="system architecture",
        thread_id="thread-1",
        resume_answer="The system is modular.",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert report["route"] == "answer_interrupt"
    assert report["interrupt_payload"]["type"] == "answer_required"
    assert report["resumed_result"]["answer"] == "The system is modular."
    assert report["resumed_result"]["status"] == "completed"
    assert report["resumed_result"]["current_node"] == "finalize"


def test_start_conditional_demo_rejects_empty_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_conditional_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    with pytest.raises(ValueError):
        start_conditional_demo(
            graph=graph,
            topic="system architecture",
            thread_id="thread-1",
            answer=" ",
        )
