import json

from app.vector_store_io import load_vector_store
from app.vector_store import search_vector_store
from app.embeddings import create_embedding


store = load_vector_store("data/vector_store.json")

benchmark_text = open("data/rag_benchmark.json", encoding="utf-8").read()
benchmark = json.loads(benchmark_text)

def evaluate(top_k: int):
    scores = []

    for item in benchmark:
        query = item["query"]
        expected_keywords = item["expected_keywords"]

        results = search_vector_store(
            query,
            store,
            top_k = top_k,
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
        # if missing_keywords:
        #     print("RETRIEVED TEXT:")
        #     print(retrieved_text[:1500])
        print("SCORE:", score)
        print("-" * 40)

    average_score = sum(scores) / len(scores)
    print("TOP_K:", top_k)
    print("AVERAGE SCORE:", average_score)

# for top_k in [1, 3, 5]:
top_k = 3
evaluate(top_k)