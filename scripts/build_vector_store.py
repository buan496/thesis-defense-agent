from app.pdf_loader import read_pdf_file
from app.document_cleaner import remove_table_of_contents_lines,remove_invalid_unicode,normalize_pdf_line_breaks
from app.text_splitter import split_text_by_paragraphs_with_metadata
from app.vector_store import build_vector_store
from app.vector_store_io import save_vector_store
from app.embeddings import create_embedding


file_path = "data/thesis.pdf"
store_path = "data/vector_store.json"

text = read_pdf_file(file_path)
text = remove_invalid_unicode(text)
text = normalize_pdf_line_breaks(text)
text = remove_table_of_contents_lines(text)

chunks = split_text_by_paragraphs_with_metadata(
    text,
    source=file_path,
    chunk_size=800,
    overlap=100,
    min_chunk_size=30,
)

print("chunk 数量:", len(chunks))

store = build_vector_store(chunks, embedding_fn=create_embedding)

save_vector_store(store, store_path)

print("向量库已保存:", store_path)