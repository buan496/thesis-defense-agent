import pytest

from app.task_executor import (
    execute_evaluate_answer_step,
    execute_evaluate_follow_up_answer_step,
    execute_generate_follow_up_step,
    execute_generate_question_step,
    execute_retrieve_context_step,
    execute_rewrite_answer_step,
    execute_summarize_training_step,
    execute_task_step,
)
from app.task_models import TaskStep
from app.vector_store import build_vector_store
from app.vector_store_io import save_vector_store


def fake_embedding(text: str) -> list[float]:
    if "系统架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


class FakeVectorStoreRepository:
    def __init__(self):
        self.search_calls = []

    def save(self, store: list[dict]) -> str:
        return "fake-vector-store"

    def load(self) -> list[dict]:
        return []

    def search(
        self,
        query: str,
        top_k: int,
        embedding_fn,
    ) -> list[dict]:
        self.search_calls.append(
            {
                "query": query,
                "top_k": top_k,
            }
        )
        return [
            {
                "id": 10,
                "text": "系统架构包括特征处理和训练模块。",
                "source": "fake-store",
                "score": 0.9,
            }
        ]


def fake_question_generator(context: str) -> list[str]:
    assert "系统架构" in context

    return [
        "系统架构为什么要拆分为多个模块？",
        "系统架构如何支持后续扩展？",
    ]


def fake_audited_question_generator(context: str) -> dict:
    assert "系统架构" in context

    return {
        "questions": [
            "系统架构为什么要拆分为多个模块？",
        ],
        "token_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 120,
        },
        "cost_estimate": {
            "input_cost": 0.001,
            "output_cost": 0.002,
            "total_cost": 0.003,
            "currency": "CNY",
        },
    }


def fake_answer_evaluator(question: str, answer: str) -> str:
    assert "系统架构" in question
    assert "降低耦合" in answer

    return "评分：7/10。回答方向正确，但需要补充模块例子。"


def fake_answer_rewriter(
    question: str,
    answer: str,
    evaluation: str | None,
) -> str:
    assert "系统架构" in question
    assert "降低耦合" in answer
    assert evaluation is not None
    assert "补充模块例子" in evaluation

    return "系统架构拆分为多个模块，主要是为了降低耦合，并便于定位问题。"


def fake_follow_up_generator(
    question: str,
    answer: str,
    evaluation: str | None = None,
    rewritten_answer: str | None = None,
) -> str:
    assert "系统架构" in question
    assert "降低耦合" in answer
    assert evaluation is not None
    assert rewritten_answer is not None

    return "请结合特征处理模块说明模块拆分如何帮助定位问题？"


def fake_follow_up_evaluator(question: str, answer: str) -> str:
    assert "特征处理模块" in question
    assert "音频读取" in answer

    return "评分：8/10。追问回答较具体。"


def fake_training_summarizer(
    question: str,
    answer: str,
    evaluation: str,
    rewritten_answer: str,
    follow_up_question: str,
    follow_up_answer: str,
    follow_up_evaluation: str,
) -> str:
    assert "系统架构" in question
    assert "降低耦合" in answer
    assert "特征处理模块" in follow_up_question
    assert "音频读取" in follow_up_answer
    assert "8/10" in follow_up_evaluation

    return "本轮训练能说明模块化价值，但还需要补充具体模块案例。"


def test_execute_retrieve_context_step(tmp_path):
    chunks = [
        {
            "id": 0,
            "text": "系统架构包括特征处理、词表管理和模型模块。",
            "source": "data/thesis.pdf",
        },
        {
            "id": 1,
            "text": "实验结果主要分析模型错误率。",
            "source": "data/thesis.pdf",
        },
    ]

    store = build_vector_store(
        chunks,
        embedding_fn=fake_embedding,
    )

    vector_store_path = tmp_path / "vector_store.json"

    save_vector_store(
        store,
        vector_store_path,
    )

    step = TaskStep(
        step_type="retrieve_context",
        input={
            "query": "系统架构",
        },
    )

    result_step = execute_retrieve_context_step(
        step,
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
    )

    assert result_step.status == "completed"
    assert result_step.output["query"] == "系统架构"
    assert "系统架构包括特征处理" in result_step.output["context"]
    assert result_step.output["sources"][0]["source"] == "data/thesis.pdf"
    assert result_step.evidence[0]["text"] == (
        "系统架构包括特征处理、词表管理和模型模块。"
    )
    assert result_step.tool_traces[0]["tool_name"] == "search_vector_store"
    assert result_step.tool_traces[0]["arguments"]["query"] == "系统架构"
    assert result_step.tool_traces[0]["arguments"]["top_k"] == 1
    assert result_step.tool_traces[0]["success"] is True
    assert result_step.tool_traces[0]["duration_ms"] >= 0


