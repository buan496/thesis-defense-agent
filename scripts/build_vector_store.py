from app.config import (
    RAG_CHUNK_OVERLAP,
    RAG_CHUNK_SIZE,
    RAG_MIN_CHUNK_SIZE,
    RAG_VECTOR_STORE_PATH,
)
from app.document_cleaner import (
    normalize_pdf_line_breaks,
    remove_invalid_unicode,
    remove_table_of_contents_lines,
)
from app.embeddings import create_embedding
from app.pdf_loader import read_pdf_file
from app.text_splitter import split_text_by_paragraphs_with_metadata
from app.vector_store import build_vector_store
from app.vector_store_io import save_vector_store


file_path = "data/thesis.pdf"

text = read_pdf_file(file_path)
text = remove_invalid_unicode(text)
text = normalize_pdf_line_breaks(text)
text = remove_table_of_contents_lines(text)

chunks = split_text_by_paragraphs_with_metadata(
    text,
    source=file_path,
    chunk_size=RAG_CHUNK_SIZE,
    overlap=RAG_CHUNK_OVERLAP,
    min_chunk_size=RAG_MIN_CHUNK_SIZE,
)

print("chunk 数量:", len(chunks))

store = build_vector_store(chunks, embedding_fn=create_embedding)

save_vector_store(store, RAG_VECTOR_STORE_PATH)

print("向量库已保存:", RAG_VECTOR_STORE_PATH)
