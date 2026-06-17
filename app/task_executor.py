import time
from collections.abc import Callable

from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.rag import build_context_from_results
from app.task_models import TaskStep
from app.vector_store import search_vector_store
from app.vector_store_io import load_vector_store
from app.config import (
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
)


def execute_task_step(
    step: TaskStep,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    question_generator: Callable[
        [str],
        list[str] | dict,
    ] = generate_questions_from_context_with_audit,
) -> TaskStep:
    if step.step_type == "retrieve_context":
        return execute_retrieve_context_step(
            step=step,
            vector_store_path=vector_store_path,
            top_k=top_k,
            embedding_fn=embedding_fn,
        )

    if step.step_type == "generate_question":
        return execute_generate_question_step(
            step=step,
            question_generator=question_generator,
        )

    raise ValueError(
        f"不支持的任务步骤类型：{step.step_type}"
    )


def execute_retrieve_context_step(
    step: TaskStep,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
) -> TaskStep:
    query = step.input.get("query") or step.input.get("topic")

    if not query:
        raise ValueError(
            "retrieve_context 步骤需要 input.query 或 input.topic"
        )

    step.mark_running()

    start_time = time.perf_counter()
    store = load_vector_store(vector_store_path)

    results = search_vector_store(
        query=query,
        store=store,
        top_k=top_k,
        embedding_fn=embedding_fn,
    )

    context = build_context_from_results(results)
    duration_ms = (time.perf_counter() - start_time) * 1000

    sources = [
        {
            "id": result.get("id"),
            "source": result.get("source"),
            "score": result.get("score"),
        }
        for result in results
    ]

    step.evidence = results
    step.tool_traces.append(
        {
            "tool_name": "search_vector_store",
            "arguments": {
                "query": query,
                "top_k": top_k,
                "vector_store_path": vector_store_path,
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    step.mark_completed(
        output={
            "query": query,
            "context": context,
            "sources": sources,
        }
    )

    return step


def execute_generate_question_step(
    step: TaskStep,
    question_generator: Callable[
        [str],
        list[str] | dict,
    ] = generate_questions_from_context_with_audit,
) -> TaskStep:
    context = step.input.get("context")

    if not context:
        raise ValueError(
            "generate_question 步骤需要 input.context"
        )

    step.mark_running()

    start_time = time.perf_counter()
    generation_result = question_generator(context)
    duration_ms = (time.perf_counter() - start_time) * 1000

    if isinstance(generation_result, dict):
        questions = generation_result.get("questions", [])
        step.token_usage = generation_result.get("token_usage", {})
        step.cost_estimate = generation_result.get("cost_estimate", {})
    else:
        questions = generation_result

    if not questions:
        raise ValueError("生成的问题列表不能为空")

    step.tool_traces.append(
        {
            "tool_name": "generate_questions_from_context",
            "arguments": {
                "context_length": len(context),
                "topic": step.input.get("topic"),
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    step.mark_completed(
        output={
            "question": questions[0],
            "questions": questions,
            "topic": step.input.get("topic"),
        }
    )

    return step
