import json


def normalize_sub_agent_plan_record(record: dict) -> dict:
    plan = record["plan"]

    return {
        "sub_agent_name": plan["sub_agent_name"],
        "role": plan["role"],
        "tool_name": plan["tool_name"],
        "tool_arguments": plan["tool_arguments"],
        "expected_output_fields": plan["expected_output_fields"],
        "max_steps": plan["max_steps"],
        "status": plan["status"],
    }


def build_sub_agent_plan_record_key(record: dict) -> str:
    normalized = normalize_sub_agent_plan_record(record)
    identity = {
        "sub_agent_name": normalized["sub_agent_name"],
        "tool_name": normalized["tool_name"],
        "tool_arguments": normalized["tool_arguments"],
    }

    return json.dumps(
        identity,
        ensure_ascii=False,
        sort_keys=True,
    )


def index_sub_agent_plan_records(records: list[dict]) -> dict[str, dict]:
    indexed = {}

    for record in records:
        key = build_sub_agent_plan_record_key(record)
        indexed[key] = record

    return indexed


def compare_sub_agent_plan_records(
    baseline_records: list[dict],
    candidate_records: list[dict],
) -> dict:
    baseline_index = index_sub_agent_plan_records(baseline_records)
    candidate_index = index_sub_agent_plan_records(candidate_records)

    baseline_keys = set(baseline_index)
    candidate_keys = set(candidate_index)

    added_keys = sorted(candidate_keys - baseline_keys)
    removed_keys = sorted(baseline_keys - candidate_keys)
    common_keys = sorted(baseline_keys & candidate_keys)

    changed = []

    for key in common_keys:
        baseline = normalize_sub_agent_plan_record(baseline_index[key])
        candidate = normalize_sub_agent_plan_record(candidate_index[key])

        field_changes = {}

        for field in [
            "role",
            "expected_output_fields",
            "max_steps",
            "status",
        ]:
            if baseline[field] != candidate[field]:
                field_changes[field] = {
                    "baseline": baseline[field],
                    "candidate": candidate[field],
                }

        if field_changes:
            changed.append(
                {
                    "key": key,
                    "changes": field_changes,
                }
            )

    return {
        "baseline_count": len(baseline_records),
        "candidate_count": len(candidate_records),
        "added_count": len(added_keys),
        "removed_count": len(removed_keys),
        "changed_count": len(changed),
        "stable_count": len(common_keys) - len(changed),
        "added": [
            normalize_sub_agent_plan_record(candidate_index[key])
            for key in added_keys
        ],
        "removed": [
            normalize_sub_agent_plan_record(baseline_index[key])
            for key in removed_keys
        ],
        "changed": changed,
        "passed": (
            len(added_keys) == 0
            and len(removed_keys) == 0
            and len(changed) == 0
        ),
    }
