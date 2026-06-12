import json
from pathlib import Path
from typing import Any


SUPPORTED_EVALUATION_TYPES = {
    "faithfulness",
    "faithfulness_stability",
}
FLOAT_COMPARISON_EPSILON = 1e-12


def load_evaluation_report(file_path: str | Path) -> dict:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"评估报告不存在：{file_path}")

    with path.open(encoding="utf-8-sig") as file:
        report = json.load(file)

    if not isinstance(report, dict):
        raise ValueError("评估报告必须是 JSON 对象")

    metadata = report.get("metadata")

    if not isinstance(metadata, dict):
        raise ValueError("评估报告缺少 metadata")

    evaluation_type = metadata.get("evaluation_type")

    if evaluation_type not in SUPPORTED_EVALUATION_TYPES:
        raise ValueError(
            f"不支持的评估报告类型：{evaluation_type}"
        )

    if not isinstance(report.get("results"), list):
        raise ValueError("评估报告缺少 results 列表")

    return report


def compare_evaluation_report_files(
    baseline_path: str | Path,
    current_path: str | Path,
    metric_tolerance: float = 0.0,
    stability_tolerance: float = 0.0,
) -> dict:
    baseline = load_evaluation_report(baseline_path)
    current = load_evaluation_report(current_path)

    comparison = compare_evaluation_reports(
        baseline=baseline,
        current=current,
        metric_tolerance=metric_tolerance,
        stability_tolerance=stability_tolerance,
    )
    comparison["baseline_path"] = str(baseline_path)
    comparison["current_path"] = str(current_path)
    return comparison


def compare_evaluation_reports(
    baseline: dict,
    current: dict,
    metric_tolerance: float = 0.0,
    stability_tolerance: float = 0.0,
) -> dict:
    _validate_tolerance("metric_tolerance", metric_tolerance)
    _validate_tolerance(
        "stability_tolerance",
        stability_tolerance,
    )

    baseline_metadata = baseline["metadata"]
    current_metadata = current["metadata"]
    evaluation_type = baseline_metadata["evaluation_type"]

    if current_metadata["evaluation_type"] != evaluation_type:
        raise ValueError("baseline 和 current 的评估类型必须一致")

    metadata_changes = _compare_metadata(
        baseline_metadata,
        current_metadata,
    )

    if evaluation_type == "faithfulness":
        metric_names = ["accuracy"]
        prediction_field = "actual_passed"
        correctness_field = "prediction_correct"
    else:
        metric_names = [
            "average_agreement",
            "unanimous_rate",
            "majority_accuracy",
        ]
        prediction_field = "majority_prediction"
        correctness_field = "majority_correct"

    metric_changes = _compare_metrics(
        baseline=baseline,
        current=current,
        metric_names=metric_names,
        tolerance=metric_tolerance,
    )
    case_comparison = _compare_cases(
        baseline_results=baseline["results"],
        current_results=current["results"],
        prediction_field=prediction_field,
        correctness_field=correctness_field,
        include_stability=(
            evaluation_type == "faithfulness_stability"
        ),
        stability_tolerance=stability_tolerance,
    )

    metric_regressions = [
        item for item in metric_changes
        if item["regressed"]
    ]
    prediction_regressions = [
        item for item in case_comparison["prediction_flips"]
        if item["regression"]
    ]
    stability_regressions = case_comparison[
        "stability_regressions"
    ]

    regression_count = (
        len(metric_regressions)
        + len(prediction_regressions)
        + len(stability_regressions)
    )

    return {
        "evaluation_type": evaluation_type,
        "tolerances": {
            "metric_tolerance": metric_tolerance,
            "stability_tolerance": stability_tolerance,
        },
        "baseline_metadata": baseline_metadata,
        "current_metadata": current_metadata,
        "metadata_changes": metadata_changes,
        "metric_changes": metric_changes,
        "prediction_flips": case_comparison[
            "prediction_flips"
        ],
        "case_score_changes": case_comparison[
            "case_score_changes"
        ],
        "stability_regressions": stability_regressions,
        "added_cases": case_comparison["added_cases"],
        "removed_cases": case_comparison["removed_cases"],
        "regression_count": regression_count,
        "has_regression": regression_count > 0,
    }


