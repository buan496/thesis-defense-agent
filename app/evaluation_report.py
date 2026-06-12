import json
from datetime import datetime
from pathlib import Path
from typing import Any


def create_evaluation_report(
    evaluation_type: str,
    model: str,
    config: dict[str, Any],
    result: dict,
    evaluated_at: str | None = None,
) -> dict:
    return {
        "metadata": {
            "evaluation_type": evaluation_type,
            "evaluated_at": (
                evaluated_at
                or datetime.now().isoformat(timespec="seconds")
            ),
            "judge_model": model,
            "config": config,
        },
        **result,
    }


def build_timestamped_report_path(
    prefix: str,
    report_directory: str = "data/reports",
    timestamp: str | None = None,
) -> Path:
    report_timestamp = (
        timestamp
        or datetime.now().strftime("%Y-%m-%d-%H%M%S")
    )
    return Path(report_directory) / (
        f"{prefix}_{report_timestamp}.json"
    )


def save_evaluation_report(
    report: dict,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path
