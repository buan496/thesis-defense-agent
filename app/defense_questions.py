from app.llm import chat_with_llm
import json

from app.agent_models import TokenUsage
from app.config import (
    LLM_INPUT_PRICE_PER_1M_TOKENS,
    LLM_MAX_TOKENS,
    LLM_OUTPUT_PRICE_PER_1M_TOKENS,
    LLM_PRICE_CURRENCY,
    LLM_TEMPERATURE,
)
from app.cost_estimator import estimate_llm_cost
from app.llm import get_llm_client

def generate_defense_questions(thesis_summary: str) -> str:
    user_message = f"""
    
    请根据下面的论文简介，生成1个中文论文答辩问题。

    要求：
    1. 问题要选择研究背景、研究方法、创新点、实验验证、局限性其一来提问。
    2. 问题要像真实答辩老师会问的问题。
    3. 只输出问题列表，不要输出额外解释。
    4. 仅输出一句话的问题，不要输出多余的内容。
    {thesis_summary}
    """
    
    answer = chat_with_llm(user_message)
    return answer


def generate_defense_questions_json(thesis_summary: str) -> list[str]:
    user_message = f"""
    请根据论文简介生成 5 个中文论文答辩问题。

    要求：
    1. 只输出 JSON，不要输出 Markdown。
    2. 不要使用 ```json 代码块。
    3. JSON 格式必须如下：
    {{
    "questions": [
        "问题1",
        "问题2",
        "问题3",
        "问题4",
        "问题5"
    ]
    }}
    
    {thesis_summary}
    """
    answer = chat_with_llm(user_message)
    # print(f"【模型返回】：{answer}")
    clean_answer = _clean_json_text(answer)
    
    try:
        data = json.loads(clean_answer)
    except json.JSONDecodeError:
        print("模型返回的不是合法的JSON")
        print(answer)
        raise
    
    if "questions" not in data:
        raise ValueError("JSON中缺少'questions'字段")
    
    if not isinstance(data["questions"], list):
        raise ValueError("questions字段必须是列表")

    if len(data["questions"]) == 0:
        raise ValueError("questions列表不能为空")
    
    return data["questions"]


def _clean_json_text(text: str) -> str:
    text = text.strip()
    # text = text.replace("“", "\"").replace("”", "\"")

    if text.startswith("```json"):
        text = text.removeprefix("```json")
        text = text.removesuffix("```")
        text = text.strip()

    if text.startswith("```"):
        text = text.removeprefix("```")
        text = text.removesuffix("```")
        text = text.strip()
        
    start = text.find("{")
    end = text.rfind("}")
    
    if start != -1 and end != -1:
        text = text[start:end + 1]

    return text

def build_questions_from_context_prompt(context: str) -> str:
    return f"""
请根据下面的论文片段生成 5 个中文论文答辩问题。

要求：
1. 问题必须基于论文片段内容，不要引入片段外的信息。
2. 问题要像真实答辩老师会问的问题。
3. 问题应覆盖系统架构、方法设计、实验验证、局限性、实现细节等角度。
4. 只输出 JSON，不要输出 Markdown。
5. 不要使用 ```json 代码块。
6. JSON 格式必须如下：
{{
    "questions": [
        "问题1",
        "问题2",
        "问题3",
        "问题4",
        "问题5"
    ]
}}

论文片段：
{context}
"""


def parse_questions_json(answer: str) -> list[str]:
    clean_answer = _clean_json_text(answer)

    try:
        data = json.loads(clean_answer)
    except json.JSONDecodeError:
        print("模型返回的不是合法的JSON")
        print(answer)
        raise

    if "questions" not in data:
        raise ValueError("JSON中缺少'questions'字段")

    if not isinstance(data["questions"], list):
        raise ValueError("questions字段必须是列表")

    if len(data["questions"]) == 0:
        raise ValueError("questions列表不能为空")

    return data["questions"]


def generate_questions_from_context(context: str) -> list[str]:
    user_message = build_questions_from_context_prompt(context)

    answer = chat_with_llm(user_message)
    return parse_questions_json(answer)


def extract_token_usage_from_response(response) -> TokenUsage:
    usage = getattr(response, "usage", None)

    if usage is None:
        return TokenUsage()

    return TokenUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", 0) or 0,
        completion_tokens=getattr(usage, "completion_tokens", 0) or 0,
        total_tokens=getattr(usage, "total_tokens", 0) or 0,
    )


def generate_questions_from_context_with_audit(
    context: str,
) -> dict:
    user_message = build_questions_from_context_prompt(context)
    client, model = get_llm_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": user_message,
            },
        ],
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    answer = response.choices[0].message.content
    questions = parse_questions_json(answer)
    token_usage = extract_token_usage_from_response(response)
    cost_estimate = estimate_llm_cost(
        token_usage=token_usage,
        input_price_per_1m_tokens=LLM_INPUT_PRICE_PER_1M_TOKENS,
        output_price_per_1m_tokens=LLM_OUTPUT_PRICE_PER_1M_TOKENS,
        currency=LLM_PRICE_CURRENCY,
    )

    return {
        "questions": questions,
        "token_usage": {
            "prompt_tokens": token_usage.prompt_tokens,
            "completion_tokens": token_usage.completion_tokens,
            "total_tokens": token_usage.total_tokens,
        },
        "cost_estimate": {
            "input_cost": cost_estimate.input_cost,
            "output_cost": cost_estimate.output_cost,
            "total_cost": cost_estimate.total_cost,
            "currency": cost_estimate.currency,
        },
    }
