from pathlib import Path
from typing import Any

from app.task_models import DefenseTask, TaskStep
from app.task_trace_analyzer import analyze_task_trace


DEFAULT_TASK_REPORT_DIRECTORY = Path("data/task_reports")


def get_latest_step_by_type(
    task: DefenseTask,
    step_type: str,
) -> TaskStep | None:
    for step in reversed(task.steps):
        if step.step_type == step_type:
            return step

    return None


def first_non_empty(*values: Any) -> str:
    for value in values:
        if value is not None and str(value).strip():
            return str(value)

    return ""


def format_section(
    title: str,
    content: str,
) -> str:
    if not content.strip():
        content = "暂无"

    return f"## {title}\n\n{content.strip()}\n"


def format_evidence(task: DefenseTask) -> str:
    evidence_items = []

    for step in task.steps:
        for evidence in step.evidence:
            evidence_items.append(evidence)

    if not evidence_items:
        return "暂无"

    lines = []

    for index, evidence in enumerate(evidence_items, start=1):
        source = evidence.get("source", "unknown")
        score = evidence.get("score")
        text = str(evidence.get("text", "")).strip()

        lines.append(f"### 证据 {index}")
        lines.append("")
        lines.append(f"- 来源：{source}")

        if score is not None:
            lines.append(f"- Score：{score}")

        lines.append("")
        lines.append(text or "暂无内容")
        lines.append("")

    return "\n".join(lines).strip()


def format_trace_summary(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- Task Status：{report['status']}",
            f"- Step Count：{report['step_count']}",
            f"- Completed Steps：{report['completed_step_count']}",
            f"- Failed Steps：{report['failed_step_count']}",
            f"- Tool Calls：{report['tool_call_count']}",
            f"- Successful Tool Calls：{report['successful_tool_call_count']}",
            f"- Failed Tool Calls：{report['failed_tool_call_count']}",
            f"- Total Duration MS：{round(report['total_duration_ms'], 2)}",
            f"- Total Tokens：{report['total_tokens']}",
            f"- Total Cost：{round(report['total_cost'], 6)} {report['currency']}",
            f"- Evidence Count：{report['evidence_count']}",
        ]
    )


def build_task_markdown_report(task: DefenseTask) -> str:
    question_step = get_latest_step_by_type(task, "generate_question")
    answer_step = get_latest_step_by_type(task, "wait_for_answer")
    evaluation_step = get_latest_step_by_type(task, "evaluate_answer")
    rewrite_step = get_latest_step_by_type(task, "rewrite_answer")
    follow_up_step = get_latest_step_by_type(task, "generate_follow_up")
    follow_up_answer_step = get_latest_step_by_type(
        task,
        "wait_for_follow_up_answer",
    )
    follow_up_evaluation_step = get_latest_step_by_type(
        task,
        "evaluate_follow_up_answer",
    )
    summary_step = get_latest_step_by_type(task, "summarize_training")

    trace_report = analyze_task_trace(task)

    question = first_non_empty(
        question_step.output.get("question") if question_step else None,
        evaluation_step.output.get("question") if evaluation_step else None,
    )
    answer = first_non_empty(
        answer_step.output.get("answer") if answer_step else None,
        evaluation_step.output.get("answer") if evaluation_step else None,
    )
    evaluation = first_non_empty(
        evaluation_step.output.get("evaluation") if evaluation_step else None,
    )
    rewritten_answer = first_non_empty(
        rewrite_step.output.get("rewritten_answer") if rewrite_step else None,
        summary_step.output.get("rewritten_answer") if summary_step else None,
    )
    follow_up_question = first_non_empty(
        follow_up_step.output.get("follow_up_question")
        if follow_up_step
        else None,
        follow_up_evaluation_step.output.get("follow_up_question")
        if follow_up_evaluation_step
        else None,
    )
    follow_up_answer = first_non_empty(
        follow_up_answer_step.output.get("follow_up_answer")
        if follow_up_answer_step
        else None,
        follow_up_evaluation_step.output.get("follow_up_answer")
        if follow_up_evaluation_step
        else None,
    )
    follow_up_evaluation = first_non_empty(
        follow_up_evaluation_step.output.get("follow_up_evaluation")
        if follow_up_evaluation_step
        else None,
    )
    summary = first_non_empty(
        summary_step.output.get("summary") if summary_step else None,
    )

    sections = [
        "# 论文答辩训练报告\n",
        format_section("任务信息", f"- Task ID：{task.task_id}\n- 训练主题：{task.topic}\n- 状态：{task.status}"),
        format_section("检索证据", format_evidence(task)),
        format_section("答辩问题", question),
        format_section("学生回答", answer),
        format_section("回答评价", evaluation),
        format_section("改写后的回答", rewritten_answer),
        format_section("追问", follow_up_question),
        format_section("追问回答", follow_up_answer),
        format_section("追问评价", follow_up_evaluation),
        format_section("本轮训练总结", summary),
        format_section("Trace 汇总", format_trace_summary(trace_report)),
    ]

    return "\n".join(sections).strip() + "\n"


def export_task_markdown_report(
    task: DefenseTask,
    output_path: str | Path | None = None,
    output_directory: str | Path = DEFAULT_TASK_REPORT_DIRECTORY,
) -> Path:
    if output_path is None:
        output_path = Path(output_directory) / f"{task.task_id}.md"
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        build_task_markdown_report(task),
        encoding="utf-8",
    )

    return output_path
