from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.rag import build_context_from_results
from app.vector_store import search_vector_store
from app.vector_store_io import load_vector_store


class LangGraphDefenseState(TypedDict, total=False):
    topic: str
    query: str
    context: str
    sources: list[dict[str, Any]]
    questions: list[str]
    question: str
    status: str
    current_node: str
    needs_human_input: bool


def retrieve_context_node(
    state: LangGraphDefenseState,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
) -> dict[str, Any]:
    query = state.get("query") or state.get("topic")

    if not query:
        raise ValueError("retrieve_context node requires state.topic or state.query")

    store = load_vector_store(vector_store_path)
    results = search_vector_store(
        query,
        store,
        top_k=top_k,
        embedding_fn=embedding_fn,
    )
    context = build_context_from_results(results)
    sources = [
        {
            "id": result.get("id"),
            "source": result.get("source"),
            "score": result.get("score"),
        }
        for result in results
    ]

    return {
        "query": query,
        "context": context,
        "sources": sources,
        "status": "context_retrieved",
        "current_node": "retrieve_context",
    }


def generate_question_node(
    state: LangGraphDefenseState,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
) -> dict[str, Any]:
    context = state.get("context")

    if not context:
        raise ValueError("generate_question node requires state.context")

    generation_result = question_generator(context)

    if isinstance(generation_result, dict):
        questions = generation_result.get("questions", [])
    else:
        questions = generation_result

    if not questions:
        raise ValueError("generate_question node produced no questions")

    return {
        "questions": questions,
        "question": questions[0],
        "status": "question_generated",
        "current_node": "generate_question",
    }


def wait_for_answer_node(
    state: LangGraphDefenseState,
) -> dict[str, Any]:
    if not state.get("question"):
        raise ValueError("wait_for_answer node requires state.question")

    return {
        "status": "waiting_for_answer",
        "current_node": "wait_for_answer",
        "needs_human_input": True,
    }


def build_demo_task_graph(
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
):
    graph = StateGraph(LangGraphDefenseState)

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
    graph.add_node("wait_for_answer", wait_for_answer_node)

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_question")
    graph.add_edge("generate_question", "wait_for_answer")
    graph.add_edge("wait_for_answer", END)

    return graph.compile()


def run_demo_task(
    topic: str,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict[str, Any],
    ] = generate_questions_from_context_with_audit,
) -> LangGraphDefenseState:
    if not topic.strip():
        raise ValueError("topic cannot be empty")

    graph = build_demo_task_graph(
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
    )

    return graph.invoke(
        {
            "topic": topic,
        }
    )
