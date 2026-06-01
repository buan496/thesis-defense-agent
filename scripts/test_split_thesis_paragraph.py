from app.document_loader import read_text_file
from app.text_splitter import split_text_by_paragraphs_with_limit

file_path = "data/thesis.txt"

text = read_text_file(file_path)

chunks = split_text_by_paragraphs_with_limit(
    text,
    chunk_size=800,
    overlap=100,
)

for index, chunk in enumerate(chunks[:5]):
    print("ID:", index)
    print("TEXT:", chunk)
    print("-" * 40)