from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from app.answer_rewrite import rewrite_answer
from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.evaluation import evaluate_answer
from app.langgraph_workflow.interrupt_demo import (
    LangGraphInterruptState,
    answer_interrupt_node,
    build_thread_config,
    get_interrupt_payload,
)
from app.langgraph_workflow.demo_task import (
    generate_question_node,
    retrieve_context_node,
)
from langgraph.types import Command


class LangGraphEvaluateRewriteState(
    LangGraphInterruptState,
    total=False,
):
    evaluation: str
    rewritten_answer: str


def evaluate_answer_node(
    state: LangGraphEvaluateRewriteState,
    answer_evaluator: Callable[[str, str], str] = evaluate_answer,
) -> dict[str, Any]:
    question = state.get("question")
    answer = state.get("answer")

    if not question:
        raise ValueError("evaluate_answer node requires state.question")

    if not answer:
        raise ValueError("evaluate_answer node requires state.answer")

    evaluation = answer_evaluator(question, answer)

    return {
        "evaluation": evaluation,
        "status": "answer_evaluated",
        "current_node": "evaluate_answer",
    }


def rewrite_answer_node(
    state: LangGraphEvaluateRewriteState,
    answer_rewriter: Callable[
        [str, str, str | None],
        str,
    ] = rewrite_answer,
) -> dict[str, Any]:
    question = state.get("question")
    answer = state.get("answer")
    evaluation = state.get("evaluation")

    if not question:
        raise ValueError("rewrite_answer node requires state.question")

    if not answer:
        raise ValueError("rewrite_answer node requires state.answer")

    rewritten_answer = answer_rewriter(
        question,
        answer,
        evaluation,
    )

    return {
        "rewritten_answer": rewritten_answer,
        "status": "answer_rewritten",
        "current_node": "rewrite_answer",
        "needs_human_input": False,
    }


def build_evaluate_rewrite_demo_graph(
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
    answer_evaluator: Callable[[str, str], str] = evaluate_answer,
    answer_rewriter: Callable[
        [str, str, str | None],
        str,
    ] = rewrite_answer,
    checkpointer: InMemorySaver | None = None,
):
    graph = StateGraph(LangGraphEvaluateRewriteState)

    graph.add_node(
        "retrieve_context",
        lambda state: retrieve_context_node(
            state=state,
            vector_store_path=vector_store_path,
            top_k=top_k,
            embedding_fn=embedding_fn,
        ),
    )
    graph.add_node(
        "generate_question",
        lambda state: generate_question_node(
            state=state,
            question_generator=question_generator,
        ),
    )
    graph.add_node("answer_interrupt", answer_interrupt_node)
    graph.add_node(
        "evaluate_answer",
        lambda state: evaluate_answer_node(
            state=state,
            answer_evaluator=answer_evaluator,
        ),
    )
    graph.add_node(
        "rewrite_answer",
        lambda state: rewrite_answer_node(
            state=state,
            answer_rewriter=answer_rewriter,
        ),
    )

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_question")
    graph.add_edge("generate_question", "answer_interrupt")
    graph.add_edge("answer_interrupt", "evaluate_answer")
    graph.add_edge("evaluate_answer", "rewrite_answer")
    graph.add_edge("rewrite_answer", END)

    return graph.compile(
        checkpointer=checkpointer or InMemorySaver(),
    )


def start_evaluate_rewrite_demo(
    graph,
    topic: str,
    thread_id: str,
) -> dict[str, Any]:
    if not topic.strip():
        raise ValueError("topic cannot be empty")

    return graph.invoke(
        {
            "topic": topic,
        },
        config=build_thread_config(thread_id),
    )


def resume_evaluate_rewrite_demo(
    graph,
    thread_id: str,
    answer: str,
) -> dict[str, Any]:
    if not answer.strip():
        raise ValueError("answer cannot be empty")

    return graph.invoke(
        Command(resume=answer),
        config=build_thread_config(thread_id),
    )


def run_evaluate_rewrite_demo(
    topic: str,
    thread_id: str,
    answer: str | None = None,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
    answer_evaluator: Callable[[str, str], str] = evaluate_answer,
    answer_rewriter: Callable[
        [str, str, str | None],
        str,
    ] = rewrite_answer,
) -> dict[str, Any]:
    graph = build_evaluate_rewrite_demo_graph(
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
        answer_evaluator=answer_evaluator,
        answer_rewriter=answer_rewriter,
    )
    interrupted_result = start_evaluate_rewrite_demo(
        graph=graph,
        topic=topic,
        thread_id=thread_id,
    )
    interrupt_payload = get_interrupt_payload(interrupted_result)
    resumed_result = None

    if answer is not None:
        resumed_result = resume_evaluate_rewrite_demo(
            graph=graph,
            thread_id=thread_id,
            answer=answer,
        )

    return {
        "thread_id": thread_id,
        "interrupted_result": interrupted_result,
        "interrupt_payload": interrupt_payload,
        "resumed_result": resumed_result,
    }
