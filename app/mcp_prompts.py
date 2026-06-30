from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class McpPromptArgument:
    name: str
    description: str
    required: bool = False


@dataclass(frozen=True)
class McpPromptSpec:
    name: str
    description: str
    arguments: tuple[McpPromptArgument, ...]


PROMPT_SPECS = {
    "defense_question_prompt": McpPromptSpec(
        name="defense_question_prompt",
        description="Generate thesis defense questions from supplied thesis context.",
        arguments=(
            McpPromptArgument(
                name="thesis_context",
                description="Retrieved thesis context used to ground the questions.",
                required=True,
            ),
        ),
    ),
    "answer_evaluation_prompt": McpPromptSpec(
        name="answer_evaluation_prompt",
        description="Evaluate a student answer without fabricating unsupported facts.",
        arguments=(
            McpPromptArgument(
                name="question",
                description="Original defense question.",
                required=True,
            ),
            McpPromptArgument(
                name="student_answer",
                description="Student answer to evaluate.",
                required=True,
            ),
        ),
    ),
    "follow_up_prompt": McpPromptSpec(
        name="follow_up_prompt",
        description="Generate one focused follow-up question.",
        arguments=(
            McpPromptArgument(
                name="question",
                description="Original defense question.",
                required=True,
            ),
            McpPromptArgument(
                name="student_answer",
                description="Student answer.",
                required=True,
            ),
            McpPromptArgument(
                name="evaluation",
                description="Optional answer evaluation feedback.",
                required=False,
            ),
        ),
    ),
}


def list_mcp_prompt_schemas() -> list[dict[str, Any]]:
    return [
        {
            "name": prompt.name,
            "description": prompt.description,
            "arguments": [
                {
                    "name": argument.name,
                    "description": argument.description,
                    "required": argument.required,
                }
                for argument in prompt.arguments
            ],
        }
        for prompt in PROMPT_SPECS.values()
    ]


def get_mcp_prompt(
    name: str,
    arguments: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if name not in PROMPT_SPECS:
        raise ValueError(f"unknown prompt name: {name}")

    prompt = PROMPT_SPECS[name]
    prompt_arguments = arguments or {}
    _validate_prompt_arguments(prompt, prompt_arguments)
    text = _render_prompt(name, prompt_arguments)

    return {
        "description": prompt.description,
        "messages": [
            {
                "role": "user",
                "content": {
                    "type": "text",
                    "text": text,
                },
            }
        ],
    }


def _validate_prompt_arguments(
    prompt: McpPromptSpec,
    arguments: dict[str, Any],
) -> None:
    for argument in prompt.arguments:
        if argument.required and not arguments.get(argument.name):
            raise ValueError(f"missing required prompt argument: {argument.name}")


def _render_prompt(name: str, arguments: dict[str, Any]) -> str:
    if name == "defense_question_prompt":
        return f"""
请根据下面的论文片段生成 5 个中文论文答辩问题。

要求：
1. 问题必须基于论文片段内容，不要引入片段外的信息。
2. 问题要像真实答辩老师会问的问题。
3. 问题应覆盖系统架构、方法设计、实验验证、局限性、实现细节等角度。
4. 只输出 JSON，不要输出 Markdown。

论文片段：
{arguments["thesis_context"]}
""".strip()

    if name == "answer_evaluation_prompt":
        return f"""
请根据下面的问题和答案，评估答案的质量。

重要限制：
1. 严禁编造实验数据、专家人数、用户人数、准确率、百分比、评分结果。
2. 如果学生回答中没有提供实验数据，只能说“可以补充某类实验设计”，不能虚构实验结果。
3. 参考回答必须基于学生已经提供的信息。
4. 对于没有数据支撑的内容，要使用“可以从……角度设计评估”，不能写成“已经完成……实验”。

问题：{arguments["question"]}
答案：{arguments["student_answer"]}
""".strip()

    if name == "follow_up_prompt":
        evaluation = arguments.get("evaluation", "")
        evaluation_text = f"\n评价反馈：{evaluation}" if evaluation else ""
        return f"""
请根据下面的问题和答案，生成 1 个有针对性的中文追问。
追问要聚焦回答中的模糊、不充分或值得深入的地方。
不要评价学生回答，只输出追问问题。

问题：{arguments["question"]}
答案：{arguments["student_answer"]}{evaluation_text}
""".strip()

    raise ValueError(f"unknown prompt name: {name}")
