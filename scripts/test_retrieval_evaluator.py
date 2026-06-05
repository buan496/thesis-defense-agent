from app.config import RAG_BENCHMARK_PATH, RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.retrieval_evaluator import evaluate_retrieval


report = evaluate_retrieval(
    benchmark_path=RAG_BENCHMARK_PATH,
    vector_store_path=RAG_VECTOR_STORE_PATH,
    top_k=RAG_TOP_K,
)

print(report["top_k"])
print(report["average_score"])

for item in report["results"]:
    print(item)