def test_execute_retrieve_context_step_accepts_topic_as_query(tmp_path):
    chunks = [
        {
            "id": 0,
            "text": "系统架构包括训练模块和推理模块。",
            "source": "data/thesis.pdf",
        },
    ]

    store = build_vector_store(
        chunks,
        embedding_fn=fake_embedding,
    )

    vector_store_path = tmp_path / "vector_store.json"

    save_vector_store(
        store,
        vector_store_path,
    )

    step = TaskStep(
        step_type="retrieve_context",
        input={
            "topic": "系统架构",
        },
    )

    result_step = execute_retrieve_context_step(
        step,
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
    )

    assert result_step.status == "completed"
    assert result_step.output["query"] == "系统架构"
    assert "训练模块" in result_step.output["context"]


def test_execute_retrieve_context_step_can_use_vector_store_repository():
    repository = FakeVectorStoreRepository()
    step = TaskStep(
        step_type="retrieve_context",
        input={
            "query": "系统架构",
        },
    )

    result_step = execute_retrieve_context_step(
        step,
        top_k=1,
        embedding_fn=fake_embedding,
        vector_store_repository=repository,
    )

    assert result_step.status == "completed"
    assert "fake-store" in result_step.output["context"]
    assert repository.search_calls == [
        {
            "query": "系统架构",
            "top_k": 1,
        }
    ]


def test_execute_retrieve_context_step_requires_query_or_topic():
    step = TaskStep(
        step_type="retrieve_context",
        input={},
    )

    with pytest.raises(
        ValueError,
        match="input.query 或 input.topic",
    ):
        execute_retrieve_context_step(step)


def test_execute_task_step_dispatches_retrieve_context(tmp_path):
    chunks = [
        {
            "id": 0,
            "text": "系统架构包括数据准备流程。",
            "source": "data/thesis.pdf",
        },
    ]

    store = build_vector_store(
        chunks,
        embedding_fn=fake_embedding,
    )

    vector_store_path = tmp_path / "vector_store.json"

    save_vector_store(
        store,
        vector_store_path,
    )

    step = TaskStep(
        step_type="retrieve_context",
        input={
            "query": "系统架构",
        },
    )

    result_step = execute_task_step(
        step,
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
    )

    assert result_step.status == "completed"
    assert "数据准备流程" in result_step.output["context"]


def test_execute_task_step_rejects_unknown_step_type():
    step = TaskStep(
        step_type="unknown_step",
    )

    with pytest.raises(
        ValueError,
        match="不支持的任务步骤类型",
    ):
        execute_task_step(step)


def test_execute_generate_question_step():
    step = TaskStep(
        step_type="generate_question",
        input={
            "topic": "系统架构",
            "context": "系统架构包括特征处理和训练模块。",
        },
    )

    result_step = execute_generate_question_step(
        step,
        question_generator=fake_question_generator,
    )

    assert result_step.status == "completed"
    assert result_step.output["topic"] == "系统架构"
    assert result_step.output["question"] == (
        "系统架构为什么要拆分为多个模块？"
    )
    assert result_step.output["questions"] == [
        "系统架构为什么要拆分为多个模块？",
        "系统架构如何支持后续扩展？",
    ]
    assert (
        result_step.tool_traces[0]["tool_name"]
        == "generate_questions_from_context"
    )
    assert result_step.tool_traces[0]["success"] is True
    assert result_step.tool_traces[0]["duration_ms"] >= 0


def test_execute_generate_question_step_requires_context():
    step = TaskStep(
        step_type="generate_question",
        input={
            "topic": "系统架构",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.context",
    ):
        execute_generate_question_step(
            step,
            question_generator=fake_question_generator,
        )


def test_execute_task_step_dispatches_generate_question():
    step = TaskStep(
        step_type="generate_question",
        input={
            "topic": "系统架构",
            "context": "系统架构包括特征处理和训练模块。",
        },
    )

    result_step = execute_task_step(
        step,
        question_generator=fake_question_generator,
    )

    assert result_step.status == "completed"
    assert result_step.output["question"] == (
        "系统架构为什么要拆分为多个模块？"
    )


def test_execute_generate_question_step_records_token_usage_and_cost():
    step = TaskStep(
        step_type="generate_question",
        input={
            "topic": "系统架构",
            "context": "系统架构包括特征处理和训练模块。",
        },
    )

    result_step = execute_generate_question_step(
        step,
        question_generator=fake_audited_question_generator,
    )

    assert result_step.status == "completed"
    assert result_step.output["question"] == (
        "系统架构为什么要拆分为多个模块？"
    )
    assert result_step.token_usage == {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
    }
    assert result_step.cost_estimate == {
        "input_cost": 0.001,
        "output_cost": 0.002,
        "total_cost": 0.003,
        "currency": "CNY",
    }


def test_execute_evaluate_answer_step():
    step = TaskStep(
        step_type="evaluate_answer",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
        },
    )

    result_step = execute_evaluate_answer_step(
        step,
        answer_evaluator=fake_answer_evaluator,
    )

    assert result_step.status == "completed"
    assert result_step.output["question"] == (
        "系统架构为什么要拆分为多个模块？"
    )
    assert result_step.output["answer"] == (
        "为了降低耦合并方便定位问题。"
    )
    assert result_step.output["evaluation"] == (
        "评分：7/10。回答方向正确，但需要补充模块例子。"
    )
    assert result_step.tool_traces[0]["tool_name"] == "evaluate_answer"
    assert result_step.tool_traces[0]["success"] is True
    assert result_step.tool_traces[0]["duration_ms"] >= 0


