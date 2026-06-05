from pathlib import Path

from app.config import (
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_TOP_K,
    RAG_VECTOR_STORE_PATH,
)
from app.document_cleaner import remove_table_of_contents_lines
from app.document_loader import read_text_file
from app.embeddings import create_embedding
from app.rag import answer_with_context, build_context_from_results
from app.text_splitter import split_text_by_paragraphs_with_metadata
from app.vector_store import build_vector_store, search_vector_store
from app.vector_store_io import load_vector_store, save_vector_store


file_path = "data/thesis.txt"

if Path(RAG_VECTOR_STORE_PATH).exists():
    print("加载已有向量库")
    store = load_vector_store(RAG_VECTOR_STORE_PATH)
else:
    print("创建新的向量库")

    text = read_text_file(file_path)
    text = remove_table_of_contents_lines(text)

    chunks = split_text_by_paragraphs_with_metadata(
        text,
        source=file_path,
        chunk_size=RAG_CHUNK_SIZE,
        overlap=RAG_CHUNK_OVERLAP,
        min_chunk_size=RAG_MIN_CHUNK_SIZE,
    )

    store = build_vector_store(chunks, embedding_fn=create_embedding)
    save_vector_store(store, RAG_VECTOR_STORE_PATH)

question = "论文中的系统架构包括哪些模块？"

results = search_vector_store(
    question,
    store,
    top_k=RAG_TOP_K,
    embedding_fn=create_embedding,
)

context = build_context_from_results(results)

print("【检索到的上下文】：")
print(context[:1000])
print("-" * 40)

answer = answer_with_context(question, context)

print("【RAG回答】：")
print(answer)
