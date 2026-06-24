from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.langgraph_workflow.demo_task import (
    generate_question_node,
    retrieve_context_node,
)


class LangGraphInterruptState(TypedDict, total=False):
    topic: str
    query: str
    context: str
    sources: list[dict[str, Any]]
    questions: list[str]
    question: str
    answer: str
    status: str
    current_node: str
    needs_human_input: bool


def answer_interrupt_node(
    state: LangGraphInterruptState,
) -> dict[str, Any]:
    question = state.get("question")

    if not question:
        raise ValueError("answer_interrupt node requires state.question")

    answer = interrupt(
        {
            "type": "answer_required",
            "question": question,
            "message": "Please provide the student's answer to resume.",
        }
    )

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("resumed answer cannot be empty")

    return {
        "answer": answer,
        "status": "answer_received",
        "current_node": "answer_interrupt",
        "needs_human_input": False,
    }


def build_interrupt_demo_graph(
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
    checkpointer: InMemorySaver | None = None,
):
    graph = StateGraph(LangGraphInterruptState)

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

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_question")
    graph.add_edge("generate_question", "answer_interrupt")
    graph.add_edge("answer_interrupt", END)

    return graph.compile(
        checkpointer=checkpointer or InMemorySaver(),
    )


def build_thread_config(thread_id: str) -> dict[str, Any]:
    if not thread_id.strip():
        raise ValueError("thread_id cannot be empty")

    return {
        "configurable": {
            "thread_id": thread_id,
        }
    }


def start_interrupt_demo(
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


def resume_interrupt_demo(
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


def get_interrupt_payload(result: dict[str, Any]) -> dict[str, Any] | None:
    interrupts = result.get("__interrupt__", [])

    if not interrupts:
        return None

    return interrupts[0].value
