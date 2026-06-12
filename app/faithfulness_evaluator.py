import json
from collections.abc import Callable

from app.llm import chat_with_llm
from app.agent_models import AgentResult,ToolTrace

def build_faithfulness_prompt(
    question: str,
    answer: str,
    evidence: str,
) -> str:
    return f"""
你是论文回答忠实度评估器。

请判断回答是否完全受到检索证据支持。

评估规则：
1. 不允许使用证据中不存在的事实。
2. 不允许改变证据的原意。
3. 不允许夸大实验结论。
4. 不允许混淆“已经完成”和“未来计划”。
5. Faithfulness 只评估回答已经陈述的内容是否有证据支持。
6. 回答遗漏证据中的部分信息属于完整性问题，不属于忠实度错误。
7. 如果回答只陈述了部分受支持事实，且没有使用“仅、只有、全部”等排他性表达，应判定为忠实。
8. 只有当回答声称内容完整或唯一，但遗漏关键事实时，才视为改变证据原意。
9. 只输出 JSON，不要输出 Markdown。

JSON 格式：
{{
    "score": 0.0,
    "passed": false,
    "reason": "判断原因",
    "unsupported_claims": [],
    "contradictions": []
}}

用户问题：
{question}

最终回答：
{answer}

检索证据：
{evidence}
""".strip()


def evaluate_faithfulness(
    question: str,
    answer: str,
    evidence: str,
    llm_fn: Callable[[str], str] = chat_with_llm,
) -> dict:
    prompt = build_faithfulness_prompt(
        question=question,
        answer=answer,
        evidence=evidence,
    )

    raw_output = llm_fn(prompt)
    clean_output = _extract_json_object(raw_output)

    try:
        result = json.loads(clean_output)
    except json.JSONDecodeError as error:
        raise ValueError("Faithfulness Judge 返回的不是合法 JSON") from error

    required_fields = {
        "score",
        "passed",
        "reason",
        "unsupported_claims",
        "contradictions",
    }

    missing_fields = required_fields - result.keys()

    if missing_fields:
        raise ValueError(
            f"Faithfulness 结果缺少字段：{sorted(missing_fields)}"
        )

    if not isinstance(result["score"], (int, float)):
        raise ValueError("score 必须是数字")

    if not 0 <= result["score"] <= 1:
        raise ValueError("score 必须在 0 到 1 之间")

    if not isinstance(result["passed"], bool):
        raise ValueError("passed 必须是布尔值")

    if not isinstance(result["reason"], str):
        raise ValueError("reason 必须是字符串")

    if not isinstance(result["unsupported_claims"], list):
        raise ValueError("unsupported_claims 必须是列表")

    if not isinstance(result["contradictions"], list):
        raise ValueError("contradictions 必须是列表")

    return result


def _extract_json_object(text: str) -> str:
    text = text.strip()

    if text.startswith("```json"):
        text = text.removeprefix("```json")
        text = text.removesuffix("```")
        text = text.strip()
    elif text.startswith("```"):
        text = text.removeprefix("```")
        text = text.removesuffix("```")
        text = text.strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return text

    return text[start:end + 1]


def extract_search_evidence(
    tool_traces: list[ToolTrace],
) -> str:
    evidence_parts = []

    for trace in tool_traces:
        if trace.tool_name != "search_thesis":
            continue

        if not trace.success:
            continue

        if not trace.result.strip():
            continue

        evidence_parts.append(trace.result)

    return "\n\n---\n\n".join(evidence_parts)

def evaluate_agent_faithfulness(
        question: str,
        agent_result: AgentResult,
        llm_fn: Callable[[str], str] = chat_with_llm,
    ) -> dict:
    evidence = extract_search_evidence(
        agent_result.tool_traces
    )

    if not evidence:
        return {
            "evaluated": False,
            "score": 0.0,
            "passed": False,
            "reason": "没有成功的 search_thesis 结果可作为证据",
            "unsupported_claims": [],
            "contradictions": [],
            "evidence": "",
        }

    result = evaluate_faithfulness(
        question=question,
        answer=agent_result.final_output,
        evidence=evidence,
        llm_fn=llm_fn,
    )

    return {
        "evaluated": True,
        **result,
        "evidence": evidence,
    }
