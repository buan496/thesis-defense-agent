from app.task_models import DefenseTask, TaskStep
from app.task_trace_analyzer import analyze_task_trace


def test_analyze_empty_task_trace():
    task = DefenseTask(topic="系统架构")

    report = analyze_task_trace(task)

    assert report["task_id"] == task.task_id
    assert report["topic"] == "系统架构"
    assert report["status"] == "created"
    assert report["current_step_id"] is None
    assert report["current_step_type"] is None
    assert report["step_count"] == 0
    assert report["tool_call_count"] == 0
    assert report["total_tokens"] == 0
    assert report["total_cost"] == 0.0
    assert report["currency"] == "CNY"
    assert report["step_summaries"] == []


def test_analyze_task_trace_summarizes_steps_tools_tokens_and_cost():
    task = DefenseTask(topic="系统架构", task_id="task-001")

    retrieve_step = TaskStep(step_type="retrieve_context", step_id="step-001")
    retrieve_step.evidence = [
        {
            "id": 1,
            "text": "系统架构包括特征处理模块。",
        },
        {
            "id": 2,
            "text": "系统架构包括训练模块。",
        },
    ]
    retrieve_step.tool_traces = [
        {
            "tool_name": "search_vector_store",
            "success": True,
            "duration_ms": 120.5,
        },
    ]
    retrieve_step.mark_completed(
        output={
            "context": "系统架构上下文",
        }
    )
    task.add_step(retrieve_step)

    question_step = TaskStep(step_type="generate_question", step_id="step-002")
    question_step.tool_traces = [
        {
            "tool_name": "generate_questions_from_context",
            "success": True,
            "duration_ms": 230.0,
        },
    ]
    question_step.token_usage = {
        "prompt_tokens": 100,
        "completion_tokens": 20,
        "total_tokens": 120,
    }
    question_step.cost_estimate = {
        "input_cost": 0.001,
        "output_cost": 0.002,
        "total_cost": 0.003,
        "currency": "CNY",
    }
    question_step.mark_completed(
        output={
            "question": "系统架构为什么要拆分模块？",
        }
    )
    task.add_step(question_step)

    report = analyze_task_trace(task)

    assert report["task_id"] == "task-001"
    assert report["current_step_id"] == "step-002"
    assert report["current_step_type"] == "generate_question"
    assert report["current_step_status"] == "completed"
    assert report["step_count"] == 2
    assert report["completed_step_count"] == 2
    assert report["failed_step_count"] == 0
    assert report["tool_call_count"] == 2
    assert report["successful_tool_call_count"] == 2
    assert report["failed_tool_call_count"] == 0
    assert report["total_duration_ms"] == 350.5
    assert report["total_prompt_tokens"] == 100
    assert report["total_completion_tokens"] == 20
    assert report["total_tokens"] == 120
    assert report["total_cost"] == 0.003
    assert report["currency"] == "CNY"
    assert report["evidence_count"] == 2
    assert report["step_summaries"] == [
        {
            "step_id": "step-001",
            "step_type": "retrieve_context",
            "status": "completed",
            "tool_call_count": 1,
            "evidence_count": 2,
            "total_tokens": 0,
            "total_cost": 0.0,
            "error": None,
        },
        {
            "step_id": "step-002",
            "step_type": "generate_question",
            "status": "completed",
            "tool_call_count": 1,
            "evidence_count": 0,
            "total_tokens": 120,
            "total_cost": 0.003,
            "error": None,
        },
    ]


def test_analyze_task_trace_counts_failed_and_pending_steps():
    task = DefenseTask(topic="系统架构")

    failed_step = TaskStep(step_type="retrieve_context")
    failed_step.tool_traces = [
        {
            "tool_name": "search_vector_store",
            "success": False,
            "duration_ms": 10.0,
        },
    ]
    failed_step.mark_failed("向量库文件不存在")
    task.add_step(failed_step)

    pending_step = TaskStep(step_type="generate_question")
    task.add_step(pending_step)

    report = analyze_task_trace(task)

    assert report["step_count"] == 2
    assert report["failed_step_count"] == 1
    assert report["pending_step_count"] == 1
    assert report["completed_step_count"] == 0
    assert report["tool_call_count"] == 1
    assert report["successful_tool_call_count"] == 0
    assert report["failed_tool_call_count"] == 1
    assert report["total_duration_ms"] == 10.0
    assert report["current_step_type"] == "generate_question"
    assert report["current_step_status"] == "pending"
