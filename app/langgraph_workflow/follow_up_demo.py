from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import Command, interrupt

from app.answer_rewrite import rewrite_answer
from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.defense_questions import generate_questions_from_context_with_audit
from app.embeddings import create_embedding
from app.evaluation import evaluate_answer
from app.follow_up import generate_follow_up_question
from app.langgraph_workflow.demo_task import (
    generate_question_node,
    retrieve_context_node,
)
from app.langgraph_workflow.evaluate_rewrite_demo import (
    LangGraphEvaluateRewriteState,
    evaluate_answer_node,
    rewrite_answer_node,
)
from app.langgraph_workflow.interrupt_demo import (
    answer_interrupt_node,
    build_thread_config,
    get_interrupt_payload,
)


class LangGraphFollowUpState(
    LangGraphEvaluateRewriteState,
    total=False,
):
    follow_up_question: str
    follow_up_answer: str
    follow_up_evaluation: str


def generate_follow_up_node(
    state: LangGraphFollowUpState,
    follow_up_generator: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
) -> dict[str, Any]:
    question = state.get("question")
    answer = state.get("answer")
    evaluation = state.get("evaluation")
    rewritten_answer = state.get("rewritten_answer")

    if not question:
        raise ValueError("generate_follow_up node requires state.question")

    if not answer:
        raise ValueError("generate_follow_up node requires state.answer")

    follow_up_question = follow_up_generator(
        question,
        answer,
        evaluation,
        rewritten_answer,
    )

    return {
        "follow_up_question": follow_up_question,
        "status": "follow_up_generated",
        "current_node": "generate_follow_up",
    }


def follow_up_interrupt_node(
    state: LangGraphFollowUpState,
) -> dict[str, Any]:
    follow_up_question = state.get("follow_up_question")

    if not follow_up_question:
        raise ValueError(
            "follow_up_interrupt node requires state.follow_up_question"
        )

    follow_up_answer = interrupt(
        {
            "type": "follow_up_answer_required",
            "question": follow_up_question,
            "message": "Please provide the student's follow-up answer.",
        }
    )

    if not isinstance(follow_up_answer, str) or not follow_up_answer.strip():
        raise ValueError("resumed follow-up answer cannot be empty")

    return {
        "follow_up_answer": follow_up_answer,
        "status": "follow_up_answer_received",
        "current_node": "follow_up_interrupt",
        "needs_human_input": False,
    }


def evaluate_follow_up_answer_node(
    state: LangGraphFollowUpState,
    follow_up_evaluator: Callable[[str, str], str] = evaluate_answer,
) -> dict[str, Any]:
    follow_up_question = state.get("follow_up_question")
    follow_up_answer = state.get("follow_up_answer")

    if not follow_up_question:
        raise ValueError(
            "evaluate_follow_up_answer node requires state.follow_up_question"
        )

    if not follow_up_answer:
        raise ValueError(
            "evaluate_follow_up_answer node requires state.follow_up_answer"
        )

    follow_up_evaluation = follow_up_evaluator(
        follow_up_question,
        follow_up_answer,
    )

    return {
        "follow_up_evaluation": follow_up_evaluation,
        "status": "follow_up_answer_evaluated",
        "current_node": "evaluate_follow_up_answer",
    }


def build_follow_up_demo_graph(
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
    follow_up_generator: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
    follow_up_evaluator: Callable[[str, str], str] = evaluate_answer,
    checkpointer: InMemorySaver | None = None,
):
    graph = StateGraph(LangGraphFollowUpState)

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
    graph.add_node(
        "generate_follow_up",
        lambda state: generate_follow_up_node(
            state=state,
            follow_up_generator=follow_up_generator,
        ),
    )
    graph.add_node("follow_up_interrupt", follow_up_interrupt_node)
    graph.add_node(
        "evaluate_follow_up_answer",
        lambda state: evaluate_follow_up_answer_node(
            state=state,
            follow_up_evaluator=follow_up_evaluator,
        ),
    )

    graph.set_entry_point("retrieve_context")
    graph.add_edge("retrieve_context", "generate_question")
    graph.add_edge("generate_question", "answer_interrupt")
    graph.add_edge("answer_interrupt", "evaluate_answer")
    graph.add_edge("evaluate_answer", "rewrite_answer")
    graph.add_edge("rewrite_answer", "generate_follow_up")
    graph.add_edge("generate_follow_up", "follow_up_interrupt")
    graph.add_edge("follow_up_interrupt", "evaluate_follow_up_answer")
    graph.add_edge("evaluate_follow_up_answer", END)

    return graph.compile(
        checkpointer=checkpointer or InMemorySaver(),
    )


def start_follow_up_demo(
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


def resume_follow_up_demo_with_answer(
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


def resume_follow_up_demo_with_follow_up_answer(
    graph,
    thread_id: str,
    follow_up_answer: str,
) -> dict[str, Any]:
    if not follow_up_answer.strip():
        raise ValueError("follow_up_answer cannot be empty")

    return graph.invoke(
        Command(resume=follow_up_answer),
        config=build_thread_config(thread_id),
    )


def run_follow_up_demo(
    topic: str,
    thread_id: str,
    answer: str | None = None,
    follow_up_answer: str | None = None,
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
    follow_up_generator: Callable[
        [str, str, str | None, str | None],
        str,
    ] = generate_follow_up_question,
    follow_up_evaluator: Callable[[str, str], str] = evaluate_answer,
) -> dict[str, Any]:
    if follow_up_answer is not None and answer is None:
        raise ValueError("answer is required before follow_up_answer")

    graph = build_follow_up_demo_graph(
        vector_store_path=vector_store_path,
        top_k=top_k,
        embedding_fn=embedding_fn,
        question_generator=question_generator,
        answer_evaluator=answer_evaluator,
        answer_rewriter=answer_rewriter,
        follow_up_generator=follow_up_generator,
        follow_up_evaluator=follow_up_evaluator,
    )
    first_result = start_follow_up_demo(
        graph=graph,
        topic=topic,
        thread_id=thread_id,
    )
    answer_interrupt_payload = get_interrupt_payload(first_result)
    answer_result = None
    follow_up_interrupt_payload = None
    final_result = None

    if answer is not None:
        answer_result = resume_follow_up_demo_with_answer(
            graph=graph,
            thread_id=thread_id,
            answer=answer,
        )
        follow_up_interrupt_payload = get_interrupt_payload(answer_result)

    if follow_up_answer is not None:
        final_result = resume_follow_up_demo_with_follow_up_answer(
            graph=graph,
            thread_id=thread_id,
            follow_up_answer=follow_up_answer,
        )

    return {
        "thread_id": thread_id,
        "first_result": first_result,
        "answer_interrupt_payload": answer_interrupt_payload,
        "answer_result": answer_result,
        "follow_up_interrupt_payload": follow_up_interrupt_payload,
        "final_result": final_result,
    }
