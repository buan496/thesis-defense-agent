from app.feedback_store import create_feedback_record


def build_trace_feedback_record(
    replay_summary: dict,
    source_id: str,
) -> dict | None:
    if not source_id.strip():
        raise ValueError("source_id must not be empty")

    issue_tags = infer_trace_feedback_tags(replay_summary)

    if not issue_tags:
        return None

    rating = infer_trace_feedback_rating(issue_tags)
    comment = build_trace_feedback_comment(
        replay_summary=replay_summary,
        issue_tags=issue_tags,
    )

    return create_feedback_record(
        source_type="trace_replay",
        source_id=source_id,
        rating=rating,
        comment=comment,
        tags=[
            "trace_replay",
            "needs_benchmark",
            *issue_tags,
        ],
        metadata={
            "record_count": replay_summary.get("record_count", 0),
            "failed_record_count": replay_summary.get(
                "failed_record_count",
                0,
            ),
            "total_tool_call_count": replay_summary.get(
                "total_tool_call_count",
                0,
            ),
            "total_failed_tool_call_count": replay_summary.get(
                "total_failed_tool_call_count",
                0,
            ),
            "total_duration_ms": replay_summary.get("total_duration_ms", 0.0),
            "by_source_type": replay_summary.get("by_source_type", {}),
            "by_tool": replay_summary.get("by_tool", {}),
        },
    )


def infer_trace_feedback_tags(
    replay_summary: dict,
) -> list[str]:
    tags = []

    if replay_summary.get("record_count", 0) == 0:
        tags.append("empty_trace")

    if replay_summary.get("failed_record_count", 0) > 0:
        tags.append("failed_trace_records")

    if replay_summary.get("total_failed_tool_call_count", 0) > 0:
        tags.append("failed_tool_calls")

    if replay_summary.get("total_tool_call_count", 0) == 0:
        tags.append("no_tool_calls")

    return tags


def infer_trace_feedback_rating(
    issue_tags: list[str],
) -> int:
    severe_tags = {
        "failed_tool_calls",
        "failed_trace_records",
    }

    if severe_tags & set(issue_tags):
        return 1

    return 2


def build_trace_feedback_comment(
    replay_summary: dict,
    issue_tags: list[str],
) -> str:
    return (
        "Trace replay detected issues: "
        f"{', '.join(issue_tags)}. "
        f"records={replay_summary.get('record_count', 0)}, "
        f"failed_records={replay_summary.get('failed_record_count', 0)}, "
        "failed_tool_calls="
        f"{replay_summary.get('total_failed_tool_call_count', 0)}."
    )
