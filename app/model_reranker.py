import json

from app.llm import chat_with_llm


def build_rerank_prompt(query: str, candidate: dict) -> str:
    text = candidate.get("text", "")
    source = candidate.get("source", "")

    return f"""
你是一个 RAG 检索结果重排序器。请判断候选论文片段与用户问题的相关性。

要求：
1. 只根据用户问题和候选片段评分。
2. 分数范围是 0 到 1。
3. 1 表示候选片段能直接回答问题。
4. 0 表示候选片段与问题无关。
5. 只输出 JSON，不要输出 Markdown。

JSON 格式：
{{
  "score": 0.0,
  "reason": "简短说明"
}}

用户问题：
{query}

候选来源：
{source}

候选片段：
{text}
"""


def score_candidate_with_llm(
    query: str,
    candidate: dict,
    llm_fn=chat_with_llm,
) -> float:
    prompt = build_rerank_prompt(query, candidate)
    answer = llm_fn(prompt)
    data = _parse_score_json(answer)

    return _clamp_score(float(data["score"]))


def rerank_results_with_model(
    query: str,
    results: list[dict],
    top_k: int,
    scorer=score_candidate_with_llm,
) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    if not results:
        return []

    reranked_results = []

    for result in results:
        model_rerank_score = scorer(query, result)
        reranked_result = dict(result)
        reranked_result["model_rerank_score"] = model_rerank_score
        reranked_results.append(reranked_result)

    reranked_results.sort(
        key=lambda item: item["model_rerank_score"],
        reverse=True,
    )

    return reranked_results[:top_k]


def _parse_score_json(text: str) -> dict:
    clean_text = _clean_json_text(text)
    data = json.loads(clean_text)

    if "score" not in data:
        raise ValueError("JSON中缺少'score'字段")

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


def _clamp_score(score: float) -> float:
    if score < 0:
        return 0.0

    if score > 1:
        return 1.0

    return score
