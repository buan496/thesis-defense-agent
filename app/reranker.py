import re


def tokenize_for_rerank(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text)


def rerank_results(
    query: str,
    results: list[dict],
    top_k: int,
) -> list[dict]:
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    if not results:
        return []

    query_tokens = set(tokenize_for_rerank(query))
    reranked_results = []

    for result in results:
        text = result.get("text", "")
        text_tokens = set(tokenize_for_rerank(text))

        keyword_hits = len(query_tokens & text_tokens)
        keyword_bonus = keyword_hits * 0.1

        section_bonus = 0.05 if ("第" in text and "章" in text) else 0.0
        short_penalty = 0.1 if len(text) < 20 else 0.0

        base_score = float(result.get("score", 0.0))
        rerank_score = (
            base_score
            + keyword_bonus
            + section_bonus
            - short_penalty
        )

        reranked_result = dict(result)
        reranked_result["rerank_score"] = rerank_score
        reranked_result["keyword_hits"] = keyword_hits

        reranked_results.append(reranked_result)

    reranked_results.sort(
        key=lambda item: item["rerank_score"],
        reverse=True,
    )

    return reranked_results[:top_k]
