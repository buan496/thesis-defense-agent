import json

from app.llm import chat_with_llm


def build_llm_query_rewrite_prompt(query: str) -> str:
    return f"""
你是一个 RAG 检索 query 改写器。请把用户问题改写成更适合检索论文内容的关键词查询。

要求：
1. 只改写检索 query，不要回答问题。
2. 保留用户问题的核心意图。
3. 可以补充论文检索中常见的专业关键词。
4. 不要编造不存在的事实、实验结果或数据。
5. 输出应尽量短，适合作为向量检索和 BM25 检索的 query。
6. 只输出 JSON，不要输出 Markdown。

JSON 格式：
{{
  "query": "改写后的检索 query"
}}

用户问题：
{query}
"""


def rewrite_query_with_llm(
    query: str,
    llm_fn=chat_with_llm,
) -> str:
    if not query.strip():
        raise ValueError("query cannot be empty")

    prompt = build_llm_query_rewrite_prompt(query)
    answer = llm_fn(prompt)
    data = _parse_rewrite_json(answer)

    rewritten_query = data["query"]

    if not isinstance(rewritten_query, str):
        raise ValueError("query字段必须是字符串")

    rewritten_query = " ".join(rewritten_query.split())

    if not rewritten_query:
        raise ValueError("query字段不能为空")

    return rewritten_query


def _parse_rewrite_json(text: str) -> dict:
    clean_text = _clean_json_text(text)
    data = json.loads(clean_text)

    if "query" not in data:
        raise ValueError("JSON中缺少'query'字段")

    return data


def _clean_json_text(text: str) -> str:
    text = text.strip()

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