def test_execute_evaluate_answer_step_requires_question():
    step = TaskStep(
        step_type="evaluate_answer",
        input={
            "answer": "为了降低耦合。",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.question",
    ):
        execute_evaluate_answer_step(
            step,
            answer_evaluator=fake_answer_evaluator,
        )


def test_execute_evaluate_answer_step_requires_answer():
    step = TaskStep(
        step_type="evaluate_answer",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.answer",
    ):
        execute_evaluate_answer_step(
            step,
            answer_evaluator=fake_answer_evaluator,
        )


def test_execute_task_step_dispatches_evaluate_answer():
    step = TaskStep(
        step_type="evaluate_answer",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
        },
    )

    result_step = execute_task_step(
        step,
        answer_evaluator=fake_answer_evaluator,
    )

    assert result_step.status == "completed"
    assert "评分：7/10" in result_step.output["evaluation"]


def test_execute_rewrite_answer_step():
    step = TaskStep(
        step_type="rewrite_answer",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确，但需要补充模块例子。",
        },
    )

    result_step = execute_rewrite_answer_step(
        step,
        answer_rewriter=fake_answer_rewriter,
    )

    assert result_step.status == "completed"
    assert result_step.output["question"] == (
        "系统架构为什么要拆分为多个模块？"
    )
    assert result_step.output["answer"] == (
        "为了降低耦合并方便定位问题。"
    )
    assert result_step.output["evaluation"] == (
        "评分：7/10。回答方向正确，但需要补充模块例子。"
    )
    assert result_step.output["rewritten_answer"] == (
        "系统架构拆分为多个模块，主要是为了降低耦合，并便于定位问题。"
    )
    assert result_step.tool_traces[0]["tool_name"] == "rewrite_answer"
    assert result_step.tool_traces[0]["success"] is True
    assert result_step.tool_traces[0]["duration_ms"] >= 0


def test_execute_rewrite_answer_step_requires_question():
    step = TaskStep(
        step_type="rewrite_answer",
        input={
            "answer": "为了降低耦合。",
            "evaluation": "评分：7/10。",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.question",
    ):
        execute_rewrite_answer_step(
            step,
            answer_rewriter=fake_answer_rewriter,
        )


def test_execute_rewrite_answer_step_requires_answer():
    step = TaskStep(
        step_type="rewrite_answer",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "evaluation": "评分：7/10。",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.answer",
    ):
        execute_rewrite_answer_step(
            step,
            answer_rewriter=fake_answer_rewriter,
        )


def test_execute_task_step_dispatches_rewrite_answer():
    step = TaskStep(
        step_type="rewrite_answer",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确，但需要补充模块例子。",
        },
    )

    result_step = execute_task_step(
        step,
        answer_rewriter=fake_answer_rewriter,
    )

    assert result_step.status == "completed"
    assert "降低耦合" in result_step.output["rewritten_answer"]


def test_execute_generate_follow_up_step():
    step = TaskStep(
        step_type="generate_follow_up",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确。",
            "rewritten_answer": "系统架构拆分为多个模块，主要是为了降低耦合。",
        },
    )

    result_step = execute_generate_follow_up_step(
        step,
        follow_up_generator=fake_follow_up_generator,
    )

    assert result_step.status == "completed"
    assert result_step.output["follow_up_question"] == (
        "请结合特征处理模块说明模块拆分如何帮助定位问题？"
    )
    assert result_step.output["question"] == (
        "系统架构为什么要拆分为多个模块？"
    )
    assert result_step.tool_traces[0]["tool_name"] == (
        "generate_follow_up_question"
    )
    assert result_step.tool_traces[0]["success"] is True
    assert result_step.tool_traces[0]["duration_ms"] >= 0