def _compare_metadata(
    baseline_metadata: dict,
    current_metadata: dict,
) -> list[dict[str, Any]]:
    changes = []

    for field in ("judge_model", "config"):
        baseline_value = baseline_metadata.get(field)
        current_value = current_metadata.get(field)

        if baseline_value != current_value:
            changes.append(
                {
                    "field": field,
                    "baseline": baseline_value,
                    "current": current_value,
                }
            )

    return changes


def _compare_metrics(
    baseline: dict,
    current: dict,
    metric_names: list[str],
    tolerance: float,
) -> list[dict]:
    changes = []

    for name in metric_names:
        baseline_value = _require_number(baseline, name)
        current_value = _require_number(current, name)
        delta = current_value - baseline_value
        drop = baseline_value - current_value

        changes.append(
            {
                "name": name,
                "baseline": baseline_value,
                "current": current_value,
                "delta": delta,
                "drop": max(drop, 0.0),
                "tolerance": tolerance,
                "regressed": (
                    drop - tolerance
                    > FLOAT_COMPARISON_EPSILON
                ),
                "improved": delta > 0,
            }
        )

    return changes


def _compare_cases(
    baseline_results: list[dict],
    current_results: list[dict],
    prediction_field: str,
    correctness_field: str,
    include_stability: bool,
    stability_tolerance: float,
) -> dict:
    baseline_by_name = _index_results(baseline_results)
    current_by_name = _index_results(current_results)
    shared_names = (
        baseline_by_name.keys() & current_by_name.keys()
    )

    prediction_flips = []
    case_score_changes = []
    stability_regressions = []

    for name in sorted(shared_names):
        baseline_item = baseline_by_name[name]
        current_item = current_by_name[name]
        baseline_prediction = baseline_item[prediction_field]
        current_prediction = current_item[prediction_field]
        baseline_correct = baseline_item[correctness_field]
        current_correct = current_item[correctness_field]

        if baseline_prediction != current_prediction:
            prediction_flips.append(
                {
                    "name": name,
                    "baseline_prediction": baseline_prediction,
                    "current_prediction": current_prediction,
                    "baseline_correct": baseline_correct,
                    "current_correct": current_correct,
                    "regression": (
                        baseline_correct and not current_correct
                    ),
                    "improvement": (
                        not baseline_correct and current_correct
                    ),
                }
            )

        if "score" in baseline_item and "score" in current_item:
            baseline_score = _require_number(
                baseline_item,
                "score",
            )
            current_score = _require_number(
                current_item,
                "score",
            )
            delta = current_score - baseline_score

            if delta != 0:
                case_score_changes.append(
                    {
                        "name": name,
                        "baseline": baseline_score,
                        "current": current_score,
                        "delta": delta,
                    }
                )

        if include_stability:
            stability_regressions.extend(
                _find_stability_regressions(
                    name=name,
                    baseline_item=baseline_item,
                    current_item=current_item,
                    tolerance=stability_tolerance,
                )
            )

    return {
        "prediction_flips": prediction_flips,
        "case_score_changes": case_score_changes,
        "stability_regressions": stability_regressions,
        "added_cases": sorted(
            current_by_name.keys() - baseline_by_name.keys()
        ),
        "removed_cases": sorted(
            baseline_by_name.keys() - current_by_name.keys()
        ),
    }


