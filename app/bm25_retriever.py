import math
import re
from collections import Counter


def tokenize_for_bm25(text: str) -> list[str]:
    tokens = []

    for match in re.finditer(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", text):
        tokens.append(match.group(0).lower())

    return tokens


def calculate_document_frequencies(
    tokenized_documents: list[list[str]],
) -> dict[str, int]:
    document_frequencies = {}

    for tokens in tokenized_documents:
        for token in set(tokens):
            document_frequencies[token] = (
                document_frequencies.get(token, 0) + 1
            )

    return document_frequencies


def calculate_inverse_document_frequency(
    document_count: int,
    document_frequency: int,
) -> float:
    return math.log(
        1
        + (
            document_count - document_frequency + 0.5
        ) / (document_frequency + 0.5)
    )


def bm25_score(
    query_tokens: list[str],
    document_tokens: list[str],
    document_frequencies: dict[str, int],
    document_count: int,
    average_document_length: float,
    k1: float = 1.5,
    b: float = 0.75,
) -> float:
    if not query_tokens or not document_tokens:
        return 0.0

    term_frequencies = Counter(document_tokens)
    document_length = len(document_tokens)
    score = 0.0

    for token in query_tokens:
        term_frequency = term_frequencies.get(token, 0)

        if term_frequency == 0:
            continue

        document_frequency = document_frequencies.get(token, 0)
        idf = calculate_inverse_document_frequency(
            document_count,
            document_frequency,
        )
        denominator = (
            term_frequency
            + k1
            * (
                1
                - b
                + b
                * document_length
                / average_document_length
            )
        )
        score += idf * (
            term_frequency * (k1 + 1)
        ) / denominator

    return score


def build_bm25_index(
    store: list[dict],
) -> dict:
    tokenized_documents = [
        tokenize_for_bm25(item["text"])
        for item in store
    ]
    document_lengths = [
        len(tokens)
        for tokens in tokenized_documents
    ]
    document_count = len(store)
    average_document_length = (
        sum(document_lengths) / document_count
        if document_count
        else 0.0
    )

    return {
        "documents": store,
        "tokenized_documents": tokenized_documents,
        "document_frequencies": calculate_document_frequencies(
            tokenized_documents
        ),
        "document_count": document_count,
        "average_document_length": average_document_length,
    }


def search_bm25(
    query: str,
    store: list[dict],
    top_k: int = 3,
) -> list[dict]:
    index = build_bm25_index(store)

    if index["document_count"] == 0:
        return []

    query_tokens = tokenize_for_bm25(query)
    results = []

    for item, document_tokens in zip(
        index["documents"],
        index["tokenized_documents"],
    ):
        score = bm25_score(
            query_tokens=query_tokens,
            document_tokens=document_tokens,
            document_frequencies=index["document_frequencies"],
            document_count=index["document_count"],
            average_document_length=index["average_document_length"],
        )
        results.append(
            {
                "id": item["id"],
                "text": item["text"],
                "source": item["source"],
                "score": score,
            }
        )

    results.sort(key=lambda item: item["score"], reverse=True)

    return results[:top_k]
