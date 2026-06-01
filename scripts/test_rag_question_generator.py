from app.vector_store_io import load_vector_store
from app.rag_question_generator import generate_rag_defense_questions


store = load_vector_store("data/vector_store.json")

query = "系统架构"

questions = generate_rag_defense_questions(
    query,
    store,
    top_k=3,
)

for index, question in enumerate(questions, start=1):
    print(f"{index}. {question}")