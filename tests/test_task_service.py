from app.task_service import (
    complete_task_step,
    create_defense_task,
    execute_current_task_step,
    get_defense_task,
    start_next_task_step,
    submit_task_answer,
)
from app.task_models import TaskStep
from app.vector_store import build_vector_store
from app.vector_store_io import save_vector_store


def fake_embedding(text: str) -> list[float]:
    if "系统架构" in text:
        return [1.0, 0.0]

    return [0.0, 1.0]


def fake_question_generator(context: str) -> list[str]:
    assert "系统架构上下文" in context

    return [
        "请说明系统架构的模块划分依据是什么？",
    ]


def fake_answer_evaluator(question: str, answer: str) -> str:
    assert "模块划分" in question
    assert "降低耦合" in answer

    return "评分：7/10。回答方向正确。"


def fake_answer_rewriter(
    question: str,
    answer: str,
    evaluation: str | None,
) -> str:
    assert "模块划分" in question
    assert "降低耦合" in answer
    assert evaluation == "评分：7/10。回答方向正确。"

    return "系统架构进行模块划分，主要是为了降低耦合并方便定位问题。"


def save_test_vector_store(tmp_path):
    chunks = [
        {
            "id": 0,
            "text": "系统架构包括特征处理、训练模块和推理模块。",
            "source": "data/thesis.pdf",
        },
        {
            "id": 1,
            "text": "实验部分讨论模型错误率。",
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

    return vector_store_path


def test_create_defense_task_saves_task(tmp_path):
    task, task_path = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    assert task.task_id
    assert task.topic == "系统架构"
    assert task.status == "created"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == task


def test_start_next_task_step_loads_updates_and_saves_task(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    updated_task, step, task_path = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        input={
            "topic": "系统架构",
        },
    )

    assert step is not None
    assert step.step_type == "retrieve_context"
    assert step.input["topic"] == "系统架构"
    assert updated_task.status == "running"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_start_next_task_step_returns_none_when_current_step_not_completed(
    tmp_path,
):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    updated_task, step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert step is None
    assert len(updated_task.steps) == 1


def test_complete_task_step_loads_updates_and_saves_task(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    updated_task, step, task_path = complete_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        output={
            "context": "系统架构相关上下文",
        },
    )

    assert step.status == "completed"
    assert step.output["context"] == "系统架构相关上下文"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_task_service_can_advance_two_steps(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    _, first_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert first_step is not None
    assert first_step.step_type == "retrieve_context"

    complete_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        output={
            "context": "系统架构上下文",
        },
    )

    updated_task, second_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert second_step is not None
    assert second_step.step_type == "generate_question"
    assert second_step.input["context"] == "系统架构上下文"
    assert len(updated_task.steps) == 2


def test_execute_current_task_step_runs_and_saves_step_output(tmp_path):
    vector_store_path = save_test_vector_store(tmp_path)
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        input={
            "topic": "系统架构",
        },
    )

    updated_task, step, task_path = execute_current_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        vector_store_path=str(vector_store_path),
        top_k=1,
        embedding_fn=fake_embedding,
    )

    assert step.status == "completed"
    assert step.output["query"] == "系统架构"
    assert "训练模块" in step.output["context"]
    assert step.output["sources"][0]["source"] == "data/thesis.pdf"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_execute_current_task_step_rejects_task_without_current_step(
    tmp_path,
):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    try:
        execute_current_task_step(
            task_id=task.task_id,
            directory=tmp_path,
        )
    except ValueError as error:
        assert "当前任务没有可执行步骤" in str(error)
    else:
        raise AssertionError("没有当前步骤时应该报错")


