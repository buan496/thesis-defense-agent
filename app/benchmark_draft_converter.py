import json
from pathlib import Path

from app.benchmark_draft_validator import validate_benchmark_draft


BENCHMARK_OUTPUT_FILENAMES = {
    "rag_retrieval": "rag_benchmark_draft.json",
    "faithfulness": "faithfulness_benchmark_draft.json",
    "agent_routing": "agent_routing_benchmark_draft.json",
    "manual": "manual_benchmark_draft.json",
}


def convert_benchmark_draft_to_entries(
    draft: dict,
) -> dict[str, list[dict]]:
    validation = validate_benchmark_draft(draft)

    if not validation["passed"]:
        raise ValueError("benchmark draft validation failed")

    entries_by_type = {
        "rag_retrieval": [],
        "faithfulness": [],
        "agent_routing": [],
        "manual": [],
    }

    for item in draft.get("items", []):
        benchmark_type = item["benchmark_type"]
        entries_by_type[benchmark_type].append(
            convert_benchmark_draft_item_to_entry(item)
        )

    return entries_by_type


def convert_benchmark_draft_item_to_entry(
    item: dict,
) -> dict:
    benchmark_type = item["benchmark_type"]
    draft_fields = item["draft_fields"]

    if benchmark_type == "rag_retrieval":
        return {
            "query": draft_fields["query"],
            "expected_keywords": draft_fields["expected_keywords"],
        }

    if benchmark_type == "faithfulness":
        return {
            "name": item.get("draft_id", ""),
            "question": draft_fields["question"],
            "evidence": draft_fields["evidence"],
            "answer": draft_fields["answer"],
            "expected_passed": draft_fields["expected_passed"],
        }

    if benchmark_type == "agent_routing":
        return {
            "user_message": draft_fields["user_message"],
            "expected_tools": draft_fields["expected_tools"],
            "argument_rules": build_agent_argument_rules(
                draft_fields["expected_arguments"]
            ),
            "completion_rules": {
                "non_empty": True,
                "required_keywords": (
                    draft_fields["expected_answer_contains"]
                ),
            },
        }

    return {
        "notes": draft_fields["notes"],
        "source_candidate_id": item.get("source_candidate_id"),
    }


def build_agent_argument_rules(
    expected_arguments: dict,
) -> list[dict]:
    argument_rules = []

    for tool_name, rule in expected_arguments.items():
        if isinstance(rule, dict):
            argument_rule = {
                "tool_name": tool_name,
                **rule,
            }
        else:
            argument_rule = {
                "tool_name": tool_name,
                "expected_value": rule,
            }

        argument_rules.append(argument_rule)

    return argument_rules


def export_validated_benchmark_draft(
    draft: dict,
    output_directory: str,
) -> dict:
    entries_by_type = convert_benchmark_draft_to_entries(draft)
    output_path = Path(output_directory)
    output_path.mkdir(parents=True, exist_ok=True)
    files = {}

    for benchmark_type, entries in entries_by_type.items():
        if not entries:
            continue

        file_path = output_path / BENCHMARK_OUTPUT_FILENAMES[benchmark_type]
        file_path.write_text(
            json.dumps(entries, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        files[benchmark_type] = str(file_path)

    return {
        "output_directory": str(output_path),
        "counts": {
            benchmark_type: len(entries)
            for benchmark_type, entries in entries_by_type.items()
        },
        "files": files,
    }
