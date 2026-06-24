import json

import pytest

from app.langgraph_workflow.demo_task import (
    generate_question_node,
    retrieve_context_node,
    run_demo_task,
    wait_for_answer_node,
)


def fake_embedding(text: str) -> list[float]:
    if "architecture" in text.lower() or "system" in text.lower():
        return [1.0, 0.0]

    return [0.0, 1.0]


def test_retrieve_context_node(tmp_path):
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

    output = retrieve_context_node(
        {"topic": "system architecture"},
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
    )

    assert output["query"] == "system architecture"
    assert "question generation" in output["context"]
    assert output["sources"][0]["id"] == 0
    assert output["status"] == "context_retrieved"
    assert output["current_node"] == "retrieve_context"


def test_generate_question_node():
    output = generate_question_node(
        {"context": "context about system architecture"},
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert output["questions"] == [
        "How is the system architecture designed?"
    ]
    assert output["question"] == "How is the system architecture designed?"
    assert output["status"] == "question_generated"


def test_wait_for_answer_node():
    output = wait_for_answer_node(
        {
            "question": "How is the system architecture designed?",
        }
    )

    assert output["status"] == "waiting_for_answer"
    assert output["current_node"] == "wait_for_answer"
    assert output["needs_human_input"] is True


def test_run_demo_task_reaches_wait_for_answer(tmp_path):
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

    state = run_demo_task(
        topic="system architecture",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert state["topic"] == "system architecture"
    assert state["query"] == "system architecture"
    assert state["question"] == "How is the system architecture designed?"
    assert state["status"] == "waiting_for_answer"
    assert state["current_node"] == "wait_for_answer"
    assert state["needs_human_input"] is True


def test_run_demo_task_rejects_empty_topic():
    with pytest.raises(ValueError):
        run_demo_task(topic=" ")