def test_execute_current_task_step_runs_generate_question_step(
    tmp_path,
):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )
    complete_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        output={
            "context": "系统架构上下文",
        },
    )
    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    updated_task, step, task_path = execute_current_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        question_generator=fake_question_generator,
    )

    assert step.step_type == "generate_question"
    assert step.status == "completed"
    assert step.output["question"] == (
        "请说明系统架构的模块划分依据是什么？"
    )
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_submit_task_answer_completes_wait_for_answer_step(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )
    wait_step = TaskStep(
        step_type="wait_for_answer",
        input={
            "question": "系统架构为什么要拆分模块？",
        },
    )
    task.add_step(wait_step)
    from app.task_store import save_defense_task

    save_defense_task(task, directory=tmp_path)

    updated_task, step, task_path = submit_task_answer(
        task_id=task.task_id,
        answer="为了降低耦合并方便定位问题。",
        directory=tmp_path,
    )

    assert step.status == "completed"
    assert step.output["question"] == "系统架构为什么要拆分模块？"
    assert step.output["answer"] == "为了降低耦合并方便定位问题。"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_submit_task_answer_rejects_empty_answer(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    try:
        submit_task_answer(
            task_id=task.task_id,
            answer="   ",
            directory=tmp_path,
        )
    except ValueError as error:
        assert "学生回答不能为空" in str(error)
    else:
        raise AssertionError("空回答应该报错")


def test_submit_task_answer_rejects_non_answer_step(tmp_path):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    try:
        submit_task_answer(
            task_id=task.task_id,
            answer="为了降低耦合。",
            directory=tmp_path,
        )
    except ValueError as error:
        assert "当前步骤不是 wait_for_answer" in str(error)
    else:
        raise AssertionError("非 wait_for_answer 步骤应该拒绝提交")


def test_execute_current_task_step_runs_evaluate_answer_step(
    tmp_path,
):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    question_step = TaskStep(step_type="generate_question")
    question_step.mark_completed(
        output={
            "question": "请说明系统架构的模块划分依据是什么？",
        }
    )
    task.add_step(question_step)

    from app.task_store import save_defense_task

    save_defense_task(task, directory=tmp_path)

    _, wait_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert wait_step is not None
    assert wait_step.step_type == "wait_for_answer"
    assert wait_step.input["question"] == (
        "请说明系统架构的模块划分依据是什么？"
    )

    submit_task_answer(
        task_id=task.task_id,
        answer="为了降低耦合并方便定位问题。",
        directory=tmp_path,
    )

    _, evaluation_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert evaluation_step is not None
    assert evaluation_step.step_type == "evaluate_answer"
    assert evaluation_step.input["question"] == (
        "请说明系统架构的模块划分依据是什么？"
    )
    assert evaluation_step.input["answer"] == "为了降低耦合并方便定位问题。"

    updated_task, step, task_path = execute_current_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        answer_evaluator=fake_answer_evaluator,
    )

    assert step.step_type == "evaluate_answer"
    assert step.status == "completed"
    assert step.output["question"] == (
        "请说明系统架构的模块划分依据是什么？"
    )
    assert step.output["answer"] == "为了降低耦合并方便定位问题。"
    assert step.output["evaluation"] == "评分：7/10。回答方向正确。"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task


def test_execute_current_task_step_runs_rewrite_answer_step(
    tmp_path,
):
    task, _ = create_defense_task(
        topic="系统架构",
        directory=tmp_path,
    )

    evaluation_step = TaskStep(step_type="evaluate_answer")
    evaluation_step.mark_completed(
        output={
            "question": "请说明系统架构的模块划分依据是什么？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确。",
        }
    )
    task.add_step(evaluation_step)

    from app.task_store import save_defense_task

    save_defense_task(task, directory=tmp_path)

    _, rewrite_step, _ = start_next_task_step(
        task_id=task.task_id,
        directory=tmp_path,
    )

    assert rewrite_step is not None
    assert rewrite_step.step_type == "rewrite_answer"
    assert rewrite_step.input["question"] == (
        "请说明系统架构的模块划分依据是什么？"
    )
    assert rewrite_step.input["answer"] == "为了降低耦合并方便定位问题。"
    assert rewrite_step.input["evaluation"] == "评分：7/10。回答方向正确。"

    updated_task, step, task_path = execute_current_task_step(
        task_id=task.task_id,
        directory=tmp_path,
        answer_rewriter=fake_answer_rewriter,
    )

    assert step.step_type == "rewrite_answer"
    assert step.status == "completed"
    assert step.output["rewritten_answer"] == (
        "系统架构进行模块划分，主要是为了降低耦合并方便定位问题。"
    )
    assert step.tool_traces[0]["tool_name"] == "rewrite_answer"
    assert task_path.exists()

    loaded_task = get_defense_task(
        task.task_id,
        directory=tmp_path,
    )

    assert loaded_task == updated_task
