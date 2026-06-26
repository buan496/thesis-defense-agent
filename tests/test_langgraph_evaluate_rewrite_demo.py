import json

import pytest

from app.langgraph_workflow.evaluate_rewrite_demo import (
    build_evaluate_rewrite_demo_graph,
    evaluate_answer_node,
    resume_evaluate_rewrite_demo,
    rewrite_answer_node,
    run_evaluate_rewrite_demo,
    start_evaluate_rewrite_demo,
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


def test_evaluate_answer_node():
    output = evaluate_answer_node(
        {
            "question": "How is the system designed?",
            "answer": "It is modular.",
        },
        answer_evaluator=lambda question, answer: "Evaluation passed.",
    )

    assert output["evaluation"] == "Evaluation passed."
    assert output["status"] == "answer_evaluated"
    assert output["current_node"] == "evaluate_answer"


def test_evaluate_answer_node_requires_question():
    with pytest.raises(ValueError):
        evaluate_answer_node(
            {
                "answer": "It is modular.",
            },
            answer_evaluator=lambda question, answer: "Evaluation passed.",
        )


def test_evaluate_answer_node_requires_answer():
    with pytest.raises(ValueError):
        evaluate_answer_node(
            {
                "question": "How is the system designed?",
            },
            answer_evaluator=lambda question, answer: "Evaluation passed.",
        )


def test_rewrite_answer_node():
    output = rewrite_answer_node(
        {
            "question": "How is the system designed?",
            "answer": "It is modular.",
            "evaluation": "Needs details.",
        },
        answer_rewriter=lambda question, answer, evaluation: (
            "The system is organized into separate modules."
        ),
    )

    assert output["rewritten_answer"] == (
        "The system is organized into separate modules."
    )
    assert output["status"] == "answer_rewritten"
    assert output["current_node"] == "rewrite_answer"
    assert output["needs_human_input"] is False


def test_rewrite_answer_node_requires_question():
    with pytest.raises(ValueError):
        rewrite_answer_node(
            {
                "answer": "It is modular.",
            },
            answer_rewriter=lambda question, answer, evaluation: "Rewrite.",
        )


def test_rewrite_answer_node_requires_answer():
    with pytest.raises(ValueError):
        rewrite_answer_node(
            {
                "question": "How is the system designed?",
            },
            answer_rewriter=lambda question, answer, evaluation: "Rewrite.",
        )


def test_evaluate_rewrite_demo_pauses_and_resumes(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_evaluate_rewrite_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
        answer_evaluator=lambda question, answer: "Answer is too brief.",
        answer_rewriter=lambda question, answer, evaluation: (
            "The architecture separates modules by responsibility."
        ),
    )

    interrupted_result = start_evaluate_rewrite_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )
    interrupt_payload = get_interrupt_payload(interrupted_result)

    assert interrupt_payload["type"] == "answer_required"
    assert interrupted_result["question"] == (
        "How is the system architecture designed?"
    )

    resumed_result = resume_evaluate_rewrite_demo(
        graph=graph,
        thread_id="thread-1",
        answer="It is modular.",
    )

    assert resumed_result["answer"] == "It is modular."
    assert resumed_result["evaluation"] == "Answer is too brief."
    assert resumed_result["rewritten_answer"] == (
        "The architecture separates modules by responsibility."
    )
    assert resumed_result["status"] == "answer_rewritten"
    assert resumed_result["current_node"] == "rewrite_answer"


def test_run_evaluate_rewrite_demo_with_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_evaluate_rewrite_demo(
        topic="system architecture",
        thread_id="thread-1",
        answer="It is modular.",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
        answer_evaluator=lambda question, answer: "Answer is too brief.",
        answer_rewriter=lambda question, answer, evaluation: (
            "The architecture separates modules by responsibility."
        ),
    )

    assert report["thread_id"] == "thread-1"
    assert report["interrupt_payload"]["type"] == "answer_required"
    assert report["resumed_result"]["evaluation"] == "Answer is too brief."
    assert report["resumed_result"]["rewritten_answer"] == (
        "The architecture separates modules by responsibility."
    )


def test_run_evaluate_rewrite_demo_without_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_evaluate_rewrite_demo(
        topic="system architecture",
        thread_id="thread-1",
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    assert report["interrupt_payload"]["type"] == "answer_required"
    assert report["resumed_result"] is None


def test_start_evaluate_rewrite_demo_rejects_empty_topic(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_evaluate_rewrite_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )

    with pytest.raises(ValueError):
        start_evaluate_rewrite_demo(
            graph=graph,
            topic=" ",
            thread_id="thread-1",
        )


def test_resume_evaluate_rewrite_demo_rejects_empty_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_evaluate_rewrite_demo_graph(
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
        question_generator=lambda context: [
            "How is the system architecture designed?"
        ],
    )
    start_evaluate_rewrite_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )

    with pytest.raises(ValueError):
        resume_evaluate_rewrite_demo(
            graph=graph,
            thread_id="thread-1",
            answer=" ",
        )
