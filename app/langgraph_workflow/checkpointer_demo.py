from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.langgraph_workflow.interrupt_demo import (
    build_interrupt_demo_graph,
    build_thread_config,
    get_interrupt_payload,
    resume_interrupt_demo,
    start_interrupt_demo,
)


def build_checkpointer_demo_graph(
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
) -> tuple[Any, InMemorySaver]:
    checkpointer = InMemorySaver()
    graph = build_interrupt_demo_graph(
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
        checkpointer=checkpointer,
    )

    return graph, checkpointer


def inspect_checkpoint_state(
    graph,
    thread_id: str,
) -> dict[str, Any]:
    snapshot = graph.get_state(
        build_thread_config(thread_id),
    )
    config = snapshot.config.get("configurable", {})
    interrupts = [
        item.value
        for item in snapshot.interrupts
    ]

    return {
        "thread_id": thread_id,
        "checkpoint_id": config.get("checkpoint_id"),
        "next": list(snapshot.next),
        "values": dict(snapshot.values),
        "interrupts": interrupts,
        "has_pending_interrupt": len(interrupts) > 0,
    }


def run_checkpointer_demo(
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
) -> dict[str, Any]:
    graph, checkpointer = build_checkpointer_demo_graph(
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
    )
    interrupted_result = start_interrupt_demo(
        graph=graph,
        topic=topic,
        thread_id=thread_id,
    )
    interrupted_checkpoint = inspect_checkpoint_state(
        graph=graph,
        thread_id=thread_id,
    )
    report = {
        "thread_id": thread_id,
        "checkpointer_type": type(checkpointer).__name__,
        "interrupt_payload": get_interrupt_payload(interrupted_result),
        "interrupted_result": interrupted_result,
        "interrupted_checkpoint": interrupted_checkpoint,
        "resumed_result": None,
        "resumed_checkpoint": None,
    }

    if answer is not None:
        resumed_result = resume_interrupt_demo(
            graph=graph,
            thread_id=thread_id,
            answer=answer,
        )
        resumed_checkpoint = inspect_checkpoint_state(
            graph=graph,
            thread_id=thread_id,
        )
        report["resumed_result"] = resumed_result
        report["resumed_checkpoint"] = resumed_checkpoint

    return report
