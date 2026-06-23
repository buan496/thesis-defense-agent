import json
from datetime import datetime
from pathlib import Path


DEFAULT_CANDIDATE_TAGS = ["needs_benchmark"]


def should_export_feedback_record(
    feedback_record: dict,
    max_rating: int = 2,
    candidate_tags: list[str] | None = None,
) -> bool:
    tags = set(feedback_record.get("tags", []))
    candidate_tag_set = set(candidate_tags or DEFAULT_CANDIDATE_TAGS)
    rating = feedback_record.get("rating")

    if isinstance(rating, int) and rating <= max_rating:
        return True

    return bool(tags & candidate_tag_set)


def build_benchmark_candidate(
    feedback_record: dict,
) -> dict:
    feedback_id = feedback_record.get("id", "")

    return {
        "candidate_id": f"feedback-{feedback_id}",
        "status": "needs_review",
        "source_feedback_id": feedback_id,
        "source_type": feedback_record.get("source_type"),
        "source_id": feedback_record.get("source_id"),
        "rating": feedback_record.get("rating"),
        "comment": feedback_record.get("comment"),
        "tags": feedback_record.get("tags", []),
        "metadata": feedback_record.get("metadata", {}),
        "recommended_action": infer_recommended_action(feedback_record),
    }


def infer_recommended_action(
    feedback_record: dict,
) -> str:
    tags = set(feedback_record.get("tags", []))
    rating = feedback_record.get("rating")

    if "needs_benchmark" in tags:
        return "review_for_benchmark"

    if isinstance(rating, int) and rating <= 2:
        return "add_regression_case"

    return "manual_review"


def export_feedback_benchmark_candidates(
    feedback_records: list[dict],
    output_file_path: str,
    max_rating: int = 2,
    candidate_tags: list[str] | None = None,
) -> dict:
    candidates = [
        build_benchmark_candidate(record)
        for record in feedback_records
        if should_export_feedback_record(
            record,
            max_rating=max_rating,
            candidate_tags=candidate_tags,
        )
    ]

    output = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "feedback",
        "max_rating": max_rating,
        "candidate_tags": candidate_tags or DEFAULT_CANDIDATE_TAGS,
        "count": len(candidates),
        "candidates": candidates,
    }

    path = Path(output_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output


def build_default_candidate_output_path(
    directory: str,
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return str(
        Path(directory) / f"feedback_candidates_{timestamp}.json"
    )
