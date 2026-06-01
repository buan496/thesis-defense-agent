from pathlib import Path

from app.vector_store_io import load_vector_store
from app.vector_store import search_vector_store
from app.embeddings import create_embedding
from app.rag import build_context_from_results
from app.defense_questions import generate_questions_from_context


store = load_vector_store("data/vector_store.json")

query = "论文中的系统架构包括哪些模块？"

results = search_vector_store(
    query,
    store,
    top_k=3,
    embedding_fn=create_embedding,
)

context = build_context_from_results(results)

questions = generate_questions_from_context(context)

for index, question in enumerate(questions, start=1):
    print(f"{index}. {question}")