def _find_stability_regressions(
    name: str,
    baseline_item: dict,
    current_item: dict,
    tolerance: float,
) -> list[dict]:
    regressions = []

    baseline_agreement = _require_number(
        baseline_item,
        "agreement_score",
    )
    current_agreement = _require_number(
        current_item,
        "agreement_score",
    )
    agreement_drop = baseline_agreement - current_agreement
    agreement_regressed = (
        agreement_drop - tolerance
        > FLOAT_COMPARISON_EPSILON
    )

    if agreement_regressed:
        regressions.append(
            {
                "name": name,
                "metric": "agreement_score",
                "baseline": baseline_agreement,
                "current": current_agreement,
                "delta": current_agreement - baseline_agreement,
                "drop": agreement_drop,
                "tolerance": tolerance,
            }
        )

    if (
        baseline_item["unanimous"]
        and not current_item["unanimous"]
        and agreement_regressed
    ):
        regressions.append(
            {
                "name": name,
                "metric": "unanimous",
                "baseline": True,
                "current": False,
                "delta": None,
                "drop": agreement_drop,
                "tolerance": tolerance,
            }
        )

    return regressions


def _index_results(results: list[dict]) -> dict[str, dict]:
    indexed = {}

    for item in results:
        name = item.get("name")

        if not isinstance(name, str) or not name:
            raise ValueError("每个评估案例必须包含非空 name")

        if name in indexed:
            raise ValueError(f"评估案例名称重复：{name}")

        indexed[name] = item

    return indexed


def _require_number(data: dict, field: str) -> float:
    value = data.get(field)

    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"评估报告字段必须是数字：{field}")

    return float(value)


def _validate_tolerance(name: str, value: float) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool):
        raise ValueError(f"{name} 必须是数字")

    if value < 0:
        raise ValueError(f"{name} 不能小于 0")


def render_evaluation_comparison_markdown(
    report: dict,
) -> str:
    status = "FAIL" if report["has_regression"] else "PASS"
    lines = [
        "# 评估回归对比报告",
        "",
        f"- 状态：**{status}**",
        f"- 评估类型：`{report['evaluation_type']}`",
        f"- 回归数量：`{report['regression_count']}`",
        (
            "- 总体指标容忍下降："
            f"`{report['tolerances']['metric_tolerance']}`"
        ),
        (
            "- 单案例稳定性容忍下降："
            f"`{report['tolerances']['stability_tolerance']}`"
        ),
        "",
        "## 总体指标",
        "",
        "| 指标 | Baseline | Current | Delta | 回归 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]

    for item in report["metric_changes"]:
        lines.append(
            f"| {item['name']} | {item['baseline']} | "
            f"{item['current']} | {item['delta']} | "
            f"{'是' if item['regressed'] else '否'} |"
        )

    lines.extend(
        _render_markdown_items(
            title="预测翻转",
            items=report["prediction_flips"],
            formatter=lambda item: (
                f"- `{item['name']}`："
                f"`{item['baseline_prediction']}` → "
                f"`{item['current_prediction']}`，"
                f"回归：`{item['regression']}`"
            ),
        )
    )
    lines.extend(
        _render_markdown_items(
            title="稳定性退化",
            items=report["stability_regressions"],
            formatter=lambda item: (
                f"- `{item['name']}` / `{item['metric']}`："
                f"`{item['baseline']}` → `{item['current']}`"
            ),
        )
    )
    lines.extend(
        _render_markdown_items(
            title="元信息变化",
            items=report["metadata_changes"],
            formatter=lambda item: (
                f"- `{item['field']}`："
                f"`{item['baseline']}` → `{item['current']}`"
            ),
        )
    )
    lines.extend(
        [
            "",
            "## Benchmark 案例变化",
            "",
            (
                "- 新增："
                f"{_format_name_list(report['added_cases'])}"
            ),
            (
                "- 删除："
                f"{_format_name_list(report['removed_cases'])}"
            ),
            "",
        ]
    )

    return "\n".join(lines)


def save_evaluation_comparison_markdown(
    report: dict,
    output_path: str | Path,
) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        render_evaluation_comparison_markdown(report),
        encoding="utf-8",
    )
    return path


def _render_markdown_items(
    title: str,
    items: list[dict],
    formatter,
) -> list[str]:
    lines = ["", f"## {title}", ""]

    if not items:
        lines.append("- 无")
        return lines

    lines.extend(formatter(item) for item in items)
    return lines


def _format_name_list(names: list[str]) -> str:
    if not names:
        return "无"

    return "、".join(f"`{name}`" for name in names)
