from dataclasses import asdict, dataclass

from app.tool_registry import REGISTERED_TOOLS


@dataclass(frozen=True)
class SubAgentSpec:
    name: str
    role: str
    description: str
    allowed_tools: list[str]
    input_fields: list[str]
    output_fields: list[str]
    max_steps: int

    def to_dict(self) -> dict:
        return asdict(self)


SUB_AGENT_SPECS: dict[str, SubAgentSpec] = {
    "retrieval_agent": SubAgentSpec(
        name="retrieval_agent",
        role="论文证据检索",
        description="根据用户问题检索论文证据，并返回来源片段。",
        allowed_tools=["search_thesis"],
        input_fields=["query"],
        output_fields=["evidence", "sources"],
        max_steps=2,
    ),
    "defense_question_agent": SubAgentSpec(
        name="defense_question_agent",
        role="答辩问题生成",
        description="基于论文证据生成中文论文答辩问题。",
        allowed_tools=["create_defense_questions"],
        input_fields=["retrieved_context"],
        output_fields=["questions"],
        max_steps=2,
    ),
    "answer_evaluation_agent": SubAgentSpec(
        name="answer_evaluation_agent",
        role="学生回答评价",
        description="根据答辩问题和学生回答生成评价与改进建议。",
        allowed_tools=["evaluate_student_answer"],
        input_fields=["question", "student_answer"],
        output_fields=["evaluation"],
        max_steps=2,
    ),
    "follow_up_agent": SubAgentSpec(
        name="follow_up_agent",
        role="答辩追问生成",
        description="根据原问题、学生回答和评价反馈生成追问。",
        allowed_tools=["generate_follow_up"],
        input_fields=["question", "student_answer"],
        output_fields=["follow_up_question"],
        max_steps=2,
    ),
    "training_record_agent": SubAgentSpec(
        name="training_record_agent",
        role="训练记录查询",
        description="根据 task_id 查询已经保存的答辩训练记录摘要。",
        allowed_tools=["query_training_record"],
        input_fields=["task_id"],
        output_fields=["training_record"],
        max_steps=1,
    ),
}


def validate_sub_agent_spec(
    spec: SubAgentSpec,
) -> None:
    if not spec.name.strip():
        raise ValueError("SubAgentSpec.name 不能为空")

    if not spec.role.strip():
        raise ValueError("SubAgentSpec.role 不能为空")

    if not spec.description.strip():
        raise ValueError("SubAgentSpec.description 不能为空")

    if not spec.allowed_tools:
        raise ValueError(f"{spec.name} 必须至少允许一个工具")

    if not spec.input_fields:
        raise ValueError(f"{spec.name} 必须至少声明一个输入字段")

    if not spec.output_fields:
        raise ValueError(f"{spec.name} 必须至少声明一个输出字段")

    if spec.max_steps <= 0:
        raise ValueError(f"{spec.name} 的 max_steps 必须大于 0")

    unknown_tools = [
        tool_name
        for tool_name in spec.allowed_tools
        if tool_name not in REGISTERED_TOOLS
    ]

    if unknown_tools:
        raise ValueError(
            f"{spec.name} 引用了未知工具：{', '.join(unknown_tools)}"
        )


def list_sub_agent_specs() -> list[SubAgentSpec]:
    specs = sorted(
        SUB_AGENT_SPECS.values(),
        key=lambda spec: spec.name,
    )

    for spec in specs:
        validate_sub_agent_spec(spec)

    return specs


def get_sub_agent_spec(
    name: str,
) -> SubAgentSpec:
    spec = SUB_AGENT_SPECS.get(name)

    if spec is None:
        raise ValueError(f"未知 Sub-Agent：{name}")

    validate_sub_agent_spec(spec)
    return spec
