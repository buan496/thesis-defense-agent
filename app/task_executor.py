import time
from collections.abc import Callable

from app.answer_rewrite import rewrite_answer
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.evaluation import evaluate_answer
from app.follow_up import generate_follow_up_question
from app.rag import build_context_from_results
from app.task_models import TaskStep
from app.training_summary import summarize_training
from app.vector_store_repository import (
    VectorStoreRepository,
    create_vector_store_repository,
)
from app.config import (
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
    VECTOR_STORE_BACKEND,
)


CORRELATION_ID_FIELD = "correlation_id"


def get_step_correlation_id(step: TaskStep) -> str | None:
    input_correlation_id = step.input.get(CORRELATION_ID_FIELD)

    if isinstance(input_correlation_id, str) and input_correlation_id:
        return input_correlation_id

    output_correlation_id = step.output.get(CORRELATION_ID_FIELD)

    if isinstance(output_correlation_id, str) and output_correlation_id:
        return output_correlation_id

    return None


def with_step_correlation_id(
    step: TaskStep,
    data: dict,
) -> dict:
    copied_data = dict(data)
    correlation_id = get_step_correlation_id(step)

    if correlation_id:
        copied_data.setdefault(CORRELATION_ID_FIELD, correlation_id)

    return copied_data


def append_tool_trace(
    step: TaskStep,
    trace: dict,
) -> None:
    step.tool_traces.append(
        with_step_correlation_id(
            step=step,
            data=trace,
        )
    )


def mark_step_completed_with_correlation_id(
    step: TaskStep,
    output: dict,
) -> None:
    step.mark_completed(
        output=with_step_correlation_id(
            step=step,
            data=output,
        )
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
    answer_evaluator: Callable[[str, str], str] = evaluate_answer,
    answer_rewriter: Callable[
        [str, str, str | None],
        str,
    ] = rewrite_answer,
    follow_up_generator: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
    follow_up_evaluator: Callable[[str, str], str] = evaluate_answer,
    training_summarizer: Callable[
        [str, str, str, str, str, str, str],
        str,
    ] = summarize_training,
    vector_store_repository: VectorStoreRepository | None = None,
) -> TaskStep:
    if step.step_type == "retrieve_context":
        return execute_retrieve_context_step(
            step=step,
            vector_store_path=vector_store_path,
            top_k=top_k,
            embedding_fn=embedding_fn,
            vector_store_repository=vector_store_repository,
        )

    if step.step_type == "generate_question":
        return execute_generate_question_step(
            step=step,
            question_generator=question_generator,
        )

    if step.step_type == "evaluate_answer":
        return execute_evaluate_answer_step(
            step=step,
            answer_evaluator=answer_evaluator,
        )

    if step.step_type == "rewrite_answer":
        return execute_rewrite_answer_step(
            step=step,
            answer_rewriter=answer_rewriter,
        )

    if step.step_type == "generate_follow_up":
        return execute_generate_follow_up_step(
            step=step,
            follow_up_generator=follow_up_generator,
        )

    if step.step_type == "evaluate_follow_up_answer":
        return execute_evaluate_follow_up_answer_step(
            step=step,
            follow_up_evaluator=follow_up_evaluator,
        )

    if step.step_type == "summarize_training":
        return execute_summarize_training_step(
            step=step,
            training_summarizer=training_summarizer,
        )

    raise ValueError(
        f"不支持的任务步骤类型：{step.step_type}"
    )


