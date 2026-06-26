import json

import pytest

from app.langgraph_workflow.follow_up_demo import (
    build_follow_up_demo_graph,
    evaluate_follow_up_answer_node,
    follow_up_interrupt_node,
    generate_follow_up_node,
    resume_follow_up_demo_with_answer,
    resume_follow_up_demo_with_follow_up_answer,
    run_follow_up_demo,
    start_follow_up_demo,
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


def test_generate_follow_up_node():
    output = generate_follow_up_node(
        {
            "question": "How is the system designed?",
            "answer": "It is modular.",
            "evaluation": "Too brief.",
            "rewritten_answer": "The system separates modules.",
        },
        follow_up_generator=lambda question, answer, evaluation, rewritten: (
            "How are module boundaries defined?"
        ),
    )

    assert output["follow_up_question"] == (
        "How are module boundaries defined?"
    )
    assert output["status"] == "follow_up_generated"
    assert output["current_node"] == "generate_follow_up"


def test_generate_follow_up_node_requires_question():
    with pytest.raises(ValueError):
        generate_follow_up_node(
            {"answer": "It is modular."},
            follow_up_generator=lambda question, answer, evaluation, rewritten: (
                "Follow up?"
            ),
        )


def test_generate_follow_up_node_requires_answer():
    with pytest.raises(ValueError):
        generate_follow_up_node(
            {"question": "How is it designed?"},
            follow_up_generator=lambda question, answer, evaluation, rewritten: (
                "Follow up?"
            ),
        )


def test_follow_up_interrupt_node_requires_follow_up_question():
    with pytest.raises(ValueError):
        follow_up_interrupt_node({})


def test_evaluate_follow_up_answer_node():
    output = evaluate_follow_up_answer_node(
        {
            "follow_up_question": "How are module boundaries defined?",
            "follow_up_answer": "By responsibility.",
        },
        follow_up_evaluator=lambda question, answer: "Follow-up passed.",
    )

    assert output["follow_up_evaluation"] == "Follow-up passed."
    assert output["status"] == "follow_up_answer_evaluated"
    assert output["current_node"] == "evaluate_follow_up_answer"


def test_evaluate_follow_up_answer_node_requires_question():
    with pytest.raises(ValueError):
        evaluate_follow_up_answer_node(
            {"follow_up_answer": "By responsibility."},
            follow_up_evaluator=lambda question, answer: "Evaluation.",
        )


def test_evaluate_follow_up_answer_node_requires_answer():
    with pytest.raises(ValueError):
        evaluate_follow_up_answer_node(
            {"follow_up_question": "How are module boundaries defined?"},
            follow_up_evaluator=lambda question, answer: "Evaluation.",
        )


def test_follow_up_demo_two_interrupts_and_final_result(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_follow_up_demo_graph(
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
        follow_up_generator=lambda question, answer, evaluation, rewritten: (
            "How are module boundaries defined?"
        ),
        follow_up_evaluator=lambda question, answer: (
            "Follow-up answer is acceptable."
        ),
    )

    first_result = start_follow_up_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )
    first_interrupt = get_interrupt_payload(first_result)

    assert first_interrupt["type"] == "answer_required"

    answer_result = resume_follow_up_demo_with_answer(
        graph=graph,
        thread_id="thread-1",
        answer="It is modular.",
    )
    follow_up_interrupt = get_interrupt_payload(answer_result)

    assert answer_result["evaluation"] == "Answer is too brief."
    assert answer_result["rewritten_answer"] == (
        "The architecture separates modules by responsibility."
    )
    assert answer_result["follow_up_question"] == (
        "How are module boundaries defined?"
    )
    assert follow_up_interrupt["type"] == "follow_up_answer_required"

    final_result = resume_follow_up_demo_with_follow_up_answer(
        graph=graph,
        thread_id="thread-1",
        follow_up_answer="By responsibility.",
    )

    assert final_result["follow_up_answer"] == "By responsibility."
    assert final_result["follow_up_evaluation"] == (
        "Follow-up answer is acceptable."
    )
    assert final_result["status"] == "follow_up_answer_evaluated"
    assert final_result["current_node"] == "evaluate_follow_up_answer"


def test_run_follow_up_demo_with_both_answers(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_follow_up_demo(
        topic="system architecture",
        thread_id="thread-1",
        answer="It is modular.",
        follow_up_answer="By responsibility.",
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
        follow_up_generator=lambda question, answer, evaluation, rewritten: (
            "How are module boundaries defined?"
        ),
        follow_up_evaluator=lambda question, answer: (
            "Follow-up answer is acceptable."
        ),
    )

    assert report["answer_interrupt_payload"]["type"] == "answer_required"
    assert report["follow_up_interrupt_payload"]["type"] == (
        "follow_up_answer_required"
    )
    assert report["final_result"]["follow_up_evaluation"] == (
        "Follow-up answer is acceptable."
    )


def test_run_follow_up_demo_with_only_first_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_follow_up_demo(
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
        follow_up_generator=lambda question, answer, evaluation, rewritten: (
            "How are module boundaries defined?"
        ),
    )

    assert report["answer_result"]["follow_up_question"] == (
        "How are module boundaries defined?"
    )
    assert report["follow_up_interrupt_payload"]["type"] == (
        "follow_up_answer_required"
    )
    assert report["final_result"] is None


def test_run_follow_up_demo_rejects_follow_up_without_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    with pytest.raises(ValueError):
        run_follow_up_demo(
            topic="system architecture",
            thread_id="thread-1",
            follow_up_answer="By responsibility.",
            vector_store_path=str(vector_store_path),
            top_k=1,
            embedding_fn=fake_embedding,
            question_generator=lambda context: [
                "How is the system architecture designed?"
            ],
        )
