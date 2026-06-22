from app.task_markdown_exporter import (
    build_task_markdown_report,
    export_task_markdown_report,
)
from app.task_models import DefenseTask, TaskStep


def build_completed_task() -> DefenseTask:
    task = DefenseTask(
        topic="系统架构",
        task_id="task-001",
    )

    retrieve_step = TaskStep(step_type="retrieve_context")
    retrieve_step.evidence = [
        {
            "source": "data/thesis.pdf",
            "score": 0.9,
            "text": "系统架构包括特征处理、训练模块和推理模块。",
        },
    ]
    retrieve_step.tool_traces = [
        {
            "tool_name": "search_vector_store",
            "success": True,
            "duration_ms": 10.0,
        },
    ]
    retrieve_step.mark_completed(
        output={
            "context": "系统架构相关上下文",
        }
    )
    task.add_step(retrieve_step)

    question_step = TaskStep(step_type="generate_question")
    question_step.mark_completed(
        output={
            "question": "系统架构为什么要拆分模块？",
        }
    )
    task.add_step(question_step)

    answer_step = TaskStep(step_type="wait_for_answer")
    answer_step.mark_completed(
        output={
            "answer": "为了降低耦合并方便定位问题。",
        }
    )
    task.add_step(answer_step)

    evaluation_step = TaskStep(step_type="evaluate_answer")
    evaluation_step.mark_completed(
        output={
            "question": "系统架构为什么要拆分模块？",
            "answer": "为了降低耦合并方便定位问题。",
            "evaluation": "评分：7/10。回答方向正确。",
        }
    )
    task.add_step(evaluation_step)

    rewrite_step = TaskStep(step_type="rewrite_answer")
    rewrite_step.mark_completed(
        output={
            "rewritten_answer": "系统架构拆分模块是为了降低耦合并提升可维护性。",
        }
    )
    task.add_step(rewrite_step)

    follow_up_step = TaskStep(step_type="generate_follow_up")
    follow_up_step.mark_completed(
        output={
            "follow_up_question": "请结合特征处理模块举例说明。",
        }
    )
    task.add_step(follow_up_step)

    follow_up_answer_step = TaskStep(
        step_type="wait_for_follow_up_answer",
    )
    follow_up_answer_step.mark_completed(
        output={
            "follow_up_answer": "如果音频读取失败，可以优先检查特征处理模块。",
        }
    )
    task.add_step(follow_up_answer_step)

    follow_up_evaluation_step = TaskStep(
        step_type="evaluate_follow_up_answer",
    )
    follow_up_evaluation_step.mark_completed(
        output={
            "follow_up_evaluation": "评分：8/10。追问回答较具体。",
        }
    )
    task.add_step(follow_up_evaluation_step)

    summary_step = TaskStep(step_type="summarize_training")
    summary_step.mark_completed(
        output={
            "summary": "本轮训练完成，下一轮应继续补充具体模块案例。",
        }
    )
    task.add_step(summary_step)
    task.mark_completed()

    return task


def test_build_task_markdown_report_contains_training_sections():
    task = build_completed_task()

    markdown = build_task_markdown_report(task)

    assert "# 论文答辩训练报告" in markdown
    assert "训练主题：系统架构" in markdown
    assert "## 检索证据" in markdown
    assert "系统架构包括特征处理、训练模块和推理模块。" in markdown
    assert "## 答辩问题" in markdown
    assert "系统架构为什么要拆分模块？" in markdown
    assert "## 学生回答" in markdown
    assert "为了降低耦合并方便定位问题。" in markdown
    assert "## 回答评价" in markdown
    assert "评分：7/10。回答方向正确。" in markdown
    assert "## 改写后的回答" in markdown
    assert "## 追问" in markdown
    assert "请结合特征处理模块举例说明。" in markdown
    assert "## 追问回答" in markdown
    assert "## 追问评价" in markdown
    assert "评分：8/10。追问回答较具体。" in markdown
    assert "## 本轮训练总结" in markdown
    assert "本轮训练完成" in markdown
    assert "## Trace 汇总" in markdown
    assert "Step Count：9" in markdown
    assert "Tool Calls：1" in markdown


def test_export_task_markdown_report_writes_file(tmp_path):
    task = build_completed_task()
    output_path = tmp_path / "task-report.md"

    saved_path = export_task_markdown_report(
        task,
        output_path=output_path,
    )

    assert saved_path == output_path
    assert output_path.exists()
    assert "论文答辩训练报告" in output_path.read_text(
        encoding="utf-8",
    )
