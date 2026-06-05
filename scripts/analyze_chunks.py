from app.config import RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE, RAG_MIN_CHUNK_SIZE
from app.document_loader import read_text_file
from app.text_splitter import split_text_by_paragraphs_with_limit


file_path = "data/thesis.txt"

text = read_text_file(file_path)

chunks = split_text_by_paragraphs_with_limit(
    text,
    chunk_size=RAG_CHUNK_SIZE,
    overlap=RAG_CHUNK_OVERLAP,
    min_chunk_size=RAG_MIN_CHUNK_SIZE,
)

lengths = [len(chunk) for chunk in chunks]

print("chunk 数量:", len(chunks))
print("最短长度:", min(lengths))
print("最长长度:", max(lengths))
print("平均长度:", sum(lengths) / len(lengths))
