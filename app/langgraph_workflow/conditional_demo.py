from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.langgraph_workflow.demo_task import (
    generate_question_node,
    retrieve_context_node,
)
from app.langgraph_workflow.interrupt_demo import (
    LangGraphInterruptState,
    answer_interrupt_node,
    build_thread_config,
    get_interrupt_payload,
    resume_interrupt_demo,
)


def route_by_answer(state: LangGraphInterruptState) -> str:
    answer = state.get("answer")

    if isinstance(answer, str) and answer.strip():
        return "finalize"

    return "answer_interrupt"


def finalize_answer_node(
    state: LangGraphInterruptState,
) -> dict[str, Any]:
    answer = state.get("answer")

    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("finalize node requires state.answer")

    return {
        "status": "completed",
        "current_node": "finalize",
        "needs_human_input": False,
    }


def build_conditional_demo_graph(
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
    graph.add_node("finalize", finalize_answer_node)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_question")
    graph.add_conditional_edges(
        "generate_question",
        route_by_answer,
        {
            "answer_interrupt": "answer_interrupt",
            "finalize": "finalize",
        },
    )
    graph.add_edge("answer_interrupt", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(
        checkpointer=checkpointer or InMemorySaver(),
    )


def start_conditional_demo(
    graph,
    topic: str,
    thread_id: str,
    answer: str | None = None,
) -> dict[str, Any]:
    if not topic.strip():
        raise ValueError("topic cannot be empty")

    initial_state: dict[str, Any] = {
        "topic": topic,
    }

    if answer is not None:
        if not answer.strip():
            raise ValueError("answer cannot be empty")

        initial_state["answer"] = answer

    return graph.invoke(
        initial_state,
        config=build_thread_config(thread_id),
    )


def run_conditional_demo(
    topic: str,
    thread_id: str,
    answer: str | None = None,
    resume_answer: str | None = None,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
) -> dict[str, Any]:
    graph = build_conditional_demo_graph(
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
    )
    first_result = start_conditional_demo(
        graph=graph,
        topic=topic,
        thread_id=thread_id,
        answer=answer,
    )
    interrupt_payload = get_interrupt_payload(first_result)
    resumed_result = None

    if resume_answer is not None:
        resumed_result = resume_interrupt_demo(
            graph=graph,
            thread_id=thread_id,
            answer=resume_answer,
        )

    return {
        "thread_id": thread_id,
        "first_result": first_result,
        "interrupt_payload": interrupt_payload,
        "resumed_result": resumed_result,
        "route": "answer_interrupt" if interrupt_payload else "finalize",
    }
