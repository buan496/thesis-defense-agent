from app.document_loader import read_text_file

file_path = "data/thesis.txt"

thesis_summary = read_text_file(file_path)

print(thesis_summary)