import json
from collections.abc import Callable
from typing import Any

from app.agent import run_agent
from app.agent_models import AgentResult
from app.faithfulness_evaluator import evaluate_agent_faithfulness


def parse_tool_arguments(arguments: str) -> dict:
    try:
        data = json.loads(arguments)
    except (json.JSONDecodeError, TypeError):
        return {}

    if not isinstance(data, dict):
        return {}

    return data


def _collect_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]

    if isinstance(value, dict):
        strings = []

        for nested_value in value.values():
            strings.extend(_collect_string_values(nested_value))

        return strings

    if isinstance(value, list):
        strings = []

        for nested_value in value:
            strings.extend(_collect_string_values(nested_value))

        return strings

    return []


def _contains_required_keyword(
    text: str,
    keyword: str | list[str],
) -> bool:
    if isinstance(keyword, list):
        return any(option in text for option in keyword)

    return keyword in text


def _uses_previous_tool_result(
    field_value: str,
    source_result: str,
    minimum_length: int,
) -> bool:
    try:
        parsed_result = json.loads(source_result)
    except json.JSONDecodeError:
        parsed_result = source_result

    source_strings = [
        "".join(text.split())
        for text in _collect_string_values(parsed_result)
        if len("".join(text.split())) >= minimum_length
    ]
    normalized_field_value = "".join(field_value.split())

    for source_text in source_strings:
        if (
            source_text in normalized_field_value
            or normalized_field_value in source_text
        ):
            return True

        for start in range(
            0,
            len(source_text) - minimum_length + 1,
            max(1, minimum_length // 4),
        ):
            source_fragment = source_text[
                start:start + minimum_length
            ]

            if source_fragment in normalized_field_value:
                return True

    return False


def evaluate_tool_arguments(
    tool_traces: list,
    argument_rules: list[dict],
) -> list[dict]:
    checks = []

    for index, rule in enumerate(argument_rules):
        expected_tool = rule["tool_name"]
        errors = []

        if index >= len(tool_traces):
            checks.append(
                {
                    "tool_name": expected_tool,
                    "arguments": {},
                    "passed": False,
                    "errors": ["缺少对应的工具调用"],
                }
            )
            continue

        trace = tool_traces[index]
        arguments = parse_tool_arguments(trace.arguments)

        try:
            raw_arguments = json.loads(trace.arguments)
            arguments_are_valid = isinstance(raw_arguments, dict)
        except (json.JSONDecodeError, TypeError):
            arguments_are_valid = False

        if trace.tool_name != expected_tool:
            errors.append(
                f"期望工具 {expected_tool}，实际为 {trace.tool_name}"
            )

        if not arguments_are_valid:
            errors.append("工具参数必须是合法的 JSON 对象")

        for field_name in rule.get("required_fields", []):
            field_value = arguments.get(field_name)

            if field_value is None or field_value == "":
                errors.append(f"缺少必填字段：{field_name}")

        argument_text = "\n".join(_collect_string_values(arguments))

        for keyword in rule.get("required_keywords", []):
            if not _contains_required_keyword(argument_text, keyword):
                label = (
                    "/".join(keyword)
                    if isinstance(keyword, list)
                    else keyword
                )
                errors.append(f"参数缺少关键词：{label}")

        for field_name, limits in rule.get(
            "integer_ranges",
            {},
        ).items():
            if field_name not in arguments:
                continue

            field_value = arguments[field_name]

            if not isinstance(field_value, int) or isinstance(
                field_value,
                bool,
            ):
                errors.append(f"{field_name} 必须是整数")
                continue

            minimum = limits.get("minimum")
            maximum = limits.get("maximum")

            if minimum is not None and field_value < minimum:
                errors.append(
                    f"{field_name} 不能小于 {minimum}"
                )

            if maximum is not None and field_value > maximum:
                errors.append(
                    f"{field_name} 不能大于 {maximum}"
                )

        context_rule = rule.get("context_from_tool")

        if context_rule is not None:
            field_name = context_rule.get("field", "context")
            source_tool = context_rule["tool_name"]
            minimum_length = context_rule.get("minimum_length", 20)
            field_value = arguments.get(field_name)
            source_trace = next(
                (
                    previous_trace
                    for previous_trace in reversed(tool_traces[:index])
                    if previous_trace.tool_name == source_tool
                    and previous_trace.success
                ),
                None,
            )

            if source_trace is None:
                errors.append(
                    f"找不到前置工具结果：{source_tool}"
                )
            elif not isinstance(field_value, str):
                errors.append(f"{field_name} 必须是字符串")
            elif not _uses_previous_tool_result(
                field_value=field_value,
                source_result=source_trace.result,
                minimum_length=minimum_length,
            ):
                errors.append(
                    f"{field_name} 未使用 {source_tool} 的检索结果"
                )

        checks.append(
            {
                "tool_name": expected_tool,
                "arguments": arguments,
                "passed": not errors,
                "errors": errors,
            }
        )

    return checks


def evaluate_task_completion(
    final_output: str,
    rules: dict,
) -> dict:
    errors = []
    output = final_output or ""
    question_count = output.count("？") + output.count("?")

    if rules.get("non_empty") and not output.strip():
        errors.append("最终回答不能为空")

    for keyword in rules.get("required_keywords", []):
        if not _contains_required_keyword(output, keyword):
            label = (
                "/".join(keyword)
                if isinstance(keyword, list)
                else keyword
            )
            errors.append(f"最终回答缺少关键词：{label}")

    minimum_question_count = rules.get("minimum_question_count")

    if (
        minimum_question_count is not None
        and question_count < minimum_question_count
    ):
        errors.append(
            "问题数量不足："
            f"期望至少 {minimum_question_count} 个，"
            f"实际 {question_count} 个"
        )

    return {
        "passed": not errors,
        "errors": errors,
        "question_count": question_count,
    }


def evaluate_groundedness(
    final_output: str,
    tool_traces: list,
    rules: dict,
) -> dict:
    required_claims = rules.get("required_claims", [])
    output = final_output or ""
    evidence_text = "\n".join(
        trace.result
        for trace in tool_traces
        if trace.tool_name == "search_thesis"
        and trace.success
    )
    errors = []
    claim_checks = []
    supported_claim_count = 0

    if required_claims and not evidence_text:
        errors.append(
            "没有成功的 search_thesis 结果可作为证据"
        )

    for claim_rule in required_claims:
        claim = claim_rule["claim"]
        answer_keywords = claim_rule.get(
            "answer_keywords",
            [claim],
        )
        evidence_keywords = claim_rule.get(
            "evidence_keywords",
            [claim],
        )
        claim_in_answer = all(
            _contains_required_keyword(output, keyword)
            for keyword in answer_keywords
        )
        missing_evidence_keywords = [
            (
                "/".join(keyword)
                if isinstance(keyword, list)
                else keyword
            )
            for keyword in evidence_keywords
            if not _contains_required_keyword(
                evidence_text,
                keyword,
            )
        ]
        evidence_found = not missing_evidence_keywords
        supported = claim_in_answer and evidence_found

        if supported:
            supported_claim_count += 1
        else:
            if not claim_in_answer:
                errors.append(
                    f"最终回答缺少待验证声明：{claim}"
                )

            if not evidence_found:
                errors.append(
                    "声明缺少检索证据："
                    f"{claim}；缺少={missing_evidence_keywords}"
                )

        claim_checks.append(
            {
                "claim": claim,
                "claim_in_answer": claim_in_answer,
                "evidence_found": evidence_found,
                "missing_evidence_keywords": (
                    missing_evidence_keywords
                ),
                "supported": supported,
            }
        )

    total_claims = len(required_claims)
    score = (
        supported_claim_count / total_claims
        if total_claims
        else 1.0
    )

    return {
        "passed": not errors,
        "score": score,
        "supported_claims": supported_claim_count,
        "total_claims": total_claims,
        "errors": errors,
        "claims": claim_checks,
    }


def evaluate_agent_routing(
    benchmark_path: str,
    agent_fn: Callable[[str], AgentResult] = run_agent,
    faithfulness_fn: Callable[
        [str, AgentResult],
        dict,
    ] = evaluate_agent_faithfulness,
) -> dict:
    with open(benchmark_path, encoding="utf-8") as file:
        benchmark = json.load(file)

    if not benchmark:
        raise ValueError("Agent 路由 benchmark 不能为空")

    results = []
    passed_count = 0
    routing_passed_count = 0
    argument_passed_count = 0
    argument_check_count = 0
    completion_passed_count = 0
    task_pipeline_passed_count = 0
    grounding_case_count = 0
    grounding_case_passed_count = 0
    grounded_claim_count = 0
    grounding_claim_count = 0
    grounded_pipeline_passed_count = 0
    faithfulness_case_count = 0
    faithfulness_passed_count = 0
    faithfulness_score_total = 0.0

    for item in benchmark:
        user_message = item["user_message"]
        expected_tools = item["expected_tools"]
        argument_rules = item.get("argument_rules", [])
        completion_rules = item.get("completion_rules", {})
        grounding_rules = item.get("grounding_rules", {})
        faithfulness_rules = item.get("faithfulness_rules", {})
        faithfulness_enabled = faithfulness_rules.get("enabled", False)
        agent_result = None

        try:
            agent_result = agent_fn(user_message)
            final_output = agent_result.final_output
            tool_traces = agent_result.tool_traces
            actual_tools = [
                trace.tool_name
                for trace in tool_traces
            ]
            argument_checks = evaluate_tool_arguments(
                tool_traces=tool_traces,
                argument_rules=argument_rules,
            )
            error = None
        except Exception as exception:
            final_output = ""
            tool_traces = []
            actual_tools = []
            argument_checks = evaluate_tool_arguments(
                tool_traces=tool_traces,
                argument_rules=argument_rules,
            )
            error = f"{type(exception).__name__}: {exception}"

        routing_passed = actual_tools == expected_tools
        arguments_passed = all(
            check["passed"]
            for check in argument_checks
        )
        completion_check = evaluate_task_completion(
            final_output=final_output,
            rules=completion_rules,
        )
        completion_passed = (
            completion_check["passed"]
            and error is None
        )
        grounding_check = evaluate_groundedness(
            final_output=final_output,
            tool_traces=tool_traces,
            rules=grounding_rules,
        )
        grounding_passed = (
            grounding_check["passed"]
            and error is None
        )
        faithfulness_check = {
            "evaluated": False,
            "score": 1.0,
            "passed": True,
            "reason": "该案例未启用 Faithfulness 评估",
            "unsupported_claims": [],
            "contradictions": [],
            "evidence": "",
        }
        faithfulness_passed = True

        if faithfulness_enabled:
            faithfulness_case_count += 1

            if agent_result is None or error is not None:
                faithfulness_check = {
                    "evaluated": False,
                    "score": 0.0,
                    "passed": False,
                    "reason": (
                        "Agent 执行失败，无法进行 Faithfulness 评估"
                    ),
                    "unsupported_claims": [],
                    "contradictions": [],
                    "evidence": "",
                }
            else:
                try:
                    faithfulness_check = faithfulness_fn(
                        user_message,
                        agent_result,
                    )
                except Exception as exception:
                    faithfulness_check = {
                        "evaluated": False,
                        "score": 0.0,
                        "passed": False,
                        "reason": (
                            "Faithfulness Judge 执行失败："
                            f"{type(exception).__name__}: {exception}"
                        ),
                        "unsupported_claims": [],
                        "contradictions": [],
                        "evidence": "",
                    }

            minimum_score = faithfulness_rules.get(
                "minimum_score",
                0.0,
            )
            faithfulness_passed = (
                faithfulness_check["evaluated"]
                and faithfulness_check["passed"]
                and faithfulness_check["score"] >= minimum_score
            )
            faithfulness_score_total += faithfulness_check["score"]

            if faithfulness_passed:
                faithfulness_passed_count += 1

        task_pipeline_passed = (
            routing_passed
            and arguments_passed
            and completion_passed
            and error is None
        )
        grounded_pipeline_passed = (
            task_pipeline_passed
            and grounding_passed
        )
        passed = (
            grounded_pipeline_passed
            and faithfulness_passed
        )

        if routing_passed:
            routing_passed_count += 1

        argument_check_count += len(argument_checks)
        argument_passed_count += sum(
            check["passed"]
            for check in argument_checks
        )

        if completion_passed:
            completion_passed_count += 1

        if task_pipeline_passed:
            task_pipeline_passed_count += 1

        if grounded_pipeline_passed:
            grounded_pipeline_passed_count += 1

        grounding_claim_count += grounding_check["total_claims"]
        grounded_claim_count += grounding_check["supported_claims"]

        if grounding_check["total_claims"]:
            grounding_case_count += 1

            if grounding_passed:
                grounding_case_passed_count += 1

        if passed:
            passed_count += 1

        results.append(
            {
                "user_message": user_message,
                "expected_tools": expected_tools,
                "actual_tools": actual_tools,
                "routing_passed": routing_passed,
                "argument_checks": argument_checks,
                "arguments_passed": arguments_passed,
                "completion_check": completion_check,
                "completion_passed": completion_passed,
                "grounding_check": grounding_check,
                "grounding_passed": grounding_passed,
                "task_pipeline_passed": task_pipeline_passed,
                "grounded_pipeline_passed": grounded_pipeline_passed,
                "faithfulness_check": faithfulness_check,
                "faithfulness_passed": faithfulness_passed,
                "final_output": final_output,
                "passed": passed,
                "error": error,
            }
        )

    total = len(results)
    argument_accuracy = (
        argument_passed_count / argument_check_count
        if argument_check_count
        else 1.0
    )
    groundedness_score = (
        grounded_claim_count / grounding_claim_count
        if grounding_claim_count
        else 1.0
    )
    grounded_task_rate = (
        grounding_case_passed_count / grounding_case_count
        if grounding_case_count
        else 1.0
    )
    faithfulness_score = (
        faithfulness_score_total / faithfulness_case_count
        if faithfulness_case_count
        else 1.0
    )
    faithfulness_pass_rate = (
        faithfulness_passed_count / faithfulness_case_count
        if faithfulness_case_count
        else 1.0
    )

    return {
        "benchmark_path": benchmark_path,
        "total": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "accuracy": passed_count / total,
        "routing_accuracy": routing_passed_count / total,
        "argument_checks": argument_check_count,
        "argument_checks_passed": argument_passed_count,
        "argument_accuracy": argument_accuracy,
        "completion_rate": completion_passed_count / total,
        "end_to_end_success_rate": (
            task_pipeline_passed_count / total
        ),
        "grounded_claims": grounded_claim_count,
        "grounding_claims": grounding_claim_count,
        "groundedness_score": groundedness_score,
        "grounding_cases": grounding_case_count,
        "grounded_task_rate": grounded_task_rate,
        "end_to_end_grounded_success_rate": (
            grounded_pipeline_passed_count / total
        ),
        "faithfulness_cases": faithfulness_case_count,
        "faithfulness_score": faithfulness_score,
        "faithfulness_pass_rate": faithfulness_pass_rate,
        "end_to_end_faithful_success_rate": passed_count / total,
        "results": results,
    }
