from app.config import RAG_TOP_K, RAG_VECTOR_STORE_PATH
from app.rag_question_generator import generate_rag_defense_questions
from app.vector_store_io import load_vector_store


store = load_vector_store(RAG_VECTOR_STORE_PATH)

query = "系统架构"

questions = generate_rag_defense_questions(
    query,
    store,
    top_k=RAG_TOP_K,
)

for index, question in enumerate(questions, start=1):
    print(f"{index}. {question}")
