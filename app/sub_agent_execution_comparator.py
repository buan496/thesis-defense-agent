import json


def parse_result_text(result_text: str) -> dict:
    try:
        data = json.loads(result_text)
    except json.JSONDecodeError:
        return {
            "json_valid": False,
            "keys": [],
            "error_type": None,
        }

    if isinstance(data, dict):
        return {
            "json_valid": True,
            "keys": sorted(data.keys()),
            "error_type": data.get("error_type"),
        }

    return {
        "json_valid": True,
        "keys": [],
        "error_type": None,
    }


def normalize_sub_agent_execution_record(record: dict) -> dict:
    execution = record["execution"]
    plan = execution["plan"]
    parsed_result = parse_result_text(execution["result_text"])

    return {
        "sub_agent_name": execution["sub_agent_name"],
        "tool_name": execution["tool_name"],
        "tool_arguments": plan["tool_arguments"],
        "success": execution["success"],
        "duration_ms": execution["duration_ms"],
        "result_json_valid": parsed_result["json_valid"],
        "result_keys": parsed_result["keys"],
        "error_type": parsed_result["error_type"],
    }


def build_sub_agent_execution_record_key(record: dict) -> str:
    normalized = normalize_sub_agent_execution_record(record)
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


def index_sub_agent_execution_records(
    records: list[dict],
) -> dict[str, dict]:
    indexed = {}

    for record in records:
        key = build_sub_agent_execution_record_key(record)
        indexed[key] = record

    return indexed


def compare_sub_agent_execution_records(
    baseline_records: list[dict],
    candidate_records: list[dict],
    max_duration_ratio: float = 2.0,
) -> dict:
    if max_duration_ratio <= 0:
        raise ValueError("max_duration_ratio must be greater than 0")

    baseline_index = index_sub_agent_execution_records(baseline_records)
    candidate_index = index_sub_agent_execution_records(candidate_records)

    baseline_keys = set(baseline_index)
    candidate_keys = set(candidate_index)

    added_keys = sorted(candidate_keys - baseline_keys)
    removed_keys = sorted(baseline_keys - candidate_keys)
    common_keys = sorted(baseline_keys & candidate_keys)

    changed = []
    duration_regressions = []

    for key in common_keys:
        baseline = normalize_sub_agent_execution_record(
            baseline_index[key]
        )
        candidate = normalize_sub_agent_execution_record(
            candidate_index[key]
        )

        field_changes = {}

        for field in [
            "success",
            "result_json_valid",
            "result_keys",
            "error_type",
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

        baseline_duration = baseline["duration_ms"]
        candidate_duration = candidate["duration_ms"]

        if (
            baseline_duration > 0
            and candidate_duration
            > baseline_duration * max_duration_ratio
        ):
            duration_regressions.append(
                {
                    "key": key,
                    "baseline_duration_ms": baseline_duration,
                    "candidate_duration_ms": candidate_duration,
                    "ratio": round(
                        candidate_duration / baseline_duration,
                        4,
                    ),
                }
            )

    return {
        "baseline_count": len(baseline_records),
        "candidate_count": len(candidate_records),
        "added_count": len(added_keys),
        "removed_count": len(removed_keys),
        "changed_count": len(changed),
        "duration_regression_count": len(duration_regressions),
        "stable_count": len(common_keys)
        - len(changed)
        - len(duration_regressions),
        "added": [
            normalize_sub_agent_execution_record(candidate_index[key])
            for key in added_keys
        ],
        "removed": [
            normalize_sub_agent_execution_record(baseline_index[key])
            for key in removed_keys
        ],
        "changed": changed,
        "duration_regressions": duration_regressions,
        "passed": (
            len(added_keys) == 0
            and len(removed_keys) == 0
            and len(changed) == 0
            and len(duration_regressions) == 0
        ),
    }