def test_execute_generate_follow_up_step_requires_question():
    step = TaskStep(
        step_type="generate_follow_up",
        input={
            "answer": "为了降低耦合。",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.question",
    ):
        execute_generate_follow_up_step(
            step,
            follow_up_generator=fake_follow_up_generator,
        )


def test_execute_generate_follow_up_step_requires_answer():
    step = TaskStep(
        step_type="generate_follow_up",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.answer",
    ):
        execute_generate_follow_up_step(
            step,
            follow_up_generator=fake_follow_up_generator,
        )


def test_execute_task_step_dispatches_generate_follow_up():
    step = TaskStep(
        step_type="generate_follow_up",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确。",
            "rewritten_answer": "系统架构拆分为多个模块，主要是为了降低耦合。",
        },
    )

    result_step = execute_task_step(
        step,
        follow_up_generator=fake_follow_up_generator,
    )

    assert result_step.status == "completed"
    assert "特征处理模块" in result_step.output["follow_up_question"]


def test_execute_evaluate_follow_up_answer_step():
    step = TaskStep(
        step_type="evaluate_follow_up_answer",
        input={
            "follow_up_question": "请结合特征处理模块说明模块拆分如何帮助定位问题？",
            "follow_up_answer": "如果音频读取失败，可以优先检查特征处理模块。",
        },
    )

    result_step = execute_evaluate_follow_up_answer_step(
        step,
        follow_up_evaluator=fake_follow_up_evaluator,
    )

    assert result_step.status == "completed"
    assert result_step.output["follow_up_evaluation"] == (
        "评分：8/10。追问回答较具体。"
    )
    assert result_step.tool_traces[0]["tool_name"] == (
        "evaluate_follow_up_answer"
    )


def test_execute_evaluate_follow_up_answer_step_requires_question():
    step = TaskStep(
        step_type="evaluate_follow_up_answer",
        input={
            "follow_up_answer": "可以检查特征处理模块。",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.follow_up_question",
    ):
        execute_evaluate_follow_up_answer_step(
            step,
            follow_up_evaluator=fake_follow_up_evaluator,
        )


def test_execute_evaluate_follow_up_answer_step_requires_answer():
    step = TaskStep(
        step_type="evaluate_follow_up_answer",
        input={
            "follow_up_question": "请结合特征处理模块说明模块拆分如何帮助定位问题？",
        },
    )

    with pytest.raises(
        ValueError,
        match="input.follow_up_answer",
    ):
        execute_evaluate_follow_up_answer_step(
            step,
            follow_up_evaluator=fake_follow_up_evaluator,
        )


def test_execute_task_step_dispatches_evaluate_follow_up_answer():
    step = TaskStep(
        step_type="evaluate_follow_up_answer",
        input={
            "follow_up_question": "请结合特征处理模块说明模块拆分如何帮助定位问题？",
            "follow_up_answer": "如果音频读取失败，可以优先检查特征处理模块。",
        },
    )

    result_step = execute_task_step(
        step,
        follow_up_evaluator=fake_follow_up_evaluator,
    )

    assert result_step.status == "completed"
    assert "8/10" in result_step.output["follow_up_evaluation"]


def test_execute_summarize_training_step():
    step = TaskStep(
        step_type="summarize_training",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确。",
            "rewritten_answer": "系统架构拆分为多个模块，主要是为了降低耦合。",
            "follow_up_question": "请结合特征处理模块说明模块拆分如何帮助定位问题？",
            "follow_up_answer": "如果音频读取失败，可以优先检查特征处理模块。",
            "follow_up_evaluation": "评分：8/10。追问回答较具体。",
        },
    )

    result_step = execute_summarize_training_step(
        step,
        training_summarizer=fake_training_summarizer,
    )

    assert result_step.status == "completed"
    assert result_step.output["summary"] == (
        "本轮训练能说明模块化价值，但还需要补充具体模块案例。"
    )
    assert result_step.output["weaknesses"] == []
    assert result_step.output["next_suggestions"] == []
    assert result_step.tool_traces[0]["tool_name"] == "summarize_training"


def test_execute_summarize_training_step_requires_fields():
    step = TaskStep(
        step_type="summarize_training",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
        },
    )

    with pytest.raises(
        ValueError,
        match="summarize_training 步骤缺少输入字段",
    ):
        execute_summarize_training_step(
            step,
            training_summarizer=fake_training_summarizer,
        )


def test_execute_task_step_dispatches_summarize_training():
    step = TaskStep(
        step_type="summarize_training",
        input={
            "question": "系统架构为什么要拆分为多个模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确。",
            "rewritten_answer": "系统架构拆分为多个模块，主要是为了降低耦合。",
            "follow_up_question": "请结合特征处理模块说明模块拆分如何帮助定位问题？",
            "follow_up_answer": "如果音频读取失败，可以优先检查特征处理模块。",
            "follow_up_evaluation": "评分：8/10。追问回答较具体。",
        },
    )

    result_step = execute_task_step(
        step,
        training_summarizer=fake_training_summarizer,
    )

    assert result_step.status == "completed"
    assert "模块化价值" in result_step.output["summary"]
