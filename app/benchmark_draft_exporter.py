import json
from datetime import datetime
from pathlib import Path


def build_benchmark_draft_item(
    candidate: dict,
) -> dict:
    return {
        "draft_id": f"draft-{candidate.get('candidate_id', '')}",
        "source_candidate_id": candidate.get("candidate_id"),
        "source_feedback_id": candidate.get("source_feedback_id"),
        "source_type": candidate.get("source_type"),
        "source_id": candidate.get("source_id"),
        "comment": candidate.get("comment"),
        "tags": candidate.get("tags", []),
        "metadata": candidate.get("metadata", {}),
        "review": candidate.get("review", {}),
        "benchmark_type": infer_benchmark_type(candidate),
        "draft_fields": build_empty_draft_fields(candidate),
    }


def infer_benchmark_type(
    candidate: dict,
) -> str:
    tags = set(candidate.get("tags", []))
    source_type = candidate.get("source_type", "")

    if "faithfulness" in tags:
        return "faithfulness"

    if "routing_error" in tags or source_type == "agent_trace":
        return "agent_routing"

    if "rag" in tags:
        return "rag_retrieval"

    return "manual"


def build_empty_draft_fields(
    candidate: dict,
) -> dict:
    benchmark_type = infer_benchmark_type(candidate)

    if benchmark_type == "rag_retrieval":
        return {
            "query": "",
            "expected_keywords": [],
        }

    if benchmark_type == "faithfulness":
        return {
            "question": "",
            "evidence": "",
            "answer": "",
            "expected_passed": None,
        }

    if benchmark_type == "agent_routing":
        return {
            "user_message": "",
            "expected_tools": [],
            "expected_arguments": {},
            "expected_answer_contains": [],
        }

    return {
        "notes": "",
    }


def export_accepted_candidates_to_benchmark_draft(
    candidate_report: dict,
    output_file_path: str,
) -> dict:
    accepted_candidates = [
        candidate
        for candidate in candidate_report.get("candidates", [])
        if candidate.get("status") == "accepted"
    ]

    draft_items = [
        build_benchmark_draft_item(candidate)
        for candidate in accepted_candidates
    ]

    output = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": "accepted_benchmark_candidates",
        "count": len(draft_items),
        "items": draft_items,
    }

    path = Path(output_file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return output


def build_default_benchmark_draft_output_path(
    directory: str,
) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    return str(Path(directory) / f"benchmark_draft_{timestamp}.json")
