from app.llm import chat_with_llm
import json

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

def generate_questions_from_context(context: str) -> list[str]:
    user_message = f"""
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

    answer = chat_with_llm(user_message)
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