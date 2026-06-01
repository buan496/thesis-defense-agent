from pathlib import Path

from app.document_loader import read_text_file
from app.text_splitter import split_text_by_paragraphs_with_metadata
from app.vector_store import build_vector_store, search_vector_store
from app.vector_store_io import save_vector_store, load_vector_store
from app.document_cleaner import remove_table_of_contents_lines
from app.embeddings import create_embedding


file_path = "data/thesis.txt"
store_path = "data/vector_store.json"

if Path(store_path).exists():
    print("加载已有向量库")
    store = load_vector_store(store_path)
else:
    print("创建新的向量库")

    text = read_text_file(file_path)
    text = remove_table_of_contents_lines(text)
    
    chunks = split_text_by_paragraphs_with_metadata(
        text,
        source=file_path,
        chunk_size=800,
        overlap=100,
        min_chunk_size=30,
    )

    store = build_vector_store(chunks, embedding_fn=create_embedding)

    save_vector_store(store, store_path)

query = "论文中的系统架构包括哪些模块？"

results = search_vector_store(
    query,
    store,
    top_k=3,
    embedding_fn=create_embedding,
)

for result in results:
    print("ID:", result["id"])
    print("SCORE:", result["score"])
    print("SOURCE:", result["source"])
    print("TEXT:", result["text"][:300])
    print("-" * 40)