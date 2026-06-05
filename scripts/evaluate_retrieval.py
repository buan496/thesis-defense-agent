import json

from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.embeddings import create_embedding
from app.vector_store import search_vector_store
from app.vector_store_io import load_vector_store


store = load_vector_store(RAG_VECTOR_STORE_PATH)

with open("data/rag_benchmark.json", encoding="utf-8") as file:
    benchmark = json.loads(file.read())


def evaluate(top_k: int):
    scores = []

    for item in benchmark:
        query = item["query"]
        expected_keywords = item["expected_keywords"]

        results = search_vector_store(
            query,
            store,
            top_k=top_k,
            embedding_fn=create_embedding,
        )

        retrieved_text = "\n".join(result["text"] for result in results)

        hit_count = 0
        missing_keywords = []

        for keyword in expected_keywords:
            if isinstance(keyword, list):
                hit = any(option in retrieved_text for option in keyword)
                label = "/".join(keyword)
            else:
                hit = keyword in retrieved_text
                label = keyword

            if hit:
                hit_count += 1
            else:
                missing_keywords.append(label)

        score = hit_count / len(expected_keywords)
        scores.append(score)

        print("QUERY:", query)
        print("HIT:", hit_count, "/", len(expected_keywords))
        print("MISSING:", missing_keywords)
        print("SCORE:", score)
        print("-" * 40)

    average_score = sum(scores) / len(scores)
    print("TOP_K:", top_k)
    print("AVERAGE SCORE:", average_score)


evaluate(RAG_TOP_K)
