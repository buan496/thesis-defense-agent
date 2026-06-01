from app.document_loader import read_text_file
from app.text_splitter import split_text_with_metadata

file_path = "data/thesis.txt"

text = read_text_file(file_path)

chunks = split_text_with_metadata(
    text,
    source=file_path,
    chunk_size=20,
    overlap=10,
)

for chunk in chunks:
    print("ID:", chunk["id"])
    print("SOURCE:", chunk["source"])
    print("START:", chunk["start"])
    print("END:", chunk["end"])
    print("TEXT:", chunk["text"])
    print("-" * 40)
    
    
    