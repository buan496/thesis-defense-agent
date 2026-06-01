from app.embeddings import create_embedding
from app.vector_store import search_vector_store
from app.rag import build_context_from_results
from app.defense_questions import generate_questions_from_context


def generate_rag_defense_questions(
    query: str,
    store: list[dict],
    top_k: int = 3,
) -> list[str]:
    results = search_vector_store(
        query,
        store,
        top_k=top_k,
        embedding_fn=create_embedding,
    )

    context = build_context_from_results(results)

    questions = generate_questions_from_context(context)

    return questions

def generate_rag_defense_questions_with_context(
    query: str,
    store: list[dict],
    top_k: int = 3,
) -> tuple[list[str], str]:
    results = search_vector_store(
        query,
        store,
        top_k=top_k,
        embedding_fn=create_embedding,
    )

    context = build_context_from_results(results)

    questions = generate_questions_from_context(context)

    return questions, context