def execute_retrieve_context_step(
    step: TaskStep,
    vector_store_path: str = RAG_VECTOR_STORE_PATH,
    top_k: int = RAG_TOP_K,
    embedding_fn: Callable[[str], list[float]] = create_embedding,
    vector_store_repository: VectorStoreRepository | None = None,
) -> TaskStep:
    query = step.input.get("query") or step.input.get("topic")

    if not query:
        raise ValueError(
            "retrieve_context 步骤需要 input.query 或 input.topic"
        )

    step.mark_running()

    start_time = time.perf_counter()
    repository = vector_store_repository or create_vector_store_repository(
        backend=VECTOR_STORE_BACKEND,
        vector_store_path=vector_store_path,
    )
    results = repository.search(
        query=query,
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
    append_tool_trace(
        step,
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
    mark_step_completed_with_correlation_id(
        step,
        output={
            "query": query,
            "context": context,
            "sources": sources,
        }
    )

    return step


def execute_evaluate_answer_step(
    step: TaskStep,
    answer_evaluator: Callable[[str, str], str] = evaluate_answer,
) -> TaskStep:
    question = step.input.get("question")
    answer = step.input.get("answer")

    if not question:
        raise ValueError(
            "evaluate_answer 步骤需要 input.question"
        )

    if not answer:
        raise ValueError(
            "evaluate_answer 步骤需要 input.answer"
        )

    step.mark_running()

    start_time = time.perf_counter()
    evaluation = answer_evaluator(question, answer)
    duration_ms = (time.perf_counter() - start_time) * 1000

    append_tool_trace(
        step,
        {
            "tool_name": "evaluate_answer",
            "arguments": {
                "question_length": len(question),
                "answer_length": len(answer),
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    mark_step_completed_with_correlation_id(
        step,
        output={
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
        }
    )

    return step


def execute_rewrite_answer_step(
    step: TaskStep,
    answer_rewriter: Callable[
        [str, str, str | None],
        str,
    ] = rewrite_answer,
) -> TaskStep:
    question = step.input.get("question")
    answer = step.input.get("answer")
    evaluation = step.input.get("evaluation")

    if not question:
        raise ValueError(
            "rewrite_answer 步骤需要 input.question"
        )

    if not answer:
        raise ValueError(
            "rewrite_answer 步骤需要 input.answer"
        )

    step.mark_running()

    start_time = time.perf_counter()
    rewritten_answer = answer_rewriter(
        question,
        answer,
        evaluation,
    )
    duration_ms = (time.perf_counter() - start_time) * 1000

    append_tool_trace(
        step,
        {
            "tool_name": "rewrite_answer",
            "arguments": {
                "question_length": len(question),
                "answer_length": len(answer),
                "evaluation_length": len(evaluation or ""),
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    mark_step_completed_with_correlation_id(
        step,
        output={
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "rewritten_answer": rewritten_answer,
        }
    )

    return step


def execute_generate_follow_up_step(
    step: TaskStep,
    follow_up_generator: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
) -> TaskStep:
    question = step.input.get("question")
    answer = step.input.get("answer")
    evaluation = step.input.get("evaluation")
    rewritten_answer = step.input.get("rewritten_answer")

    if not question:
        raise ValueError(
            "generate_follow_up 步骤需要 input.question"
        )

    if not answer:
        raise ValueError(
            "generate_follow_up 步骤需要 input.answer"
        )

    step.mark_running()

    start_time = time.perf_counter()
    follow_up_question = follow_up_generator(
        question,
        answer,
        evaluation,
        rewritten_answer,
    )
    duration_ms = (time.perf_counter() - start_time) * 1000

    append_tool_trace(
        step,
        {
            "tool_name": "generate_follow_up_question",
            "arguments": {
                "question_length": len(question),
                "answer_length": len(answer),
                "evaluation_length": len(evaluation or ""),
                "rewritten_answer_length": len(rewritten_answer or ""),
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    mark_step_completed_with_correlation_id(
        step,
        output={
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "rewritten_answer": rewritten_answer,
            "follow_up_question": follow_up_question,
        }
    )

    return step


def execute_evaluate_follow_up_answer_step(
    step: TaskStep,
    follow_up_evaluator: Callable[[str, str], str] = evaluate_answer,
) -> TaskStep:
    follow_up_question = step.input.get("follow_up_question")
    follow_up_answer = step.input.get("follow_up_answer")

    if not follow_up_question:
        raise ValueError(
            "evaluate_follow_up_answer 步骤需要 input.follow_up_question"
        )

    if not follow_up_answer:
        raise ValueError(
            "evaluate_follow_up_answer 步骤需要 input.follow_up_answer"
        )

    step.mark_running()

    start_time = time.perf_counter()
    follow_up_evaluation = follow_up_evaluator(
        follow_up_question,
        follow_up_answer,
    )
    duration_ms = (time.perf_counter() - start_time) * 1000

    append_tool_trace(
        step,
        {
            "tool_name": "evaluate_follow_up_answer",
            "arguments": {
                "follow_up_question_length": len(follow_up_question),
                "follow_up_answer_length": len(follow_up_answer),
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    mark_step_completed_with_correlation_id(
        step,
        output={
            "question": step.input.get("question"),
            "answer": step.input.get("answer"),
            "evaluation": step.input.get("evaluation"),
            "rewritten_answer": step.input.get("rewritten_answer"),
            "follow_up_question": follow_up_question,
            "follow_up_answer": follow_up_answer,
            "follow_up_evaluation": follow_up_evaluation,
        }
    )

    return step


def execute_summarize_training_step(
    step: TaskStep,
    training_summarizer: Callable[
        [str, str, str, str, str, str, str],
        str,
    ] = summarize_training,
) -> TaskStep:
    required_fields = [
        "question",
        "answer",
        "evaluation",
        "rewritten_answer",
        "follow_up_question",
        "follow_up_answer",
        "follow_up_evaluation",
    ]
    missing_fields = [
        field
        for field in required_fields
        if not step.input.get(field)
    ]

    if missing_fields:
        raise ValueError(
            "summarize_training 步骤缺少输入字段："
            + ", ".join(missing_fields)
        )

    question = step.input["question"]
    answer = step.input["answer"]
    evaluation = step.input["evaluation"]
    rewritten_answer = step.input["rewritten_answer"]
    follow_up_question = step.input["follow_up_question"]
    follow_up_answer = step.input["follow_up_answer"]
    follow_up_evaluation = step.input["follow_up_evaluation"]

    step.mark_running()

    start_time = time.perf_counter()
    summary = training_summarizer(
        question,
        answer,
        evaluation,
        rewritten_answer,
        follow_up_question,
        follow_up_answer,
        follow_up_evaluation,
    )
    duration_ms = (time.perf_counter() - start_time) * 1000

    append_tool_trace(
        step,
        {
            "tool_name": "summarize_training",
            "arguments": {
                "question_length": len(question),
                "answer_length": len(answer),
                "evaluation_length": len(evaluation),
                "rewritten_answer_length": len(rewritten_answer),
                "follow_up_question_length": len(follow_up_question),
                "follow_up_answer_length": len(follow_up_answer),
                "follow_up_evaluation_length": len(follow_up_evaluation),
            },
            "success": True,
            "duration_ms": duration_ms,
        }
    )
    mark_step_completed_with_correlation_id(
        step,
        output={
            "question": question,
            "answer": answer,
            "evaluation": evaluation,
            "rewritten_answer": rewritten_answer,
            "follow_up_question": follow_up_question,
            "follow_up_answer": follow_up_answer,
            "follow_up_evaluation": follow_up_evaluation,
            "summary": summary,
            "weaknesses": [],
            "next_suggestions": [],
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

    append_tool_trace(
        step,
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
    mark_step_completed_with_correlation_id(
        step,
        output={
            "question": questions[0],
            "questions": questions,
            "topic": step.input.get("topic"),
        }
    )

    return step
