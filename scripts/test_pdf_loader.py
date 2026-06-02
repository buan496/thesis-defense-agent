from app.pdf_loader import read_pdf_file

text = read_pdf_file("data/thesis.pdf")

print(text[:1000])