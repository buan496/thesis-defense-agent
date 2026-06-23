import json
from datetime import datetime
from pathlib import Path


VALID_REVIEW_STATUSES = {"accepted", "rejected"}


def load_candidate_report(file_path: str) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"候选集文件不存在：{file_path}")

    return json.loads(path.read_text(encoding="utf-8"))


def save_candidate_report(
    file_path: str,
    candidate_report: dict,
) -> str:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(candidate_report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return str(path)


def review_benchmark_candidate(
    candidate_report: dict,
    candidate_id: str,
    status: str,
    reviewer: str,
    reason: str,
) -> dict:
    if status not in VALID_REVIEW_STATUSES:
        raise ValueError("status must be accepted or rejected")

    if not reviewer.strip():
        raise ValueError("reviewer must not be empty")

    if not reason.strip():
        raise ValueError("reason must not be empty")

    candidate = find_candidate(candidate_report, candidate_id)

    if candidate is None:
        raise ValueError(f"candidate not found: {candidate_id}")

    candidate["status"] = status
    candidate["review"] = {
        "reviewer": reviewer,
        "reason": reason,
        "reviewed_at": datetime.now().isoformat(timespec="seconds"),
    }

    return candidate


def find_candidate(
    candidate_report: dict,
    candidate_id: str,
) -> dict | None:
    for candidate in candidate_report.get("candidates", []):
        if candidate.get("candidate_id") == candidate_id:
            return candidate

    return None


def summarize_candidate_review_status(
    candidate_report: dict,
) -> dict:
    status_counts = {}

    for candidate in candidate_report.get("candidates", []):
        status = candidate.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    return {
        "count": len(candidate_report.get("candidates", [])),
        "status_counts": status_counts,
    }
