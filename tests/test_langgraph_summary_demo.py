import json

import pytest

from app.langgraph_workflow.interrupt_demo import get_interrupt_payload
from app.langgraph_workflow.summary_demo import (
    build_summary_demo_graph,
    resume_summary_demo_with_answer,
    resume_summary_demo_with_follow_up_answer,
    run_summary_demo,
    start_summary_demo,
    summarize_training_node,
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


def fake_summary(
    question,
    answer,
    evaluation,
    rewritten_answer,
    follow_up_question,
    follow_up_answer,
    follow_up_evaluation,
):
    return "Training summary: improve architecture details."


def test_summarize_training_node():
    output = summarize_training_node(
        {
            "question": "How is the system designed?",
            "answer": "It is modular.",
            "evaluation": "Too brief.",
            "rewritten_answer": "The system separates modules.",
            "follow_up_question": "How are boundaries defined?",
            "follow_up_answer": "By responsibility.",
            "follow_up_evaluation": "Acceptable.",
        },
        training_summarizer=fake_summary,
    )

    assert output["summary"] == (
        "Training summary: improve architecture details."
    )
    assert output["weaknesses"] == []
    assert output["next_suggestions"] == []
    assert output["status"] == "training_summarized"
    assert output["current_node"] == "summarize_training"
    assert output["needs_human_input"] is False


def test_summarize_training_node_requires_full_round():
    with pytest.raises(ValueError) as error:
        summarize_training_node(
            {
                "question": "How is the system designed?",
            },
            training_summarizer=fake_summary,
        )

    assert "summarize_training node missing fields" in str(error.value)
    assert "answer" in str(error.value)


def test_summary_demo_two_interrupts_and_summary(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)
    graph = build_summary_demo_graph(
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
        training_summarizer=fake_summary,
    )

    first_result = start_summary_demo(
        graph=graph,
        topic="system architecture",
        thread_id="thread-1",
    )
    first_interrupt = get_interrupt_payload(first_result)

    assert first_interrupt["type"] == "answer_required"

    answer_result = resume_summary_demo_with_answer(
        graph=graph,
        thread_id="thread-1",
        answer="It is modular.",
    )
    follow_up_interrupt = get_interrupt_payload(answer_result)

    assert follow_up_interrupt["type"] == "follow_up_answer_required"

    final_result = resume_summary_demo_with_follow_up_answer(
        graph=graph,
        thread_id="thread-1",
        follow_up_answer="By responsibility.",
    )

    assert final_result["follow_up_evaluation"] == (
        "Follow-up answer is acceptable."
    )
    assert final_result["summary"] == (
        "Training summary: improve architecture details."
    )
    assert final_result["status"] == "training_summarized"
    assert final_result["current_node"] == "summarize_training"


def test_run_summary_demo_with_both_answers(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_summary_demo(
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
        training_summarizer=fake_summary,
    )

    assert report["answer_interrupt_payload"]["type"] == "answer_required"
    assert report["follow_up_interrupt_payload"]["type"] == (
        "follow_up_answer_required"
    )
    assert report["final_result"]["summary"] == (
        "Training summary: improve architecture details."
    )


def test_run_summary_demo_with_only_first_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    report = run_summary_demo(
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


def test_run_summary_demo_rejects_follow_up_without_answer(tmp_path):
    vector_store_path = build_test_vector_store(tmp_path)

    with pytest.raises(ValueError):
        run_summary_demo(
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
