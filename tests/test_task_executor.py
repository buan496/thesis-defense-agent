import pytest

from app.task_executor import (
    execute_retrieve_context_step,
    execute_task_step,
)
from app.task_models import TaskStep
from app.vector_store import build_vector_store
from app.vector_store_io import save_vector_store


def fake_embedding(text: str) -> list[float]:
    if "系统架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


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
